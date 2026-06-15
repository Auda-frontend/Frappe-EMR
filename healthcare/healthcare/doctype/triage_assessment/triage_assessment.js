// Triage Assessment — routes to age-specific forms

frappe.ui.form.on("Triage Assessment", {
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
			if (!frm.doc.arrival_date) frm.set_value("arrival_date", frappe.datetime.get_today());
			if (!frm.doc.arrival_time) frm.set_value("arrival_time", frappe.datetime.now_time());
		}
	},

	refresh(frm) {
		route_triage_form(frm);
		update_triage_priority_alert(frm);
		toggle_notification_fields(frm);
		rw_triage_assessment_add_create_button(frm);
		if (frm.doc.vital_signs_record) {
			frm.add_custom_button(__("Open Vital Signs"), () => {
				frappe.set_route("Form", "Vital Signs", frm.doc.vital_signs_record);
			}, __("Workflow"));
		}

		// Orientation buttons (moved from Vital Signs)
		if (!frm.is_new() && !frm.doc.patient_oriented) {
			frm.add_custom_button(__("Orient to service"), () => rw_triage_assessment_open_orientation(frm), __("Workflow"));
			frm.add_custom_button(__("Open orientation desk"), () => frappe.set_route("patient-orientation"), __("Workflow"));
		} else if (frm.doc.patient_oriented) {
			frm.set_intro(__("Patient oriented — visit created. Use Department Queue to call patient."), "green");
		}
	},

	// patient(frm) {
	// 	if (!frm.doc.patient) return;
	// 	frappe.db.get_value(
	// 		"Patient",
	// 		{ name: frm.doc.patient },
	// 		["patient_name", "dob", "sex", "rw_is_maternity", "name", "default_company"],
	// 		(r) => {
	// 			frm.set_value("patient_name", r.patient_name);
	// 			frm.set_value("patient_gender", r.sex);
	// 			frm.set_value("medical_record_number", r.name);
	// 			frm.set_value("is_maternity", r.rw_is_maternity || 0);
	// 			if (r.default_company && !frm.doc.company) frm.set_value("company", r.default_company);
	// 			if (r.dob) {
	// 				const years = moment().diff(moment(r.dob, "YYYY-MM-DD"), "years");
	// 				const months = moment().diff(moment(r.dob, "YYYY-MM-DD"), "months");
	// 				frm.set_value("date_of_birth", r.dob);
	// 				frm.set_value("patient_age", years);
	// 				frm.set_value("patient_age_months", months);
	// 			}
	// 			route_triage_form(frm);
	// 		}
	// 	);
	// },
	patient(frm) {
    if (!frm.doc.patient) return;

    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Patient",
            name: frm.doc.patient
        },
        callback(r) {
            if (!r.message) return;
            let p = r.message;

            frm.set_value("patient_name", p.patient_name);
            frm.set_value("patient_gender", p.sex);

            if (p.dob) {
                let today = frappe.datetime.nowdate();
                let years  = moment(today).diff(moment(p.dob), "years");
                let months = moment(today).diff(moment(p.dob), "months");
                frm.set_value("patient_age", years);
                frm.set_value("patient_age_months", months);
            }

            frm.set_value("is_maternity", p.rw_is_maternity || 0);

            if (!frm.doc.company && p.default_company) {
                frm.set_value("company", p.default_company);
            }
            if (!frm.doc.arrival_date) {
                frm.set_value("arrival_date", frappe.datetime.nowdate());
            }
            if (!frm.doc.arrival_time) {
                frm.set_value("arrival_time", frappe.datetime.now_time());
            }

            route_triage_form(frm);
        }
    });
},

	is_maternity(frm) {
		route_triage_form(frm);
	},

	triage_color(frm) {
		toggle_notification_fields(frm);
	},

	manual_priority_override(frm) {
		toggle_notification_fields(frm);
	},
});

function route_triage_form(frm) {
	const months = frm.doc.patient_age_months || 0;
	const age = frm.doc.patient_age || 0;
	const mat = frm.doc.is_maternity;

	let form_type = mat ? "Maternity" : months <= 36 ? "Infant" : age <= 12 ? "Child" : "Adult";

	if (frm.doc.form_type !== form_type) {
		frm.set_value("form_type", form_type);
	}

	frm.toggle_display("adult_triage_form", form_type === "Adult");
	frm.toggle_display("child_triage_form", form_type === "Child");
	frm.toggle_display("infant_triage_form", form_type === "Infant");
	frm.toggle_display("maternity_triage_form", form_type === "Maternity");
}

function update_triage_priority_alert(frm) {
	const color = frm.doc.triage_color;
	const is_critical = ["RED", "ORANGE"].includes(color);

	if (is_critical && !frm.doc.patient_oriented) {
		frm.dashboard.set_headline_alert(
			__("{0} priority — orient this patient immediately.", [__(color)]),
			color === "RED" ? "red" : "orange"
		);
		frm.set_intro(
			__("Immediate orientation required for this {0} priority patient.", [__(color)]),
			color === "RED" ? "red" : "orange"
		);
	} else if (frm.doc.patient_oriented) {
		frm.dashboard.clear_headline_alert();
		frm.set_intro(__("Patient oriented — visit created. Use Department Queue to call patient."), "green");
	} else {
		frm.dashboard.clear_headline_alert();
		frm.set_intro(__("Use the triage color below to determine priority and orientation urgency."), "blue");
	}
}

function toggle_notification_fields(frm) {
	const is_critical = ["RED", "ORANGE"].includes(frm.doc.triage_color);
	["notified_color", "notified_at", "doctor_name", "doctor_attended_at"].forEach((f) => {
		if (frm.fields_dict[f]) frm.toggle_display(f, is_critical);
	});
	if (frm.fields_dict.override_reason) {
		frm.toggle_display("override_reason", frm.doc.manual_priority_override);
	}
}

function rw_triage_assessment_add_create_button(frm) {
	if (frm.is_new() || frm.doc.docstatus === 1) return;

	const map = {
		Adult: { doctype: "Adult Triage Form", field: "adult_triage_form" },
		Child: { doctype: "Child Triage Form", field: "child_triage_form" },
		Infant: { doctype: "Infant Triage Form", field: "infant_triage_form" },
		Maternity: { doctype: "Maternity Triage Form", field: "maternity_triage_form" },
	};
	const cfg = map[frm.doc.form_type];
	if (!cfg || frm.doc[cfg.field]) return;

	frm.add_custom_button(__("Create {0} Form", [frm.doc.form_type]), () => {
		frappe.new_doc(cfg.doctype, {
			triage_assessment: frm.doc.name,
			patient: frm.doc.patient,
			patient_name: frm.doc.patient_name,
			age: frm.doc.patient_age,
			medical_record_number: frm.doc.medical_record_number,
			chief_complaint: frm.doc.chief_complaint,
			date: frm.doc.arrival_date,
			arrival_time: frm.doc.arrival_time,
			patient_age_months: frm.doc.patient_age_months,
			patient_gender: frm.doc.patient_gender,
			date_of_birth: frm.doc.date_of_birth,
			company: frm.doc.company,
		});
	}, __("Triage"));
}

function rw_triage_assessment_open_orientation(frm) {
	// patient-orientation expects a Vital Signs docname as `triage` route option
	const triage = frm.doc.vital_signs_record;
	if (!triage) {
		frappe.msgprint(__("Open or link a Vital Signs record before orienting the patient."));
		return;
	}
	frappe.route_options = { triage: triage };
	frappe.set_route("patient-orientation");
}
