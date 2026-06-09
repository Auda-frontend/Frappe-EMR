// Copyright (c) 2026, Rwanda EMR and contributors

frappe.ui.form.on("Triage Visit", {
	refresh(frm) {
		if (frm.doc.patient) {
			rw_triage_visit_set_patient_type(frm);
		} else {
			rw_triage_visit_update_banner(frm);
		}
		if (frm.doc.rw_triage_category) {
			apply_color_style(frm, frm.doc.rw_triage_category);
		}
	},

	patient(frm) {
		rw_triage_visit_set_patient_type(frm);
	},

	rw_triage_form_selector(frm) {
		rw_triage_visit_apply_form_selector(frm);
	},

	respiratory_rate(frm) {
		calculate_tews(frm);
	},
	pulse(frm) {
		calculate_tews(frm);
	},
	bp_systolic(frm) {
		calculate_tews(frm);
	},
	temperature(frm) {
		calculate_tews(frm);
	},
	tews_mobility(frm) {
		calculate_tews(frm);
	},
	tews_avpu(frm) {
		calculate_tews(frm);
	},
	tews_trauma(frm) {
		calculate_tews(frm);
	},
	rw_spo2(frm) {
		set_triage_color(frm);
	},
	rw_triage_manual_override(frm) {
		set_triage_color(frm);
	},

	height(frm) {
		calculate_bmi(frm);
	},
	weight(frm) {
		calculate_bmi(frm);
	},
});

function rw_triage_visit_patient_sex(patient) {
	const sex = (patient.sex || "").trim();
	if (!sex) {
		return "";
	}
	return sex;
}

function rw_triage_visit_is_female(sex) {
	return String(sex).toLowerCase() === "female";
}

function rw_triage_visit_resolve_form_type(age_years, sex) {
	if (age_years >= 3 && age_years <= 12) {
		return {
			is_child: 1,
			is_maternity: 0,
			is_adult: 0,
			label: __("Child Triage (3–12 years)"),
		};
	}
	if (age_years > 12 && rw_triage_visit_is_female(sex)) {
		return {
			is_child: 0,
			is_maternity: 1,
			is_adult: 0,
			label: __("Maternity Triage (Female, over 12 years)"),
		};
	}
	if (age_years > 12) {
		return {
			is_child: 0,
			is_maternity: 0,
			is_adult: 1,
			label: __("Adult Triage (Over 12 years)"),
		};
	}
	// Under 3 years — use child form as closest match
	return {
		is_child: 1,
		is_maternity: 0,
		is_adult: 0,
		label: __("Child Triage (under 3 years)"),
	};
}

function rw_triage_visit_set_patient_type(frm) {
	if (!frm.doc.patient) {
		return;
	}
	frappe.db.get_doc("Patient", frm.doc.patient).then((patient) => {
		const sex = rw_triage_visit_patient_sex(patient);
		let age_years = 0;
		if (patient.dob) {
			age_years = moment().diff(moment(patient.dob, "YYYY-MM-DD"), "years");
		}

		frm.set_value("patient_name", patient.patient_name);
		frm.set_value("patient_gender", sex);
		frm.set_value("patient_dob", patient.dob);
		frm.set_value("patient_age", age_years);

		if (!frm.doc.medical_record_number) {
			frm.set_value("medical_record_number", patient.name);
		}
		if (!frm.doc.company && patient.default_company) {
			frm.set_value("company", patient.default_company);
		}

		const selector = frm.doc.rw_triage_form_selector || "Auto (from patient)";
		if (selector === "Auto (from patient)") {
			const form = rw_triage_visit_resolve_form_type(age_years, sex);
			frm.set_value("is_child", form.is_child);
			frm.set_value("is_maternity", form.is_maternity);
			frm.set_value("is_adult", form.is_adult);
			frm.set_value("rw_triage_form_type", form.label);
			rw_triage_visit_update_banner(frm, form.label, age_years, sex);
		} else {
			rw_triage_visit_apply_form_selector(frm, age_years, sex);
		}
		frm.refresh_fields();
	});
}

function rw_triage_visit_apply_form_selector(frm, age_years, sex) {
	const selector = frm.doc.rw_triage_form_selector || "Auto (from patient)";
	age_years = age_years != null ? age_years : frm.doc.patient_age;
	sex = sex || frm.doc.patient_gender || "";

	if (selector === "Auto (from patient)") {
		if (frm.doc.patient) {
			rw_triage_visit_set_patient_type(frm);
		}
		return;
	}

	let form;
	if (selector === "Show All Forms") {
		form = {
			is_child: 0,
			is_maternity: 0,
			is_adult: 0,
			label: __("All Triage Forms (Adult, Child & Maternity)"),
		};
	} else if (selector === "Child") {
		form = { is_child: 1, is_maternity: 0, is_adult: 0, label: __("Child Triage") };
	} else if (selector === "Maternity") {
		form = { is_child: 0, is_maternity: 1, is_adult: 0, label: __("Maternity Triage") };
	} else {
		form = { is_child: 0, is_maternity: 0, is_adult: 1, label: __("Adult Triage") };
	}

	frm.set_value("is_child", form.is_child);
	frm.set_value("is_maternity", form.is_maternity);
	frm.set_value("is_adult", form.is_adult);
	frm.set_value("rw_triage_form_type", form.label);
	rw_triage_visit_update_banner(frm, form.label, age_years, sex);
	frm.refresh_fields();
}

function rw_triage_visit_update_banner(frm, label, age_years, sex) {
	label = label || frm.doc.rw_triage_form_type || __("Select a patient");
	age_years = age_years != null ? age_years : frm.doc.patient_age;
	sex = sex || frm.doc.patient_gender || "";

	let alert_class = "text-muted";
	if (frm.doc.is_maternity) {
		alert_class = "alert alert-info";
	} else if (frm.doc.is_child) {
		alert_class = "alert alert-warning";
	} else if (frm.doc.is_adult) {
		alert_class = "alert alert-primary";
	}

	const html = `<div class="${alert_class}" style="margin-bottom:8px;">
		<strong>${frappe.utils.escape_html(label)}</strong>
		${age_years != null ? ` &mdash; ${__("Age")}: ${age_years}, ${__("Gender")}: ${frappe.utils.escape_html(sex || "?")}` : ""}
	</div>`;

	if (frm.fields_dict.rw_form_type_banner) {
		frm.fields_dict.rw_form_type_banner.$wrapper.html(html);
	}
}

function calculate_tews(frm) {
	let score = 0;
	let doc = frm.doc;
	let child = doc.is_child;

	score += parseInt(doc.tews_mobility || 0, 10);

	let rr = parseInt(doc.respiratory_rate || 0, 10);
	let rr_score = 0;
	if (child) {
		if (rr < 15) rr_score = 3;
		else if (rr <= 16) rr_score = 2;
		else if (rr <= 21) rr_score = 0;
		else if (rr <= 26) rr_score = 1;
		else rr_score = 2;
	} else {
		if (rr < 9) rr_score = 2;
		else if (rr <= 14) rr_score = 0;
		else if (rr <= 20) rr_score = 1;
		else if (rr <= 29) rr_score = 2;
		else rr_score = 3;
	}
	score += rr_score;
	frm.set_value("tews_rr", rr_score);

	let hr = parseInt(doc.pulse || 0, 10);
	let hr_score = 0;
	if (child) {
		if (hr < 60) hr_score = 3;
		else if (hr <= 79) hr_score = 2;
		else if (hr <= 99) hr_score = 1;
		else if (hr <= 129) hr_score = 0;
		else hr_score = 2;
	} else {
		if (hr < 41) hr_score = 3;
		else if (hr <= 50) hr_score = 2;
		else if (hr <= 100) hr_score = 0;
		else if (hr <= 110) hr_score = 1;
		else if (hr <= 129) hr_score = 2;
		else hr_score = 3;
	}
	score += hr_score;
	frm.set_value("tews_hr", hr_score);

	let sbp_score = 0;
	if (!child) {
		let sbp = parseInt(doc.bp_systolic || 0, 10);
		if (sbp < 71) sbp_score = 3;
		else if (sbp <= 80) sbp_score = 2;
		else if (sbp <= 100) sbp_score = 1;
		else if (sbp <= 199) sbp_score = 0;
		else sbp_score = 2;
		score += sbp_score;
	}
	frm.set_value("tews_sbp", sbp_score);

	let temp = parseFloat(doc.temperature || 0);
	let temp_score = 0;
	if (temp > 0 && temp < 35) temp_score = 2;
	else if (temp >= 35 && temp <= 38.4) temp_score = 0;
	else if (temp > 38.4) temp_score = 1;
	score += temp_score;
	frm.set_value("tews_temp", temp_score);

	const avpu_map = {
		Alert: 0,
		Confused: 1,
		Voice: 2,
		Pain: 3,
		Unresponsive: 3,
	};
	let avpu_score = avpu_map[doc.tews_avpu] || 0;
	score += avpu_score;
	frm.set_value("tews_avpu_score", avpu_score);

	let trauma_score = doc.tews_trauma === "Yes" ? 1 : 0;
	score += trauma_score;
	frm.set_value("tews_trauma_score", trauma_score);

	frm.set_value("tews_total", score);
	set_triage_color(frm);
}

function set_triage_color(frm) {
	if (frm.doc.rw_triage_manual_override) {
		frm.set_value("rw_triage_category", frm.doc.rw_triage_manual_override);
		apply_color_style(frm, frm.doc.rw_triage_manual_override);
		return;
	}

	let score = parseInt(frm.doc.tews_total || 0, 10);
	let spo2 = parseFloat(frm.doc.rw_spo2 || 100);
	let color;

	if (score >= 7 || spo2 < 92) color = "RED";
	else if (score >= 5) color = "ORANGE";
	else if (score >= 3) color = "YELLOW";
	else color = "GREEN";

	frm.set_value("rw_triage_category", color);
	apply_color_style(frm, color);
}

function apply_color_style(frm, color) {
	if (!frm.fields_dict.rw_triage_category) {
		return;
	}
	const map = { RED: "#c0392b", ORANGE: "#e67e22", YELLOW: "#f1c40f", GREEN: "#27ae60" };
	const text = { RED: "#fff", ORANGE: "#fff", YELLOW: "#333", GREEN: "#fff" };
	frm.fields_dict.rw_triage_category.$wrapper.find(".control-value, input").css({
		"background-color": map[color] || "",
		color: text[color] || "",
		"font-weight": "bold",
		"border-radius": "4px",
		padding: "2px 8px",
	});
}

function calculate_bmi(frm) {
	let h = parseFloat(frm.doc.height || 0);
	let w = parseFloat(frm.doc.weight || 0);
	if (h > 0 && w > 0) {
		frm.set_value("bmi", Math.round((w / (h * h)) * 10) / 10);
	}
}
