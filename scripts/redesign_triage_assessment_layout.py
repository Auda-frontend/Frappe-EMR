#!/usr/bin/env python3
"""Safely reorganise the Triage Assessment DocType layout.

Default: generate a preview only.
Use --apply only after reviewing the preview.
"""

import argparse
import copy
import json
import sys
from pathlib import Path

SOURCE = Path(
    "healthcare/healthcare/doctype/triage_assessment/triage_assessment.json"
)
PREVIEW = Path("/tmp/triage_assessment_ux_preview.json")
BACKUP = Path("/tmp/triage_assessment.before_ux_redesign.json")

parser = argparse.ArgumentParser()
parser.add_argument(
    "--apply",
    action="store_true",
    help="Apply the reviewed layout to the source JSON",
)
args = parser.parse_args()


def fail(message):
    print(f"\nERROR: {message}")
    sys.exit(1)


if not SOURCE.exists():
    fail(f"Cannot find DocType JSON: {SOURCE}")

with SOURCE.open(encoding="utf-8") as handle:
    original = json.load(handle)

original_fields = original.get("fields", [])
original_names = [f.get("fieldname") for f in original_fields]

if not original_names or any(not name for name in original_names):
    fail("A field is missing its fieldname.")

if len(original_names) != len(set(original_names)):
    fail("The original JSON already contains duplicate fieldnames.")

fields = {
    field["fieldname"]: copy.deepcopy(field)
    for field in original_fields
}

used = set()
ordered = []


def take(name):
    """Take one existing field, preserving all its original properties."""
    if name not in fields:
        fail(f"Expected existing field is missing: {name}")
    if name in used:
        fail(f"Field was included more than once: {name}")

    used.add(name)
    ordered.append(copy.deepcopy(fields[name]))


def take_many(names):
    for name in names:
        take(name)


def take_matching(predicate):
    """Take matching original fields in their existing relative order."""
    names = [
        name for name in original_names
        if name not in used and predicate(fields[name])
    ]
    take_many(names)


def add_section(name, label, description):
    if name in fields or name in used:
        fail(f"New section fieldname already exists: {name}")

    ordered.append({
        "fieldname": name,
        "fieldtype": "Section Break",
        "label": label,
        "description": description,
    })
    used.add(name)


def add_column(name):
    if name in fields or name in used:
        fail(f"New column fieldname already exists: {name}")

    ordered.append({
        "fieldname": name,
        "fieldtype": "Column Break",
    })
    used.add(name)


def add_two_columns(names, column_name):
    """Split a group into two columns without changing its field definitions."""
    midpoint = (len(names) + 1) // 2

    take_many(names[:midpoint])

    if names[midpoint:]:
        add_column(column_name)
        take_many(names[midpoint:])


def update_section(name, label, description):
    if name not in fields:
        fail(f"Existing section break is missing: {name}")

    if fields[name].get("fieldtype") != "Section Break":
        fail(f"{name} is not a Section Break.")

    fields[name]["label"] = label
    fields[name]["description"] = description


# Reuse the existing section breaks. Only their presentation labels change.
update_section(
    "sb_routing",
    "Patient classification",
    "Confirm the patient's clinical category before completing the assessment.",
)
update_section(
    "sb_clinical_assessment",
    "Immediate danger signs",
    "Assess emergency signs first. Any emergency sign takes priority over the TEWS score.",
)
update_section(
    "sb_result",
    "Triage decision",
    "Review the server-calculated triage result and record an override only when justified.",
)
update_section(
    "sb_notification",
    "Escalation and notification",
    "Record notification and clinical attendance for patients requiring escalation.",
)
update_section(
    "sb_outcome",
    "Clinical notes and disposition",
    "Record the linked Vital Signs entry, clinical notes and patient orientation.",
)

# 1. Patient and visit information.
take("naming_series")
add_section(
    "sb_patient_details",
    "Patient and visit information",
    "Select the patient and confirm their demographic and visit details.",
)

patient_left = [
    "patient",
    "patient_name",
    "date_of_birth",
    "patient_age",
    "patient_age_months",
    "patient_gender",
    "medical_record_number",
    "is_maternity",
]

patient_right = [
    "chief_complaint",
    "arrival_date",
    "arrival_time",
    "company",
]

take_many(patient_left)
add_column("cb_patient_details")
take_many(patient_right)
take("sb_routing")
take("form_type")

# Place the visit details after patient classification in the same workflow.
# The existing classification section remains intact.

# 2. Emergency signs.
take("sb_clinical_assessment")

emergency_names = [
    name for name in original_names
    if (
        name.startswith("alarm_")
        or name.startswith("dehydration_")
        or name in {
            "convulsion_glucose",
            "coma_glucose",
        }
    )
]

add_two_columns(emergency_names, "cb_emergency_signs")

# 3. Clinical observations.
add_section(
    "sb_vital_observations",
    "Clinical observations and TEWS measurements",
    "Enter the available measurements. Do not estimate or enter zero for an unmeasured observation.",
)

observation_names = [
    "mobility",
    "mobility_score",
    "rr",
    "rr_score",
    "hr",
    "hr_score",
    "sbp",
    "sbp_score",
    "temperature",
    "temp_score",
    "avpu",
    "avpu_score",
    "trauma",
    "trauma_score",
    "spo2",
    "pain_score",
    "muac",
]

add_two_columns(observation_names, "cb_vital_observations")

# 4. Urgent signs.
add_section(
    "sb_urgent_signs",
    "Urgent signs",
    "Assess the urgent signs applicable to the patient's age group or maternity status.",
)

urgent_names = [
    name for name in original_names
    if name.startswith("yellow_")
]

add_two_columns(urgent_names, "cb_urgent_signs")

# 5. Less urgent signs.
add_section(
    "sb_less_urgent_signs",
    "Other clinical signs",
    "Assess the additional clinical signs applicable to the patient.",
)

less_urgent_names = [
    name for name in original_names
    if name.startswith("green_")
]

add_two_columns(less_urgent_names, "cb_less_urgent_signs")

# 6. Triage result.
take("sb_result")
take_many([
    "triage_color",
    "tews_score",
    "manual_priority_override",
    "override_reason",
])

# 7. Escalation and notification.
take("sb_notification")
take_many([
    "notified_color",
    "notified_at",
    "nurse_name",
    "triage_finish_time",
    "doctor_name",
    "doctor_attended_at",
])

# 8. Outcome and notes.
take("sb_outcome")
take_many([
    "vital_signs_record",
    "triage_notes",
    "patient_oriented",
])

# Integrity checks: every original field must appear exactly once.
missing = set(original_names) - used
unexpected = used - set(original_names) - {
    "sb_patient_details",
    "cb_patient_details",
    "cb_emergency_signs",
    "sb_vital_observations",
    "cb_vital_observations",
    "sb_urgent_signs",
    "cb_urgent_signs",
    "sb_less_urgent_signs",
    "cb_less_urgent_signs",
}

if missing:
    fail(f"Original fields missing from redesigned layout: {sorted(missing)}")

if unexpected:
    fail(f"Unexpected fields in redesigned layout: {sorted(unexpected)}")

new_names = [field["fieldname"] for field in ordered]

if len(new_names) != len(set(new_names)):
    fail("Duplicate fieldnames found in redesigned layout.")

if not set(original_names).issubset(set(new_names)):
    fail("Not all original fields survived the redesign.")

# Verify that original field definitions are unchanged, except for the
# five existing section labels/descriptions intentionally updated above.
intentional_section_changes = {
    "sb_routing",
    "sb_clinical_assessment",
    "sb_result",
    "sb_notification",
    "sb_outcome",
}

for name in original_names:
    if name in intentional_section_changes:
        continue

    if ordered[new_names.index(name)] != fields[name]:
        fail(f"Unexpected field definition change: {name}")

result = copy.deepcopy(original)
result["fields"] = ordered
result["field_order"] = new_names

# Ensure every field_order entry corresponds to exactly one field.
if len(result["field_order"]) != len(result["fields"]):
    fail("field_order length does not match fields length.")

if set(result["field_order"]) != {
    field["fieldname"] for field in result["fields"]
}:
    fail("field_order does not match the redesigned field definitions.")

# Write a preview without modifying the source.
PREVIEW.write_text(
    json.dumps(result, indent=1, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

print("\n========== TRIAGE LAYOUT PREVIEW ==========")

section_labels = {
    "sb_patient_details": "PATIENT AND VISIT INFORMATION",
    "sb_routing": "PATIENT CLASSIFICATION",
    "sb_clinical_assessment": "IMMEDIATE DANGER SIGNS",
    "sb_vital_observations": "CLINICAL OBSERVATIONS AND TEWS",
    "sb_urgent_signs": "URGENT SIGNS",
    "sb_less_urgent_signs": "OTHER CLINICAL SIGNS",
    "sb_result": "TRIAGE DECISION",
    "sb_notification": "ESCALATION AND NOTIFICATION",
    "sb_outcome": "CLINICAL NOTES AND DISPOSITION",
}

for index, field in enumerate(ordered, 1):
    name = field["fieldname"]
    fieldtype = field.get("fieldtype", "")
    label = field.get("label", name)

    if fieldtype == "Section Break":
        print(f"\n--- {section_labels.get(name, label)} ---")
    elif fieldtype == "Column Break":
        print("    | NEW COLUMN |")
    else:
        print(
            f"{index:03}. {label} | {name} | {fieldtype}"
            f" | depends_on={field.get('depends_on', '')}"
        )

print("\n========== INTEGRITY REPORT ==========")
print(f"Original fields:       {len(original_names)}")
print(f"Redesigned fields:     {len(ordered)}")
print(f"Original fields kept:  {len(set(original_names) & set(new_names))}")
print(f"New layout controls:   {len(new_names) - len(original_names)}")
print(f"Unique fieldnames:     {len(set(new_names))}")
print("Missing original fields: 0")
print("Duplicate fieldnames:    0")
print("Unexpected field changes: 0")
print("field_order consistency: PASS")
print(f"\nPreview written to: {PREVIEW}")

if args.apply:
    if BACKUP.exists():
        fail(
            f"Backup already exists at {BACKUP}. "
            "Do not overwrite it. Review it before proceeding."
        )

    BACKUP.write_text(
        SOURCE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    SOURCE.write_text(
        json.dumps(result, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Read back the written source and verify it.
    with SOURCE.open(encoding="utf-8") as handle:
        applied = json.load(handle)

    if applied["field_order"] != new_names:
        fail("Post-write verification failed.")

    print(f"\nAPPLIED successfully.")
    print(f"Original source backup: {BACKUP}")
else:
    print("\nPREVIEW ONLY: source JSON has NOT been modified.")
    print("Review the layout before running this script with --apply.")
