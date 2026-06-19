// ============================================================
// Rwanda Triage — Shared Form Logic
// Covers: Adult (>12 yrs), Child (3–12 yrs), Infant (0–3 yrs), Maternity
// ============================================================

function rwanda_triage_form_init(form_key, doctype) {

	const TEWS_RANGES = {
		adult: {
			rr: [
				{ min: 0,   max: 8,   score: 3 },
				{ min: 9,   max: 14,  score: 0 },
				{ min: 15,  max: 20,  score: 1 },
				{ min: 21,  max: 29,  score: 2 },
				{ min: 30,  max: 999, score: 3 }
			],
			hr: [
				{ min: 0,   max: 40,  score: 3 },
				{ min: 41,  max: 50,  score: 1 },
				{ min: 51,  max: 100, score: 0 },
				{ min: 101, max: 110, score: 1 },
				{ min: 111, max: 129, score: 2 },
				{ min: 130, max: 999, score: 3 }
			],
			sbp: [
				{ min: 0,   max: 70,  score: 3 },
				{ min: 71,  max: 80,  score: 2 },
				{ min: 81,  max: 100, score: 1 },
				{ min: 101, max: 199, score: 0 },
				{ min: 200, max: 999, score: 2 }
			],
			temperature: [
				{ min: 0,    max: 34.9, score: 2 },
				{ min: 35,   max: 38.4, score: 0 },
				{ min: 38.5, max: 999,  score: 1 }
			]
		},

		child: {
			rr: [
				{ min: 0,  max: 14,  score: 3 },
				{ min: 15, max: 16,  score: 0 },
				{ min: 17, max: 21,  score: 1 },
				{ min: 22, max: 26,  score: 2 },
				{ min: 27, max: 999, score: 3 }
			],
			hr: [
				{ min: 0,   max: 59,  score: 3 },
				{ min: 60,  max: 79,  score: 2 },
				{ min: 80,  max: 99,  score: 1 },
				{ min: 100, max: 129, score: 0 },
				{ min: 130, max: 999, score: 3 }
			],
			temperature: [
				{ min: 0,    max: 34.9, score: 2 },
				{ min: 35,   max: 38.4, score: 0 },
				{ min: 38.5, max: 999,  score: 1 }
			]
		},

		infant: {
			rr: [
				{ min: 0,  max: 19,  score: 3 },
				{ min: 20, max: 25,  score: 1 },
				{ min: 26, max: 39,  score: 0 },
				{ min: 40, max: 49,  score: 1 },
				{ min: 50, max: 999, score: 2 }
			],
			hr: [
				{ min: 0,   max: 69,  score: 3 },
				{ min: 70,  max: 79,  score: 2 },
				{ min: 80,  max: 130, score: 0 },
				{ min: 131, max: 159, score: 2 },
				{ min: 160, max: 999, score: 3 }
			],
			temperature: [
				{ min: 0,    max: 34.9, score: 2 },
				{ min: 35,   max: 38.4, score: 0 },
				{ min: 38.5, max: 999,  score: 1 }
			]
		},

		maternity: {
			rr: [
				{ min: 0,   max: 8,   score: 3 },
				{ min: 9,   max: 14,  score: 0 },
				{ min: 15,  max: 20,  score: 1 },
				{ min: 21,  max: 29,  score: 2 },
				{ min: 30,  max: 999, score: 3 }
			],
			hr: [
				{ min: 0,   max: 40,  score: 3 },
				{ min: 41,  max: 50,  score: 1 },
				{ min: 51,  max: 100, score: 0 },
				{ min: 101, max: 110, score: 1 },
				{ min: 111, max: 129, score: 2 },
				{ min: 130, max: 999, score: 3 }
			],
			sbp: [
				{ min: 0,   max: 70,  score: 3 },
				{ min: 71,  max: 80,  score: 2 },
				{ min: 81,  max: 100, score: 1 },
				{ min: 101, max: 199, score: 0 },
				{ min: 200, max: 999, score: 2 }
			],
			temperature: [
				{ min: 0,    max: 34.9, score: 2 },
				{ min: 35,   max: 38.4, score: 0 },
				{ min: 38.5, max: 999,  score: 1 }
			]
		}
	};

	const BASE_ALARM_FIELDS = [
		"alarm_not_breathing",
		"alarm_obstructed_breathing",
		"alarm_severe_resp_distress",
		"alarm_cardiac_arrest",
		"alarm_hemorrhage_uncontrolled",
		"alarm_stab_gunshot",
		"alarm_lethargic",
		"alarm_weak_fast_pulse",
		"alarm_cap_refill_3sec",
		"alarm_cold_hands",
		"alarm_convulsion",
		"alarm_coma",
		"alarm_hypoglycemia",
		"alarm_purpuric_rash",
		"alarm_burn_face_inhalation"
	];

	const CHILD_INFANT_EXTRA_ALARMS = [
		"alarm_not_breathing_weak",
		"alarm_central_cyanosis",
		"alarm_pulse_low_absent"
	];

	const MATERNITY_EXTRA_ALARMS = [
		"alarm_prolapsed_cord",
		"alarm_no_fetal_movement",
		"alarm_bandel_ring",
		"alarm_abnormal_ctg",
		"alarm_stab_gunshot_maternity",
		"alarm_imminent_birth"
	];

	const YELLOW_ADULT_CHILD = [
		"yellow_focal_neuro",
		"yellow_altered_mental",
		"yellow_chest_pain",
		"yellow_poisoning",
		"yellow_coughing_blood",
		"yellow_diabetic_high",
		"yellow_aggression",
		"yellow_acute_sob",
		"yellow_severe_pain",
		"yellow_burn_20_urgent",
		"yellow_fracture_open",
		"yellow_threatened_limb",
		"yellow_eye_injury",
		"yellow_large_joint_disloc",
		"yellow_severe_mechanism",
		"yellow_abdominal_trauma"
	];

	const YELLOW_INFANT = [
		"yellow_more_sleep",
		"yellow_focal_neuro",
		"yellow_inconsolable_cry",
		"yellow_floppy_irritable",
		"yellow_chest_pain",
		"yellow_poisoning",
		"yellow_tiny_baby",
		"yellow_burn_10_urgent",
		"yellow_fracture_open",
		"yellow_threatened_limb",
		"yellow_eye_injury",
		"yellow_large_joint_disloc",
		"yellow_severe_mechanism"
	];

	const YELLOW_MATERNITY = [
		"yellow_multipara_active_labour",
		"yellow_uterine_contraction",
		"yellow_rom",
		"yellow_decreased_fetal_movements",
		"yellow_bleeding_spotting",
		"yellow_preterm_labour",
		"yellow_contraction_planned_cs",
		"yellow_preeclampsia",
		"yellow_altered_mental",
		"yellow_burn_20_urgent",
		"yellow_poisoning",
		"yellow_fracture_open",
		"yellow_large_joint_disloc",
		"yellow_major_trauma",
		"yellow_coughing_blood",
		"yellow_abdominal_trauma_severe_pain"
	];

	const GREEN_ADULT_CHILD = [
		"green_cant_drink",
		"green_very_pale",
		"green_resp_distress",
		"green_diabetic_high",
		"green_malnutrition",
		"green_moderate_pain",
		"green_disloc_finger_toe",
		"green_fracture_closed",
		"green_burn_no_urgency"
	];

	const GREEN_INFANT = [
		"green_pitting_oedema",
		"green_cant_drink",
		"green_severe_pallor",
		"green_resp_distress",
		"green_known_diabetes",
		"green_malnutrition",
		"green_diarrhea_vomiting",
		"green_dv_sunken_eyes",
		"green_dv_dry_mouth",
		"green_dv_decreased_urine",
		"green_dv_skin_pinch_slow",
		"green_disloc_finger_toe",
		"green_fracture_closed",
		"green_burn_no_urgency",
		"green_moderate_pain"
	];

	const GREEN_MATERNITY = [
		"green_active_labor",
		"green_miscarriage",
		"green_malpresentation",
		"green_planned_cs_multiple",
		"green_rom_above_6hr",
		"green_cant_drink",
		"green_known_diabetes",
		"green_malnutrition",
		"green_fracture_closed_moderate_pain",
		"green_burn_no_urgency"
	];

	function get_alarm_fields(fk) {
		const fields = [...BASE_ALARM_FIELDS];
		if (fk === "child" || fk === "infant") {
			fields.push(...CHILD_INFANT_EXTRA_ALARMS);
		}
		if (fk === "maternity") {
			fields.push(...MATERNITY_EXTRA_ALARMS);
		}
		return fields;
	}

	function get_yellow_fields(fk) {
		if (fk === "infant") return YELLOW_INFANT;
		if (fk === "maternity") return YELLOW_MATERNITY;
		return YELLOW_ADULT_CHILD;
	}

	function get_green_fields(fk) {
		if (fk === "infant") return GREEN_INFANT;
		if (fk === "maternity") return GREEN_MATERNITY;
		return GREEN_ADULT_CHILD;
	}

	function get_range_score(value, ranges) {
		if (value === null || value === undefined || value === "") return 0;
		for (let r of ranges) {
			if (value >= r.min && value <= r.max) return r.score;
		}
		return 0;
	}

	function get_avpu_score(avpu) {
		return { "Alert": 0, "Confused": 1, "Voice": 2, "Pain": 3, "Unresponsive": 3 }[avpu] || 0;
	}

	function get_mobility_score(mobility) {
		return parseInt(mobility) || 0;
	}

	function calculate_tews(frm, fk, ranges) {
		const r = ranges[fk] || ranges.adult;
		let tews = 0;

		const rr_score = get_range_score(frm.doc.rr, r.rr);
		frm.set_value("rr_score", rr_score);
		tews += rr_score;

		const hr_score = get_range_score(frm.doc.hr, r.hr);
		frm.set_value("hr_score", hr_score);
		tews += hr_score;

		if (fk === "adult" || fk === "maternity") {
			const sbp_score = get_range_score(frm.doc.sbp, r.sbp);
			frm.set_value("sbp_score", sbp_score);
			tews += sbp_score;
		}

		const temp_score = get_range_score(frm.doc.temperature, r.temperature);
		frm.set_value("temp_score", temp_score);
		tews += temp_score;

		const avpu_score = get_avpu_score(frm.doc.avpu);
		frm.set_value("avpu_score", avpu_score);
		tews += avpu_score;

		const mobility_score = get_mobility_score(frm.doc.mobility);
		frm.set_value("mobility_score", mobility_score);
		tews += mobility_score;

		const trauma_score = frm.doc.trauma ? 2 : 0;
		frm.set_value("trauma_score", trauma_score);
		tews += trauma_score;

		frm.set_value("tews_score", tews);
	}

	function apply_triage_color_display(frm, color) {
		if (!frm.fields_dict.triage_color || !color) return;
		const colors = {
			RED: "#dc2626",
			ORANGE: "#ea580c",
			YELLOW: "#ca8a04",
			GREEN: "#16a34a",
		};
		frm.fields_dict.triage_color.$wrapper
			.find(".control-value, .form-control, input, select")
			.css({
				"background-color": colors[color] || "",
				color: "#fff",
				"font-weight": "bold",
			});
	}

	function assign_triage_color(frm, fk) {
		if (frm.doc.manual_priority_override) {
			update_triage_priority_alert(frm);
			apply_triage_color_display(frm, frm.doc.triage_color);
			return;
		}

		let color = "GREEN";

		const alarm_fields = get_alarm_fields(fk);
		for (let f of alarm_fields) {
			if (frm.doc[f]) { color = "RED"; break; }
		}

		if (color !== "RED") {
			const dehyd = [
				frm.doc.dehydration_skin_pinch,
				frm.doc.dehydration_lethargy,
				frm.doc.dehydration_sunken_eyes
			].filter(Boolean).length;
			if (dehyd >= 2) color = "RED";
		}

		if (color !== "RED") {
			const tews = frm.doc.tews_score || 0;
			const spo2 = frm.doc.spo2;
			if (tews >= 7) color = "RED";
			else if (spo2 !== null && spo2 !== undefined && spo2 !== "" && spo2 < 92) color = "RED";
		}

		if (color === "GREEN") {
			const tews = frm.doc.tews_score || 0;
			if (tews >= 5 && tews <= 6) color = "ORANGE";
		}

		if (color === "GREEN") {
			const yellow_fields = get_yellow_fields(fk);
			for (let f of yellow_fields) {
				if (frm.doc[f]) { color = "YELLOW"; break; }
			}
		}

		if (color === "GREEN") {
			const tews = frm.doc.tews_score || 0;
			if (tews >= 3 && tews <= 4) color = "YELLOW";
		}

		frm.set_value("triage_color", color);
		frm.set_df_property("triage_color", "bold", true);
		apply_triage_color_display(frm, color);
		update_triage_priority_alert(frm, color);
	}

	function recompute(frm) {
		calculate_tews(frm, form_key, TEWS_RANGES);
		assign_triage_color(frm, form_key);
	}

	const vitals = ["rr", "hr", "sbp", "temperature", "avpu", "mobility", "trauma", "spo2", "pain_score"];
	const all_triggers = vitals.concat(
		get_alarm_fields(form_key),
		["dehydration_skin_pinch", "dehydration_lethargy", "dehydration_sunken_eyes"],
		get_yellow_fields(form_key),
		get_green_fields(form_key)
	);

	const handlers = {
		onload(frm) {
			if (frm.is_new() && frappe.route_options && frappe.route_options.parent_triage) {
				frm.set_value("parent_triage", frappe.route_options.parent_triage);
			}
		},

		refresh(frm) {
			update_triage_priority_alert(frm);
			apply_triage_color_display(frm, frm.doc.triage_color);
		},

		manual_priority_override(frm) {
			if (!frm.doc.manual_priority_override) {
				recompute(frm);
			} else {
				update_triage_priority_alert(frm);
				apply_triage_color_display(frm, frm.doc.triage_color);
			}
		},
	};

	all_triggers.forEach((field) => {
		handlers[field] = function (frm) {
			if (["rr", "hr", "sbp", "temperature", "avpu", "mobility", "trauma"].includes(field)) {
				calculate_tews(frm, form_key, TEWS_RANGES);
			}
			assign_triage_color(frm, form_key);
		};
	});

	frappe.ui.form.on(doctype, handlers);
}

window.rwanda_triage_form_init = rwanda_triage_form_init;

window.update_triage_priority_alert = function update_triage_priority_alert(frm, color) {
	color = color || frm.doc.triage_color;
	if (!color) return;

	const COLOR_STYLE = {
		RED: "red",
		ORANGE: "orange",
		YELLOW: "yellow",
		GREEN: "green",
	};
	const style = COLOR_STYLE[color] || "blue";

	if (color === "RED" || color === "ORANGE") {
		frm.dashboard.set_headline_alert(
			__("{0} — orient this patient immediately.", [__(color)]),
			style
		);
		frm.set_intro(
			__("Immediate orientation required. {0} priority patient.", [__(color)]),
			style
		);
	} else if (color === "YELLOW") {
		frm.dashboard.clear_headline_alert();
		frm.set_intro(__("YELLOW priority — seen within 60 minutes."), "yellow");
	} else {
		frm.dashboard.clear_headline_alert();
		frm.set_intro(__("GREEN priority — seen within 4 hours."), "green");
	}
};

// Adult doctype script has init disabled; register it here.
rwanda_triage_form_init("adult", "Adult Triage Form");
