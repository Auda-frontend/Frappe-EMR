"""Rwanda laboratory flow.

Lab tests are ordered from the open encounter ("Send to lab"), the Queue brings the patient to the
Laboratory unit, results are entered on the Lab Test, and the doctor is notified. Nobody creates a Lab
Test by hand.
"""
import frappe
from frappe import _
from frappe.utils import escape_html

# Names the test column of the encounter's lab table can have in this fork.
CODE_FIELDS = ("lab_test_code", "lab_test", "template", "test_template")

LAB_FIELDS = {
	"Lab Test": [
		{
			"fieldname": "rw_encounter",
			"fieldtype": "Link",
			"label": "Patient Encounter",
			"options": "Patient Encounter",
			"read_only": 1,
			"no_copy": 1,
			"insert_after": "service_request",
		},
		{
			"fieldname": "rw_encounter_row",
			"fieldtype": "Data",
			"label": "Encounter row",
			"read_only": 1,
			"no_copy": 1,
			"hidden": 1,
			"insert_after": "rw_encounter",
		},
	],
	"Patient Encounter": [
		{
			"fieldname": "rw_lab_results_html",
			"fieldtype": "HTML",
			"label": "Lab results",
			"insert_after": "lab_test_prescription",
		},
	],
}

# Placeholder tests so the flow can be tried. Replace with the real list.
STARTER_TESTS = [
	("STOOL DIRECT EXAM", "Microbiology", "Not applicable"),
	("BLOOD THIN SMEAR", "Microbiology", "No parasites seen"),
	("MALARIA RDT", "Microbiology", "Negative"),
	("HEMOGLOBIN", "Haematology", "Men 13-17 g/dL, women 12-15 g/dL"),
	("RANDOM BLOOD GLUCOSE", "Biochemistry", "3.9-7.8 mmol/L"),
	("URINALYSIS", "Biochemistry", "Not applicable"),
	("HIV RAPID TEST", "Serology", "Non-reactive"),
	("PREGNANCY TEST (URINE)", "Serology", "Negative"),
]


# Stock sections the lab does not use; hiding a section hides its fields.
LAB_HIDDEN_SECTIONS = (
	"sb_customresult",
	"medical_coding_section",
	"worksheet_section",
	"result_legend_section",
	"more_information_section",
)


def install_rwanda_lab():
	"""Custom fields for the lab flow. Safe to run on every migrate."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(LAB_FIELDS, update=True)

	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	for fieldname in LAB_HIDDEN_SECTIONS:
		make_property_setter("Lab Test", fieldname, "hidden", 1, "Check")


def get_lab_unit(company=None):
	filters = {"service_unit_type": "Laboratory", "is_group": 0}
	if company:
		unit = frappe.db.get_value("Healthcare Service Unit", {**filters, "company": company}, "name")
		if unit:
			return unit
	return frappe.db.get_value("Healthcare Service Unit", filters, "name")


@frappe.whitelist()
def send_to_lab(encounter):
	"""Create one draft Lab Test for each test in the encounter's lab table. Safe to press twice."""
	frappe.has_permission("Patient Encounter", "write", doc=encounter, throw=True)
	frappe.has_permission("Lab Test", "create", throw=True)

	doc = frappe.get_doc("Patient Encounter", encounter)
	if doc.docstatus != 0:
		frappe.throw(_("Tests can only be sent to the lab while the consultation is open."), title=_("Lab"))

	unit = get_lab_unit(doc.company)
	if not unit:
		frappe.throw(
			_("There is no Laboratory service unit. Ask an administrator to create one."), title=_("Lab")
		)

	row_doctype = doc.meta.get_field("lab_test_prescription").options
	row_meta = frappe.get_meta(row_doctype)
	code_field = next((f for f in CODE_FIELDS if row_meta.has_field(f)), None)
	if not code_field:
		frappe.throw(
			_("The lab table {0} has no test column I recognise. Fields: {1}").format(
				row_doctype, ", ".join(df.fieldname for df in row_meta.fields)
			),
			title=_("Lab"),
		)

	rows = [row for row in doc.get("lab_test_prescription") if row.get(code_field)]
	if not rows:
		frappe.throw(_("Add at least one test to the Lab Tests table first."), title=_("Lab"))

	from healthcare.healthcare.doctype.lab_test.lab_test import create_lab_test_doc

	patient = frappe.get_doc("Patient", doc.patient)
	created, existing = [], []
	for row in rows:
		found = frappe.db.get_value(
			"Lab Test",
			{"rw_encounter": doc.name, "rw_encounter_row": row.name, "docstatus": ["<", 2]},
			"name",
		)
		if found:
			existing.append(found)
			continue
		template = frappe.get_doc("Lab Test Template", row.get(code_field))
		if template.disabled:
			frappe.throw(_("Test {0} is disabled.").format(template.lab_test_name), title=_("Lab"))
		test = create_lab_test_doc(doc.practitioner, patient, template, doc.company, service_unit=unit)
		test.rw_encounter = doc.name
		test.rw_encounter_row = row.name
		test.insert(ignore_permissions=True)
		created.append(test.name)

	return {"created": created, "existing": existing, "lab_unit": unit}


@frappe.whitelist()
def get_pending_lab_tests(queue):
	"""The patient's draft lab tests, for Proceed and Open on a Laboratory queue entry."""
	frappe.has_permission("Queue", "read", doc=queue, throw=True)
	patient = frappe.db.get_value("Queue", queue, "patient")
	if not patient:
		return []
	return frappe.get_all(
		"Lab Test",
		filters={"patient": patient, "docstatus": 0, "rw_encounter": ["is", "set"]},
		pluck="name",
		order_by="creation asc",
	)


@frappe.whitelist()
def get_lab_results(encounter):
	"""A small results table for the encounter: every test ordered from it, pending or done."""
	frappe.has_permission("Patient Encounter", "read", doc=encounter, throw=True)
	tests = frappe.get_all(
		"Lab Test",
		filters={"rw_encounter": encounter, "docstatus": ["<", 2]},
		fields=["name", "lab_test_name", "template", "status", "docstatus", "result_date"],
		order_by="creation asc",
	)
	if not tests:
		return {"html": ""}

	has_result_value = frappe.get_meta("Normal Test Result").has_field("result_value")
	body = ""
	for test in tests:
		result = ""
		if test.docstatus == 1 and has_result_value:
			values = frappe.get_all(
				"Normal Test Result",
				filters={"parent": test.name, "parenttype": "Lab Test"},
				pluck="result_value",
			)
			result = ", ".join(str(v) for v in values if v)
		status = _("Pending") if test.docstatus == 0 else _(test.status or "Completed")
		body += (
			"<tr><td><a href='/app/lab-test/{name}'>{test_name}</a></td><td>{status}</td>"
			"<td>{result}</td><td>{date}</td></tr>"
		).format(
			name=escape_html(test.name),
			test_name=escape_html(test.lab_test_name or test.template or test.name),
			status=escape_html(status),
			result=escape_html(result),
			date=escape_html(str(test.result_date or "")),
		)

	html = (
		"<table class='table table-bordered table-sm'><thead><tr><th>{t}</th><th>{s}</th>"
		"<th>{r}</th><th>{d}</th></tr></thead><tbody>{body}</tbody></table>"
	).format(t=_("Test"), s=_("Status"), r=_("Result"), d=_("Date"), body=body)
	return {"html": html}


def block_manual_lab_tests(doc, method=None):
	"""A Lab Test exists only because a doctor ordered it from an encounter."""
	if doc.get("rw_encounter") or doc.flags.get("from_rwanda_lab"):
		return
	frappe.throw(
		_("Lab tests are ordered from the patient's encounter (Send to lab). They are not created by hand."),
		title=_("Lab Test"),
	)


@frappe.whitelist()
def mark_lab_in_service(lab_test):
	"""Opening a pending lab test starts the patient's Laboratory queue entry, whether or not Proceed was used."""
	frappe.has_permission("Lab Test", "read", doc=lab_test, throw=True)
	test = frappe.db.get_value("Lab Test", lab_test, ["patient", "docstatus"], as_dict=True)
	if not test or test.docstatus != 0:
		return None

	from healthcare.healthcare.queue_api import start_entry_for_patient

	return start_entry_for_patient(test.patient, "Laboratory")


def notify_doctor(doc, method=None):
	"""A result is submitted: close the lab queue entry when nothing is left, and tell the doctor.

	A failure here never blocks the lab.
	"""
	if not doc.get("rw_encounter"):
		return

	try:
		still_pending = frappe.db.count(
			"Lab Test", {"patient": doc.patient, "rw_encounter": ["is", "set"], "docstatus": 0}
		)
		if not still_pending:
			from healthcare.healthcare.queue_api import complete_entry_for_patient

			complete_entry_for_patient(doc.patient, "Laboratory")
	except Exception:
		frappe.log_error(title="Lab queue entry could not be completed")

	try:
		enc = frappe.db.get_value(
			"Patient Encounter", doc.rw_encounter, ["practitioner", "patient_name"], as_dict=True
		)
		user = frappe.db.get_value("Healthcare Practitioner", enc.practitioner, "user_id") if enc else None
		if not user:
			return
		pending = frappe.db.count("Lab Test", {"rw_encounter": doc.rw_encounter, "docstatus": 0})
		patient_name = enc.patient_name or doc.patient
		test_name = doc.get("lab_test_name") or doc.get("template")
		tail = _("all results are ready") if not pending else _("{0} still pending").format(pending)
		subject = _("Lab result ready: {0} for {1} ({2})").format(test_name, patient_name, tail)
		frappe.get_doc(
			{
				"doctype": "Notification Log",
				"for_user": user,
				"from_user": frappe.session.user,
				"type": "Alert",
				"document_type": "Patient Encounter",
				"document_name": doc.rw_encounter,
				"subject": subject,
			}
		).insert(ignore_permissions=True)

		if not pending:
			from frappe.utils import get_url_to_form

			link = get_url_to_form("Patient Encounter", doc.rw_encounter)
			frappe.sendmail(
				recipients=[user],
				subject=_("All lab results are ready for {0}").format(patient_name),
				message=_("The lab has finished all tests ordered for {0}. Open the consultation: {1}").format(
					escape_html(patient_name), "<a href='{0}'>{1}</a>".format(link, escape_html(doc.rw_encounter))
				),
				reference_doctype="Patient Encounter",
				reference_name=doc.rw_encounter,
			)
	except Exception:
		frappe.log_error(title="Lab result notification failed")


def seed_lab_starter_data():
	"""One-off: a Laboratory unit for each company that has none, and the placeholder tests.

	Run with: bench --site <site> execute healthcare.healthcare.rwanda_lab.seed_lab_starter_data
	"""
	report = []

	for company in frappe.get_all("Company", pluck="name"):
		if frappe.db.exists(
			"Healthcare Service Unit",
			{"company": company, "service_unit_type": "Laboratory", "is_group": 0},
		):
			report.append("unit: {0} already has a Laboratory unit".format(company))
			continue
		root = frappe.db.get_value(
			"Healthcare Service Unit",
			{"company": company, "is_group": 1, "parent_healthcare_service_unit": ["in", ["", None]]},
			"name",
		)
		if not root:
			report.append("unit: {0} has no root service unit - create the Laboratory unit by hand".format(company))
			continue
		unit = frappe.get_doc(
			{
				"doctype": "Healthcare Service Unit",
				"healthcare_service_unit_name": "Laboratory",
				"parent_healthcare_service_unit": root,
				"is_group": 0,
				"service_unit_type": "Laboratory",
				"company": company,
			}
		).insert(ignore_permissions=True)
		report.append("unit: created {0}".format(unit.name))

	if not frappe.db.exists("Item Group", "Laboratory"):
		frappe.get_doc(
			{"doctype": "Item Group", "item_group_name": "Laboratory", "parent_item_group": "All Item Groups"}
		).insert(ignore_permissions=True)
		report.append("item group: created Laboratory")

	for name, department, normal_range in STARTER_TESTS:
		if frappe.db.exists("Lab Test Template", {"lab_test_name": name}):
			report.append("test: {0} already exists".format(name))
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Lab Test Template",
					"lab_test_name": name,
					"lab_test_code": name,
					"department": department,
					"lab_test_group": "Laboratory",
					"lab_test_template_type": "Single",
					"is_billable": 0,
					"lab_test_normal_range": normal_range,
				}
			).insert(ignore_permissions=True)
			report.append("test: created {0}".format(name))
		except Exception as exc:
			report.append("test: {0} FAILED - {1}".format(name, exc))

	frappe.db.commit()
	for line in report:
		print(line)
	return report
