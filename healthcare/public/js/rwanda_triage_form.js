// Shared Triage Form Logic
// This template is used by all 4 age-specific triage forms
// Each form passes its specific FORM_TYPE and configuration to this function

function rwanda_triage_form_init(form_key, doctype) {
	// TEWS Scoring ranges by form type
	const TEWS_RANGES = {
		adult: {
			rr: [
				{ min: 0, max: 8, score: -2 },
				{ min: 9, max: 14, score: 0 },
				{ min: 15, max: 20, score: 1 },
				{ min: 21, max: 29, score: 2 },
				{ min: 30, max: 999, score: 3 }
			],
			hr: [
				{ min: 0, max: 40, score: 3 },
				{ min: 41, max: 50, score: 1 },
				{ min: 51, max: 100, score: 0 },
				{ min: 101, max: 110, score: 1 },
				{ min: 111, max: 129, score: 2 },
				{ min: 130, max: 999, score: 3 }
			],
			sbp: [
				{ min: 0, max: 90, score: 3 },
				{ min: 91, max: 100, score: 2 },
				{ min: 101, max: 199, score: 0 },
				{ min: 200, max: 999, score: 2 }
			],
			temperature: [
				{ min: 0, max: 35, score: 2 },
				{ min: 35.1, max: 38.4, score: 0 },
				{ min: 38.5, max: 39, score: 1 },
				{ min: 39.1, max: 999, score: 2 }
			]
		},
		child: {
			rr: [
				{ min: 0, max: 14, score: 3 },
				{ min: 15, max: 16, score: 0 },
				{ min: 17, max: 21, score: 1 },
				{ min: 22, max: 26, score: 2 },
				{ min: 27, max: 999, score: 3 }
			],
			hr: [
				{ min: 0, max: 80, score: 3 },
				{ min: 81, max: 100, score: 0 },
				{ min: 101, max: 110, score: 1 },
				{ min: 111, max: 130, score: 2 },
				{ min: 131, max: 999, score: 3 }
			],
			temperature: [
				{ min: 0, max: 35, score: 2 },
				{ min: 35.1, max: 38.4, score: 0 },
				{ min: 38.5, max: 39, score: 1 },
				{ min: 39.1, max: 999, score: 2 }
			]
		},
		infant: {
			rr: [
				{ min: 0, max: 19, score: 3 },
				{ min: 20, max: 25, score: 1 },
				{ min: 26, max: 39, score: 0 },
				{ min: 40, max: 49, score: 1 },
				{ min: 50, max: 999, score: 2 }
			],
			hr: [
				{ min: 0, max: 100, score: 3 },
				{ min: 101, max: 120, score: 0 },
				{ min: 121, max: 140, score: 1 },
				{ min: 141, max: 160, score: 2 },
				{ min: 161, max: 999, score: 3 }
			],
			temperature: [
				{ min: 0, max: 35, score: 2 },
				{ min: 35.1, max: 38.4, score: 0 },
				{ min: 38.5, max: 39, score: 1 },
				{ min: 39.1, max: 999, score: 2 }
			]
		},
		maternity: {
			rr: [
				{ min: 0, max: 8, score: -2 },
				{ min: 9, max: 14, score: 0 },
				{ min: 15, max: 20, score: 1 },
				{ min: 21, max: 29, score: 2 },
				{ min: 30, max: 999, score: 3 }
			],
			hr: [
				{ min: 0, max: 40, score: 3 },
				{ min: 41, max: 50, score: 1 },
				{ min: 51, max: 100, score: 0 },
				{ min: 101, max: 110, score: 1 },
				{ min: 111, max: 129, score: 2 },
				{ min: 130, max: 999, score: 3 }
			],
			sbp: [
				{ min: 0, max: 90, score: 3 },
				{ min: 91, max: 100, score: 2 },
				{ min: 101, max: 199, score: 0 },
				{ min: 200, max: 999, score: 2 }
			],
			temperature: [
				{ min: 0, max: 35, score: 2 },
				{ min: 35.1, max: 38.4, score: 0 },
				{ min: 38.5, max: 39, score: 1 },
				{ min: 39.1, max: 999, score: 2 }
			]
		}
	};

	frappe.ui.form.on(doctype, {
		onload(frm) {
			if (frm.is_new() && frappe.route_options && frappe.route_options.parent_triage) {
				frm.set_value("parent_triage", frappe.route_options.parent_triage);
			}
		},

		refresh(frm) {
			calculate_tews(frm, form_key, TEWS_RANGES);
			assign_triage_color(frm);
		},

		rr(frm) {
			calculate_tews(frm, form_key, TEWS_RANGES);
		},
		hr(frm) {
			calculate_tews(frm, form_key, TEWS_RANGES);
		},
		sbp(frm) {
			calculate_tews(frm, form_key, TEWS_RANGES);
		},
		temperature(frm) {
			calculate_tews(frm, form_key, TEWS_RANGES);
		},
		avpu(frm) {
			calculate_tews(frm, form_key, TEWS_RANGES);
		},
		mobility(frm) {
			calculate_tews(frm, form_key, TEWS_RANGES);
		},

		// Alarm signs change
		alarm_not_breathing(frm) { assign_triage_color(frm); },
		alarm_obstructed_breathing(frm) { assign_triage_color(frm); },
		alarm_severe_resp_distress(frm) { assign_triage_color(frm); },
		alarm_cardiac_arrest(frm) { assign_triage_color(frm); },
		alarm_hemorrhage_uncontrolled(frm) { assign_triage_color(frm); },
		alarm_stab_gunshot(frm) { assign_triage_color(frm); },
		alarm_lethargic(frm) { assign_triage_color(frm); },
		alarm_weak_fast_pulse(frm) { assign_triage_color(frm); },
		alarm_cap_refill_3sec(frm) { assign_triage_color(frm); },
		alarm_cold_hands(frm) { assign_triage_color(frm); },
		alarm_convulsion(frm) { assign_triage_color(frm); },
		alarm_coma(frm) { assign_triage_color(frm); },
		alarm_hypoglycemia(frm) { assign_triage_color(frm); },
		alarm_purpuric_rash(frm) { assign_triage_color(frm); },
		alarm_burn_face_inhalation(frm) { assign_triage_color(frm); },

		// Dehydration
		dehydration_skin_pinch(frm) { assign_triage_color(frm); },
		dehydration_lethargy(frm) { assign_triage_color(frm); },
		dehydration_sunken_eyes(frm) { assign_triage_color(frm); },

		// Yellow signs
		yellow_focal_neuro(frm) { assign_triage_color(frm); },
		yellow_altered_mental(frm) { assign_triage_color(frm); },
		yellow_chest_pain(frm) { assign_triage_color(frm); },
		yellow_poisoning(frm) { assign_triage_color(frm); },
		yellow_coughing_blood(frm) { assign_triage_color(frm); },
		yellow_diabetic_high(frm) { assign_triage_color(frm); },
		yellow_aggression(frm) { assign_triage_color(frm); },
		yellow_acute_sob(frm) { assign_triage_color(frm); },
		yellow_severe_pain(frm) { assign_triage_color(frm); },
		yellow_burn_20_urgent(frm) { assign_triage_color(frm); },
		yellow_fracture_open(frm) { assign_triage_color(frm); },
		yellow_threatened_limb(frm) { assign_triage_color(frm); },
		yellow_eye_injury(frm) { assign_triage_color(frm); },
		yellow_large_joint_disloc(frm) { assign_triage_color(frm); },
		yellow_severe_mechanism(frm) { assign_triage_color(frm); },
		yellow_abdominal_trauma(frm) { assign_triage_color(frm); },

		// Green signs
		green_cant_drink(frm) { assign_triage_color(frm); },
		green_very_pale(frm) { assign_triage_color(frm); },
		green_resp_distress(frm) { assign_triage_color(frm); },
		green_diabetic_high(frm) { assign_triage_color(frm); },
		green_malnutrition(frm) { assign_triage_color(frm); },
		green_moderate_pain(frm) { assign_triage_color(frm); },
		green_disloc_finger_toe(frm) { assign_triage_color(frm); },
		green_fracture_closed(frm) { assign_triage_color(frm); },
		green_burn_no_urgency(frm) { assign_triage_color(frm); },

		spo2(frm) {
			assign_triage_color(frm);
		},
		pain_score(frm) {
			assign_triage_color(frm);
		}
	});

	function get_tews_score(value, ranges) {
		if (!value) return 0;
		for (let range of ranges) {
			if (value >= range.min && value <= range.max) {
				return range.score;
			}
		}
		return 0;
	}

	function get_avpu_score(avpu) {
		const scores = {
			"Alert": 0,
			"Confused": 1,
			"Voice": 2,
			"Pain": 3,
			"Unresponsive": 3
		};
		return scores[avpu] || 0;
	}

	function get_mobility_score(mobility) {
		const scores = {
			"0": 0,
			"1": 1,
			"2": 2,
			"3": 3
		};
		return scores[mobility] || 0;
	}

	function calculate_tews(frm, form_key, ranges) {
		const form_ranges = ranges[form_key] || ranges.adult;
		let tews = 0;

		// RR Score
		const rr_score = get_tews_score(frm.doc.rr, form_ranges.rr);
		frm.set_value("rr_score", rr_score);
		tews += rr_score;

		// HR Score
		const hr_score = get_tews_score(frm.doc.hr, form_ranges.hr);
		frm.set_value("hr_score", hr_score);
		tews += hr_score;

		// SBP Score (only for adult and maternity)
		if (form_key === "adult" || form_key === "maternity") {
			const sbp_score = get_tews_score(frm.doc.sbp, form_ranges.sbp);
			frm.set_value("sbp_score", sbp_score);
			tews += sbp_score;
		}

		// Temperature Score
		const temp_score = get_tews_score(frm.doc.temperature, form_ranges.temperature);
		frm.set_value("temp_score", temp_score);
		tews += temp_score;

		// AVPU Score
		const avpu_score = get_avpu_score(frm.doc.avpu);
		frm.set_value("avpu_score", avpu_score);
		tews += avpu_score;

		// Mobility Score
		const mobility_score = get_mobility_score(frm.doc.mobility);
		frm.set_value("mobility_score", mobility_score);
		tews += mobility_score;

		// Trauma Score
		const trauma_score = frm.doc.trauma ? 2 : 0;
		frm.set_value("trauma_score", trauma_score);
		tews += trauma_score;

		frm.set_value("tews_score", tews);
	}

	function assign_triage_color(frm) {
		let color = "GREEN";  // Default

		// Check for alarm signs (RED)
		const alarm_fields = [
			"alarm_not_breathing", "alarm_obstructed_breathing", "alarm_severe_resp_distress",
			"alarm_cardiac_arrest", "alarm_hemorrhage_uncontrolled", "alarm_stab_gunshot",
			"alarm_lethargic", "alarm_weak_fast_pulse", "alarm_cap_refill_3sec", "alarm_cold_hands",
			"alarm_convulsion", "alarm_coma", "alarm_hypoglycemia", "alarm_purpuric_rash",
			"alarm_burn_face_inhalation"
		];

		for (let field of alarm_fields) {
			if (frm.doc[field]) {
				color = "RED";
				break;
			}
		}

		// Check for severe dehydration (≥2 of 3 fields = RED)
		if (color !== "RED") {
			const dehydration_count = [
				frm.doc.dehydration_skin_pinch,
				frm.doc.dehydration_lethargy,
				frm.doc.dehydration_sunken_eyes
			].filter(v => v).length;
			if (dehydration_count >= 2) {
				color = "RED";
			}
		}

		// Check TEWS thresholds
		if (color === "GREEN") {
			const tews = frm.doc.tews_score || 0;
			if (tews >= 7) {
				color = "RED";
			} else if (tews >= 5) {
				color = "ORANGE";
			} else if (tews >= 3) {
				color = "YELLOW";
			}
		}

		// Check SpO2 threshold
		if (color === "GREEN" || color === "YELLOW") {
			const spo2 = frm.doc.spo2 || 0;
			if (spo2 < 92) {
				color = color === "YELLOW" ? "YELLOW" : "ORANGE";
			}
		}

		// Check for ORANGE thresholds
		if (color === "YELLOW" || color === "GREEN") {
			const tews = frm.doc.tews_score || 0;
			if (tews >= 5 && tews < 7) {
				color = "ORANGE";
			}
		}

		// Check yellow signs
		if (color === "GREEN") {
			const yellow_fields = [
				"yellow_focal_neuro", "yellow_altered_mental", "yellow_chest_pain",
				"yellow_poisoning", "yellow_coughing_blood", "yellow_diabetic_high",
				"yellow_aggression", "yellow_acute_sob", "yellow_severe_pain",
				"yellow_burn_20_urgent", "yellow_fracture_open", "yellow_threatened_limb",
				"yellow_eye_injury", "yellow_large_joint_disloc", "yellow_severe_mechanism",
				"yellow_abdominal_trauma"
			];

			for (let field of yellow_fields) {
				if (frm.doc[field]) {
					color = "YELLOW";
					break;
				}
			}
		}

		// Check green signs (if still GREEN)
		if (color === "GREEN") {
			const green_fields = [
				"green_cant_drink", "green_very_pale", "green_resp_distress",
				"green_diabetic_high", "green_malnutrition", "green_moderate_pain",
				"green_disloc_finger_toe", "green_fracture_closed", "green_burn_no_urgency"
			];

			let has_green_sign = false;
			for (let field of green_fields) {
				if (frm.doc[field]) {
					has_green_sign = true;
					break;
				}
			}

			// Only turn YELLOW if has green sign
			if (has_green_sign) {
				// stays GREEN unless other factors make it YELLOW
			}
		}

		// Display color with background
		frm.set_value("triage_color", color);
		frm.set_df_property("triage_color", "bold", true);
		update_triage_priority_alert(frm, color);
	}
}

function update_triage_priority_alert(frm, color) {
	color = color || frm.doc.triage_color;
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

