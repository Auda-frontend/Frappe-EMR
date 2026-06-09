# -*- coding: utf-8 -*-
# Rwanda national registration: patient identifiers, residence, insurance (single form flow).
# Integrated into the healthcare app (no separate bench app).

import json

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import cint

RWANDA_MPI_ROLES = ("System Manager", "Rwanda MPI Admin")

# Legacy custom fields / table from earlier iteration — removed on install.
OBSOLETE_PATIENT_CUSTOM_FIELDS = (
	"rw_registration_sb",
	"rw_col_reg_1",
	"rw_col_reg_2",
	"rw_insurance_section",
	"rw_insurance_coverage",
	"rw_col_identification",
	# Former tab breaks / nested relative sections (single-page layout)
	"rw_tab_father",
	"rw_tab_mother",
	"rw_tab_guardian",
	"rw_sb_contact",
	"rw_sb_social",
	"rw_father_sb_personal",
	"rw_father_sb_contact",
	"rw_mother_sb_personal",
	"rw_mother_sb_contact",
	"rw_guardian_sb_personal",
	"rw_guardian_sb_contact",
	# Replaced by simpler single-page sections
	"rw_sb_administrative",
	"rw_sb_medical",
	"rw_sb_contact_social",
	"rw_sb_medical_contact",
	# Guardian section removed from registration form
	"rw_sb_guardian",
	"rw_guardian_id_type",
	"rw_guardian_id_number",
	"rw_guardian_names",
	"rw_guardian_religion",
	"rw_guardian_col_contact",
	"rw_guardian_phone",
	"rw_guardian_occupation",
)

RELATIVE_UNKNOWN_ROLE_TAGS = {"father": "F", "mother": "M"}


def install_rwanda_patient_registration():
	"""Idempotent: strip legacy layout, apply unified fields on Patient, MPI role."""
	remove_obsolete_rwanda_patient_fields()
	remove_patient_insurance_coverage_doctype_if_unused()
	create_custom_fields(get_rwanda_patient_custom_fields(), update=True)
	hide_patient_customer_details_on_form()
	hide_patient_registration_clutter()
	hide_patient_medical_history_on_registration()
	apply_patient_registration_labels()
	apply_patient_ebuzima_field_order()
	apply_triage_labels()
	ensure_rwanda_mpi_role()
	extend_patient_quick_search_fields()
	extend_patient_list_filters()
	frappe.db.commit()
	frappe.clear_cache(doctype="Patient")
	frappe.clear_cache()


def install_rwanda_phase_a_registration():
	"""Re-apply Phase A registration fields and desk metadata (safe on existing sites)."""
	install_rwanda_patient_registration()


def remove_obsolete_rwanda_patient_fields():
	for row in frappe.get_all(
		"Custom Field",
		filters={"dt": "Patient", "fieldname": ["in", list(OBSOLETE_PATIENT_CUSTOM_FIELDS)]},
		pluck="name",
	):
		try:
			frappe.delete_doc("Custom Field", row, force=1, ignore_permissions=True)
		except Exception:
			frappe.db.delete("Custom Field", {"name": row})
	frappe.db.commit()


def remove_patient_insurance_coverage_doctype_if_unused():
	"""Drop child DocType/table from the old multi-row insurance design."""
	if not frappe.db.exists("DocType", "Patient Insurance Coverage"):
		return
	try:
		frappe.delete_doc("DocType", "Patient Insurance Coverage", force=1, ignore_permissions=True)
	except Exception:
		pass
	frappe.db.commit()


# Shown on Sales Invoice / billing — hidden on Patient registration.
PATIENT_CUSTOMER_AND_BILLING_DEFAULT_FIELDS = (
	"customer_details_section",
	"customer",
	"customer_group",
	"territory",
	"column_break_24",
	"default_currency",
	"default_price_list",
	"language",
)


def hide_patient_customer_details_on_form():
	"""Route party & price defaults to billing (Sales Invoice), not Patient form."""
	for fieldname in PATIENT_CUSTOMER_AND_BILLING_DEFAULT_FIELDS:
		set_patient_field_hidden(fieldname, hidden=1)


def set_patient_field_hidden(fieldname, hidden=1):
	"""Property Setter on core Patient fields (idempotent)."""
	val = "1" if hidden else "0"
	name = frappe.db.get_value(
		"Property Setter",
		{
			"doc_type": "Patient",
			"field_name": fieldname,
			"property": "hidden",
		},
		"name",
	)
	if name:
		frappe.db.set_value("Property Setter", name, "value", val)
		return
	frappe.make_property_setter(
		{
			"doctype": "Property Setter",
			"doctype_or_field": "DocField",
			"doc_type": "Patient",
			"field_name": fieldname,
			"property": "hidden",
			"property_type": "Check",
			"value": val,
		},
		validate_fields_for_doctype=False,
	)


# Core Patient fields hidden on the eBuzima-style registration form.
PATIENT_REGISTRATION_HIDDEN_FIELDS = (
	"naming_series",
	"uid",
	"status",
	"inpatient_record",
	"inpatient_status",
	"image",
	"column_break_14",
	"column_break_25",
	"invite_user",
	"user_id",
	"more_info",
	"patient_details",
	"dashboard_tab",
	"address_and_contact_tab",
	"address_contacts",
	"address_html",
	"column_break_22",
	"contact_html",
	"sb_relation",
	"patient_relation",
	"medical_history_tab",
	"allergy_medical_and_surgical_history",
	"allergies",
	"medication",
	"column_break_20",
	"medical_history",
	"surgical_history",
	"risk_factors",
	"tobacco_past_use",
	"tobacco_current_use",
	"alcohol_past_use",
	"alcohol_current_use",
	"column_break_32",
	"surrounding_factors",
	"other_risk_factors",
	"rw_col_addr",
	"rw_residence_province",
	"rw_residence_district",
	"rw_residence_sector",
	"rw_mark_special_case",
	"rw_insurance_valid_to",
	"rw_rssb_last_verified_on",
	"rw_rssb_validation_notes",
	"rw_upid_is_temporary",
	"rw_upid_source",
)

PATIENT_MEDICAL_HISTORY_FIELDS = (
	"medical_history_tab",
	"allergy_medical_and_surgical_history",
	"allergies",
	"medication",
	"column_break_20",
	"medical_history",
	"surgical_history",
	"risk_factors",
	"tobacco_past_use",
	"tobacco_current_use",
	"alcohol_past_use",
	"alcohol_current_use",
	"column_break_32",
	"surrounding_factors",
	"other_risk_factors",
)

UNKNOWN_ID_PREFIX = "RW-UNK-"


def hide_patient_registration_clutter():
	for fieldname in PATIENT_REGISTRATION_HIDDEN_FIELDS:
		set_patient_field_hidden(fieldname, hidden=1)
	for fieldname in ("marital_status", "report_preference"):
		set_patient_field_hidden(fieldname, hidden=0)


def hide_patient_medical_history_on_registration():
	"""Ensure medical history tab and all related fields stay hidden on Patient registration."""
	for fieldname in PATIENT_MEDICAL_HISTORY_FIELDS:
		set_patient_field_hidden(fieldname, hidden=1)


def apply_patient_registration_labels():
	"""Desk labels aligned with eBuzima-style registration."""
	set_patient_field_property("basic_info", "label", "Patient Registration")
	set_patient_field_property("first_name", "label", "First Name")
	set_patient_field_property("middle_name", "label", "Middle Name (optional)")
	set_patient_field_property("last_name", "label", "Last Name")
	set_patient_field_property("sex", "label", "Gender")
	set_patient_field_property("mobile", "label", "Mobile")
	set_patient_field_property("phone", "label", "Phone")
	set_patient_field_property("dob", "label", "Date of Birth")
	set_patient_field_property("age_html", "label", "Age")
	set_patient_field_property("blood_group", "label", "Blood Group")
	set_patient_field_property("occupation", "label", "Occupation")
	set_patient_field_property("rw_sb_identification", "label", "Identification")
	set_patient_field_property("rw_col_identification", "label", "UPID & registry")
	set_patient_field_property("rw_record_status", "label", "Status")


def set_patient_field_property(fieldname, property_name, value):
	name = frappe.db.get_value(
		"Property Setter",
		{"doc_type": "Patient", "field_name": fieldname, "property": property_name},
		"name",
	)
	if name:
		frappe.db.set_value("Property Setter", name, "value", value)
		return
	frappe.make_property_setter(
		{
			"doctype": "Property Setter",
			"doctype_or_field": "DocField",
			"doc_type": "Patient",
			"field_name": fieldname,
			"property": property_name,
			"property_type": "Data",
			"value": value,
		},
		validate_fields_for_doctype=False,
	)


def extend_patient_list_filters():
	"""Promote Rwanda identifiers in list view filters."""
	for fieldname in (
		"rw_national_id",
		"rw_upid",
		"rw_insurance_member_number",
		"rw_patient_insured",
		"rw_insurance_type",
	):
		frappe.db.set_value(
			"Custom Field",
			{"dt": "Patient", "fieldname": fieldname},
			"in_standard_filter",
			1,
		)


def apply_triage_labels():
	"""__('Vital Signs') and similar resolve to Triage in the default language."""
	ensure_translation_vital_signs_to_triage()


def ensure_translation_vital_signs_to_triage():
	lang = frappe.db.get_single_value("System Settings", "language")
	if not lang or not frappe.db.exists("Language", lang):
		lang = frappe.db.get_value("Language", {}, "name") or "en"
	source = "Vital Signs"
	target = "Triage"
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
			{
				"doctype": "Translation",
				"language": lang,
				"source_text": source,
				"translated_text": target,
			}
		).insert(ignore_permissions=True)


def ensure_rwanda_mpi_role():
	if frappe.db.exists("Role", {"role_name": "Rwanda MPI Admin"}):
		return
	frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": "Rwanda MPI Admin",
			"desk_access": 1,
			"is_custom": 1,
		}
	).insert(ignore_permissions=True)


def extend_patient_quick_search_fields():
	"""Ensure NIN, UPID, and insurance member appear in Patient quick search."""
	meta = frappe.get_meta("Patient")
	parts = [p.strip() for p in (meta.search_fields or "").split(",") if p.strip()]
	before = len(parts)
	for fname in ("rw_national_id", "rw_upid", "rw_insurance_member_number"):
		if fname not in parts:
			parts.append(fname)
	if len(parts) == before:
		return
	new_val = ",".join(parts)
	ps_name = frappe.db.get_value(
		"Property Setter",
		{
			"doc_type": "Patient",
			"property": "search_fields",
			"doctype_or_field": "DocType",
		},
		"name",
	)
	if ps_name:
		ps = frappe.get_doc("Property Setter", ps_name)
		ps.value = new_val
		ps.save(ignore_permissions=True)
	else:
		frappe.make_property_setter(
			{
				"doctype": "Property Setter",
				"doc_type": "Patient",
				"doctype_or_field": "DocType",
				"property": "search_fields",
				"property_type": "Small Text",
				"value": new_val,
			},
			validate_fields_for_doctype=False,
		)


def get_rwanda_identification_type_options():
	return "\n".join(
		["UNKNOWN", "NID", "UPID", "NID_APPLICATION_NUMBER", "PASSPORT", "REFUGEE_ID"]
	)


def get_rwanda_insurance_provider_options():
	return "\n".join(
		[
			"",
			"Africa",
			"CBHI (Mutuelle de sante)",
			"CBHI (Mutuelle de sante) (INDIGENT) 100%",
			"CBHI (Mutuelle de sante) 100%",
			"CBHI (Mutuelle de sante) 90%",
			"East Africa",
			"EDEN CARE 100%",
			"EDEN CARE 85%",
			"GBV",
			"MMI_NEANT 100%",
			"PRIME INSURANCE 100%",
			"RSSB (RAMA) 85%",
			"RSSB Mutuelle",
			"Private commercial",
			"Employer scheme",
			"Other",
		]
	)


def get_rwanda_religion_options():
	return "\nChristian\nMuslim\nOther\nPrefer not to say"


def _relative_section_fields(prefix, label, insert_after):
	"""Father / Mother — collapsible section on the main registration form."""
	id_type = get_rwanda_identification_type_options()
	return [
		{
			"fieldname": f"rw_sb_{prefix}",
			"fieldtype": "Section Break",
			"label": label,
			"collapsible": 1,
			"css_class": f"rw-patient-{prefix}-section",
			"insert_after": insert_after,
		},
		{
			"fieldname": f"rw_{prefix}_id_type",
			"fieldtype": "Select",
			"label": "Identification Type",
			"options": id_type,
			"default": "UNKNOWN",
			"insert_after": f"rw_sb_{prefix}",
		},
		{
			"fieldname": f"rw_{prefix}_id_number",
			"fieldtype": "Data",
			"label": "Identification Number",
			"insert_after": f"rw_{prefix}_id_type",
		},
		{
			"fieldname": f"rw_{prefix}_names",
			"fieldtype": "Data",
			"label": "Names",
			"insert_after": f"rw_{prefix}_id_number",
		},
		{
			"fieldname": f"rw_{prefix}_religion",
			"fieldtype": "Select",
			"label": "Religion",
			"options": get_rwanda_religion_options(),
			"insert_after": f"rw_{prefix}_names",
		},
		{
			"fieldname": f"rw_{prefix}_col_contact",
			"fieldtype": "Column Break",
			"insert_after": f"rw_{prefix}_religion",
		},
		{
			"fieldname": f"rw_{prefix}_phone",
			"fieldtype": "Data",
			"label": "Phone",
			"options": "Phone",
			"insert_after": f"rw_{prefix}_col_contact",
		},
		{
			"fieldname": f"rw_{prefix}_occupation",
			"fieldtype": "Data",
			"label": "Occupation",
			"insert_after": f"rw_{prefix}_phone",
		},
	]


def get_rwanda_patient_custom_fields():
	"""Single-page registration: names → ID → insurance (grouped) → medical/contact → relatives."""
	fields = [
		{
			"fieldname": "rw_reg_search_help",
			"fieldtype": "HTML",
			"label": "Registration",
			"insert_after": "basic_info",
			"options": (
				'<div class="text-muted small">'
				"Before saving, use <b>Find Existing Patient</b> (UPID, name, NIN, phone, insurance number)."
				"</div>"
			),
		},
		{
			"fieldname": "rw_sb_identification",
			"fieldtype": "Section Break",
			"label": "Identification",
			"collapsible": 1,
			"collapsible_depends_on": "eval:1",
			"css_class": "rw-patient-identification-section",
			"insert_after": "rw_reg_search_help",
		},
		# {
		# 	"fieldname": "rw_col_identification",
		# 	"fieldtype": "Column Break",
		# 	"label": "UPID & registry",
		# 	"insert_after": "age_html",
		# },
		{
			"fieldname": "rw_identification_type",
			"fieldtype": "Select",
			"label": "Identification Type",
			"options": get_rwanda_identification_type_options(),
			"default": "UNKNOWN",
			"insert_after": "rw_col_identification",
			"in_standard_filter": 1,
		},
		{
			"fieldname": "rw_national_id",
			"fieldtype": "Data",
			"label": "Identification Number",
			"description": "Cannot be changed after save except by MPI administrators.",
			"insert_after": "rw_identification_type",
			"in_standard_filter": 1,
			"in_list_view": 1,
		},
		{
			"fieldname": "rw_upid",
			"fieldtype": "Data",
			"label": "UPID",
			"description": "Unique patient identifier (client registry / HIE)",
			"insert_after": "rw_national_id",
			"in_standard_filter": 1,
			"in_list_view": 1,
		},
		{
			"fieldname": "rw_nid_application_number",
			"fieldtype": "Data",
			"label": "NID Application Number",
			"depends_on": 'eval:doc.rw_identification_type=="NID_APPLICATION_NUMBER"',
			"insert_after": "rw_upid",
		},
		{
			"fieldname": "rw_nationality",
			"fieldtype": "Select",
			"label": "Nationality",
			"options": "Rwanda\nOther",
			"default": "Rwanda",
			"insert_after": "rw_nid_application_number",
		},
		{
			"fieldname": "rw_tracnet_id",
			"fieldtype": "Data",
			"label": "TraceNet ID",
			"insert_after": "rw_nationality",
		},
		{
			"fieldname": "rw_patient_id_set",
			"fieldtype": "Check",
			"label": "Patient ID Set",
			"default": "0",
			"insert_after": "rw_tracnet_id",
		},
		{
			"fieldname": "rw_go_manual",
			"fieldtype": "Check",
			"label": "Go Manual",
			"default": "0",
			"insert_after": "rw_patient_id_set",
		},
		{
			"fieldname": "rw_upid_is_temporary",
			"fieldtype": "Check",
			"label": "Temporary UPID",
			"default": "0",
			"depends_on": "eval:doc.rw_go_manual",
			"insert_after": "rw_go_manual",
		},
		{
			"fieldname": "rw_upid_source",
			"fieldtype": "Select",
			"label": "UPID source",
			"options": "HIE Client Registry\nLocal Temporary\nManual Assignment",
			"depends_on": "eval:doc.rw_upid_is_temporary || doc.rw_go_manual",
			"insert_after": "rw_upid_is_temporary",
		},
		{
			"fieldname": "rw_sb_insurance",
			"fieldtype": "Section Break",
			"label": "Insurance",
			"collapsible": 1,
			"css_class": "rw-patient-insurance-section",
			"insert_after": "rw_upid_source",
		},
		{
			"fieldname": "rw_patient_insured",
			"fieldtype": "Select",
			"label": "Patient insured?",
			"options": "No\nYes",
			"default": "No",
			"reqd": 1,
			"insert_after": "rw_sb_insurance",
			"in_standard_filter": 1,
		},
		{
			"fieldname": "rw_col_insurance",
			"fieldtype": "Column Break",
			"insert_after": "rw_patient_insured",
		},
		{
			"fieldname": "rw_insurance_type",
			"fieldtype": "Select",
			"label": "Insurance Provider",
			"options": get_rwanda_insurance_provider_options(),
			"depends_on": 'eval:doc.rw_patient_insured=="Yes"',
			"mandatory_depends_on": 'eval:doc.rw_patient_insured=="Yes"',
			"insert_after": "rw_col_insurance",
			"in_standard_filter": 1,
		},
		{
			"fieldname": "rw_insurance_member_number",
			"fieldtype": "Data",
			"label": "Insurance Number",
			"depends_on": 'eval:doc.rw_patient_insured=="Yes"',
			"mandatory_depends_on": 'eval:doc.rw_patient_insured=="Yes"',
			"insert_after": "rw_insurance_type",
			"in_standard_filter": 1,
		},
		{
			"fieldname": "rw_is_main_insurer",
			"fieldtype": "Check",
			"label": "Is patient main insurer?",
			"default": "1",
			"depends_on": 'eval:doc.rw_patient_insured=="Yes"',
			"insert_after": "rw_insurance_member_number",
		},
		{
			"fieldname": "rw_main_insured_name",
			"fieldtype": "Data",
			"label": "Main Insured",
			"depends_on": 'eval:doc.rw_patient_insured=="Yes" && !doc.rw_is_main_insurer',
			"mandatory_depends_on": 'eval:doc.rw_patient_insured=="Yes" && !doc.rw_is_main_insurer',
			"insert_after": "rw_is_main_insurer",
		},
		{
			"fieldname": "rw_main_insured_insurance_number",
			"fieldtype": "Data",
			"label": "Main Insured Insurance Number",
			"depends_on": 'eval:doc.rw_patient_insured=="Yes" && !doc.rw_is_main_insurer',
			"mandatory_depends_on": 'eval:doc.rw_patient_insured=="Yes" && !doc.rw_is_main_insurer',
			"insert_after": "rw_main_insured_name",
		},
		{
			"fieldname": "rw_mark_special_case",
			"fieldtype": "Check",
			"label": "Mark as special case",
			"default": "0",
			"depends_on": 'eval:doc.rw_patient_insured=="Yes"',
			"insert_after": "rw_main_insured_insurance_number",
		},
		{
			"fieldname": "rw_insurance_valid_to",
			"fieldtype": "Date",
			"label": "Insurance valid to",
			"depends_on": 'eval:doc.rw_patient_insured=="Yes"',
			"insert_after": "rw_mark_special_case",
		},
		{
			"fieldname": "rw_rssb_last_verified_on",
			"fieldtype": "Datetime",
			"label": "Insurance last verified",
			"read_only": 1,
			"depends_on": 'eval:doc.rw_patient_insured=="Yes"',
			"insert_after": "rw_insurance_valid_to",
		},
		{
			"fieldname": "rw_rssb_validation_notes",
			"fieldtype": "Small Text",
			"label": "Insurance verification notes",
			"read_only": 1,
			"depends_on": 'eval:doc.rw_patient_insured=="Yes"',
			"insert_after": "rw_rssb_last_verified_on",
		},
		{
			"fieldname": "rw_sb_social",
			"fieldtype": "Section Break",
			"label": "Social Information",
			"collapsible": 1,
			"css_class": "rw-patient-social-section",
			"insert_after": "rw_rssb_validation_notes",
		},
		{
			"fieldname": "rw_set_dob_manually",
			"fieldtype": "Check",
			"label": "Set DOB Manually",
			"default": "0",
			"insert_after": "rw_sb_social",
		},
		{
			"fieldname": "rw_education_level",
			"fieldtype": "Select",
			"label": "Level of Education",
			"options": "\nNone\nPrimary\nSecondary\nTVET\nUniversity\nOther",
			"insert_after": "rw_set_dob_manually",
		},
		{
			"fieldname": "rw_religion",
			"fieldtype": "Select",
			"label": "Religion",
			"options": get_rwanda_religion_options(),
			"insert_after": "rw_education_level",
		},
		# Residence (kept but hidden — available for future HMIS)
		{
			"fieldname": "rw_col_addr",
			"fieldtype": "Column Break",
			"insert_after": "rw_religion",
		},
		{
			"fieldname": "rw_residence_province",
			"fieldtype": "Data",
			"label": "Residence province",
			"insert_after": "rw_col_addr",
		},
		{
			"fieldname": "rw_residence_district",
			"fieldtype": "Data",
			"label": "Residence district",
			"insert_after": "rw_residence_province",
		},
		{
			"fieldname": "rw_residence_sector",
			"fieldtype": "Data",
			"label": "Residence sector",
			"insert_after": "rw_residence_district",
		},
		{
			"fieldname": "rw_record_status",
			"fieldtype": "Select",
			"label": "Status",
			"options": "Active\nInactive",
			"default": "Active",
			"insert_after": "rw_residence_sector",
			"in_standard_filter": 1,
			"in_list_view": 1,
		},
		{
			"fieldname": "rw_inactive_reason",
			"fieldtype": "Small Text",
			"label": "Inactive reason",
			"depends_on": 'eval:doc.rw_record_status=="Inactive"',
			"mandatory_depends_on": 'eval:doc.rw_record_status=="Inactive"',
			"insert_after": "rw_record_status",
		},
	]
	fields.extend(_relative_section_fields("father", "Father Information", "rw_inactive_reason"))
	fields.extend(_relative_section_fields("mother", "Mother Information", "rw_father_occupation"))
	return {"Patient": fields}


def _dedupe_field_order(fieldnames):
	"""Each field once — duplicates in field_order break the desk layout."""
	seen = set()
	order = []
	for fieldname in fieldnames:
		if fieldname in seen:
			continue
		seen.add(fieldname)
		order.append(fieldname)
	return order


def get_patient_ebuzima_field_order():
	"""Identification: one column break — left = IDs, person, contact; right = UPID extras."""
	visible = [
		"basic_info",
		"rw_reg_search_help",
		"rw_sb_identification",
		# Left column
		"rw_identification_type",
		"rw_national_id",
		"first_name",
		"middle_name",
		"last_name",
		"rw_nationality",
		"patient_name",
		"sex",
		"blood_group",
		"rw_tracnet_id",
		"rw_patient_id_set",
		"rw_go_manual",
		"rw_record_status",
		"marital_status",
		"mobile",
		"phone",
		"email",
		"occupation",
		"report_preference",
		"rw_set_dob_manually",
		"dob",
		"age_html",
		# "rw_col_identification",
		# Right column — UPID / manual registry fields
		"rw_inactive_reason",
		"rw_upid",
		"rw_nid_application_number",
		"rw_upid_is_temporary",
		"rw_upid_source",
		"rw_sb_insurance",
		"rw_patient_insured",
		"rw_col_insurance",
		"rw_insurance_type",
		"rw_insurance_member_number",
		"rw_is_main_insurer",
		"rw_main_insured_name",
		"rw_main_insured_insurance_number",
		"rw_sb_social",
		"rw_education_level",
		"rw_religion",
		"rw_col_addr",
		"rw_residence_province",
		"rw_residence_district",
		"rw_residence_sector",
		"rw_sb_father",
		"rw_father_id_type",
		"rw_father_id_number",
		"rw_father_names",
		"rw_father_religion",
		"rw_father_col_contact",
		"rw_father_phone",
		"rw_father_occupation",
		"rw_sb_mother",
		"rw_mother_id_type",
		"rw_mother_id_number",
		"rw_mother_names",
		"rw_mother_religion",
		"rw_mother_col_contact",
		"rw_mother_phone",
		"rw_mother_occupation",
	]
	hidden_tail = [
		"naming_series",
		"uid",
		"status",
		"inpatient_record",
		"inpatient_status",
		"image",
		"column_break_14",
		"column_break_25",
		"invite_user",
		"user_id",
		"customer_details_section",
		"customer",
		"customer_group",
		"territory",
		"column_break_24",
		"default_currency",
		"default_price_list",
		"language",
		"more_info",
		"patient_details",
		"dashboard_tab",
		"address_and_contact_tab",
		"address_contacts",
		"address_html",
		"column_break_22",
		"contact_html",
		"sb_relation",
		"patient_relation",
		"medical_history_tab",
		"allergy_medical_and_surgical_history",
		"allergies",
		"medication",
		"column_break_20",
		"medical_history",
		"surgical_history",
		"risk_factors",
		"tobacco_past_use",
		"tobacco_current_use",
		"alcohol_past_use",
		"alcohol_current_use",
		"column_break_32",
		"surrounding_factors",
		"other_risk_factors",
		"rw_mark_special_case",
		"rw_insurance_valid_to",
		"rw_rssb_last_verified_on",
		"rw_rssb_validation_notes",
	]
	visible_set = set(visible)
	return _dedupe_field_order(visible + [f for f in hidden_tail if f not in visible_set])


def apply_patient_ebuzima_field_order():
	"""Push field_order Property Setter — required for desk layout (custom fields alone are not enough)."""
	order = get_patient_ebuzima_field_order()
	value = json.dumps(order)
	filters = {
		"doc_type": "Patient",
		"property": "field_order",
		"doctype_or_field": "DocType",
	}
	name = frappe.db.get_value("Property Setter", filters, "name")
	if name:
		frappe.db.set_value("Property Setter", name, "value", value, update_modified=False)
	else:
		frappe.make_property_setter(
			{
				"doctype": "Property Setter",
				"doctype_or_field": "DocType",
				"doc_type": "Patient",
				"property": "field_order",
				"property_type": "Data",
				"value": value,
			},
			validate_fields_for_doctype=False,
		)
	frappe.clear_cache(doctype="Patient")


def install_rwanda_patient_ebuzima_layout():
	"""Re-apply eBuzima patient registration layout (safe on existing sites)."""
	install_rwanda_patient_registration()


@frappe.whitelist()
def apply_rwanda_patient_registration_layout():
	"""Desk/bench: force Patient registration field order and labels onto the site."""
	frappe.only_for(("System Manager", "Healthcare Administrator"), message=True)
	install_rwanda_patient_registration()
	return {"ok": True, "message": "Patient registration layout applied. Hard-refresh the Patient form."}


def validate_rwanda_patient_registration(doc, method=None):
	"""National ID / UPID / registration rules (called from Patient.validate)."""
	if doc.doctype != "Patient":
		return

	_normalize_identification_type(doc)
	_ensure_unknown_identification_number(doc)
	_ensure_relative_unknown_identification_numbers(doc)
	_sync_identification_to_uid(doc)
	_sync_registration_status(doc)

	nin = _clean_id(doc.get("rw_national_id"))
	if nin:
		doc.rw_national_id = nin

	_validate_nin_immutable(doc)
	_validate_duplicate_ids(doc)
	_validate_inactive_reason(doc)
	_validate_patient_id_set(doc)
	_validate_insurance(doc)


LEGACY_IDENTIFICATION_TYPE_MAP = {
	"NIDA / NIN": "NID",
	"Passport": "PASSPORT",
	"Foreign ID": "PASSPORT",
	"Refugee ID": "REFUGEE_ID",
}


def _normalize_identification_type(doc):
	id_type = (doc.get("rw_identification_type") or "").strip()
	if id_type in LEGACY_IDENTIFICATION_TYPE_MAP:
		doc.rw_identification_type = LEGACY_IDENTIFICATION_TYPE_MAP[id_type]


def _is_system_generated_unknown_id(value):
	nin = _clean_id(value)
	return bool(nin) and nin.startswith(UNKNOWN_ID_PREFIX)


def _generate_unique_unknown_identification_number():
	"""System ID for patients registered without official identification."""
	for _ in range(20):
		candidate = UNKNOWN_ID_PREFIX + frappe.generate_hash(length=10).upper()
		if not frappe.db.exists("Patient", {"rw_national_id": candidate}):
			return candidate
	frappe.throw(
		_("Could not generate a unique identification number. Retry."),
		title=_("Patient registration"),
	)


def _ensure_unknown_identification_number(doc):
	"""Auto-fill identification number when type is UNKNOWN."""
	id_type = doc.get("rw_identification_type") or "UNKNOWN"
	if id_type != "UNKNOWN":
		return
	if _clean_id(doc.get("rw_national_id")):
		return
	doc.rw_national_id = _generate_unique_unknown_identification_number()


def _relative_unknown_id_prefix(role):
	tag = RELATIVE_UNKNOWN_ROLE_TAGS.get(role)
	if not tag:
		return None
	return f"{UNKNOWN_ID_PREFIX}{tag}-"


def _is_system_generated_relative_unknown_id(value, role):
	prefix = _relative_unknown_id_prefix(role)
	if not prefix:
		return False
	nin = _clean_id(value)
	return bool(nin) and nin.startswith(prefix)


def _generate_unique_relative_unknown_identification_number(role):
	"""System ID for father/mother when identification type is UNKNOWN."""
	prefix = _relative_unknown_id_prefix(role)
	if not prefix:
		frappe.throw(_("Invalid relative role for identification number generation."))
	fieldname = f"rw_{role}_id_number"
	for _ in range(20):
		candidate = prefix + frappe.generate_hash(length=8).upper()
		if not frappe.db.exists("Patient", {fieldname: candidate}):
			return candidate
	frappe.throw(
		_("Could not generate a unique identification number for {0}. Retry.").format(role),
		title=_("Patient registration"),
	)


def _ensure_relative_unknown_identification_numbers(doc):
	"""Auto-fill father/mother identification numbers when type is UNKNOWN."""
	for role in RELATIVE_UNKNOWN_ROLE_TAGS:
		id_type = doc.get(f"rw_{role}_id_type") or "UNKNOWN"
		if id_type != "UNKNOWN":
			continue
		id_field = f"rw_{role}_id_number"
		if _clean_id(doc.get(id_field)):
			continue
		doc.set(id_field, _generate_unique_relative_unknown_identification_number(role))


def _sync_identification_to_uid(doc):
	id_type = doc.get("rw_identification_type") or "UNKNOWN"
	if id_type == "UPID":
		upid = _clean_id(doc.get("rw_upid"))
		if upid:
			doc.uid = upid
		return
	if id_type == "NID_APPLICATION_NUMBER":
		app_no = _clean_id(doc.get("rw_nid_application_number"))
		if app_no:
			doc.uid = app_no
		return
	nin = _clean_id(doc.get("rw_national_id"))
	if nin and id_type in ("NID", "PASSPORT", "REFUGEE_ID", "UNKNOWN"):
		doc.uid = nin


def _sync_registration_status(doc):
	if doc.get("rw_record_status") == "Inactive":
		doc.status = "Disabled"
	else:
		doc.status = "Active"


def _validate_patient_id_set(doc):
	if not cint(doc.get("rw_patient_id_set")):
		return
	id_type = doc.get("rw_identification_type") or "UNKNOWN"
	if id_type == "UPID" and not _clean_id(doc.get("rw_upid")):
		frappe.throw(_("UPID is required when Patient ID Set is checked."), title=_("Identification"))
	if id_type == "NID_APPLICATION_NUMBER" and not _clean_id(doc.get("rw_nid_application_number")):
		frappe.throw(
			_("NID Application Number is required when Patient ID Set is checked."),
			title=_("Identification"),
		)
	if id_type in ("NID", "PASSPORT", "REFUGEE_ID") and not _clean_id(doc.get("rw_national_id")):
		frappe.throw(
			_("Identification number is required when Patient ID Set is checked."),
			title=_("Identification"),
		)


def _clean_id(val):
	if val is None:
		return ""
	return str(val).strip()


def _can_edit_nin():
	roles = set(frappe.get_roles())
	return bool(roles.intersection(set(RWANDA_MPI_ROLES)))


def _validate_nin_immutable(doc):
	if doc.is_new():
		return
	prev = doc.get_doc_before_save()
	if not prev:
		return
	old_nin = _clean_id(prev.get("rw_national_id"))
	new_nin = _clean_id(doc.get("rw_national_id"))
	if old_nin and new_nin != old_nin and not _can_edit_nin():
		prev_type = prev.get("rw_identification_type") or "UNKNOWN"
		curr_type = doc.get("rw_identification_type") or "UNKNOWN"
		if _is_system_generated_unknown_id(old_nin) or (
			prev_type == "UNKNOWN" and curr_type != "UNKNOWN"
		):
			return
		frappe.throw(
			_("National ID (NIN) cannot be changed after it is set. Contact an MPI administrator."),
			title=_("Restricted change"),
		)


def _validate_duplicate_ids(doc):
	name = doc.name
	nin = _clean_id(doc.get("rw_national_id"))
	if nin:
		existing = frappe.db.sql(
			"""
			select name from `tabPatient`
			where rw_national_id = %s and name != %s limit 1
			""",
			(nin, name),
		)
		if existing:
			frappe.throw(
				_("National ID (NIN) is already registered to patient {0}").format(existing[0][0]),
				title=_("Duplicate NIN"),
			)

	upid = _clean_id(doc.get("rw_upid"))
	if upid and not doc.get("rw_upid_is_temporary"):
		existing = frappe.db.sql(
			"""
			select name from `tabPatient`
			where rw_upid = %s and ifnull(rw_upid_is_temporary, 0) = 0 and name != %s limit 1
			""",
			(upid, name),
		)
		if existing:
			frappe.throw(
				_("UPID is already assigned to patient {0}").format(existing[0][0]),
				title=_("Duplicate UPID"),
			)


def _validate_inactive_reason(doc):
	if doc.get("rw_record_status") == "Inactive" and not _clean_id(doc.get("rw_inactive_reason")):
		frappe.throw(
			_("Inactive reason is required when registration status is Inactive."),
			title=_("Missing reason"),
		)


def _validate_insurance(doc):
	if doc.get("rw_patient_insured") != "Yes":
		for fieldname in (
			"rw_insurance_type",
			"rw_mark_special_case",
			"rw_insurance_member_number",
			"rw_insurance_valid_to",
			"rw_main_insured_name",
			"rw_main_insured_insurance_number",
			"rw_rssb_last_verified_on",
			"rw_rssb_validation_notes",
		):
			doc.set(fieldname, None)
		doc.rw_is_main_insurer = 1
		doc.rw_mark_special_case = 0
		return
	if not _clean_id(doc.get("rw_insurance_type")):
		frappe.throw(_("Insurance provider is required when the patient is insured."), title=_("Insurance"))
	if not _clean_id(doc.get("rw_insurance_member_number")):
		frappe.throw(
			_("Insurance member / policy number is required when the patient is insured."),
			title=_("Insurance"),
		)
	if not cint(doc.get("rw_is_main_insurer")):
		if not _clean_id(doc.get("rw_main_insured_name")):
			frappe.throw(_("Main insured name is required for dependents."), title=_("Insurance"))
		if not _clean_id(doc.get("rw_main_insured_insurance_number")):
			frappe.throw(_("Main insured insurance number is required for dependents."), title=_("Insurance"))


def _ensure_patient_read():
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"), frappe.PermissionError)
	frappe.has_permission("Patient", "read", throw=True)


@frappe.whitelist()
def search_patients_rw(
	search_text=None,
	national_id=None,
	upid=None,
	phone=None,
	insurance_member=None,
	limit_start=0,
	limit_page_length=50,
):
	"""Registration desk search by name, UID, NIN, UPID, phone, or insurance member number."""
	_ensure_patient_read()

	limit_start = int(limit_start or 0)
	limit_page_length = min(max(int(limit_page_length or 50), 1), 100)

	st = (search_text or "").strip()
	nid = (national_id or "").strip()
	up = (upid or "").strip()
	ph = (phone or "").strip()
	im = (insurance_member or "").strip()

	clauses = []
	params = []

	if nid:
		clauses.append("p.rw_national_id = %s")
		params.append(nid)
	if up:
		clauses.append("p.rw_upid = %s")
		params.append(up)
	if ph:
		clauses.append("(p.mobile = %s OR p.phone = %s)")
		params.extend([ph, ph])

	if st:
		like = f"%{st}%"
		clauses.append(
			"(p.patient_name LIKE %s OR p.first_name LIKE %s OR p.last_name LIKE %s OR "
			"p.uid LIKE %s OR IFNULL(p.rw_national_id,'') LIKE %s OR IFNULL(p.rw_upid,'') LIKE %s OR IFNULL(p.rw_insurance_member_number,'') LIKE %s)"
		)
		params.extend([like, like, like, like, like, like, like])

	if im:
		clauses.append("IFNULL(p.rw_insurance_member_number,'') = %s")
		params.append(im)

	if not clauses:
		return []

	where_sql = " AND ".join(clauses)
	sql = f"""
		SELECT
			p.name,
			p.patient_name,
			p.sex,
			p.uid,
			p.rw_national_id,
			p.rw_upid,
			p.rw_insurance_type,
			p.rw_insurance_member_number,
			p.dob,
			p.mobile,
			p.phone,
			p.rw_record_status,
			p.modified,
			p.image
		FROM `tabPatient` p
		WHERE {where_sql}
		ORDER BY p.modified DESC
		LIMIT %s OFFSET %s
	"""
	params.extend([limit_page_length, limit_start])

	try:
		return frappe.db.sql(sql, tuple(params), as_dict=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Rwanda patient search")
		frappe.throw(
			_("Patient search failed. Run `bench migrate` after upgrading healthcare."),
			title=_("Patient registration"),
		)


@frappe.whitelist()
def generate_rw_unknown_identification_number():
	"""System-generated identification number when identification type is UNKNOWN."""
	if not frappe.has_permission("Patient", "create"):
		frappe.throw(_("Not permitted to generate an identification number."), frappe.PermissionError)
	return _generate_unique_unknown_identification_number()


@frappe.whitelist()
def generate_rw_relative_unknown_identification_number(role):
	"""System-generated ID for father/mother when identification type is UNKNOWN."""
	if not frappe.has_permission("Patient", "create"):
		frappe.throw(_("Not permitted to generate an identification number."), frappe.PermissionError)
	role = (role or "").strip().lower()
	if role not in RELATIVE_UNKNOWN_ROLE_TAGS:
		frappe.throw(_("Role must be father or mother."))
	return _generate_unique_relative_unknown_identification_number(role)


@frappe.whitelist()
def generate_rw_temp_upid():
	"""Temporary UPID when HIE / client registry is offline."""
	if not (set(frappe.get_roles()).intersection(set(RWANDA_MPI_ROLES)) or frappe.has_permission("Patient", "create")):
		frappe.throw(_("Not permitted to generate a temporary UPID."), frappe.PermissionError)
	prefix = "RW-TMP-"
	for _ in range(20):
		candidate = prefix + frappe.generate_hash(length=8).upper()
		if not frappe.db.exists("Patient", {"rw_upid": candidate}):
			return candidate
	frappe.throw(_("Could not generate a unique temporary UPID. Retry."), title=_("Patient registration"))


@frappe.whitelist()
def check_insurance_eligibility(patient):
	"""Stub RSSB eligibility check — records verification timestamp on the patient."""
	frappe.has_permission("Patient", "write", doc=patient, throw=True)
	doc = frappe.get_doc("Patient", patient)

	if doc.get("rw_patient_insured") != "Yes":
		frappe.throw(_("Set Patient insured? to Yes before checking eligibility."))

	if not _clean_id(doc.get("rw_insurance_member_number")):
		frappe.throw(_("Enter insurance member / policy number before checking eligibility."))

	now = frappe.utils.now_datetime()
	notes = _(
		"Eligibility recorded from desk (stub). Connect RSSB API in a later release for live validation."
	)
	frappe.db.set_value("Patient", patient, "rw_rssb_last_verified_on", now, update_modified=False)
	frappe.db.set_value("Patient", patient, "rw_rssb_validation_notes", notes, update_modified=False)

	return {
		"valid": True,
		"message": _("Insurance verification recorded at {0}").format(
			frappe.utils.format_datetime(now)
		),
	}
