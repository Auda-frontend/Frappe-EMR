# -*- coding: utf-8 -*-
# Rwanda OPD consultation form (Patient Encounter) — fields, validation, desk UX.

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import flt, getdate, today

from healthcare.healthcare.consultation_api import CONSULTATION_STATUSES, RW_STATUS_MAP

VISIT_OUTCOMES = (
	"Discharged home",
	"Follow-up required",
	"Referred out",
	"Admitted",
	"Left without being seen",
	"Deceased",
	"Other",
)

# Core Marley fields hidden or de-emphasized on the Rwanda consultation form.
CONSULTATION_HIDDEN_FIELDS = (
	"google_meet_link",
	"get_applicable_treatment_plans",
	"submit_orders_on_save",
	"therapy_plan",
	"rehabilitation_section",
	"therapies",
	"custom_patient_details",
	"rw_opd_sb",
	"rw_tab_visit",
	"rw_opd_visit_status",
	"rw_visit_type",
	"rw_oriented_service",
	"rw_patient_upid",
	"rw_patient_nin",
	"rw_queue_number",
	"rw_oriented_department",
	"rw_col_opd",
	"rw_hmis_origin",
	"rw_service_point",
	"rw_col_visit",
	"rw_triage",
	"rw_triage_category",
	"rw_oriented_at",
	"rw_triaged_at",
	"rw_consultation_started_at",
	"rw_visit_completed_at",
	"rw_triage_vitals_html",
	"rw_insurance_sb",
	"rw_insurance_provider",
	"rw_insurance_member_number",
	"rw_patient_insured",
	"rw_chief_complaint",
	"rw_tab_medical_history",
	"rw_allergies",
	"rw_current_medication",
	"rw_col_hist",
	"rw_past_medical_history",
	"rw_surgical_history",
	"rw_risk_sb",
	"rw_tobacco_past_use",
	"rw_tobacco_current_use",
	"rw_alcohol_past_use",
	"rw_alcohol_current_use",
	"rw_other_risk_factors",
	"rw_tab_consultation",
	"rw_tab_orders",
	"rw_tab_discharge",
)


def install_rwanda_consultation():
	create_custom_fields(get_rwanda_consultation_custom_fields(), update=True)
	apply_consultation_form_labels()
	reposition_follow_up_fields()
	hide_consultation_clutter_fields()
	backfill_consultation_status()
	frappe.clear_cache()


def get_rwanda_consultation_custom_fields():
	return {
		"Patient Encounter": get_consultation_encounter_fields(),
	}


def get_consultation_encounter_fields():
	return [
		# --- Status & workflow (Details tab) ---
		{
			"fieldname": "consultation_status",
			"fieldtype": "Select",
			"label": "Consultation Status",
			"options": "\n".join(CONSULTATION_STATUSES),
			"default": "Draft",
			"insert_after": "tab_consultation",
			"in_list_view": 1,
			"in_standard_filter": 1,
			"read_only": 1,
		},
		{
			"fieldname": "consultation_duration",
			"fieldtype": "Duration",
			"label": "Duration",
			"insert_after": "consultation_status",
		},
		{
			"fieldname": "consultation_notes",
			"fieldtype": "Text Editor",
			"label": "Consultation Notes",
			"insert_after": "consultation_duration",
		},
		{
			"fieldname": "consultation_items_total",
			"fieldtype": "Currency",
			"label": "Items Total",
			"insert_after": "consultation_notes",
			"read_only": 1,
		},
		{
			"fieldname": "rw_follow_up_indicator_html",
			"fieldtype": "HTML",
			"label": "Follow-up Indicator",
			"insert_after": "consultation_items_total",
		},
		# --- Clinical narrative ---
		{
			"fieldname": "rw_history_present_illness",
			"fieldtype": "Text Editor",
			"label": "History of present illness (HPI)",
			"insert_after": "rw_follow_up_indicator_html",
		},
		{
			"fieldname": "rw_physical_examination_notes",
			"fieldtype": "Text Editor",
			"label": "Physical examination",
			"insert_after": "rw_history_present_illness",
		},
		{
			"fieldname": "rw_clinical_impression",
			"fieldtype": "Small Text",
			"label": "Clinical impression",
			"insert_after": "rw_physical_examination_notes",
		},
		{
			"fieldname": "rw_diagnosis_help",
			"fieldtype": "HTML",
			"options": (
				'<p class="text-muted small">'
				"<b>Diagnosis is mandatory</b> before submitting this consultation. "
				"Add at least one diagnosis below (ICD / facility diagnosis list)."
				"</p>"
			),
			"insert_after": "rw_clinical_impression",
		},
		# --- Items tab ---
		{
			"fieldname": "rw_tab_items",
			"fieldtype": "Tab Break",
			"label": "Items",
			"insert_after": "rw_diagnosis_help",
		},
		{
			"fieldname": "consultation_items",
			"fieldtype": "Table",
			"label": "Consultation Items",
			"options": "Encounter Consultation Item",
			"insert_after": "rw_tab_items",
		},
		# --- Tasks tab ---
		{
			"fieldname": "rw_tab_tasks",
			"fieldtype": "Tab Break",
			"label": "Tasks",
			"insert_after": "consultation_items",
		},
		{
			"fieldname": "consultation_tasks",
			"fieldtype": "Table",
			"label": "Tasks",
			"options": "Encounter Consultation Task",
			"insert_after": "rw_tab_tasks",
		},
		# --- Follow-up tab (uses existing rw_* discharge fields from rwanda_opd) ---
		{
			"fieldname": "rw_tab_followup_detail",
			"fieldtype": "Tab Break",
			"label": "Follow-up",
			"insert_after": "consultation_tasks",
		},
		# --- History tab ---
		{
			"fieldname": "rw_tab_history",
			"fieldtype": "Tab Break",
			"label": "History",
			"insert_after": "rw_referral_reason",
		},
		{
			"fieldname": "consultation_timeline_html",
			"fieldtype": "HTML",
			"label": "Audit Trail",
			"insert_after": "rw_tab_history",
		},
	]


def apply_consultation_form_labels():
	from healthcare.healthcare.rwanda_opd import set_encounter_field_property

	set_encounter_field_property("sb_medications", "label", "Medications (Drug Prescription)")
	set_encounter_field_property("diagnosis", "label", "Diagnosis (required)")
	set_encounter_field_property("encounter_comment", "label", "Internal consultation notes")


def hide_consultation_clutter_fields():
	from healthcare.healthcare.rwanda_opd import set_encounter_field_hidden

	for fieldname in CONSULTATION_HIDDEN_FIELDS:
		set_encounter_field_hidden(fieldname, hidden=1)


def reposition_follow_up_fields():
	"""Move discharge/follow-up fields under the Follow-up tab."""
	order = (
		("rw_visit_outcome", "rw_tab_followup_detail"),
		("rw_discharge_summary", "rw_visit_outcome"),
		("rw_patient_instructions", "rw_discharge_summary"),
		("rw_col_followup", "rw_patient_instructions"),
		("rw_follow_up_required", "rw_col_followup"),
		("rw_follow_up_date", "rw_follow_up_required"),
		("rw_follow_up_notes", "rw_follow_up_date"),
		("rw_referral_sb", "rw_follow_up_notes"),
		("rw_referral_required", "rw_referral_sb"),
		("rw_referral_facility", "rw_referral_required"),
		("rw_referral_department", "rw_referral_facility"),
		("rw_referral_reason", "rw_referral_department"),
		("rw_tab_history", "rw_referral_reason"),
		("consultation_timeline_html", "rw_tab_history"),
	)
	for fieldname, insert_after in order:
		name = frappe.db.get_value(
			"Custom Field", {"dt": "Patient Encounter", "fieldname": fieldname}, "name"
		)
		if name:
			frappe.db.set_value("Custom Field", name, "insert_after", insert_after)


def backfill_consultation_status():
	"""Set consultation_status on existing encounters from rw_opd_visit_status."""
	for rw_status, consultation_status in (
		("Waiting", "Draft"),
		("In Consultation", "In Progress"),
		("Completed", "Completed"),
		("Cancelled", "Cancelled"),
	):
		frappe.db.sql(
			"""
			update `tabPatient Encounter`
			set consultation_status = %s
			where ifnull(consultation_status, '') = ''
				and rw_opd_visit_status = %s
				and docstatus < 2
			""",
			(consultation_status, rw_status),
		)
	frappe.db.sql(
		"""
		update `tabPatient Encounter`
		set consultation_status = 'Follow-up'
		where rw_follow_up_required = 1
			and consultation_status = 'Completed'
			and docstatus < 2
		"""
	)


def validate_rwanda_consultation(doc, method=None):
	if doc.doctype != "Patient Encounter":
		return

	sync_consultation_status(doc)
	calculate_consultation_items(doc)
	update_consultation_tasks(doc)
	_validate_consultation_workflow_state(doc)
	_validate_follow_up_permissions(doc)

	if doc.flags.get("ignore_rwanda_consultation_validation"):
		return

	# Draft saves while in consultation: soft checks only
	if doc.docstatus == 0 and doc.get("rw_opd_visit_status") == "In Consultation":
		_validate_follow_up_and_referral(doc)


def before_submit_rwanda_consultation(doc, method=None):
	if doc.doctype != "Patient Encounter":
		return
	_validate_mandatory_diagnosis(doc)
	_validate_follow_up_and_referral(doc)
	_validate_visit_outcome_on_submit(doc)


def validate_before_complete_consultation(doc):
	"""Called from complete_consultation API."""
	if doc.docstatus != 1:
		frappe.throw(_("Submit the consultation before completing the visit."), title=_("Consultation"))
	_validate_mandatory_diagnosis(doc)
	_validate_follow_up_and_referral(doc)
	_validate_open_tasks(doc)
	if not doc.get("rw_visit_outcome"):
		frappe.throw(_("Select a visit outcome before completing the visit."), title=_("Consultation"))


def sync_consultation_status(doc):
	"""Keep consultation_status and rw_opd_visit_status aligned."""
	if doc.flags.get("skip_consultation_status_sync"):
		return

	status = doc.get("consultation_status")
	rw_status = doc.get("rw_opd_visit_status")

	if status == "Cancelled" or rw_status == "Cancelled":
		doc.consultation_status = "Cancelled"
		doc.rw_opd_visit_status = "Cancelled"
		return

	if status in CONSULTATION_STATUSES and status in RW_STATUS_MAP:
		if rw_status != RW_STATUS_MAP[status]:
			doc.rw_opd_visit_status = RW_STATUS_MAP[status]
		return

	if rw_status == "Waiting":
		doc.consultation_status = "Draft"
	elif rw_status == "In Consultation":
		doc.consultation_status = "In Progress"
	elif rw_status == "Completed":
		if doc.get("rw_follow_up_required") and doc.get("consultation_status") == "Follow-up":
			doc.consultation_status = "Follow-up"
		else:
			doc.consultation_status = "Completed"
	elif rw_status == "Cancelled":
		doc.consultation_status = "Cancelled"
	elif not status:
		doc.consultation_status = "Draft"


def set_consultation_status(doc, status):
	doc.flags.skip_consultation_status_sync = True
	doc.consultation_status = status
	if status in RW_STATUS_MAP:
		doc.rw_opd_visit_status = RW_STATUS_MAP[status]
	doc.flags.skip_consultation_status_sync = False


def calculate_consultation_items(doc):
	total = 0
	for row in doc.get("consultation_items") or []:
		row.amount = flt(row.quantity) * flt(row.rate)
		total += flt(row.amount)
	doc.consultation_items_total = total


def update_consultation_tasks(doc):
	for row in doc.get("consultation_tasks") or []:
		if row.status == "Completed" and not row.completed_on:
			row.completed_on = today()
		elif row.status != "Completed":
			row.completed_on = None


def _validate_open_tasks(doc):
	open_tasks = [
		row.task_name
		for row in doc.get("consultation_tasks") or []
		if row.status not in ("Completed", "Cancelled")
	]
	if open_tasks and doc.consultation_status == "Completed":
		frappe.msgprint(
			_("Some tasks are still open: {0}").format(", ".join(open_tasks[:3])),
			indicator="orange",
			title=_("Tasks"),
		)


def _validate_follow_up_permissions(doc):
	if not doc.has_value_changed("rw_follow_up_date"):
		return
	if "System Manager" in frappe.get_roles():
		return
	practitioner_user = frappe.db.get_value("Healthcare Practitioner", doc.practitioner, "user_id")
	if practitioner_user != frappe.session.user:
		frappe.throw(_("Only the assigned practitioner can change the follow-up date."), title=_("Follow-up"))


def _validate_consultation_workflow_state(doc):
	"""Encounters from orientation should be started from the queue before clinical entry."""
	if doc.is_new():
		return
	if doc.get("rw_opd_visit_status") == "Waiting" and doc.has_value_changed(
		"rw_history_present_illness"
	):
		frappe.msgprint(
			_("Use Proceed to attend from the department queue before documenting the consultation."),
			indicator="orange",
			title=_("Consultation"),
		)


def _validate_mandatory_diagnosis(doc):
	if not doc.get("diagnosis") or len(doc.diagnosis) == 0:
		frappe.throw(
			_("At least one diagnosis is required before submitting the consultation."),
			title=_("Diagnosis required"),
		)


def _validate_follow_up_and_referral(doc):
	if doc.get("rw_follow_up_required") and not doc.get("rw_follow_up_date"):
		frappe.throw(_("Follow-up date is required when follow-up is checked."), title=_("Follow-up"))
	if doc.get("rw_referral_required"):
		if not _text(doc.get("rw_referral_facility")):
			frappe.throw(_("Referral facility is required."), title=_("Referral"))
		if not _text(doc.get("rw_referral_reason")):
			frappe.throw(_("Referral reason is required."), title=_("Referral"))
	if doc.get("rw_visit_outcome") == "Referred out" and not doc.get("rw_referral_required"):
		frappe.msgprint(
			_("Visit outcome is Referred out — consider completing the referral section."),
			indicator="orange",
			title=_("Referral"),
		)


def _validate_visit_outcome_on_submit(doc):
	if not doc.get("rw_visit_outcome"):
		frappe.msgprint(
			_("Select a visit outcome before completing the visit."),
			indicator="orange",
			title=_("Visit outcome"),
		)


def build_triage_vitals_html(triage_name):
	if not triage_name or not frappe.db.exists("Vital Signs", triage_name):
		return "<p class='text-muted small'>" + _("No triage vitals linked.") + "</p>"

	vs = frappe.get_doc("Vital Signs", triage_name)
	rows = [
		(_("Priority"), vs.get("rw_triage_category") or "—"),
		(_("Temperature"), vs.get("temperature") or "—"),
		(_("Pulse"), vs.get("pulse") or "—"),
		(_("Resp. rate"), vs.get("respiratory_rate") or "—"),
		(_("BP"), vs.get("bp") or "—"),
		(_("SpO₂"), vs.get("rw_spo2") or "—"),
		(_("MUAC"), vs.get("rw_muac") or "—"),
		(_("Pain"), vs.get("rw_pain_score") if vs.get("rw_pain_score") is not None else "—"),
		(_("Weight"), vs.get("weight") or "—"),
		(_("Height"), vs.get("height") or "—"),
		(_("BMI"), vs.get("bmi") or "—"),
	]
	alerts = vs.get("rw_triage_alerts") or ""

	html = "<div class='rw-triage-vitals-summary'><table class='table table-sm table-bordered'><tbody>"
	for label, val in rows:
		html += f"<tr><td class='text-muted' style='width:35%'>{frappe.utils.escape_html(str(label))}</td>"
		html += f"<td><b>{frappe.utils.escape_html(str(val))}</b></td></tr>"
	html += "</tbody></table>"
	if alerts:
		html += (
			"<p class='text-danger small mb-0'><b>"
			+ frappe.utils.escape_html(_("Alerts"))
			+ ":</b> "
			+ frappe.utils.escape_html(alerts.replace("\n", "; "))
			+ "</p>"
		)
	html += "</div>"
	return html


@frappe.whitelist()
def get_consultation_triage_summary(encounter):
	frappe.has_permission("Patient Encounter", "read", doc=encounter, throw=True)
	triage = frappe.db.get_value("Patient Encounter", encounter, "rw_triage")
	return {"html": build_triage_vitals_html(triage)}


def _text(val):
	if val is None:
		return ""
	return str(val).strip()
