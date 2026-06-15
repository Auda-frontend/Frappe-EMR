// Rwanda triage desk — auto priority, then orientation (visit created at orient)

frappe.ui.form.on("Vital Signs", {
	refresh(frm) {
		rw_triage_setup_desk(frm);
		rw_triage_apply_color_lock(frm);
		rw_triage_calc_bmi(frm);
	},

	onload(frm) {
		if (frm.is_new() && frappe.route_options) {
			const ro = frappe.route_options;
			["patient", "encounter", "appointment", "company"].forEach((f) => {
				if (ro[f] && !frm.doc[f]) {
					frm.set_value(f, ro[f]);
				}
			});
			if (ro.rw_chief_complaint && !frm.doc.rw_chief_complaint) {
				frm.set_value("rw_chief_complaint", ro.rw_chief_complaint);
			}
		}
	},

	rw_triage_manual_override(frm) {
		rw_triage_recompute(frm);
	},

	temperature(frm) {
		rw_triage_recompute(frm);
	},
	pulse(frm) {
		rw_triage_recompute(frm);
	},
	respiratory_rate(frm) {
		rw_triage_recompute(frm);
	},
	bp_systolic(frm) {
		rw_triage_recompute(frm);
	},
	bp_diastolic(frm) {
		rw_triage_recompute(frm);
	},
	rw_spo2(frm) {
		rw_triage_recompute(frm);
	},
	rw_pain_score(frm) {
		rw_triage_recompute(frm);
	},

	height(frm) {
		rw_triage_calc_bmi(frm);
	},
	weight(frm) {
		rw_triage_calc_bmi(frm);
	},
});

function rw_triage_calc_bmi(frm) {
	const h = parseFloat(frm.doc.height || 0);
	const w = parseFloat(frm.doc.weight || 0);
	if (h > 0 && w > 0) {
		frm.set_value("bmi", Math.round((w / (h * h)) * 10) / 10);
	}
}

function rw_triage_apply_color_lock(frm) {
	const auto_filled = [
		"rw_triage_category",
		"rw_triage_color",
		"rw_spo2",
		"rw_pain_score",
		"temperature",
		"pulse",
		"respiratory_rate",
		"bp_systolic",
		"rw_tews_score",
		"rw_form_type",
		"rw_triage_assessment",
		"signs_date",
		"signs_time",
	];
	auto_filled.forEach((f) => {
		if (frm.fields_dict[f]) frm.set_df_property(f, "read_only", 1);
	});

	const nurse_doctor_fields = [
		"rw_muac",
		"rw_triage_notes",
		"rw_oriented",
		"rw_chief_complaint",
		"tongue",
		"abdomen",
		"reflexes",
		"bp_diastolic",
		"vital_signs_note",
		"height",
		"weight",
		"bmi",
	];

	const color = frm.doc.rw_triage_color;
	const opd = frm.doc.rw_triage_category;
	const is_critical =
		["RED", "ORANGE"].includes(color) || ["Emergency", "Urgent"].includes(opd);
	const is_nurse =
		frappe.user.has_role("Nursing User") ||
		frappe.user.has_role("Nurse") ||
		frappe.user.has_role("Triage Nurse");
	const is_doctor = frappe.user.has_role("Physician") || frappe.user.has_role("Doctor");
	const override = frm.doc.rw_triage_manual_override;

	if (is_critical && is_nurse && !is_doctor && !override) {
		nurse_doctor_fields.forEach((f) => {
			if (frm.fields_dict[f]) frm.set_df_property(f, "read_only", 1);
		});
		if (frm.dashboard) {
			frm.dashboard.set_headline_alert(
				'<span style="color:#dc2626;font-weight:bold;">RED/ORANGE — remaining fields to be completed by attending doctor</span>'
			);
		}
	} else {
		nurse_doctor_fields.forEach((f) => {
			if (frm.fields_dict[f] && !frm.doc.rw_triage_assessment) {
				// chief complaint may stay read-only when from assessment
				if (f === "rw_chief_complaint" && frm.doc.rw_triage_assessment) return;
			}
			if (frm.fields_dict[f]) frm.set_df_property(f, "read_only", 0);
		});
		if (frm.doc.rw_triage_assessment && frm.fields_dict.rw_chief_complaint) {
			frm.set_df_property("rw_chief_complaint", "read_only", 1);
		}
	}
}

function rw_triage_setup_desk(frm) {
	if (!frm.fields_dict.rw_triage_category) {
		return;
	}

	if (frm.doc.rw_triage_category === "Emergency") {
		frm.dashboard.add_indicator(__("Emergency — attend immediately"), "red");
	} else if (frm.doc.rw_triage_category === "Urgent") {
		frm.dashboard.add_indicator(__("Urgent"), "orange");
	}

	if (frm.is_new()) {
		frm.set_intro(
			__(
				"Record vitals and chief complaint. Priority is set automatically from alarming signs. After save, orient the patient to a service (OPD, NCD, …) to create their visit."
			),
			"blue"
		);
	}

	if (!frm.is_new() && !frm.doc.rw_oriented) {
		frm.add_custom_button(__("Orient to service"), () => rw_triage_open_orientation(frm), __("Workflow"));
		frm.add_custom_button(
			__("Open orientation desk"),
			() => frappe.set_route("patient-orientation"),
			__("Workflow")
		);
	} else if (frm.doc.rw_oriented) {
		frm.set_intro(__("Patient oriented — visit created. Use Department Queue to call patient."), "green");
	}
}

function rw_triage_recompute(frm) {
	if (frm.doc.rw_triage_manual_override) {
		return;
	}
	frappe.call({
		method: "healthcare.healthcare.rwanda_opd.compute_triage_priority_api",
		args: { doc: frm.doc },
		callback(r) {
			if (!r.message) {
				return;
			}
			frm.set_value("rw_triage_category", r.message.category);
			frm.set_value("rw_triage_alerts", (r.message.alerts || []).join("\n"));
		},
	});
}

function rw_triage_open_orientation(frm) {
	if (!frm.doc.name) {
		frappe.msgprint(__("Save triage before orienting the patient."));
		return;
	}
	frappe.route_options = { triage: frm.doc.name };
	frappe.set_route("patient-orientation");
}
