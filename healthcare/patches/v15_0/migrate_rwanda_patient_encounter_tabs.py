def execute():
	import frappe
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	from healthcare.healthcare.rwanda_consultation import install_rwanda_consultation
	from healthcare.healthcare.rwanda_opd import get_patient_encounter_opd_fields

	create_custom_fields({"Patient Encounter": get_patient_encounter_opd_fields()}, update=True)

	orders_tab = frappe.db.get_value(
		"Custom Field",
		{"dt": "Patient Encounter", "fieldname": "rw_tab_orders"},
		"name",
	)
	if not orders_tab:
		frappe.throw("Patient Encounter Custom Field rw_tab_orders was not found")
	frappe.db.set_value("Custom Field", orders_tab, "insert_after", "amended_from")

	install_rwanda_consultation()
	frappe.clear_cache(doctype="Patient Encounter")
