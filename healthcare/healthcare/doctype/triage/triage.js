// Triage — Master triage record with form routing and notifications

frappe.ui.form.on("Triage", {
	onload(frm) {
		if (frm.is_new() && frappe.route_options) {
			const ro = frappe.route_options;
			if (ro.patient && !frm.doc.patient) {
				frm.set_value("patient", ro.patient);
			}
			if (ro.company && !frm.doc.company) {
				frm.set_value("company", ro.company);
			}
		}
		if (frm.is_new()) {
			if (!frm.doc.signs_date) frm.set_value("signs_date", frappe.datetime.get_today());
			if (!frm.doc.signs_time) frm.set_value("signs_time", frappe.datetime.now_time());
		}
	},

	refresh(frm) {
		setup_triage_form(frm);
		route_triage_form(frm);
		toggle_notification_fields(frm);
		apply_role_lock(frm);
	},

	after_save(frm) {
		route_triage_form(frm);
	},

	patient(frm) {
		if (!frm.doc.patient) return;
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Patient",
				name: frm.doc.patient
			},
			callback(r) {
				if (r.message) {
					const dob = r.message.dob;
					const is_maternity = r.message.rw_is_maternity || 0;
					
					frm.set_value("rw_dob", dob);
					frm.set_value("rw_is_maternity", is_maternity);
					if (r.message.default_company && !frm.doc.company) {
						frm.set_value("company", r.message.default_company);
					}
					if (dob) {
						const years = moment().diff(moment(dob, "YYYY-MM-DD"), "years");
						const months = moment().diff(moment(dob, "YYYY-MM-DD"), "months");
						frm.set_value("rw_patient_age", years);
						frm.set_value("rw_patient_age_months", months);
					}
					
					route_triage_form(frm);
				}
			}
		});
	},

	rw_is_maternity(frm) {
		route_triage_form(frm);
	},

	rw_form_type(frm) {
		route_triage_form(frm);
	},

	height(frm) {
		calc_bmi(frm);
	},

	weight(frm) {
		calc_bmi(frm);
	}
});

function setup_triage_form(frm) {
	// Setup initial form based on patient age and maternity status
	route_triage_form(frm);
}

function route_triage_form(frm) {
	// Determine which age-specific form to show based on patient age
	const age_years = frm.doc.rw_patient_age || 0;
	const age_months = frm.doc.rw_patient_age_months || 0;
	const is_maternity = frm.doc.rw_is_maternity;
	let form_type = "Adult";

	if (is_maternity) {
		form_type = "Maternity";
	} else if (age_years >= 16) {
		form_type = "Adult";
	} else if (age_years >= 5) {
		form_type = "Child";
	} else {
		form_type = "Infant";
	}

	frm.set_value("rw_form_type", form_type);

	// Show/hide form links
	frm.set_df_property("rw_adult_triage_form", "hidden", form_type !== "Adult");
	frm.set_df_property("rw_child_triage_form", "hidden", form_type !== "Child");
	frm.set_df_property("rw_infant_triage_form", "hidden", form_type !== "Infant");
	frm.set_df_property("rw_maternity_triage_form", "hidden", form_type !== "Maternity");

	// Add button to create or open the appropriate form
	if (!frm.is_new()) {
		add_triage_form_button(frm, form_type);
	}
}

function add_triage_form_button(frm, form_type) {
	frm.clear_custom_buttons();

	const field_name = `rw_${form_type.toLowerCase()}_triage_form`;
	const doctype = form_type.replace(/\b\w/g, l => l.toUpperCase()) + " Triage Form";
	const link_value = frm.doc[field_name];

	frm.add_custom_button(__("Open " + doctype), () => {
		if (link_value) {
			frappe.set_route("Form", doctype, link_value);
		} else {
			frappe.new_doc(doctype, {
				parent_triage: frm.doc.name
			});
		}
	}, __("Triage Forms"));
}

function toggle_notification_fields(frm) {
	// Show notification fields only if triage has RED or ORANGE color
	const color = frm.doc.rw_triage_category;
	const show_notification = color === "RED" || color === "ORANGE";

	frm.set_df_property("rw_notified_color", "hidden", !show_notification);
	frm.set_df_property("rw_notified_at", "hidden", !show_notification);
	frm.set_df_property("rw_doctor_name", "hidden", !show_notification);
	frm.set_df_property("rw_doctor_attended_at", "hidden", !show_notification);
	frm.set_df_property("rw_override_reason", "hidden", !frm.doc.rw_triage_manual_override);
}

function apply_role_lock(frm) {
	// Lock fields for roles other than Nurse when RED/ORANGE
	const color = frm.doc.rw_triage_category;
	const is_locked = color === "RED" || color === "ORANGE";
	
	if (is_locked && frappe.session.user_roles.includes("Physician") && !frappe.session.user_roles.includes("Nurse")) {
		const locked_fields = [
			"tongue", "abdomen", "reflexes", "bp_diastolic", "vital_signs_note",
			"height", "weight", "bmi", "rw_muac", "rw_triage_notes", "rw_oriented"
		];
		
		locked_fields.forEach(field => {
			frm.set_df_property(field, "read_only", 1);
		});
	}
}

function calc_bmi(frm) {
	// Calculate BMI from height and weight
	const height = frm.doc.height || 0;
	const weight = frm.doc.weight || 0;

	if (height && weight) {
		const bmi = weight / (height * height);
		frm.set_value("bmi", parseFloat(bmi.toFixed(2)));
	}
}
