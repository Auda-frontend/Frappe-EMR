def execute():
	import frappe

	from healthcare.healthcare.rwanda_consultation import apply_encounter_field_order
	from healthcare.healthcare.rwanda_opd import (
		set_encounter_field_hidden,
		set_encounter_field_property,
	)

	set_encounter_field_hidden("custom_patient_details", hidden=0)
	set_encounter_field_property("patient_sector", "label", "Catchment Area")
	apply_encounter_field_order()
	frappe.clear_cache(doctype="Patient Encounter")
