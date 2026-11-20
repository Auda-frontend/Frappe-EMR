# -*- coding: utf-8 -*-
"""
Authoritative Rwanda TEWS scoring and triage categorisation.

Source: the Rwanda four-page triage PDF, as transcribed in "TEWS Scoring Tables:
Adult, Maternity, Child and Infant Triage" (19 Nov 2026).

Rulings confirmed on 19 Nov 2026:
  * A blank cell in a scoring table means that row has no band at that score.
    It does not mean "not recorded".
  * Temperature scores 2 below 35, 0 from 35 to 38.4, and 2 above 38.4 on
    every form.
  * Age 3 years belongs to Infant.
  * The consciousness row is called AVUP (the DocType field is still `avpu`).

Do not change thresholds without clinical approval.
"""

from datetime import date, datetime
from typing import Any

FORMS = ("Adult", "Child", "Infant", "Maternity")
ADULT_LIKE = ("Adult", "Maternity")  # same values, and both score SBP

# Age groups, in completed months on the arrival date.
INFANT_MAX_MONTHS = 36   # 0-3 years; exactly 3 years is Infant
CHILD_MAX_MONTHS = 144   # over 3 up to and including 12 years; over 12 is Adult

TEMP_LOW_BELOW = 35
TEMP_HIGH_ABOVE = 38.4
SPO2_RED_BELOW = 92

# Mobility is stored as its score. Adults/maternity: 0 walking, 1 with help or
# wheelchair, 2 stretcher or immobile. Child/infant: 0 normal for age, 2 unable
# to move as normal (there is no 1).
VALID_MOBILITY = {
    "Adult": (0, 1, 2),
    "Maternity": (0, 1, 2),
    "Child": (0, 2),
    "Infant": (0, 2),
}

# Each band list is ((upper_bound_exclusive, score), ...) in ascending order;
# a value at or above the last bound takes the fallback score.
# Written from the lower edge of each band so integer vitals leave no gaps.
ADULT_RR = (((9, 2), (15, 0), (21, 1), (30, 2)), 3)
ADULT_HR = (((41, 2), (51, 1), (101, 0), (111, 1), (130, 2)), 3)
ADULT_SBP = (((71, 3), (81, 2), (101, 1), (200, 0)), 2)

CHILD_RR = (((15, 3), (17, 2), (22, 0), (27, 1)), 2)
CHILD_HR = (((60, 3), (80, 2), (100, 0), (130, 1)), 2)

INFANT_RR = (((20, 3), (26, 2), (40, 0), (50, 1)), 2)
INFANT_HR = (((70, 3), (80, 2), (131, 0), (160, 1)), 2)

RR_BANDS = {
    "Adult": ADULT_RR, "Maternity": ADULT_RR,
    "Child": CHILD_RR, "Infant": INFANT_RR,
}
HR_BANDS = {
    "Adult": ADULT_HR, "Maternity": ADULT_HR,
    "Child": CHILD_HR, "Infant": INFANT_HR,
}

AVUP_SCORES = {
    "Alert": 0,
    "Voice": 1,
    "Reacts to Voice": 1,
    "React to Voice": 1,
    "Pain": 2,
    "Reacts to Pain": 2,
    "React to pain": 2,
    "Confused": 2,
    "Unresponsive": 3,
}


# Emergency signs from the age-specific forms.
BASE_EMERGENCY_FIELDS = (
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
)

CHILD_INFANT_EMERGENCY_FIELDS = (
    "alarm_not_breathing_weak",
    "alarm_central_cyanosis",
    "alarm_pulse_low_absent",
)

MATERNITY_EMERGENCY_FIELDS = (
    "alarm_prolapsed_cord",
    "alarm_no_fetal_movement",
    "alarm_bandel_ring",
    "alarm_abnormal_ctg",
    "alarm_stab_gunshot_maternity",
    "alarm_imminent_birth",
)


# Very urgent signs: positive finding routes to ORANGE
# when TEWS is in the 0-4 pathway.
VERY_URGENT_FIELDS = {
    "Adult": (
        "yellow_focal_neuro", "yellow_altered_mental",
        "yellow_chest_pain", "yellow_poisoning",
        "yellow_coughing_blood", "yellow_diabetic_high",
        "yellow_aggression", "yellow_acute_sob",
        "yellow_severe_pain", "yellow_burn_20_urgent",
        "yellow_fracture_open", "yellow_threatened_limb",
        "yellow_eye_injury", "yellow_large_joint_disloc",
        "yellow_severe_mechanism", "yellow_abdominal_trauma",
    ),
    "Child": (
        "yellow_focal_neuro", "yellow_altered_mental",
        "yellow_chest_pain", "yellow_poisoning",
        "yellow_coughing_blood", "yellow_diabetic_high",
        "yellow_aggression", "yellow_acute_sob",
        "yellow_severe_pain", "yellow_burn_20_urgent",
        "yellow_fracture_open", "yellow_threatened_limb",
        "yellow_eye_injury", "yellow_large_joint_disloc",
        "yellow_severe_mechanism", "yellow_abdominal_trauma",
    ),
    "Infant": (
        "yellow_more_sleep", "yellow_focal_neuro",
        "yellow_inconsolable_cry", "yellow_floppy_irritable",
        "yellow_chest_pain", "yellow_poisoning",
        "yellow_tiny_baby", "yellow_burn_10_urgent",
        "yellow_fracture_open", "yellow_threatened_limb",
        "yellow_eye_injury", "yellow_large_joint_disloc",
        "yellow_severe_mechanism",
    ),
    "Maternity": (
        "yellow_multipara_active_labour",
        "yellow_uterine_contraction", "yellow_rom",
        "yellow_decreased_fetal_movements",
        "yellow_bleeding_spotting", "yellow_preterm_labour",
        "yellow_contraction_planned_cs", "yellow_preeclampsia",
        "yellow_altered_mental", "yellow_burn_20_urgent",
        "yellow_poisoning", "yellow_fracture_open",
        "yellow_large_joint_disloc", "yellow_major_trauma",
        "yellow_coughing_blood",
        "yellow_abdominal_trauma_severe_pain",
    ),
}


# Urgent signs: positive finding routes to YELLOW
# when TEWS is 0-2 and there are no very urgent signs.
URGENT_FIELDS = {
    "Adult": (
        "green_cant_drink", "green_very_pale",
        "green_resp_distress", "green_diabetic_high",
        "green_malnutrition", "green_moderate_pain",
        "green_disloc_finger_toe", "green_fracture_closed",
        "green_burn_no_urgency",
    ),
    "Child": (
        "green_cant_drink", "green_very_pale",
        "green_resp_distress", "green_diabetic_high",
        "green_malnutrition", "green_moderate_pain",
        "green_disloc_finger_toe", "green_fracture_closed",
        "green_burn_no_urgency",
    ),
    "Infant": (
        "green_pitting_oedema", "green_cant_drink",
        "green_severe_pallor", "green_resp_distress",
        "green_known_diabetes", "green_malnutrition",
        "green_diarrhea_vomiting", "green_disloc_finger_toe",
        "green_fracture_closed", "green_burn_no_urgency",
        "green_moderate_pain",
    ),
    "Maternity": (
        "green_active_labor", "green_miscarriage",
        "green_malpresentation", "green_planned_cs_multiple",
        "green_rom_above_6hr", "green_cant_drink",
        "green_known_diabetes", "green_malnutrition",
        "green_fracture_closed_moderate_pain",
        "green_burn_no_urgency",
    ),
}


# --------------------------------------------------------------------------
# Reading values
# --------------------------------------------------------------------------

def _value(data: Any, fieldname: str):
    # Works for a plain dict and for a Frappe Document.
    return data.get(fieldname)


def _number(data: Any, fieldname: str):
    value = _value(data, fieldname)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _measurement(data: Any, fieldname: str):
    """
    A measured vital sign, or None when it has not been recorded.

    Frappe stores an unset Int/Float field as 0, and a living patient cannot
    have a respiratory rate, heart rate, blood pressure, temperature or SpO2 of
    0 (cardiac arrest is an emergency sign). So 0 or less means "not recorded".
    This is about input fields only; it has nothing to do with blank cells in
    the scoring tables.
    """
    number = _number(data, fieldname)
    if number is None or number <= 0:
        return None
    return number


def _has_choice(data: Any, fieldname: str):
    value = _value(data, fieldname)
    return value is not None and str(value).strip() != ""


def _checked(data: Any, fields):
    return any(bool(_value(data, fieldname)) for fieldname in fields)


def _band_score(value: float, bands):
    limits, fallback = bands
    for upper_exclusive, score in limits:
        if value < upper_exclusive:
            return score
    return fallback


def _temperature_score(temperature: float):
    if temperature < TEMP_LOW_BELOW or temperature > TEMP_HIGH_ABOVE:
        return 2
    return 0


def _age_emergency_fields(form_type):
    fields = list(BASE_EMERGENCY_FIELDS)

    if form_type in ("Child", "Infant"):
        fields.extend(CHILD_INFANT_EMERGENCY_FIELDS)
    elif form_type == "Maternity":
        fields.extend(MATERNITY_EMERGENCY_FIELDS)

    return tuple(fields)


# --------------------------------------------------------------------------
# Patient group from age
# --------------------------------------------------------------------------

def _to_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def age_in_months(date_of_birth, on_date=None):
    """Completed months between the date of birth and on_date (default today)."""
    dob = _to_date(date_of_birth)
    if dob is None:
        return None

    on = _to_date(on_date) or date.today()
    if dob > on:
        raise ValueError("Date of birth is after the arrival date.")

    months = (on.year - dob.year) * 12 + (on.month - dob.month)
    if on.day < dob.day:
        months -= 1
    return months


def detect_form_type(date_of_birth, is_maternity, on_date=None):
    """
    Maternity for a maternity patient of any age, otherwise by age:
    Infant up to and including 3 years, Child up to and including 12 years,
    Adult over 12 years.
    """
    if is_maternity:
        return "Maternity"

    months = age_in_months(date_of_birth, on_date)
    if months is None:
        raise ValueError("Date of birth is required to choose the triage form.")

    if months <= INFANT_MAX_MONTHS:
        return "Infant"
    if months <= CHILD_MAX_MONTHS:
        return "Child"
    return "Adult"


# --------------------------------------------------------------------------
# TEWS
# --------------------------------------------------------------------------

def calculate_tews(form_type: str, data: Any):
    """
    Return component scores and total.

    `total` is None when a required observation has not been recorded. A
    recorded value is always scored; a missing one is never treated as zero.
    SBP is scored on the adult and maternity forms only.
    """

    if form_type not in FORMS:
        raise ValueError(f"Unsupported form type: {form_type}")

    adult_like = form_type in ADULT_LIKE

    missing = []
    if not _has_choice(data, "mobility"):
        missing.append("mobility")
    if _measurement(data, "rr") is None:
        missing.append("rr")
    if _measurement(data, "hr") is None:
        missing.append("hr")
    if adult_like and _measurement(data, "sbp") is None:
        missing.append("sbp")
    if _measurement(data, "temperature") is None:
        missing.append("temperature")
    if not _has_choice(data, "avpu"):
        missing.append("avpu")

    avup = _value(data, "avpu")
    if "avpu" not in missing and avup not in AVUP_SCORES:
        missing.append("avpu")

    if missing:
        return {
            "complete": False,
            "missing_fields": missing,
            "component_scores": {},
            "total": None,
        }

    mobility = _number(data, "mobility")
    if mobility not in VALID_MOBILITY[form_type]:
        allowed = ", ".join(str(v) for v in VALID_MOBILITY[form_type])
        raise ValueError(
            f"{form_type} mobility must be one of {allowed}."
        )

    scores = {
        "mobility_score": int(mobility),
        "rr_score": _band_score(_measurement(data, "rr"), RR_BANDS[form_type]),
        "hr_score": _band_score(_measurement(data, "hr"), HR_BANDS[form_type]),
    }

    if adult_like:
        scores["sbp_score"] = _band_score(_measurement(data, "sbp"), ADULT_SBP)

    scores["temp_score"] = _temperature_score(_measurement(data, "temperature"))
    scores["avpu_score"] = AVUP_SCORES[avup]
    scores["trauma_score"] = 1 if bool(_value(data, "trauma")) else 0

    return {
        "complete": True,
        "missing_fields": [],
        "component_scores": scores,
        "total": sum(scores.values()),
    }


def determine_triage_color(form_type: str, data: Any, tews_result: dict):
    """
    Apply the emergency, TEWS and danger-sign decision pathway.
    """

    if form_type not in VERY_URGENT_FIELDS:
        raise ValueError(f"Unsupported form type: {form_type}")

    # Emergency alarm signs take precedence over the score.
    if _checked(data, _age_emergency_fields(form_type)):
        return "RED"

    spo2 = _measurement(data, "spo2")
    if spo2 is not None and spo2 < SPO2_RED_BELOW:
        return "RED"

    if not tews_result or not tews_result.get("complete"):
        return None

    total = tews_result["total"]

    if total >= 7:
        return "RED"

    if total >= 5:
        return "ORANGE"

    if _checked(data, VERY_URGENT_FIELDS[form_type]):
        return "ORANGE"

    if total >= 3:
        return "YELLOW"

    if _checked(data, URGENT_FIELDS[form_type]):
        return "YELLOW"

    return "GREEN"
