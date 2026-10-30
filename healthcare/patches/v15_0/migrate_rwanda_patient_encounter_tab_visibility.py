def execute():
	import frappe

	from healthcare.healthcare.rwanda_opd import set_encounter_field_hidden

	for fieldname in ("rw_tab_consultation", "rw_tab_discharge"):
		custom_field = frappe.db.get_value(
			"Custom Field",
			{"dt": "Patient Encounter", "fieldname": fieldname},
			"name",
		)
		if not custom_field:
			frappe.throw(f"Patient Encounter Custom Field {fieldname} was not found")

		frappe.db.set_value(
			"Custom Field",
			custom_field,
			{"hidden": 1, "insert_after": "amended_from"},
		)
		set_encounter_field_hidden(fieldname, hidden=1)

	frappe.clear_cache(doctype="Patient Encounter")
