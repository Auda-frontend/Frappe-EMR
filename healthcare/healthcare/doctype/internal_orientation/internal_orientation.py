import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

from healthcare.healthcare.queue_api import cancel_queue_entry, complete_open_entries, create_queue_entry
from healthcare.healthcare.rwanda_triage.scoring import map_triage_color_to_opd_priority

PRIORITIES = ("Emergency", "Urgent", "Non-urgent", "Routine")


class InternalOrientation(Document):
	def validate(self):
		self.attach_open_assessment()
		self.apply_triage_assessment()
		if self.orientation_from == self.orientation_to:
			frappe.throw(_("Orientation From and Orientation To must be different."), title=_("Orientation"))
		for fieldname in ("orientation_from", "orientation_to"):
			unit = self.get(fieldname)
			if unit and frappe.db.get_value("Healthcare Service Unit", unit, "is_group"):
				frappe.throw(
					_("{0} is a group. Choose a service unit where patients are seen.").format(unit),
					title=_("Orientation"),
				)

	def attach_open_assessment(self):
		"""A draft orientation picks up the patient's triage assessment for the day, whichever way it was opened."""
		if self.docstatus != 0 or self.triage_assessment or not self.patient:
			return
		found = find_open_assessment(self.patient, self.date)
		if found:
			self.triage_assessment = found.name

	def apply_triage_assessment(self):
		"""When oriented from a Triage Assessment, the priority is the triage colour, not what was typed."""
		if not self.triage_assessment:
			return
		ta = frappe.db.get_value(
			"Triage Assessment",
			self.triage_assessment,
			["patient", "docstatus", "triage_color"],
			as_dict=True,
		)
		if not ta:
			frappe.throw(_("Triage Assessment {0} was not found.").format(self.triage_assessment), title=_("Orientation"))
		if ta.docstatus != 1:
			frappe.throw(_("Submit the Triage Assessment before orienting the patient."), title=_("Orientation"))
		if ta.patient != self.patient:
			frappe.throw(_("This Triage Assessment belongs to another patient."), title=_("Orientation"))
		if not ta.triage_color:
			frappe.throw(_("The Triage Assessment has no triage colour."), title=_("Orientation"))

		other = frappe.db.get_value(
			"Internal Orientation",
			{"triage_assessment": self.triage_assessment, "docstatus": ["<", 2], "name": ["!=", self.name or ""]},
			"name",
		)
		if other:
			frappe.throw(
				_("This patient was already oriented from this assessment ({0}).").format(other),
				title=_("Orientation"),
			)

		priority = map_triage_color_to_opd_priority(ta.triage_color)
		if priority not in PRIORITIES:
			frappe.throw(
				_("Triage colour {0} has no matching queue priority.").format(ta.triage_color),
				title=_("Orientation"),
			)
		self.priority = priority

	def on_submit(self):
		# The patient leaves the unit they came from and joins the queue of the unit they go to.
		complete_open_entries(self.patient, self.orientation_from, self.date)
		entry = create_queue_entry(
			patient=self.patient,
			service_unit=self.orientation_to,
			queue_date=self.date,
			priority=self.priority,
			internal_orientation=self.name,
		)
		self.db_set("queue", entry.name)
		if self.triage_assessment:
			frappe.db.set_value("Triage Assessment", self.triage_assessment, "patient_oriented", 1, update_modified=False)

	def on_cancel(self):
		cancel_queue_entry(self.queue)
		if self.triage_assessment:
			frappe.db.set_value("Triage Assessment", self.triage_assessment, "patient_oriented", 0, update_modified=False)


def find_open_assessment(patient, date=None):
	"""The patient's latest submitted Triage Assessment for the day that has not been used for an orientation."""
	day = getdate(date or today())
	rows = frappe.get_all(
		"Triage Assessment",
		filters={"patient": patient, "docstatus": 1},
		fields=["name", "triage_color", "arrival_date", "creation", "patient_oriented"],
		order_by="creation desc",
		limit=20,
	)
	for row in rows:
		visit_day = getdate(row.arrival_date) if row.arrival_date else getdate(row.creation)
		if visit_day != day or not row.triage_color or row.patient_oriented:
			continue
		if frappe.db.exists("Internal Orientation", {"triage_assessment": row.name, "docstatus": ["<", 2]}):
			continue
		return row
	return None


@frappe.whitelist()
def get_open_assessment(patient, date=None):
	"""For the orientation form: the assessment that will be attached, and the priority it gives."""
	frappe.has_permission("Internal Orientation", "create", throw=True)
	row = find_open_assessment(patient, date)
	if not row:
		return None
	return {
		"name": row.name,
		"triage_color": row.triage_color,
		"priority": map_triage_color_to_opd_priority(row.triage_color),
	}
