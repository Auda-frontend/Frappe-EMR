# -*- coding: utf-8 -*-
# Consultation dashboard API, workflow transitions, and follow-up automation.

import json

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, now_datetime, today

CONSULTATION_STATUSES = ("Draft", "In Progress", "Completed", "Follow-up", "Cancelled")

STATUS_COLORS = {
	"Draft": "grey",
	"In Progress": "blue",
	"Completed": "green",
	"Follow-up": "orange",
	"Cancelled": "red",
}

RW_STATUS_MAP = {
	"Draft": "Waiting",
	"In Progress": "In Consultation",
	"Completed": "Completed",
	"Follow-up": "Completed",
	"Cancelled": "Cancelled",
}


@frappe.whitelist()
def get_consultation_stats():
	"""Dashboard KPI cards for Patient Encounter consultations."""
	frappe.has_permission("Patient Encounter", "read", throw=True)
	base_filters = {"docstatus": ["<", 2]}
	stats = {"total": frappe.db.count("Patient Encounter", base_filters)}
	for status in CONSULTATION_STATUSES:
		key = status.lower().replace(" ", "_").replace("-", "_")
		stats[key] = frappe.db.count(
			"Patient Encounter", {**base_filters, "consultation_status": status}
		)
	stats["overdue_follow_up"] = len(get_overdue_follow_up_records())
	return stats


@frappe.whitelist()
def get_follow_up_overdue():
	frappe.has_permission("Patient Encounter", "read", throw=True)
	return get_overdue_follow_up_records()


def get_overdue_follow_up_records():
	today_date = today()
	return frappe.get_all(
		"Patient Encounter",
		filters={
			"docstatus": ["<", 2],
			"rw_follow_up_required": 1,
			"rw_follow_up_date": ["<", today_date],
			"consultation_status": ["in", ["Follow-up", "In Progress", "Draft"]],
		},
		fields=[
			"name",
			"title",
			"patient",
			"patient_name",
			"practitioner",
			"practitioner_name",
			"rw_follow_up_date",
			"consultation_status",
		],
		order_by="rw_follow_up_date asc",
		limit=100,
	)


@frappe.whitelist()
def get_recent_consultations(limit=10):
	frappe.has_permission("Patient Encounter", "read", throw=True)
	return frappe.get_all(
		"Patient Encounter",
		filters={"docstatus": ["<", 2]},
		fields=[
			"name",
			"title",
			"patient_name",
			"consultation_status",
			"encounter_date",
			"practitioner_name",
			"rw_follow_up_date",
			"rw_follow_up_required",
		],
		order_by="modified desc",
		limit=cint(limit),
	)


@frappe.whitelist()
def get_consultation_timeline(encounter):
	frappe.has_permission("Patient Encounter", "read", doc=encounter, throw=True)
	comments = frappe.get_all(
		"Comment",
		filters={"reference_doctype": "Patient Encounter", "reference_name": encounter},
		fields=["content", "creation", "owner", "comment_type"],
		order_by="creation desc",
		limit=50,
	)
	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Patient Encounter", "docname": encounter},
		fields=["data", "modified", "owner"],
		order_by="modified desc",
		limit=20,
	)
	timeline = []
	for version in versions:
		changes = _summarize_version_data(version.data)
		if changes:
			timeline.append(
				{
					"type": "version",
					"when": version.modified,
					"who": version.owner,
					"summary": changes,
				}
			)
	for comment in comments:
		timeline.append(
			{
				"type": "comment",
				"when": comment.creation,
				"who": comment.owner,
				"summary": comment.content,
				"comment_type": comment.comment_type,
			}
		)
	timeline.sort(key=lambda row: row["when"], reverse=True)
	return timeline[:30]


@frappe.whitelist()
def get_status_distribution():
	frappe.has_permission("Patient Encounter", "read", throw=True)
	total = frappe.db.count("Patient Encounter", {"docstatus": ["<", 2]}) or 1
	rows = frappe.db.sql(
		"""
		select consultation_status as status, count(*) as count
		from `tabPatient Encounter`
		where docstatus < 2 and ifnull(consultation_status, '') != ''
		group by consultation_status
		""",
		as_dict=True,
	)
	for row in rows:
		row["percentage"] = round((row.count * 100.0) / total, 1)
	return rows


@frappe.whitelist()
def get_monthly_trend(months=6):
	frappe.has_permission("Patient Encounter", "read", throw=True)
	return frappe.db.sql(
		"""
		select date_format(encounter_date, '%%Y-%%m') as month,
			count(*) as count
		from `tabPatient Encounter`
		where docstatus < 2
			and encounter_date >= date_sub(curdate(), interval %s month)
		group by date_format(encounter_date, '%%Y-%%m')
		order by month asc
		""",
		(cint(months),),
		as_dict=True,
	)


@frappe.whitelist()
def schedule_follow_up(encounter, follow_up_date=None, follow_up_notes=None):
	"""In Progress → Follow-up."""
	doc = _get_encounter(encounter, "write")
	if doc.consultation_status not in ("In Progress", "Draft"):
		frappe.throw(_("Follow-up can only be scheduled from Draft or In Progress."), title=_("Follow-up"))

	if not follow_up_date and not doc.rw_follow_up_date:
		frappe.throw(_("Follow-up date is required."), title=_("Follow-up"))

	doc.rw_follow_up_required = 1
	if follow_up_date:
		doc.rw_follow_up_date = follow_up_date
	if follow_up_notes:
		doc.rw_follow_up_notes = follow_up_notes
	doc.consultation_status = "Follow-up"
	doc.rw_opd_visit_status = RW_STATUS_MAP["Follow-up"]
	doc.save()
	_notify_status_change(doc, "Follow-up scheduled")
	return {"name": doc.name, "consultation_status": doc.consultation_status}


@frappe.whitelist()
def complete_follow_up(encounter):
	"""Follow-up → Completed."""
	doc = _get_encounter(encounter, "write")
	if doc.consultation_status != "Follow-up":
		frappe.throw(_("Only consultations in Follow-up status can be completed."), title=_("Follow-up"))

	doc.consultation_status = "Completed"
	doc.rw_opd_visit_status = "Completed"
	doc.rw_visit_completed_at = doc.rw_visit_completed_at or now_datetime()
	doc.save()
	_notify_status_change(doc, "Follow-up completed")
	return {"name": doc.name, "consultation_status": doc.consultation_status}


@frappe.whitelist()
def cancel_consultation(encounter, reason=None):
	"""Any → Cancelled (System Manager only)."""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only System Manager can cancel a consultation."), title=_("Permission"))

	doc = _get_encounter(encounter, "write")
	doc.consultation_status = "Cancelled"
	doc.rw_opd_visit_status = "Cancelled"
	if reason:
		doc.add_comment("Info", _("Consultation cancelled: {0}").format(reason))
	doc.save()
	_notify_status_change(doc, "Cancelled")
	return {"name": doc.name, "consultation_status": doc.consultation_status}


def send_follow_up_reminders():
	"""Daily scheduled job — email reminders at 7, 3, 1, and 0 days before follow-up."""
	today_date = getdate(today())
	encounters = frappe.get_all(
		"Patient Encounter",
		filters={
			"docstatus": ["<", 2],
			"rw_follow_up_required": 1,
			"consultation_status": ["in", ["Follow-up", "In Progress"]],
			"rw_follow_up_date": ["is", "set"],
		},
		fields=[
			"name",
			"title",
			"patient_name",
			"practitioner",
			"practitioner_name",
			"rw_follow_up_date",
			"rw_follow_up_notes",
		],
	)

	for enc in encounters:
		days_remaining = (getdate(enc.rw_follow_up_date) - today_date).days
		if days_remaining not in (7, 3, 1, 0):
			continue
		_send_follow_up_email(enc, days_remaining)


def on_consultation_update(doc, method=None):
	if doc.doctype != "Patient Encounter":
		return
	previous = doc.get_doc_before_save()
	if not previous or previous.consultation_status == doc.consultation_status:
		return
	_notify_status_change(doc, doc.consultation_status)


def _get_encounter(name, perm="read"):
	frappe.has_permission("Patient Encounter", perm, doc=name, throw=True)
	return frappe.get_doc("Patient Encounter", name)


def _notify_status_change(doc, status_label):
	user = frappe.db.get_value("Healthcare Practitioner", doc.practitioner, "user_id")
	if not user:
		return
	frappe.publish_realtime(
		"consultation_status_update",
		{
			"message": _("Consultation '{0}' — {1}").format(doc.title or doc.name, status_label),
			"docname": doc.name,
			"status": doc.consultation_status,
		},
		user=user,
	)


def _send_follow_up_email(enc, days_remaining):
	practitioner_user = frappe.db.get_value("Healthcare Practitioner", enc.practitioner, "user_id")
	if not practitioner_user:
		return
	email = frappe.db.get_value("User", practitioner_user, "email")
	if not email:
		return

	subject = _("Follow-up reminder: {0}").format(enc.title or enc.name)
	if days_remaining == 0:
		body = _("Follow-up for {0} is due today.").format(enc.patient_name)
	elif days_remaining < 0:
		body = _("Follow-up for {0} is overdue.").format(enc.patient_name)
	else:
		body = _("Follow-up for {0} is due in {1} day(s).").format(enc.patient_name, days_remaining)

	if enc.rw_follow_up_notes:
		body += f"\n\n{enc.rw_follow_up_notes}"

	frappe.sendmail(recipients=[email], subject=subject, message=body, now=True)


def _summarize_version_data(data):
	if not data:
		return ""
	try:
		payload = json.loads(data) if isinstance(data, str) else data
	except (TypeError, json.JSONDecodeError):
		return _("Record updated")

	changed = payload.get("changed") or []
	if not changed:
		return _("Record updated")

	parts = []
	for row in changed[:5]:
		if len(row) >= 3:
			parts.append(f"{row[0]}: {row[1]} → {row[2]}")
		elif len(row) >= 2:
			parts.append(f"{row[0]}: {row[1]}")
	return "; ".join(parts) if parts else _("Record updated")


def cint(val):
	from frappe.utils import cint as _cint

	return _cint(val)
