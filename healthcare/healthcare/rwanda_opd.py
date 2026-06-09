# -*- coding: utf-8 -*-
import json

# Rwanda OPD workflow:
# Registration → Triage (auto priority) → Orientation (creates visit) → Department queue → Consultation

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import cint, flt, getdate, now_datetime, today

# Visit is created at orientation; clinician pulls from department queue.
VISIT_STATUSES = ("Waiting", "In Consultation", "Completed", "Cancelled")

# Legacy statuses from earlier Phase B builds — still shown in department queue.
LEGACY_QUEUE_STATUSES = ("Registered", "Oriented", "Triaged")
QUEUE_OPEN_STATUSES = VISIT_STATUSES[:2] + LEGACY_QUEUE_STATUSES

TRIAGE_CATEGORIES = ("Emergency", "Urgent", "Non-urgent", "Routine")

ORIENTED_SERVICES = (
	"OPD",
	"NCD",
	"MCH",
	"ART",
	"TB",
	"Emergency",
	"Pharmacy",
	"Laboratory",
	"Other",
)

PATIENT_HISTORY_ON_ENCOUNTER = (
	("rw_allergies", "allergies"),
	("rw_current_medication", "medication"),
	("rw_past_medical_history", "medical_history"),
	("rw_surgical_history", "surgical_history"),
	("rw_tobacco_past_use", "tobacco_past_use"),
	("rw_tobacco_current_use", "tobacco_current_use"),
	("rw_alcohol_past_use", "alcohol_past_use"),
	("rw_alcohol_current_use", "alcohol_current_use"),
	("rw_other_risk_factors", "other_risk_factors"),
)

def install_rwanda_opd():
	create_custom_fields(get_rwanda_opd_custom_fields(), update=True)
	apply_opd_ui_labels()
	hide_patient_medical_history_on_registration()
	extend_opd_list_filters()
	_install_rwanda_consultation()
	frappe.clear_cache()


def _install_rwanda_consultation():
	from healthcare.healthcare.rwanda_consultation import install_rwanda_consultation

	install_rwanda_consultation()


def install_rwanda_phase_b_opd():
	install_rwanda_opd()


def install_rwanda_opd_workflow():
	"""Re-apply workflow fields and UI (post Phase B redesign)."""
	install_rwanda_opd()
	backfill_oriented_department_on_encounters()
	normalize_legacy_visit_statuses()


def get_rwanda_opd_custom_fields():
	return {
		"Patient Encounter": get_patient_encounter_opd_fields(),
		"Vital Signs": get_vital_signs_triage_fields(),
	}


def get_patient_encounter_opd_fields():
	return [
		{
			"fieldname": "rw_tab_visit",
			"fieldtype": "Tab Break",
			"label": "Visit & triage",
			"insert_after": "patient_age",
		},
		{
			"fieldname": "rw_opd_visit_status",
			"fieldtype": "Select",
			"label": "Visit status",
			"options": "\n".join(VISIT_STATUSES),
			"default": "Waiting",
			"insert_after": "rw_tab_visit",
			"in_list_view": 1,
			"in_standard_filter": 1,
			"read_only": 1,
		},
		{
			"fieldname": "rw_oriented_service",
			"fieldtype": "Select",
			"label": "Oriented service",
			"options": "\n".join(ORIENTED_SERVICES),
			"insert_after": "rw_opd_visit_status",
			"in_standard_filter": 1,
			"read_only": 1,
		},
		{
			"fieldname": "rw_oriented_department",
			"fieldtype": "Link",
			"label": "Oriented department (queue)",
			"options": "Medical Department",
			"insert_after": "rw_oriented_service",
			"in_standard_filter": 1,
			"read_only": 1,
			"in_list_view": 1,
		},
		{
			"fieldname": "rw_queue_number",
			"fieldtype": "Int",
			"label": "Queue number",
			"read_only": 1,
			"insert_after": "rw_oriented_department",
			"in_list_view": 1,
		},
		{
			"fieldname": "rw_patient_upid",
			"fieldtype": "Data",
			"label": "Patient UPID",
			"fetch_from": "patient.rw_upid",
			"read_only": 1,
			"insert_after": "rw_queue_number",
		},
		{
			"fieldname": "rw_patient_nin",
			"fieldtype": "Data",
			"label": "Patient NIN",
			"fetch_from": "patient.rw_national_id",
			"read_only": 1,
			"insert_after": "rw_patient_upid",
		},
		{
			"fieldname": "rw_col_visit",
			"fieldtype": "Column Break",
			"insert_after": "rw_patient_nin",
		},
		{
			"fieldname": "rw_triage",
			"fieldtype": "Link",
			"label": "Triage record",
			"options": "Vital Signs",
			"read_only": 1,
			"insert_after": "rw_col_visit",
		},
		{
			"fieldname": "rw_triage_category",
			"fieldtype": "Data",
			"label": "Triage priority",
			"read_only": 1,
			"insert_after": "rw_triage",
		},
		{
			"fieldname": "rw_triage_alerts",
			"fieldtype": "Small Text",
			"label": "Triage alerts",
			"read_only": 1,
			"insert_after": "rw_triage_category",
		},
		{
			"fieldname": "rw_chief_complaint",
			"fieldtype": "Small Text",
			"label": "Chief complaint",
			"read_only": 1,
			"insert_after": "rw_triage_alerts",
		},
		{
			"fieldname": "rw_oriented_at",
			"fieldtype": "Datetime",
			"label": "Oriented at",
			"read_only": 1,
			"insert_after": "rw_chief_complaint",
		},
		{
			"fieldname": "rw_consultation_started_at",
			"fieldtype": "Datetime",
			"label": "Consultation started at",
			"read_only": 1,
			"insert_after": "rw_oriented_at",
		},
		{
			"fieldname": "rw_visit_completed_at",
			"fieldtype": "Datetime",
			"label": "Visit completed at",
			"read_only": 1,
			"insert_after": "rw_consultation_started_at",
		},
		{
			"fieldname": "rw_tab_medical_history",
			"fieldtype": "Tab Break",
			"label": "Medical history",
			"insert_after": "rw_visit_completed_at",
		},
		{
			"fieldname": "rw_allergies",
			"fieldtype": "Small Text",
			"label": "Allergies",
			"insert_after": "rw_tab_medical_history",
		},
		{
			"fieldname": "rw_current_medication",
			"fieldtype": "Small Text",
			"label": "Current medication",
			"insert_after": "rw_allergies",
		},
		{
			"fieldname": "rw_col_hist",
			"fieldtype": "Column Break",
			"insert_after": "rw_current_medication",
		},
		{
			"fieldname": "rw_past_medical_history",
			"fieldtype": "Small Text",
			"label": "Past medical history",
			"insert_after": "rw_col_hist",
		},
		{
			"fieldname": "rw_surgical_history",
			"fieldtype": "Small Text",
			"label": "Surgical history",
			"insert_after": "rw_past_medical_history",
		},
		{
			"fieldname": "rw_risk_sb",
			"fieldtype": "Section Break",
			"label": "Risk factors",
			"insert_after": "rw_surgical_history",
			"collapsible": 1,
		},
		{
			"fieldname": "rw_tobacco_past_use",
			"fieldtype": "Select",
			"label": "Tobacco past use",
			"options": "\nYes\nNo",
			"insert_after": "rw_risk_sb",
		},
		{
			"fieldname": "rw_tobacco_current_use",
			"fieldtype": "Select",
			"label": "Tobacco current use",
			"options": "\nYes\nNo",
			"insert_after": "rw_tobacco_past_use",
		},
		{
			"fieldname": "rw_alcohol_past_use",
			"fieldtype": "Select",
			"label": "Alcohol past use",
			"options": "\nYes\nNo",
			"insert_after": "rw_tobacco_current_use",
		},
		{
			"fieldname": "rw_alcohol_current_use",
			"fieldtype": "Select",
			"label": "Alcohol current use",
			"options": "\nYes\nNo",
			"insert_after": "rw_alcohol_past_use",
		},
		{
			"fieldname": "rw_other_risk_factors",
			"fieldtype": "Small Text",
			"label": "Other risk factors",
			"insert_after": "rw_alcohol_current_use",
		},
		{
			"fieldname": "rw_tab_consultation",
			"fieldtype": "Tab Break",
			"label": "Consultation",
			"insert_after": "submit_orders_on_save",
		},
	]


def get_vital_signs_triage_fields():
	return [
		{
			"fieldname": "rw_triage_category",
			"fieldtype": "Select",
			"label": "Triage priority",
			"options": "\n".join(TRIAGE_CATEGORIES),
			"insert_after": "patient_name",
			"in_list_view": 1,
			"in_standard_filter": 1,
			"read_only": 1,
		},
		{
			"fieldname": "rw_triage_manual_override",
			"fieldtype": "Check",
			"label": "Manual priority override",
			"default": "0",
			"insert_after": "rw_triage_category",
		},
		{
			"fieldname": "rw_triage_category_manual",
			"fieldtype": "Select",
			"label": "Manual priority",
			"options": "\n".join(TRIAGE_CATEGORIES),
			"depends_on": "eval:doc.rw_triage_manual_override",
			"mandatory_depends_on": "eval:doc.rw_triage_manual_override",
			"insert_after": "rw_triage_manual_override",
		},
		{
			"fieldname": "rw_triage_alerts",
			"fieldtype": "Small Text",
			"label": "Alarming signs (auto)",
			"read_only": 1,
			"insert_after": "rw_triage_category_manual",
		},
		{
			"fieldname": "rw_chief_complaint",
			"fieldtype": "Small Text",
			"label": "Chief complaint",
			"insert_after": "rw_triage_alerts",
			"reqd": 1,
		},
		{
			"fieldname": "rw_col_triage",
			"fieldtype": "Column Break",
			"insert_after": "rw_chief_complaint",
		},
		{
			"fieldname": "rw_spo2",
			"fieldtype": "Data",
			"label": "SpO2 (%)",
			"insert_after": "rw_col_triage",
		},
		{
			"fieldname": "rw_muac",
			"fieldtype": "Float",
			"label": "MUAC (cm)",
			"insert_after": "rw_spo2",
		},
		{
			"fieldname": "rw_pain_score",
			"fieldtype": "Int",
			"label": "Pain score (0–10)",
			"insert_after": "rw_muac",
		},
		{
			"fieldname": "rw_triage_notes",
			"fieldtype": "Small Text",
			"label": "Triage notes",
			"insert_after": "rw_pain_score",
		},
		{
			"fieldname": "rw_triaged_by",
			"fieldtype": "Link",
			"label": "Triaged by",
			"options": "User",
			"read_only": 1,
			"insert_after": "rw_triage_notes",
		},
		{
			"fieldname": "rw_oriented",
			"fieldtype": "Check",
			"label": "Patient oriented",
			"default": "0",
			"read_only": 1,
			"insert_after": "rw_triaged_by",
			"in_standard_filter": 1,
		},
	]


def hide_patient_medical_history_on_registration():
	from healthcare.healthcare.rwanda_registration import hide_patient_medical_history_on_registration as _hide

	_hide()


def apply_opd_ui_labels():
	_ensure_translation("Patient Encounter", "Consultation")
	set_encounter_field_property("sb_symptoms", "label", "Present illness & examination")
	set_encounter_field_property("sb_drug_prescription", "label", "Prescriptions")
	set_encounter_field_property("sb_test_prescription", "label", "Investigations & procedures")
	set_encounter_field_property("appointment", "label", "Booking (optional)")


def set_encounter_field_property(fieldname, property_name, value, property_type="Data"):
	name = frappe.db.get_value(
		"Property Setter",
		{"doc_type": "Patient Encounter", "field_name": fieldname, "property": property_name},
		"name",
	)
	if name:
		frappe.db.set_value("Property Setter", name, "value", value)
		return
	frappe.make_property_setter(
		{
			"doctype": "Property Setter",
			"doctype_or_field": "DocField",
			"doc_type": "Patient Encounter",
			"field_name": fieldname,
			"property": property_name,
			"property_type": property_type,
			"value": value,
		},
		validate_fields_for_doctype=False,
	)


def set_encounter_field_hidden(fieldname, hidden=1):
	set_encounter_field_property(fieldname, "hidden", "1" if hidden else "0", property_type="Check")


def _ensure_translation(source, target):
	lang = frappe.db.get_single_value("System Settings", "language")
	if not lang or not frappe.db.exists("Language", lang):
		lang = frappe.db.get_value("Language", {}, "name") or "en"
	names = frappe.get_all(
		"Translation",
		filters={"language": lang, "source_text": source},
		pluck="name",
		limit=1,
	)
	if names:
		frappe.db.set_value("Translation", names[0], "translated_text", target)
	else:
		frappe.get_doc(
			{"doctype": "Translation", "language": lang, "source_text": source, "translated_text": target}
		).insert(ignore_permissions=True)


def extend_opd_list_filters():
	for dt, fieldnames in (
		("Patient Encounter", ("rw_opd_visit_status", "rw_oriented_service", "rw_patient_upid", "rw_queue_number")),
		("Vital Signs", ("rw_triage_category", "rw_oriented")),
	):
		for fieldname in fieldnames:
			frappe.db.set_value(
				"Custom Field",
				{"dt": dt, "fieldname": fieldname},
				"in_standard_filter",
				1,
			)


def _parse_vital(val):
	if val is None or val == "":
		return None
	try:
		return flt(str(val).strip().replace(",", "."))
	except (TypeError, ValueError):
		return None


def compute_triage_priority(doc):
	"""Return (category, alerts list) from vitals — Rwanda OPD alarming-sign rules."""
	alerts = []
	urgency = 0

	temp = _parse_vital(doc.get("temperature"))
	if temp is not None:
		if temp >= 39:
			alerts.append(_("Very high temperature ({0} °C)").format(temp))
			urgency = max(urgency, 3)
		elif temp >= 38:
			alerts.append(_("Fever ({0} °C)").format(temp))
			urgency = max(urgency, 2)

	spo2 = _parse_vital(doc.get("rw_spo2"))
	if spo2 is not None:
		if spo2 < 90:
			alerts.append(_("Critical SpO2 ({0}%)").format(spo2))
			urgency = max(urgency, 3)
		elif spo2 < 94:
			alerts.append(_("Low SpO2 ({0}%)").format(spo2))
			urgency = max(urgency, 2)

	sys_bp = _parse_vital(doc.get("bp_systolic"))
	if sys_bp is not None:
		if sys_bp >= 180 or sys_bp < 90:
			alerts.append(_("Abnormal systolic BP ({0})").format(sys_bp))
			urgency = max(urgency, 3 if sys_bp < 90 else 2)
		elif sys_bp >= 160:
			alerts.append(_("High systolic BP ({0})").format(sys_bp))
			urgency = max(urgency, 2)

	pulse = _parse_vital(doc.get("pulse"))
	if pulse is not None:
		if pulse > 120 or pulse < 50:
			alerts.append(_("Abnormal pulse ({0})").format(pulse))
			urgency = max(urgency, 3 if pulse < 50 else 2)

	rr = _parse_vital(doc.get("respiratory_rate"))
	if rr is not None:
		if rr > 30 or rr < 10:
			alerts.append(_("Abnormal respiratory rate ({0})").format(rr))
			urgency = max(urgency, 3)

	pain = doc.get("rw_pain_score")
	if pain is not None and pain != "":
		pain = cint(pain)
		if pain >= 8:
			alerts.append(_("Severe pain ({0}/10)").format(pain))
			urgency = max(urgency, 2)

	if urgency >= 3:
		category = "Emergency"
	elif urgency == 2:
		category = "Urgent"
	elif alerts:
		category = "Non-urgent"
	else:
		category = "Routine"

	return category, alerts


@frappe.whitelist()
def compute_triage_priority_api(doc):
	"""Desk preview of auto triage priority from vitals (before save)."""
	if isinstance(doc, str):
		doc = json.loads(doc)
	category, alerts = compute_triage_priority(frappe._dict(doc))
	return {"category": category, "alerts": alerts}


def apply_auto_triage(doc):
	category, alerts = compute_triage_priority(doc)
	doc.rw_triage_alerts = "\n".join(alerts) if alerts else _("No alarming signs detected")

	if doc.get("rw_triage_manual_override") and doc.get("rw_triage_category_manual"):
		doc.rw_triage_category = doc.rw_triage_category_manual
	else:
		doc.rw_triage_category = category
		if doc.get("rw_triage_manual_override"):
			doc.rw_triage_category_manual = category


def validate_rwanda_triage(doc, method=None):
	if doc.doctype != "Vital Signs":
		return

	if not _text(doc.get("rw_chief_complaint")):
		frappe.throw(_("Chief complaint is required for triage."), title=_("Triage"))

	pain = doc.get("rw_pain_score")
	if pain is not None and pain != "":
		pain = cint(pain)
		if pain < 0 or pain > 10:
			frappe.throw(_("Pain score must be between 0 and 10."), title=_("Triage"))
		doc.rw_pain_score = pain

	if not doc.get("rw_triaged_by"):
		doc.rw_triaged_by = frappe.session.user

	apply_auto_triage(doc)


def on_triage_saved(doc, method=None):
	"""Triage is saved before orientation — no visit update until orient."""
	pass


def load_patient_history_on_encounter(doc):
	if not doc.patient or not doc.is_new():
		return
	patient = frappe.get_doc("Patient", doc.patient)
	for enc_field, pat_field in PATIENT_HISTORY_ON_ENCOUNTER:
		if not _text(doc.get(enc_field)) and _text(patient.get(pat_field)):
			doc.set(enc_field, patient.get(pat_field))


def sync_encounter_history_to_patient(doc):
	if not doc.patient:
		return
	patient = frappe.get_doc("Patient", doc.patient)
	changed = False
	for enc_field, pat_field in PATIENT_HISTORY_ON_ENCOUNTER:
		val = doc.get(enc_field)
		if _text(val) and patient.get(pat_field) != val:
			patient.set(pat_field, val)
			changed = True
	if changed:
		patient.flags.ignore_permissions = True
		patient.save()


def validate_rwanda_opd_encounter(doc, method=None):
	if doc.doctype != "Patient Encounter":
		return

	if not doc.get("rw_opd_visit_status"):
		doc.rw_opd_visit_status = "Waiting"

	if doc.is_new():
		load_patient_history_on_encounter(doc)

	if doc.docstatus == 0 and doc.get("rw_opd_visit_status") not in ("Cancelled",):
		sync_encounter_history_to_patient(doc)

	if doc.get("rw_opd_visit_status") == "Completed" and not doc.get("rw_visit_completed_at"):
		doc.rw_visit_completed_at = now_datetime()


def backfill_oriented_department_on_encounters():
	"""Copy department onto queue field when orientation ran before this field existed."""
	frappe.db.sql(
		"""
		update `tabPatient Encounter`
		set rw_oriented_department = medical_department
		where ifnull(rw_oriented_department, '') = ''
			and ifnull(medical_department, '') != ''
		"""
	)


def normalize_legacy_visit_statuses():
	"""Map old visit statuses into Waiting so the department queue lists them."""
	for old_status in LEGACY_QUEUE_STATUSES:
		frappe.db.sql(
			"""
			update `tabPatient Encounter`
			set rw_opd_visit_status = 'Waiting'
			where rw_opd_visit_status = %s and docstatus < 2
			""",
			old_status,
		)


def _next_queue_number(oriented_department, visit_date):
	result = frappe.db.sql(
		"""
		select max(ifnull(rw_queue_number, 0))
		from `tabPatient Encounter`
		where ifnull(rw_oriented_department, medical_department) = %s
			and encounter_date = %s
			and docstatus < 2
		""",
		(oriented_department, visit_date),
	)
	return cint(result[0][0] if result else 0) + 1


@frappe.whitelist()
def get_patients_pending_orientation(visit_date=None):
	"""Patients triaged today but not yet oriented to a service."""
	frappe.has_permission("Vital Signs", "read", throw=True)
	visit_date = getdate(visit_date or today())

	return frappe.db.sql(
		"""
		select
			vs.name as triage,
			vs.patient,
			vs.patient_name,
			vs.rw_triage_category,
			vs.rw_triage_alerts,
			vs.rw_chief_complaint,
			vs.signs_time,
			p.rw_upid,
			p.rw_national_id
		from `tabVital Signs` vs
		inner join `tabPatient` p on p.name = vs.patient
		where vs.docstatus < 2
			and vs.signs_date = %s
			and ifnull(vs.rw_oriented, 0) = 0
		order by
			field(vs.rw_triage_category, 'Emergency', 'Urgent', 'Non-urgent', 'Routine'),
			vs.signs_time asc
		""",
		(visit_date,),
		as_dict=True,
	)


@frappe.whitelist()
def orient_patient_to_service(triage, oriented_service, medical_department, practitioner=None, company=None):
	"""Create visit (Patient Encounter) when patient is oriented to a department/service."""
	frappe.has_permission("Patient Encounter", "create", throw=True)

	triage_doc = frappe.get_doc("Vital Signs", triage)
	if triage_doc.get("rw_oriented"):
		frappe.throw(_("This patient has already been oriented."), title=_("Orientation"))

	if oriented_service not in ORIENTED_SERVICES:
		frappe.throw(_("Invalid service."), title=_("Orientation"))

	if not medical_department:
		frappe.throw(_("Medical Department is required."), title=_("Orientation"))

	visit_date = getdate(triage_doc.signs_date or today())
	now = now_datetime()

	existing = frappe.db.exists(
		"Patient Encounter",
		{
			"patient": triage_doc.patient,
			"encounter_date": visit_date,
			"rw_oriented_service": oriented_service,
			"medical_department": medical_department,
			"docstatus": ["<", 2],
			"rw_opd_visit_status": ["in", ["Waiting", "In Consultation"]],
		},
	)
	if existing:
		frappe.throw(
			_("Patient already has an open visit for {0} in {1}.").format(oriented_service, medical_department),
			title=_("Orientation"),
		)

	if not practitioner:
		practitioner = frappe.db.get_value(
			"Healthcare Practitioner",
			{"user_id": frappe.session.user, "status": "Active"},
			"name",
		)
	if not practitioner:
		practitioner = frappe.db.get_value("Healthcare Practitioner", {"status": "Active"}, "name")
	if not practitioner:
		frappe.throw(_("No Healthcare Practitioner found. Set practitioner on orientation."), title=_("Orientation"))

	if not company:
		company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
			"Global Defaults", "default_company"
		)

	enc = frappe.new_doc("Patient Encounter")
	enc.patient = triage_doc.patient
	enc.practitioner = practitioner
	enc.company = company
	enc.encounter_date = visit_date
	enc.encounter_time = now.time()
	enc.rw_opd_visit_status = "Waiting"
	enc.rw_oriented_service = oriented_service
	enc.rw_oriented_department = medical_department
	enc.rw_triage = triage_doc.name
	enc.rw_triage_category = triage_doc.rw_triage_category
	enc.rw_triage_alerts = triage_doc.rw_triage_alerts
	enc.rw_chief_complaint = triage_doc.rw_chief_complaint
	enc.rw_oriented_at = now
	enc.rw_queue_number = _next_queue_number(medical_department, visit_date)
	load_patient_history_on_encounter(enc)
	enc.insert(ignore_permissions=True)

	# medical_department is fetch_from practitioner (read-only) — persist orientation target explicitly.
	frappe.db.set_value(
		"Patient Encounter",
		enc.name,
		{
			"medical_department": medical_department,
			"rw_oriented_department": medical_department,
		},
		update_modified=False,
	)

	frappe.db.set_value("Vital Signs", triage, "rw_oriented", 1, update_modified=False)

	return {"encounter": enc.name, "queue_number": enc.rw_queue_number}


@frappe.whitelist()
def get_default_queue_department():
	"""Default department filter for the logged-in user."""
	dept = frappe.db.get_value(
		"Healthcare Practitioner",
		{"user_id": frappe.session.user, "status": "Active"},
		"department",
	)
	if dept:
		return dept
	return frappe.db.get_value("Medical Department", {}, "name")


@frappe.whitelist()
def get_department_queue(medical_department, oriented_service=None, visit_date=None, company=None):
	"""Department queue: oriented patients waiting or in consultation, critical first."""
	frappe.has_permission("Patient Encounter", "read", throw=True)

	if not medical_department:
		frappe.throw(_("Select a Medical Department."), title=_("Queue"))

	visit_date = getdate(visit_date or today())
	status_placeholders = ", ".join(["%s"] * len(QUEUE_OPEN_STATUSES))
	params = [visit_date, medical_department, medical_department] + list(QUEUE_OPEN_STATUSES)

	company_clause = ""
	if company:
		company_clause = " and pe.company = %s"
		params.append(company)

	service_clause = ""
	if oriented_service:
		service_clause = " and pe.rw_oriented_service = %s"
		params.append(oriented_service)

	rows = frappe.db.sql(
		f"""
		select
			pe.name,
			pe.patient,
			pe.patient_name,
			pe.rw_opd_visit_status,
			pe.rw_oriented_service,
			pe.rw_oriented_department,
			pe.rw_queue_number,
			pe.rw_patient_upid,
			pe.rw_patient_nin,
			pe.rw_triage_category,
			pe.rw_triage_alerts,
			pe.rw_chief_complaint,
			pe.practitioner,
			pe.practitioner_name,
			pe.encounter_time,
			pe.medical_department,
			pe.encounter_date
		from `tabPatient Encounter` pe
		where pe.docstatus = 0
			and pe.encounter_date = %s
			and (
				pe.rw_oriented_department = %s
				or (ifnull(pe.rw_oriented_department, '') = '' and pe.medical_department = %s)
			)
			and pe.rw_opd_visit_status in ({status_placeholders})
			{company_clause}
			{service_clause}
		order by pe.rw_queue_number asc, pe.encounter_time asc
		limit 300
		""",
		tuple(params),
		as_dict=True,
	)

	_priority = {"Emergency": 0, "Urgent": 1, "Non-urgent": 2, "Routine": 3}
	rows.sort(
		key=lambda r: (
			_priority.get(r.get("rw_triage_category") or "Routine", 9),
			cint(r.get("rw_queue_number") or 9999),
		)
	)
	return rows


@frappe.whitelist()
def start_consultation(encounter):
	"""Clinician attends patient from department queue — opens consultation."""
	frappe.has_permission("Patient Encounter", "write", doc=encounter, throw=True)
	doc = frappe.get_doc("Patient Encounter", encounter)

	if doc.rw_opd_visit_status == "In Consultation":
		return {"name": doc.name, "rw_opd_visit_status": doc.rw_opd_visit_status}

	if doc.rw_opd_visit_status != "Waiting":
		frappe.throw(_("Only patients in Waiting status can be called from the queue."), title=_("Consultation"))

	doc.rw_opd_visit_status = "In Consultation"
	if not doc.rw_consultation_started_at:
		doc.rw_consultation_started_at = now_datetime()
	doc.save()

	return {"name": doc.name, "rw_opd_visit_status": doc.rw_opd_visit_status}


@frappe.whitelist()
def complete_consultation(encounter):
	frappe.has_permission("Patient Encounter", "write", doc=encounter, throw=True)
	doc = frappe.get_doc("Patient Encounter", encounter)
	from healthcare.healthcare.rwanda_consultation import validate_before_complete_consultation

	validate_before_complete_consultation(doc)
	doc.rw_opd_visit_status = "Completed"
	doc.rw_visit_completed_at = now_datetime()
	doc.save()
	return {"name": doc.name, "rw_opd_visit_status": doc.rw_opd_visit_status}


# Backward-compatible alias for older desk pages
@frappe.whitelist()
def get_opd_queue(company=None, medical_department=None, visit_date=None, oriented_service=None):
	return get_department_queue(medical_department, oriented_service, visit_date, company)


def _text(val):
	if val is None:
		return ""
	return str(val).strip()
