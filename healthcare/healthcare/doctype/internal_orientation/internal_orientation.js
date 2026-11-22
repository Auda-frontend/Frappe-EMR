
// The patient's triage assessment is attached whichever way the form was opened, and it decides the priority.
frappe.ui.form.on("Internal Orientation", {
	patient(frm) {
		rw_attach_triage(frm);
	},
	date(frm) {
		rw_attach_triage(frm);
	},
});

function rw_attach_triage(frm) {
	if (frm.doc.docstatus !== 0 || !frm.doc.patient) return;
	frappe
		.xcall("healthcare.healthcare.doctype.internal_orientation.internal_orientation.get_open_assessment", {
			patient: frm.doc.patient,
			date: frm.doc.date,
		})
		.then((found) => {
			frm.set_value("triage_assessment", found ? found.name : "");
			if (found) {
				frm.set_value("priority", found.priority);
				frm.dashboard.set_headline_alert(
					__("Triage {0}: priority set to {1}.", [found.triage_color, found.priority]),
					found.triage_color === "RED" ? "red" : found.triage_color === "ORANGE" ? "orange" : "blue"
				);
			} else {
				frm.dashboard.clear_headline();
			}
		});
}
