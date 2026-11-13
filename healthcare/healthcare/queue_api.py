"""Queue helpers for Internal Orientation and Queue.

Every function that changes a queue entry takes a database lock first, so two users working at the
same moment can never get the same counter or call the same patient.
"""
import hashlib

import frappe
from frappe import _
from frappe.utils import cint, getdate, now_datetime, today

OPEN_STATUSES = ("Waiting", "In Service")


def _counter_key(service_unit, queue_date):
	digest = hashlib.md5(str(service_unit).encode("utf-8")).hexdigest()[:12]
	return f"QUEUE-{getdate(queue_date or today())}-{digest}"


def take_counter(service_unit, queue_date=None):
	"""Return the next counter for a service unit and day, with no duplicates.

	The counter row is locked (SELECT ... FOR UPDATE) until the request commits, so a second request
	for the same unit and day waits and then continues from the committed value.
	"""
	key = _counter_key(service_unit, queue_date)
	for _attempt in range(3):
		row = frappe.db.sql("select `current` from `tabSeries` where `name` = %s for update", (key,))
		if row:
			frappe.db.sql("update `tabSeries` set `current` = `current` + 1 where `name` = %s", (key,))
			return cint(row[0][0]) + 1
		try:
			frappe.db.sql("insert into `tabSeries` (`name`, `current`) values (%s, 1)", (key,))
			return 1
		except Exception as e:
			# 1062 = duplicate entry: another request created the row first, so lock it and retry
			if not (getattr(e, "args", None) and e.args[0] == 1062):
				raise
	frappe.throw(_("Could not assign a queue counter. Please try again."), title=_("Queue"))


def create_queue_entry(patient, service_unit, queue_date=None, priority=None, internal_orientation=None):
	entry = frappe.new_doc("Queue")
	entry.patient = patient
	entry.service_unit = service_unit
	entry.queue_date = getdate(queue_date or today())
	entry.priority = priority
	entry.internal_orientation = internal_orientation
	entry.flags.from_orientation = True
	entry.insert(ignore_permissions=True)
	return entry


def get_open_entries(patient, service_unit, queue_date=None, lock=True):
	"""Waiting or In Service entries for a patient at a unit on a day (latest committed data)."""
	statuses = ", ".join(["%s"] * len(OPEN_STATUSES))
	query = f"""
		select name from `tabQueue`
		where patient = %s and service_unit = %s and queue_date = %s
			and status in ({statuses})
	"""
	if lock:
		query += " for update"
	params = (patient, service_unit, getdate(queue_date or today()), *OPEN_STATUSES)
	return [r[0] for r in frappe.db.sql(query, params)]


def complete_open_entries(patient, service_unit, queue_date=None):
	"""Close the patient's open entries at the unit they are leaving."""
	for name in get_open_entries(patient, service_unit, queue_date):
		frappe.db.set_value(
			"Queue",
			name,
			{"status": "Completed", "completed_at": now_datetime()},
			update_modified=True,
		)


def _locked_status(name):
	row = frappe.db.sql("select `status` from `tabQueue` where `name` = %s for update", (name,))
	if not row:
		frappe.throw(_("Queue entry {0} was not found.").format(name), title=_("Queue"))
	return row[0][0]


def cancel_queue_entry(name):
	"""Cancel an entry that has not been called yet."""
	if not name:
		return
	status = _locked_status(name)
	if status == "Cancelled":
		return
	if status != "Waiting":
		frappe.throw(
			_("Queue entry {0} is already {1} and cannot be cancelled.").format(name, status),
			title=_("Queue"),
		)
	frappe.db.set_value("Queue", name, "status", "Cancelled")


@frappe.whitelist()
def proceed(queue):
	"""Call the patient: Waiting -> In Service. Only one user can succeed."""
	frappe.has_permission("Queue", "write", doc=queue, throw=True)
	status = _locked_status(queue)
	if status != "Waiting":
		frappe.throw(
			_("This patient is already {0}.").format(status),
			title=_("Queue"),
		)
	frappe.db.set_value(
		"Queue",
		queue,
		{"status": "In Service", "called_at": now_datetime(), "called_by": frappe.session.user},
	)
	return frappe.db.get_value("Queue", queue, ["name", "patient", "service_unit", "counter"], as_dict=True)


@frappe.whitelist()
def complete(queue):
	frappe.has_permission("Queue", "write", doc=queue, throw=True)
	status = _locked_status(queue)
	if status != "In Service":
		frappe.throw(_("Only a patient who is In Service can be completed."), title=_("Queue"))
	frappe.db.set_value("Queue", queue, {"status": "Completed", "completed_at": now_datetime()})


@frappe.whitelist()
def get_or_create_encounter(queue):
	"""Return the consultation (Patient Encounter) for a Queue entry, creating it once.

	Created on the server so it is always linked to its Queue entry, and the entry is locked so two
	clicks can never create two encounters. The doctor is the Healthcare Practitioner linked to the
	user who calls the patient.
	"""
	frappe.has_permission("Queue", "write", doc=queue, throw=True)
	frappe.has_permission("Patient Encounter", "create", throw=True)

	rows = frappe.db.sql(
		"select `patient`, `service_unit`, `queue_date`, `status` from `tabQueue` where `name` = %s for update",
		(queue,),
		as_dict=True,
	)
	if not rows:
		frappe.throw(_("Queue entry {0} was not found.").format(queue), title=_("Queue"))
	entry = rows[0]
	if entry.status != "In Service":
		frappe.throw(_("Call the patient first (status must be In Service)."), title=_("Queue"))

	# Locking read, so a click that waited for the lock sees the encounter the first click created.
	existing = frappe.db.sql(
		"select `name` from `tabPatient Encounter` where `rw_queue` = %s and `docstatus` < 2 limit 1 for update",
		(queue,),
	)
	if existing:
		return existing[0][0]

	practitioner = frappe.db.get_value(
		"Healthcare Practitioner", {"user_id": frappe.session.user, "status": "Active"}, "name"
	)
	if not practitioner:
		frappe.throw(
			_(
				"Your user is not linked to an active Healthcare Practitioner, so a consultation cannot be "
				"opened. Ask an administrator to link your user to a practitioner."
			),
			title=_("Queue"),
		)

	company = frappe.db.get_value("Healthcare Service Unit", entry.service_unit, "company")
	if not company:
		company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
			"Global Defaults", "default_company"
		)

	from healthcare.healthcare.rwanda_consultation import set_consultation_status

	now = now_datetime()
	encounter = frappe.new_doc("Patient Encounter")
	encounter.patient = entry.patient
	encounter.practitioner = practitioner
	encounter.company = company
	encounter.encounter_date = entry.queue_date
	encounter.encounter_time = now.time()
	encounter.rw_queue = queue
	# Calling the patient is what unlocks the clinical fields, so the visit starts in consultation.
	set_consultation_status(encounter, "In Progress")
	encounter.rw_consultation_started_at = now
	encounter.insert(ignore_permissions=True)
	return encounter.name


def complete_for_encounter(encounter):
	"""Close the Queue entry a consultation was opened from, once the consultation is finished.

	Does nothing if the encounter has no queue entry, or the entry is already closed (for example
	because the patient was already oriented onward, which completes it).
	"""
	queue = frappe.db.get_value("Patient Encounter", encounter, "rw_queue")
	if not queue:
		return
	if _locked_status(queue) == "In Service":
		frappe.db.set_value("Queue", queue, {"status": "Completed", "completed_at": now_datetime()})


@frappe.whitelist()
def mark_no_show(queue):
	frappe.has_permission("Queue", "write", doc=queue, throw=True)
	status = _locked_status(queue)
	if status != "Waiting":
		frappe.throw(_("Only a waiting patient can be marked as no-show."), title=_("Queue"))
	frappe.db.set_value("Queue", queue, {"status": "No Show", "completed_at": now_datetime()})
