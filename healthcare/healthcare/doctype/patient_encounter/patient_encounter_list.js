// Department queue indicators on Consultation (Patient Encounter) list

const RW_VISIT_STATUS_COLORS = {
	Waiting: "blue",
	"In Consultation": "yellow",
	Completed: "green",
	Cancelled: "red",
};

frappe.listview_settings["Patient Encounter"] = {
	add_fields: [
		"rw_opd_visit_status",
		"rw_oriented_service",
		"rw_queue_number",
		"rw_patient_upid",
		"rw_triage_category",
		"patient",
		"medical_department",
		"encounter_date",
	],
	filters: [["docstatus", "!=", 2]],
	get_indicator(doc) {
		const status = doc.rw_opd_visit_status;
		if (status && RW_VISIT_STATUS_COLORS[status]) {
			return [__(status), RW_VISIT_STATUS_COLORS[status], `rw_opd_visit_status,=,${status}`];
		}
		return [__("Open"), "blue", "docstatus,=,0"];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Department queue"), () => frappe.set_route("department-queue"));
		listview.page.add_inner_button(__("Patient orientation"), () => frappe.set_route("patient-orientation"));
		listview.can_create = false;
		listview.page.set_title(__("Outpatient Consultation"));
		frappe.breadcrumbs.$breadcrumbs.find("li").last().find("a").text(__("Outpatient Consultation"));
		listview.page.clear_primary_action();
	},
};
