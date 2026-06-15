const FORM_TYPE = "Child";
const DOCTYPE_NAME = "Child Triage Form";

rwanda_triage_form_init(FORM_TYPE.toLowerCase(), DOCTYPE_NAME);

// Additional Child-specific logic can be added here
frappe.ui.form.on(DOCTYPE_NAME, {
	onload(frm) {
		if (frm.is_new() && frappe.route_options) {
			const ro = frappe.route_options;
			if (ro.triage_assessment && !frm.doc.triage_assessment) {
				frm.set_value("triage_assessment", ro.triage_assessment);
			} else if (ro.parent_triage && !frm.doc.parent_triage) {
				frm.set_value("parent_triage", ro.parent_triage);
			}
		}
	},

	after_save(frm) {
		if (frm.doc.triage_assessment || frm.doc.parent_triage) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: DOCTYPE_NAME,
					name: frm.doc.name
				},
				callback(r) {
					if (r.message) {
						const form_data = r.message;
						frappe.call({
							method: "healthcare.healthcare.doctype.child_triage_form.child_triage_form.sync_to_parent_triage",
							args: {
								form_data: form_data
							}
						});
					}
				}
			});
		}
	}
});

frappe.ui.form.on(DOCTYPE_NAME, {
	refresh(frm) {
		update_triage_priority_alert(frm);
	},
});