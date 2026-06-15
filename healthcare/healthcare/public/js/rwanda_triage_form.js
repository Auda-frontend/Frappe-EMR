// Shared TEWS scoring for Adult / Child / Infant / Maternity triage forms.

window.rwanda_triage_form_init = function (FORM_TYPE, DOCTYPE) {
	const BASE_ALARM_FIELDS = [
		"alarm_not_breathing", "alarm_obstructed_breathing", "alarm_severe_resp_distress",
		"alarm_cardiac_arrest", "alarm_hemorrhage_uncontrolled", "alarm_stab_gunshot",
		"alarm_lethargic", "alarm_weak_fast_pulse", "alarm_cap_refill_3sec", "alarm_cold_hands",
		"alarm_convulsion", "alarm_coma", "alarm_hypoglycemia", "alarm_purpuric_rash",
		"alarm_burn_face_inhalation",
	];
	const CHILD_INFANT_EXTRA = [
		"alarm_not_breathing_weak", "alarm_central_cyanosis", "alarm_pulse_low_absent",
	];
	const MATERNITY_EXTRA = [
		"alarm_prolapsed_cord", "alarm_no_fetal_movement", "alarm_bandel_ring",
		"alarm_abnormal_ctg", "alarm_stab_gunshot_maternity", "alarm_imminent_birth",
	];
	const YELLOW_ADULT_CHILD = [
		"yellow_focal_neuro", "yellow_altered_mental", "yellow_chest_pain", "yellow_poisoning",
		"yellow_coughing_blood", "yellow_diabetic_high", "yellow_aggression", "yellow_acute_sob",
		"yellow_severe_pain", "yellow_burn_20_urgent", "yellow_fracture_open",
		"yellow_threatened_limb", "yellow_eye_injury", "yellow_large_joint_disloc",
		"yellow_severe_mechanism", "yellow_abdominal_trauma",
	];
	const YELLOW_INFANT = [
		"yellow_more_sleep", "yellow_focal_neuro", "yellow_inconsolable_cry",
		"yellow_floppy_irritable", "yellow_chest_pain", "yellow_poisoning", "yellow_tiny_baby",
		"yellow_burn_10_urgent", "yellow_fracture_open", "yellow_threatened_limb",
		"yellow_eye_injury", "yellow_large_joint_disloc", "yellow_severe_mechanism",
	];
	const YELLOW_MATERNITY = [
		"yellow_multipara_active_labour", "yellow_uterine_contraction", "yellow_rom",
		"yellow_decreased_fetal_movements", "yellow_bleeding_spotting", "yellow_preterm_labour",
		"yellow_contraction_planned_cs", "yellow_preeclampsia", "yellow_altered_mental",
		"yellow_burn_20_urgent", "yellow_poisoning", "yellow_fracture_open",
		"yellow_large_joint_disloc", "yellow_major_trauma", "yellow_coughing_blood",
		"yellow_abdominal_trauma_severe_pain",
	];
	const GREEN_ADULT_CHILD = [
		"green_cant_drink", "green_very_pale", "green_resp_distress", "green_diabetic_high",
		"green_malnutrition", "green_moderate_pain", "green_disloc_finger_toe",
		"green_fracture_closed", "green_burn_no_urgency",
	];
	const GREEN_INFANT = [
		"green_pitting_oedema", "green_cant_drink", "green_severe_pallor", "green_resp_distress",
		"green_known_diabetes", "green_malnutrition", "green_diarrhea_vomiting",
		"green_dv_sunken_eyes", "green_dv_dry_mouth", "green_dv_decreased_urine",
		"green_dv_skin_pinch_slow", "green_disloc_finger_toe", "green_fracture_closed",
		"green_burn_no_urgency", "green_moderate_pain",
	];
	const GREEN_MATERNITY = [
		"green_active_labor", "green_miscarriage", "green_malpresentation",
		"green_planned_cs_multiple", "green_rom_above_6hr", "green_cant_drink",
		"green_known_diabetes", "green_malnutrition", "green_fracture_closed_moderate_pain",
		"green_burn_no_urgency",
	];

	function get_alarm_fields() {
		if (FORM_TYPE === "adult") return BASE_ALARM_FIELDS;
		if (FORM_TYPE === "maternity") return BASE_ALARM_FIELDS.concat(MATERNITY_EXTRA);
		return BASE_ALARM_FIELDS.concat(CHILD_INFANT_EXTRA);
	}
	function get_yellow_fields() {
		if (FORM_TYPE === "infant") return YELLOW_INFANT;
		if (FORM_TYPE === "maternity") return YELLOW_MATERNITY;
		return YELLOW_ADULT_CHILD;
	}
	function get_green_fields() {
		if (FORM_TYPE === "infant") return GREEN_INFANT;
		if (FORM_TYPE === "maternity") return GREEN_MATERNITY;
		return GREEN_ADULT_CHILD;
	}

	function score_rr(rr) {
		rr = parseInt(rr || 0, 10);
		if (FORM_TYPE === "adult" || FORM_TYPE === "maternity") {
			if (rr < 9) return -2;
			if (rr <= 14) return 0;
			if (rr <= 20) return 1;
			if (rr <= 29) return 2;
			return 3;
		}
		if (FORM_TYPE === "child") {
			if (rr < 15) return 3;
			if (rr <= 16) return 0;
			if (rr <= 21) return 1;
			if (rr <= 26) return 2;
			return 3;
		}
		if (rr < 20) return 3;
		if (rr <= 25) return 1;
		if (rr <= 39) return 0;
		if (rr <= 49) return 1;
		return 2;
	}

	function score_hr(hr) {
		hr = parseInt(hr || 0, 10);
		if (FORM_TYPE === "adult" || FORM_TYPE === "maternity") {
			if (hr < 41) return -3;
			if (hr <= 50) return -2;
			if (hr <= 100) return 0;
			if (hr <= 110) return 1;
			if (hr <= 129) return 2;
			return 3;
		}
		if (FORM_TYPE === "child") {
			if (hr < 60) return 3;
			if (hr <= 79) return 0;
			if (hr <= 99) return 1;
			if (hr <= 129) return 2;
			return 3;
		}
		if (hr < 70) return 3;
		if (hr <= 79) return 1;
		if (hr <= 130) return 0;
		if (hr <= 159) return 1;
		return 2;
	}

	function score_sbp(sbp) {
		sbp = parseInt(sbp || 0, 10);
		if (sbp < 71) return -3;
		if (sbp <= 80) return -2;
		if (sbp <= 100) return -1;
		if (sbp <= 199) return 0;
		return 2;
	}

	function score_temp(t) {
		t = parseFloat(t || 0);
		if (!t) return 0;
		if (t < 35) return 3;
		if (t <= 38.4) return 0;
		return 1;
	}

	function score_avpu(avpu) {
		return { Alert: 0, Confused: -1, Voice: 1, Pain: 2, Unresponsive: 3 }[avpu] || 0;
	}

	function score_mobility(val) {
		if (FORM_TYPE === "adult" || FORM_TYPE === "maternity") {
			return parseInt(val || 0, 10) || 0;
		}
		return parseInt(val, 10) === 1 ? 3 : 0;
	}

	function calc_tews(frm) {
		const d = frm.doc;
		const rr = score_rr(d.rr);
		const hr = score_hr(d.hr);
		const sbp = FORM_TYPE === "adult" || FORM_TYPE === "maternity" ? score_sbp(d.sbp) : 0;
		const tmp = score_temp(d.temperature);
		const av = score_avpu(d.avpu);
		const mob = score_mobility(d.mobility);
		const tr = d.trauma ? 1 : 0;
		frm.set_value("rr_score", rr);
		frm.set_value("hr_score", hr);
		if (FORM_TYPE === "adult" || FORM_TYPE === "maternity") frm.set_value("sbp_score", sbp);
		frm.set_value("temp_score", tmp);
		frm.set_value("avpu_score", av);
		frm.set_value("mobility_score", mob);
		frm.set_value("trauma_score", tr);
		frm.set_value("tews_score", rr + hr + sbp + tmp + av + mob + tr);
	}

	function check_dehydration_alarm(frm) {
		const count = ["dehydration_skin_pinch", "dehydration_lethargy", "dehydration_sunken_eyes"]
			.filter((f) => frm.doc[f]).length;
		return count >= 2;
	}

	function set_color(frm, color) {
		frm.set_value("triage_color", color);
		const colors = { RED: "#dc2626", ORANGE: "#ea580c", YELLOW: "#ca8a04", GREEN: "#16a34a" };
		if (frm.fields_dict.triage_color) {
			frm.fields_dict.triage_color.$wrapper
				.find(".control-value, .form-control, input, select")
				.css({ "background-color": colors[color] || "", color: "#fff", "font-weight": "bold" });
		}
	}

	function assign_color(frm) {
		if (frm.doc.manual_priority_override) return;
		const alarms = get_alarm_fields();
		let has_alarm = alarms.some((f) => frm.doc[f]);
		if (!has_alarm) has_alarm = check_dehydration_alarm(frm);
		if (has_alarm) return set_color(frm, "RED");

		const t = parseInt(frm.doc.tews_score || 0, 10);
		const o2 = parseFloat(frm.doc.spo2);
		if (t >= 7 || (o2 && o2 < 92)) return set_color(frm, "RED");
		if (t >= 5) return set_color(frm, "ORANGE");
		if (t >= 3) return set_color(frm, "YELLOW");
		const yellow = get_yellow_fields();
		if (yellow.some((f) => frm.doc[f])) return set_color(frm, "YELLOW");
		set_color(frm, "GREEN");
	}

	function toggle_conditional_fields(frm) {
		frm.toggle_display("convulsion_glucose", !!frm.doc.alarm_convulsion);
		frm.toggle_display("coma_glucose", !!frm.doc.alarm_coma);
		if (frm.fields_dict.yellow_focal_neuro_glucose) {
			frm.toggle_display("yellow_focal_neuro_glucose", !!frm.doc.yellow_focal_neuro);
		}
		const critical = ["RED", "ORANGE"].includes(frm.doc.triage_color);
		["notified_color", "notified_at", "doctor_name", "doctor_attended_at"].forEach((f) => {
			if (frm.fields_dict[f]) frm.toggle_display(f, critical);
		});
	}

	function recompute(frm) {
		calc_tews(frm);
		assign_color(frm);
		toggle_conditional_fields(frm);
	}

	const vitals = ["rr", "hr", "sbp", "temperature", "avpu", "mobility", "trauma", "spo2", "pain_score"];
	const all_triggers = vitals.concat(
		get_alarm_fields(),
		["dehydration_skin_pinch", "dehydration_lethargy", "dehydration_sunken_eyes"],
		get_yellow_fields(),
		get_green_fields()
	);

	const handlers = {
		refresh(frm) {
			toggle_conditional_fields(frm);
			if (frm.doc.triage_color) set_color(frm, frm.doc.triage_color);
		},
		manual_priority_override(frm) {
			if (!frm.doc.manual_priority_override) recompute(frm);
		},
	};
	all_triggers.forEach((field) => {
		handlers[field] = function (frm) {
			recompute(frm);
		};
	});
	handlers.alarm_convulsion = function (frm) {
		recompute(frm);
		toggle_conditional_fields(frm);
	};
	handlers.alarm_coma = handlers.alarm_convulsion;
	handlers.yellow_focal_neuro = handlers.alarm_convulsion;

	frappe.ui.form.on(DOCTYPE, handlers);
};
