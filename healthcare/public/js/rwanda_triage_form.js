// ============================================================
// Rwanda Triage — Shared Form Logic
// Covers: Adult (>12 yrs), Child (3–12 yrs), Infant (0–3 yrs), Maternity
//
// Corrections from paper-form audit (June 2026):
//   - Adult/Maternity SBP ranges corrected to match paper (<71→3, 71-80→2, 81-100→1, 101-199→0, >199→2)
//   - Adult/Maternity Temperature: only two bands (paper has no score-2 high-temp band)
//   - Child HR ranges corrected to match paper
//   - Infant HR ranges corrected to match paper
//   - SpO2 <92% → RED (not ORANGE) per paper flowchart
//   - Child/Infant extra alarm fields (central_cyanosis, pulse_low_absent, not_breathing_weak) now checked for RED
//   - Maternity extra alarm fields (prolapsed_cord, no_fetal_movement, bandel_ring, abnormal_ctg, imminent_birth) now checked for RED
//   - Infant-specific yellow fields now checked
//   - Maternity-specific yellow fields now checked
//   - Infant-specific green fields now checked
//   - Maternity-specific green fields now checked
//   - Removed redundant duplicate ORANGE TEWS block
//   - Fixed SpO2 YELLOW→ORANGE escalation
//   - calculate_tews no longer fires on refresh (avoids dirty-form on load)
// ============================================================

function rwanda_triage_form_init(form_key, doctype) {

	// ── TEWS Scoring Ranges (verified against paper forms) ───────────────────

	const TEWS_RANGES = {
		adult: {
			rr: [
				{ min: 0,   max: 8,   score: 3 },  // <9 → 3  (paper: score col is left-of-0)
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
			// Paper: <71→3, 71-80→2, 81-100→1, 101-199→0, >199→2
			sbp: [
				{ min: 0,   max: 70,  score: 3 },
				{ min: 71,  max: 80,  score: 2 },
				{ min: 81,  max: 100, score: 1 },
				{ min: 101, max: 199, score: 0 },
				{ min: 200, max: 999, score: 2 }
			],
			// Paper: <35→2, 35-38.4→0, >38.5→1  (only two abnormal bands)
			temperature: [
				{ min: 0,    max: 34.9, score: 2 },
				{ min: 35,   max: 38.4, score: 0 },
				{ min: 38.5, max: 999,  score: 1 }
			]
		},

		child: {
			// Paper: <15→3, 15-16→0, 17-21→1, 22-26→2, 27+→3
			rr: [
				{ min: 0,  max: 14,  score: 3 },
				{ min: 15, max: 16,  score: 0 },
				{ min: 17, max: 21,  score: 1 },
				{ min: 22, max: 26,  score: 2 },
				{ min: 27, max: 999, score: 3 }
			],
			// Paper: <60→3, 60-79→2, 80-99→1, 100-129→0, 130+→3
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
			// Paper: <20→3, 20-25→1, 26-39→0, 40-49→1, 50+→2
			rr: [
				{ min: 0,  max: 19,  score: 3 },
				{ min: 20, max: 25,  score: 1 },
				{ min: 26, max: 39,  score: 0 },
				{ min: 40, max: 49,  score: 1 },
				{ min: 50, max: 999, score: 2 }
			],
			// Paper: <70→3, 70-79→2, 80-130→0, 131-159→2, 160+→3
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

		// Maternity uses same ranges as Adult
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

	// ── Alarm field lists by form type ───────────────────────────────────────

	// Base alarms shared by all four forms → RED
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

	// Extra alarm fields for child and infant
	const CHILD_INFANT_EXTRA_ALARMS = [
		"alarm_not_breathing_weak",
		"alarm_central_cyanosis",
		"alarm_pulse_low_absent"
	];

	// Extra alarm fields for maternity
	const MATERNITY_EXTRA_ALARMS = [
		"alarm_prolapsed_cord",
		"alarm_no_fetal_movement",
		"alarm_bandel_ring",
		"alarm_abnormal_ctg",
		"alarm_stab_gunshot_maternity",
		"alarm_imminent_birth"
	];

	// ── Yellow sign field lists by form type ─────────────────────────────────

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

	// ── Green sign field lists by form type ──────────────────────────────────

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

	// ── Helper: get all alarm fields for this form type ──────────────────────

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
		if (fk === "infant")   return YELLOW_INFANT;
		if (fk === "maternity") return YELLOW_MATERNITY;
		return YELLOW_ADULT_CHILD; // adult + child
	}

	function get_green_fields(fk) {
		if (fk === "infant")   return GREEN_INFANT;
		if (fk === "maternity") return GREEN_MATERNITY;
		return GREEN_ADULT_CHILD;
	}

	// ── Frappe event registration ─────────────────────────────────────────────

	frappe.ui.form.on(doctype, {

		onload(frm) {
			if (frm.is_new() && frappe.route_options && frappe.route_options.parent_triage) {
				frm.set_value("parent_triage", frappe.route_options.parent_triage);
			}
		},

		// On refresh we only update the alert banner; we do NOT recalculate
		// TEWS here to avoid marking a saved record as dirty on every load.
		refresh(frm) {
			update_triage_priority_alert(frm);
		},

		// Vitals — recalculate TEWS then reassign color
		rr(frm)          { calculate_tews(frm, form_key, TEWS_RANGES); assign_triage_color(frm, form_key); },
		hr(frm)          { calculate_tews(frm, form_key, TEWS_RANGES); assign_triage_color(frm, form_key); },
		sbp(frm)         { calculate_tews(frm, form_key, TEWS_RANGES); assign_triage_color(frm, form_key); },
		temperature(frm) { calculate_tews(frm, form_key, TEWS_RANGES); assign_triage_color(frm, form_key); },
		avpu(frm)        { calculate_tews(frm, form_key, TEWS_RANGES); assign_triage_color(frm, form_key); },
		mobility(frm)    { calculate_tews(frm, form_key, TEWS_RANGES); assign_triage_color(frm, form_key); },
		trauma(frm)      { calculate_tews(frm, form_key, TEWS_RANGES); assign_triage_color(frm, form_key); },
		spo2(frm)        { assign_triage_color(frm, form_key); },
		pain_score(frm)  { assign_triage_color(frm, form_key); },

		// Alarm signs
		alarm_not_breathing(frm)           { assign_triage_color(frm, form_key); },
		alarm_obstructed_breathing(frm)    { assign_triage_color(frm, form_key); },
		alarm_severe_resp_distress(frm)    { assign_triage_color(frm, form_key); },
		alarm_cardiac_arrest(frm)          { assign_triage_color(frm, form_key); },
		alarm_hemorrhage_uncontrolled(frm) { assign_triage_color(frm, form_key); },
		alarm_stab_gunshot(frm)            { assign_triage_color(frm, form_key); },
		alarm_lethargic(frm)               { assign_triage_color(frm, form_key); },
		alarm_weak_fast_pulse(frm)         { assign_triage_color(frm, form_key); },
		alarm_cap_refill_3sec(frm)         { assign_triage_color(frm, form_key); },
		alarm_cold_hands(frm)              { assign_triage_color(frm, form_key); },
		alarm_convulsion(frm)              { assign_triage_color(frm, form_key); },
		alarm_coma(frm)                    { assign_triage_color(frm, form_key); },
		alarm_hypoglycemia(frm)            { assign_triage_color(frm, form_key); },
		alarm_purpuric_rash(frm)           { assign_triage_color(frm, form_key); },
		alarm_burn_face_inhalation(frm)    { assign_triage_color(frm, form_key); },

		// Child/Infant extra alarms
		alarm_not_breathing_weak(frm)  { assign_triage_color(frm, form_key); },
		alarm_central_cyanosis(frm)    { assign_triage_color(frm, form_key); },
		alarm_pulse_low_absent(frm)    { assign_triage_color(frm, form_key); },

		// Maternity extra alarms
		alarm_prolapsed_cord(frm)        { assign_triage_color(frm, form_key); },
		alarm_no_fetal_movement(frm)     { assign_triage_color(frm, form_key); },
		alarm_bandel_ring(frm)           { assign_triage_color(frm, form_key); },
		alarm_abnormal_ctg(frm)          { assign_triage_color(frm, form_key); },
		alarm_stab_gunshot_maternity(frm){ assign_triage_color(frm, form_key); },
		alarm_imminent_birth(frm)        { assign_triage_color(frm, form_key); },

		// Dehydration
		dehydration_skin_pinch(frm)  { assign_triage_color(frm, form_key); },
		dehydration_lethargy(frm)    { assign_triage_color(frm, form_key); },
		dehydration_sunken_eyes(frm) { assign_triage_color(frm, form_key); },

		// Yellow signs — Adult/Child
		yellow_focal_neuro(frm)        { assign_triage_color(frm, form_key); },
		yellow_altered_mental(frm)     { assign_triage_color(frm, form_key); },
		yellow_chest_pain(frm)         { assign_triage_color(frm, form_key); },
		yellow_poisoning(frm)          { assign_triage_color(frm, form_key); },
		yellow_coughing_blood(frm)     { assign_triage_color(frm, form_key); },
		yellow_diabetic_high(frm)      { assign_triage_color(frm, form_key); },
		yellow_aggression(frm)         { assign_triage_color(frm, form_key); },
		yellow_acute_sob(frm)          { assign_triage_color(frm, form_key); },
		yellow_severe_pain(frm)        { assign_triage_color(frm, form_key); },
		yellow_burn_20_urgent(frm)     { assign_triage_color(frm, form_key); },
		yellow_fracture_open(frm)      { assign_triage_color(frm, form_key); },
		yellow_threatened_limb(frm)    { assign_triage_color(frm, form_key); },
		yellow_eye_injury(frm)         { assign_triage_color(frm, form_key); },
		yellow_large_joint_disloc(frm) { assign_triage_color(frm, form_key); },
		yellow_severe_mechanism(frm)   { assign_triage_color(frm, form_key); },
		yellow_abdominal_trauma(frm)   { assign_triage_color(frm, form_key); },

		// Yellow signs — Infant-specific
		yellow_more_sleep(frm)         { assign_triage_color(frm, form_key); },
		yellow_inconsolable_cry(frm)   { assign_triage_color(frm, form_key); },
		yellow_floppy_irritable(frm)   { assign_triage_color(frm, form_key); },
		yellow_tiny_baby(frm)          { assign_triage_color(frm, form_key); },
		yellow_burn_10_urgent(frm)     { assign_triage_color(frm, form_key); },

		// Yellow signs — Maternity-specific
		yellow_multipara_active_labour(frm)  { assign_triage_color(frm, form_key); },
		yellow_uterine_contraction(frm)      { assign_triage_color(frm, form_key); },
		yellow_rom(frm)                      { assign_triage_color(frm, form_key); },
		yellow_decreased_fetal_movements(frm){ assign_triage_color(frm, form_key); },
		yellow_bleeding_spotting(frm)        { assign_triage_color(frm, form_key); },
		yellow_preterm_labour(frm)           { assign_triage_color(frm, form_key); },
		yellow_contraction_planned_cs(frm)   { assign_triage_color(frm, form_key); },
		yellow_preeclampsia(frm)             { assign_triage_color(frm, form_key); },
		yellow_major_trauma(frm)             { assign_triage_color(frm, form_key); },
		yellow_abdominal_trauma_severe_pain(frm) { assign_triage_color(frm, form_key); },

		// Green signs — Adult/Child
		green_cant_drink(frm)       { assign_triage_color(frm, form_key); },
		green_very_pale(frm)        { assign_triage_color(frm, form_key); },
		green_resp_distress(frm)    { assign_triage_color(frm, form_key); },
		green_diabetic_high(frm)    { assign_triage_color(frm, form_key); },
		green_malnutrition(frm)     { assign_triage_color(frm, form_key); },
		green_moderate_pain(frm)    { assign_triage_color(frm, form_key); },
		green_disloc_finger_toe(frm){ assign_triage_color(frm, form_key); },
		green_fracture_closed(frm)  { assign_triage_color(frm, form_key); },
		green_burn_no_urgency(frm)  { assign_triage_color(frm, form_key); },

		// Green signs — Infant-specific
		green_pitting_oedema(frm)        { assign_triage_color(frm, form_key); },
		green_severe_pallor(frm)         { assign_triage_color(frm, form_key); },
		green_known_diabetes(frm)        { assign_triage_color(frm, form_key); },
		green_diarrhea_vomiting(frm)     { assign_triage_color(frm, form_key); },
		green_dv_sunken_eyes(frm)        { assign_triage_color(frm, form_key); },
		green_dv_dry_mouth(frm)          { assign_triage_color(frm, form_key); },
		green_dv_decreased_urine(frm)    { assign_triage_color(frm, form_key); },
		green_dv_skin_pinch_slow(frm)    { assign_triage_color(frm, form_key); },

		// Green signs — Maternity-specific
		green_active_labor(frm)              { assign_triage_color(frm, form_key); },
		green_miscarriage(frm)               { assign_triage_color(frm, form_key); },
		green_malpresentation(frm)           { assign_triage_color(frm, form_key); },
		green_planned_cs_multiple(frm)       { assign_triage_color(frm, form_key); },
		green_rom_above_6hr(frm)             { assign_triage_color(frm, form_key); },
		green_fracture_closed_moderate_pain(frm) { assign_triage_color(frm, form_key); },
	});

	// ── Scoring helpers ───────────────────────────────────────────────────────

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

	function get_mobility_score(mobility, fk) {
		// Child/infant: 0=Normal, 1=Unable → scores 0 and 1
		// Adult/maternity: 0=Walking, 1=Help/Wheelchair, 2=Stretcher, 3=Immobile
		return parseInt(mobility) || 0;
	}

	// ── TEWS Calculation ──────────────────────────────────────────────────────

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

		const mobility_score = get_mobility_score(frm.doc.mobility, fk);
		frm.set_value("mobility_score", mobility_score);
		tews += mobility_score;

		const trauma_score = frm.doc.trauma ? 2 : 0;
		frm.set_value("trauma_score", trauma_score);
		tews += trauma_score;

		frm.set_value("tews_score", tews);
	}

	// ── Triage Color Assignment ───────────────────────────────────────────────
	//
	// Priority waterfall (matches paper flowchart exactly):
	//
	//  1. Any alarm sign checked?              → RED  (immediate)
	//  2. Severe dehydration (≥2 of 3)?        → RED
	//  3. TEWS ≥ 7 OR SpO2 < 92%?             → RED
	//  4. TEWS 5–6?                            → ORANGE
	//  5. Any yellow sign checked?
	//     a. TEWS 3–4?                         → YELLOW (paper: "No and TEWS=3-4")
	//     b. TEWS 0–2 but yellow sign present? → YELLOW
	//  6. Any green sign checked?              → GREEN  (already default)
	//  7. Nothing checked, TEWS 0–2?           → GREEN

	function assign_triage_color(frm, fk) {
		let color = "GREEN"; // default

		// ── Step 1: Alarm signs → RED ──────────────────────────────────────
		const alarm_fields = get_alarm_fields(fk);
		for (let f of alarm_fields) {
			if (frm.doc[f]) { color = "RED"; break; }
		}

		// ── Step 2: Severe dehydration (≥2 of 3) → RED ────────────────────
		if (color !== "RED") {
			const dehyd = [
				frm.doc.dehydration_skin_pinch,
				frm.doc.dehydration_lethargy,
				frm.doc.dehydration_sunken_eyes
			].filter(Boolean).length;
			if (dehyd >= 2) color = "RED";
		}

		// ── Step 3: TEWS ≥ 7 OR SpO2 < 92% → RED ─────────────────────────
		if (color !== "RED") {
			const tews = frm.doc.tews_score || 0;
			const spo2 = frm.doc.spo2;
			if (tews >= 7) color = "RED";
			else if (spo2 !== null && spo2 !== undefined && spo2 !== "" && spo2 < 92) color = "RED";
		}

		// ── Step 4: TEWS 5–6 → ORANGE ─────────────────────────────────────
		if (color === "GREEN") {
			const tews = frm.doc.tews_score || 0;
			if (tews >= 5 && tews <= 6) color = "ORANGE";
		}

		// ── Step 5: Yellow signs → YELLOW (only if not already RED/ORANGE) ─
		// Paper: yellow signs apply when TEWS 0-4; TEWS 3-4 with yellow → YELLOW
		if (color === "GREEN") {
			const yellow_fields = get_yellow_fields(fk);
			for (let f of yellow_fields) {
				if (frm.doc[f]) { color = "YELLOW"; break; }
			}
		}

		// TEWS 3–4 with no alarm/orange escalation but no yellow sign → YELLOW
		// (paper flowchart: "No and TEWS=3-4" arrow points to YELLOW)
		if (color === "GREEN") {
			const tews = frm.doc.tews_score || 0;
			if (tews >= 3 && tews <= 4) color = "YELLOW";
		}

		// Green signs: color stays GREEN — no change needed, already default.
		// (Confirmed by paper: green signs just confirm the GREEN bucket.)

		frm.set_value("triage_color", color);
		frm.set_df_property("triage_color", "bold", true);
		update_triage_priority_alert(frm, color);
	}
}

// ── Dashboard alert banner (global — called from form-specific scripts too) ──

function update_triage_priority_alert(frm, color) {
	color = color || frm.doc.triage_color;
	if (!color) return;

	const COLOR_STYLE = {
		RED:    "red",
		ORANGE: "orange",
		YELLOW: "yellow",
		GREEN:  "green"
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
}