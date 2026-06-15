# -*- coding: utf-8 -*-
"""Field definitions for Rwanda TEWS triage forms (Adult / Child / Infant / Maternity)."""

from __future__ import annotations

# ── Shared header fields (read-only from Triage Assessment) ──────────────────

HEADER_FIELDS = [
	{"fieldname": "triage_assessment", "fieldtype": "Link", "label": "Triage Assessment", "options": "Triage Assessment", "reqd": 1, "read_only": 1},
	{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Patient", "read_only": 1, "in_list_view": 1},
	{"fieldname": "patient_name", "fieldtype": "Data", "label": "Patient Name", "read_only": 1},
	{"fieldname": "age", "fieldtype": "Int", "label": "Age (years)", "read_only": 1},
	{"fieldname": "medical_record_number", "fieldtype": "Data", "label": "Medical Record Number", "read_only": 1},
	{"fieldname": "chief_complaint", "fieldtype": "Small Text", "label": "Chief Complaint", "read_only": 1},
	{"fieldname": "date", "fieldtype": "Date", "label": "Date", "read_only": 1},
	{"fieldname": "arrival_time", "fieldtype": "Time", "label": "Arrival Time", "read_only": 1},
]

BASE_ALARM_FIELDS = [
	("alarm_not_breathing", "Airway — Not Breathing"),
	("alarm_obstructed_breathing", "Airway — Obstructed Breathing"),
	("alarm_severe_resp_distress", "Airway — Severe Respiratory Distress"),
	("alarm_cardiac_arrest", "Circulation — Cardiac Arrest"),
	("alarm_hemorrhage_uncontrolled", "Circulation — Hemorrhage Uncontrolled"),
	("alarm_stab_gunshot", "Circulation — Stab/Gunshot Wound to Neck or Chest"),
	("alarm_lethargic", "Lethargic"),
	("alarm_weak_fast_pulse", "Pulse Weak and Fast"),
	("alarm_cap_refill_3sec", "Capillary Refill ≥ 3 seconds"),
	("alarm_cold_hands", "Cold Hands"),
	("alarm_convulsion", "Convulsion — Current Seizure or Post-ictal (not alert)"),
	("alarm_coma", "Coma — Unresponsive or Responsive Only to Pain"),
	("alarm_hypoglycemia", "Hypoglycemia — Glucose < 3 mmol/L or < 60 mg/dL"),
	("alarm_purpuric_rash", "Purpuric Rash"),
	("alarm_burn_face_inhalation", "Burn — Face or Inhalation"),
]

CHILD_INFANT_EXTRA_ALARMS = [
	("alarm_not_breathing_weak", "Not Breathing or Weak Breathing"),
	("alarm_central_cyanosis", "Central Cyanosis"),
	("alarm_pulse_low_absent", "Pulse Low or Absent"),
]

MATERNITY_EXTRA_ALARMS = [
	("alarm_prolapsed_cord", "Prolapsed Cord"),
	("alarm_no_fetal_movement", "No Fetal Movement"),
	("alarm_bandel_ring", "Bandel Ring"),
	("alarm_abnormal_ctg", "Abnormal CTG"),
	("alarm_stab_gunshot_maternity", "Stab / Gunshot Wound"),
	("alarm_imminent_birth", "Imminent Birth"),
]

DEHYDRATION_FIELDS = [
	("dehydration_skin_pinch", "Severe Dehydration — Skin Pinch ≥ 2 sec"),
	("dehydration_lethargy", "Severe Dehydration — Lethargy"),
	("dehydration_sunken_eyes", "Severe Dehydration — Sunken Eyes"),
]

YELLOW_ADULT_CHILD = [
	("yellow_focal_neuro", "Focal Neurological Deficit — Acute (< 1 day)"),
	("yellow_altered_mental", "Altered Mental Status — Acute (< 1 day)"),
	("yellow_chest_pain", "Chest Pain"),
	("yellow_poisoning", "Poisoning / Overdose"),
	("yellow_coughing_blood", "Coughing or Vomiting Blood"),
	("yellow_diabetic_high", "Unwell with Diabetes — Glucose > 200 mg/dL or > 11 mmol/L"),
	("yellow_aggression", "Aggression"),
	("yellow_acute_sob", "Shortness of Breath — Acute (< 1 day)"),
	("yellow_severe_pain", "Very Severe Pain (≥ 7)"),
	("yellow_burn_20_urgent", "Burn > 20% or with Urgent Signs"),
	("yellow_fracture_open", "Fracture Open (with skin break)"),
	("yellow_threatened_limb", "Threatened Limb — No Pulse or Pale"),
	("yellow_eye_injury", "Eye Injury"),
	("yellow_large_joint_disloc", "Dislocation of Large Joint (not finger/toe)"),
	("yellow_severe_mechanism", "Severe Mechanism of Injury — Fall > 1 m, RTA, or Other Significant Trauma"),
	("yellow_abdominal_trauma", "Abdominal Trauma"),
]

YELLOW_INFANT = [
	("yellow_more_sleep", "More Sleep Than Normal"),
	("yellow_focal_neuro", "Focal Neurological Deficit — Acute (< 1 day)"),
	("yellow_inconsolable_cry", "Inconsolable Crying / Severe Pain (> 7)"),
	("yellow_floppy_irritable", "Floppy, Irritable, or Restless"),
	("yellow_chest_pain", "Chest Pain"),
	("yellow_poisoning", "Poisoning / Overdose"),
	("yellow_tiny_baby", "Tiny Baby (younger than 2 months)"),
	("yellow_burn_10_urgent", "Burn > 10% or with Urgent Signs"),
	("yellow_fracture_open", "Fracture Open (with skin break)"),
	("yellow_threatened_limb", "Threatened Limb — No Pulse or Pale"),
	("yellow_eye_injury", "Eye Injury"),
	("yellow_large_joint_disloc", "Dislocation of Large Joint (not finger/toe)"),
	("yellow_severe_mechanism", "Severe Mechanism of Injury — Fall > Child's Height, RTA, Other Significant Trauma"),
]

YELLOW_MATERNITY = [
	("yellow_multipara_active_labour", "Multipara in Active Labour"),
	("yellow_uterine_contraction", "Detectable Uterine Contraction"),
	("yellow_rom", "Rupture of Membranes (ROM)"),
	("yellow_decreased_fetal_movements", "Decreased Fetal Movements"),
	("yellow_bleeding_spotting", "Bleeding More Than Spotting"),
	("yellow_preterm_labour", "Preterm Labour < 37 Weeks"),
	("yellow_contraction_planned_cs", "Active Contraction on Planned C-Section"),
	("yellow_preeclampsia", "Signs of Pre-Eclampsia"),
	("yellow_altered_mental", "Altered Mental Status — Acute (< 1 day)"),
	("yellow_burn_20_urgent", "Burn > 20% with Urgent Signs"),
	("yellow_poisoning", "Poisoning / Overdose"),
	("yellow_fracture_open", "Fracture Open (with skin break)"),
	("yellow_large_joint_disloc", "Dislocation of Large Joint"),
	("yellow_major_trauma", "Major Trauma"),
	("yellow_coughing_blood", "Coughing or Vomiting Blood"),
	("yellow_abdominal_trauma_severe_pain", "Abdominal Trauma / Severe Pain (> 7)"),
]

GREEN_ADULT_CHILD = [
	("green_cant_drink", "Unable to Drink or Vomits Everything"),
	("green_very_pale", "Very Pale"),
	("green_resp_distress", "Respiratory Distress (less urgent)"),
	("green_diabetic_high", "Diabetic (not unwell) — Glucose > 300 mg/dL or > 17 mmol/L"),
	("green_malnutrition", "Severe Malnutrition / Wasting"),
	("green_moderate_pain", "Moderate Pain (5–6)"),
	("green_disloc_finger_toe", "Dislocation — Finger or Toe"),
	("green_fracture_closed", "Fracture Closed"),
	("green_burn_no_urgency", "Burn without Urgent Signs"),
]

GREEN_INFANT = [
	("green_pitting_oedema", "Pitting Oedema of Both Feet or Face"),
	("green_cant_drink", "Unable to Drink or Vomits Everything"),
	("green_severe_pallor", "Severe Pallor"),
	("green_resp_distress", "Some Respiratory Distress"),
	("green_known_diabetes", "Unwell with Known Diabetes"),
	("green_malnutrition", "Severe Malnutrition / Wasting"),
	("green_diarrhea_vomiting", "Diarrhoea and/or Vomiting"),
	("green_dv_sunken_eyes", "— Sunken Eyes"),
	("green_dv_dry_mouth", "— Dry Mouth"),
	("green_dv_decreased_urine", "— Decreased Urine Output"),
	("green_dv_skin_pinch_slow", "— Skin Pinch Slow (< 2 seconds)"),
	("green_disloc_finger_toe", "Dislocation — Finger or Toe"),
	("green_fracture_closed", "Fracture Closed"),
	("green_burn_no_urgency", "Burn without Urgent Signs"),
	("green_moderate_pain", "Moderate Pain (5–6)"),
]

GREEN_MATERNITY = [
	("green_active_labor", "Active Labor"),
	("green_miscarriage", "Miscarriage"),
	("green_malpresentation", "Malpresentation"),
	("green_planned_cs_multiple", "Planned C-Section / Multiple Gestation"),
	("green_rom_above_6hr", "Rupture of Membranes > 6 Hours"),
	("green_cant_drink", "Unable to Drink or Vomits Everything"),
	("green_known_diabetes", "Unwell with Known Diabetes"),
	("green_malnutrition", "Severe Malnutrition / Wasting"),
	("green_fracture_closed_moderate_pain", "Fracture Closed / Moderate Pain (5–6)"),
	("green_burn_no_urgency", "Burn without Urgent Signs"),
]

FINAL_FIELDS = [
	{"fieldname": "nurse_name", "fieldtype": "Link", "label": "Nurse Name", "options": "User"},
	{"fieldname": "triage_finish_time", "fieldtype": "Datetime", "label": "Triage Finish Time"},
	{"fieldname": "notified_color", "fieldtype": "Select", "label": "Notified Color", "options": "RED\nORANGE", "depends_on": 'eval:["RED","ORANGE"].includes(doc.triage_color)'},
	{"fieldname": "notified_at", "fieldtype": "Datetime", "label": "Notified At", "depends_on": 'eval:["RED","ORANGE"].includes(doc.triage_color)'},
	{"fieldname": "doctor_name", "fieldtype": "Link", "label": "Doctor Name", "options": "User", "depends_on": 'eval:["RED","ORANGE"].includes(doc.triage_color)'},
	{"fieldname": "doctor_attended_at", "fieldtype": "Datetime", "label": "Doctor Attended At", "depends_on": 'eval:["RED","ORANGE"].includes(doc.triage_color)'},
	{"fieldname": "manual_priority_override", "fieldtype": "Check", "label": "Manual Priority Override", "default": "0"},
]


def _check_fields(pairs):
	return [{"fieldname": fn, "fieldtype": "Check", "label": label} for fn, label in pairs]


def _section(label, fieldname=None):
	return {"fieldname": fieldname or label.lower().replace(" ", "_").replace("—", "").replace("/", "")[:140], "fieldtype": "Section Break", "label": label}


def _hidden_score(fieldname, label):
	return {"fieldname": fieldname, "fieldtype": "Int", "label": label, "read_only": 1, "hidden": 1}


def build_tews_fields(form_type: str):
	"""TEWS section fields — SBP omitted for child/infant."""
	if form_type in ("adult", "maternity"):
		mobility_options = "0\n1\n2\n3"
		mobility_desc = "0=Walking, 1=With help/Wheelchair, 2=Stretcher, 3=Immobile"
	else:
		mobility_options = "0\n1"
		mobility_desc = "0=Normal for age, 1=Unable to move as normal"

	fields = [
		_section("TEWS Score", "sb_tews"),
		{"fieldname": "mobility", "fieldtype": "Select", "label": "Mobility", "options": mobility_options, "description": mobility_desc},
		_hidden_score("mobility_score", "Mobility Score"),
		{"fieldname": "rr", "fieldtype": "Int", "label": "Respiratory Rate (breaths/min)"},
		_hidden_score("rr_score", "RR Score"),
		{"fieldname": "hr", "fieldtype": "Int", "label": "Heart Rate / Pulse (bpm)"},
		_hidden_score("hr_score", "HR Score"),
	]
	if form_type in ("adult", "maternity"):
		fields.extend([
			{"fieldname": "sbp", "fieldtype": "Int", "label": "Blood Pressure Systolic (mmHg)"},
			_hidden_score("sbp_score", "SBP Score"),
		])
	fields.extend([
		{"fieldname": "temperature", "fieldtype": "Float", "label": "Body Temperature (°C)"},
		_hidden_score("temp_score", "Temperature Score"),
		{"fieldname": "avpu", "fieldtype": "Select", "label": "AVPU", "options": "Alert\nConfused\nVoice\nPain\nUnresponsive"},
		_hidden_score("avpu_score", "AVPU Score"),
		{"fieldname": "trauma", "fieldtype": "Check", "label": "Trauma"},
		_hidden_score("trauma_score", "Trauma Score"),
		{"fieldname": "tews_score", "fieldtype": "Int", "label": "Total TEWS Score", "read_only": 1, "bold": 1},
		{"fieldname": "spo2", "fieldtype": "Float", "label": "SpO2 (%)"},
		{"fieldname": "pain_score", "fieldtype": "Int", "label": "Pain Score (0–10)"},
		{
			"fieldname": "triage_color",
			"fieldtype": "Select",
			"label": "Triage Color",
			"options": "RED\nORANGE\nYELLOW\nGREEN",
			"read_only": 1,
			"bold": 1,
			"in_list_view": 1,
		},
	])
	return fields


def build_form_fields(form_type: str):
	"""Build complete field list for an age-specific triage form."""
	fields = list(HEADER_FIELDS)

	# Section A — Emergency
	fields.append(_section("Emergency Signs (RED Alarm)", "sb_emergency"))
	alarms = list(BASE_ALARM_FIELDS)
	if form_type in ("child", "infant"):
		alarms.extend(CHILD_INFANT_EXTRA_ALARMS)
	if form_type == "maternity":
		alarms.extend(MATERNITY_EXTRA_ALARMS)
	fields.extend(_check_fields(alarms))
	fields.extend(_check_fields(DEHYDRATION_FIELDS))
	fields.append({
		"fieldname": "convulsion_glucose",
		"fieldtype": "Float",
		"label": "Convulsion Glucose Reading",
		"depends_on": "eval:doc.alarm_convulsion==1",
	})
	fields.append({
		"fieldname": "coma_glucose",
		"fieldtype": "Float",
		"label": "Coma Glucose Reading",
		"depends_on": "eval:doc.alarm_coma==1",
	})
	fields.append({
		"fieldname": "yellow_focal_neuro_glucose",
		"fieldtype": "Float",
		"label": "Focal Neuro Glucose Reading",
		"depends_on": "eval:doc.yellow_focal_neuro==1",
	})

	fields.extend(build_tews_fields(form_type))

	# Section C — Yellow
	fields.append(_section("Very Urgent Signs — YELLOW (within 60 min)", "sb_yellow"))
	if form_type == "infant":
		yellow = YELLOW_INFANT
		fields.append({"fieldname": "yellow_sleep_glucose", "fieldtype": "Float", "label": "Glucose Reading (sleep complaint)", "depends_on": "eval:doc.yellow_more_sleep==1"})
	elif form_type == "maternity":
		yellow = YELLOW_MATERNITY
	else:
		yellow = YELLOW_ADULT_CHILD
	fields.extend(_check_fields(yellow))

	# Section D — Green
	fields.append(_section("Urgent Signs — GREEN (within 4 hours)", "sb_green"))
	if form_type == "infant":
		green = GREEN_INFANT
		fields.extend(_check_fields(green))
		fields.append({"fieldname": "green_cant_drink_glucose", "fieldtype": "Float", "label": "Glucose Reading (unable to drink)", "depends_on": "eval:doc.green_cant_drink==1"})
		fields.append({"fieldname": "green_diabetes_glucose", "fieldtype": "Float", "label": "Glucose Reading (diabetes)", "depends_on": "eval:doc.green_known_diabetes==1"})
	else:
		green = GREEN_MATERNITY if form_type == "maternity" else GREEN_ADULT_CHILD
		fields.extend(_check_fields(green))

	fields.append(_section("Staff & notification", "sb_final"))
	fields.extend(FINAL_FIELDS)
	return fields


FORM_META = {
	"Adult Triage Form": {"form_type": "adult", "naming_series": "ADTF-.YYYY.-", "prefix": "adult_triage_form"},
	"Child Triage Form": {"form_type": "child", "naming_series": "CHTF-.YYYY.-", "prefix": "child_triage_form"},
	"Infant Triage Form": {"form_type": "infant", "naming_series": "INTF-.YYYY.-", "prefix": "infant_triage_form"},
	"Maternity Triage Form": {"form_type": "maternity", "naming_series": "MATF-.YYYY.-", "prefix": "maternity_triage_form"},
}


TRIAGE_ASSESSMENT_FIELDS = [
	{"fieldname": "patient", "fieldtype": "Link", "label": "Patient", "options": "Patient", "reqd": 1, "in_list_view": 1},
	{"fieldname": "patient_name", "fieldtype": "Data", "label": "Patient Name", "read_only": 1, "in_list_view": 1},
	{"fieldname": "date_of_birth", "fieldtype": "Date", "label": "Date of Birth", "read_only": 1},
	{"fieldname": "patient_age", "fieldtype": "Int", "label": "Patient Age (years)", "read_only": 1},
	{"fieldname": "patient_age_months", "fieldtype": "Int", "label": "Patient Age (months)", "read_only": 1},
	{"fieldname": "patient_gender", "fieldtype": "Data", "label": "Patient Gender", "read_only": 1},
	{"fieldname": "medical_record_number", "fieldtype": "Data", "label": "Medical Record Number", "read_only": 1},
	{"fieldname": "is_maternity", "fieldtype": "Check", "label": "Is Maternity Patient", "default": "0"},
	{"fieldname": "chief_complaint", "fieldtype": "Small Text", "label": "Chief Complaint", "reqd": 1},
	{"fieldname": "arrival_date", "fieldtype": "Date", "label": "Arrival Date", "reqd": 1, "default": "Today"},
	{"fieldname": "arrival_time", "fieldtype": "Time", "label": "Arrival Time", "reqd": 1},
	{"fieldname": "company", "fieldtype": "Link", "label": "Company", "options": "Company", "reqd": 1},
	_section("Form routing", "sb_routing"),
	{"fieldname": "form_type", "fieldtype": "Select", "label": "Detected Form Type", "options": "Adult\nChild\nInfant\nMaternity", "read_only": 1, "in_list_view": 1},
	{"fieldname": "adult_triage_form", "fieldtype": "Link", "label": "Adult Triage Form", "options": "Adult Triage Form", "depends_on": 'eval:doc.form_type=="Adult"'},
	{"fieldname": "child_triage_form", "fieldtype": "Link", "label": "Child Triage Form", "options": "Child Triage Form", "depends_on": 'eval:doc.form_type=="Child"'},
	{"fieldname": "infant_triage_form", "fieldtype": "Link", "label": "Infant Triage Form", "options": "Infant Triage Form", "depends_on": 'eval:doc.form_type=="Infant"'},
	{"fieldname": "maternity_triage_form", "fieldtype": "Link", "label": "Maternity Triage Form", "options": "Maternity Triage Form", "depends_on": 'eval:doc.form_type=="Maternity"'},
	_section("Triage result", "sb_result"),
	{"fieldname": "triage_color", "fieldtype": "Select", "label": "Triage Color", "options": "RED\nORANGE\nYELLOW\nGREEN", "read_only": 1, "in_list_view": 1},
	{"fieldname": "tews_score", "fieldtype": "Int", "label": "TEWS Score", "read_only": 1},
	{"fieldname": "spo2", "fieldtype": "Float", "label": "SpO2 (%)", "read_only": 1},
	{"fieldname": "pain_score", "fieldtype": "Int", "label": "Pain Score (0–10)", "read_only": 1},
	{"fieldname": "manual_priority_override", "fieldtype": "Check", "label": "Manual Priority Override", "default": "0"},
	{"fieldname": "override_reason", "fieldtype": "Small Text", "label": "Override Reason", "depends_on": "eval:doc.manual_priority_override==1"},
	_section("Notification", "sb_notification"),
	{"fieldname": "notified_color", "fieldtype": "Select", "label": "Notified Color", "options": "RED\nORANGE", "depends_on": 'eval:["RED","ORANGE"].includes(doc.triage_color)'},
	{"fieldname": "notified_at", "fieldtype": "Datetime", "label": "Notified At", "depends_on": 'eval:["RED","ORANGE"].includes(doc.triage_color)'},
	{"fieldname": "nurse_name", "fieldtype": "Link", "label": "Nurse Name", "options": "User", "reqd": 1},
	{"fieldname": "triage_finish_time", "fieldtype": "Datetime", "label": "Triage Finish Time"},
	{"fieldname": "doctor_name", "fieldtype": "Link", "label": "Doctor Name", "options": "User", "depends_on": 'eval:["RED","ORANGE"].includes(doc.triage_color)'},
	{"fieldname": "doctor_attended_at", "fieldtype": "Datetime", "label": "Doctor Attended At", "depends_on": 'eval:["RED","ORANGE"].includes(doc.triage_color)'},
	_section("Outcome", "sb_outcome"),
	{"fieldname": "vital_signs_record", "fieldtype": "Link", "label": "Vital Signs Record", "options": "Vital Signs", "read_only": 1},
	{"fieldname": "muac", "fieldtype": "Float", "label": "MUAC (cm)"},
	{"fieldname": "triage_notes", "fieldtype": "Text Editor", "label": "Triage Notes"},
	{"fieldname": "patient_oriented", "fieldtype": "Small Text", "label": "Patient Oriented To"},
]
