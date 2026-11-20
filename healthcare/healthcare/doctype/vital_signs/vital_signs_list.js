frappe.listview_settings["Vital Signs"] = {
	add_fields: ["rw_triage_category", "rw_oriented", "patient", "signs_date"],
	get_indicator(doc) {
		if (doc.rw_oriented) {
			return [__("Oriented"), "green", "rw_oriented,=,1"];
		}
		const cat = doc.rw_triage_category;
		const colors = { Emergency: "red", Urgent: "orange", "Non-urgent": "yellow", Routine: "blue" };
		if (cat) {
			return [__(cat), colors[cat] || "grey", `rw_triage_category,=,${cat}`];
		}
		return [__("Triage"), "blue"];
	},
	onload(listview) {
		rw_hide_add_button(listview);
		listview.page.add_inner_button(__("Orientation desk"), () => frappe.set_route("List", "Internal Orientation"));
	},
	refresh(listview) {
		rw_hide_add_button(listview);
	},
};

function rw_hide_add_button(listview) {
	if (listview.page.clear_primary_action) {
		listview.page.clear_primary_action();
	}
	if (listview.page.btn_primary) {
		listview.page.btn_primary.hide();
	}
}
