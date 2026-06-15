# -*- coding: utf-8 -*-
"""TEWS color rules and OPD priority mapping."""

TEWS_COLORS = ("RED", "ORANGE", "YELLOW", "GREEN")

# Existing OPD workflow uses Emergency / Urgent / Non-urgent / Routine
COLOR_TO_OPD_PRIORITY = {
	"RED": "Emergency",
	"ORANGE": "Urgent",
	"YELLOW": "Non-urgent",
	"GREEN": "Routine",
}

OPD_PRIORITY_TO_COLOR = {v: k for k, v in COLOR_TO_OPD_PRIORITY.items()}


def map_triage_color_to_opd_priority(triage_color):
	return COLOR_TO_OPD_PRIORITY.get(triage_color) or "Routine"


def detect_form_type(age_years, age_months, is_maternity):
	if is_maternity:
		return "Maternity"
	if age_months is not None and age_months <= 36:
		return "Infant"
	if age_years is not None and age_years <= 12:
		return "Child"
	return "Adult"


FORM_TYPE_DOCTYPE = {
	"Adult": ("Adult Triage Form", "adult_triage_form"),
	"Child": ("Child Triage Form", "child_triage_form"),
	"Infant": ("Infant Triage Form", "infant_triage_form"),
	"Maternity": ("Maternity Triage Form", "maternity_triage_form"),
}

BASE_ALARM_FIELDS = [
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
	"alarm_burn_face_inhalation",
]

CHILD_INFANT_EXTRA_ALARMS = [
	"alarm_not_breathing_weak",
	"alarm_central_cyanosis",
	"alarm_pulse_low_absent",
]

MATERNITY_EXTRA_ALARMS = [
	"alarm_prolapsed_cord",
	"alarm_no_fetal_movement",
	"alarm_bandel_ring",
	"alarm_abnormal_ctg",
	"alarm_stab_gunshot_maternity",
	"alarm_imminent_birth",
]

DEHYDRATION_FIELDS = [
	"dehydration_skin_pinch",
	"dehydration_lethargy",
	"dehydration_sunken_eyes",
]
