frappe.listview_settings["Triage Assessment"] = {
	add_fields: ["triage_color", "patient", "patient_oriented"],
	get_indicator(doc) {
		const color = doc.triage_color || "GREEN";
		const status = color.toLowerCase();
		return [__(color), status, `triage_color,=,${color}`];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Orientation desk"), () => frappe.set_route("patient-orientation"));
	},
};
