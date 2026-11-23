# -*- coding: utf-8 -*-
"""Authoritative server-side Rwanda Triage Assessment workflow."""

import re

import frappe
from frappe.model.document import Document
from frappe.utils import flt, today

from healthcare.healthcare.rwanda_triage.tews import (
    calculate_tews,
    detect_form_type,
    determine_triage_color,
)
from healthcare.healthcare.rwanda_triage.scoring import (
    map_triage_color_to_opd_priority,
)


VALID_TRIAGE_COLOURS = ("RED", "ORANGE", "YELLOW", "GREEN")

# Data-entry sanity limits only (they stop typing mistakes). They are NOT triage thresholds.
# Have a clinician confirm them, then change the numbers here.
BODY_LIMITS = {
    "bp_diastolic": (20, 200, "mmHg"),
    "weight": (0.3, 400, "kg"),
    "height": (20, 250, "cm"),
}


class TriageAssessment(Document):
    def validate(self):
        if not self.nurse_name:
            self.nurse_name = frappe.session.user

        self.enforce_maternity_for_females_only()
        self.set_authoritative_form_type()
        self.clear_signs_for_other_groups()
        self.validate_queue_link()
        self.validate_body_measurements()
        self.calculate_and_set_triage_result()


    def after_insert(self):
        """Creating the assessment, from the Queue or not, puts the patient In Service at the nursing station."""
        from healthcare.healthcare.queue_api import start_entry_for_patient

        queue = start_entry_for_patient(self.patient, "Triage")
        if queue and not self.queue:
            self.db_set("queue", queue, update_modified=False)

    def validate_queue_link(self):
        """An assessment opened from the Queue belongs to that patient, and each entry has only one."""
        if not self.queue:
            return
        patient = frappe.db.get_value("Queue", self.queue, "patient")
        if patient and patient != self.patient:
            frappe.throw(frappe._("This Queue entry belongs to another patient."), title=frappe._("Queue"))
        other = frappe.db.get_value(
            "Triage Assessment",
            {"queue": self.queue, "docstatus": ["<", 2], "name": ["!=", self.name or ""]},
            "name",
        )
        if other:
            frappe.throw(
                frappe._("This Queue entry already has a Triage Assessment ({0}). Open that one.").format(other),
                title=frappe._("Queue"),
            )

    def enforce_maternity_for_females_only(self):
        """A maternity assessment is only valid for a female patient."""
        if not self.is_maternity:
            return
        sex = frappe.db.get_value("Patient", self.patient, "sex") if self.patient else None
        if (sex or "").strip().lower() != "female":
            self.is_maternity = 0

    def clear_signs_for_other_groups(self):
        """Signs that belong to another patient group must never count towards this result.

        A field is group-specific when its depends_on only lists form types, for example
        eval:doc.form_type=="Child" || doc.form_type=="Infant". If the patient group changed
        after a sign was ticked, the hidden value is cleared here.
        """
        group_only = re.compile(r'^eval:\s*(doc\.form_type\s*==\s*"[A-Za-z]+"\s*(\|\|\s*)?)+$')
        for df in frappe.get_meta(self.doctype).fields:
            if df.fieldtype not in ("Check", "Int", "Float"):
                continue
            rule = df.depends_on or ""
            if not group_only.match(rule):
                continue
            if self.form_type in re.findall(r'"([A-Za-z]+)"', rule):
                continue
            if self.get(df.fieldname):
                self.set(df.fieldname, 0 if df.fieldtype == "Check" else None)

    def set_authoritative_form_type(self):
        """Derive the patient group from maternity status and the patient's date of birth."""
        dob = frappe.db.get_value("Patient", self.patient, "dob") if self.patient else None
        try:
            self.form_type = detect_form_type(
                dob or self.get("date_of_birth"),
                self.is_maternity,
                self.arrival_date or today(),
            )
        except ValueError as exc:
            frappe.throw(frappe._(str(exc)))

    # def set_authoritative_form_type(self):
    #     """Derive the patient group from maternity status and recorded age."""
    #     if self.is_maternity:
    #         self.form_type = "Maternity"
    #         return

    #     age_months = self.get("patient_age_months")
    #     age_years = self.get("patient_age")

    #     if age_months is not None and age_months != "":
    #         age_months = flt(age_months)
    #         if age_months <= 36:
    #             self.form_type = "Infant"
    #         elif age_months <= 144:
    #             self.form_type = "Child"
    #         else:
    #             self.form_type = "Adult"
    #         return

    #     if age_years is not None and age_years != "":
    #         age_years = flt(age_years)
    #         if age_years <= 3:
    #             self.form_type = "Infant"
    #         elif age_years <= 12:
    #             self.form_type = "Child"
    #         else:
    #             self.form_type = "Adult"

    #     if self.form_type not in ("Adult", "Child", "Infant", "Maternity"):
    #         frappe.throw(
    #             frappe._("Patient age or a valid patient type is required for triage.")
    #         )

    def calculate_and_set_triage_result(self):
        """Recalculate component scores and colour from this assessment only."""
        try:
            result = calculate_tews(self.form_type, self)
            colour = determine_triage_color(self.form_type, self, result)
        except ValueError as exc:
            frappe.throw(frappe._(str(exc)))

        score_fields = (
            "mobility_score",
            "rr_score",
            "hr_score",
            "sbp_score",
            "temp_score",
            "avpu_score",
            "trauma_score",
        )

        # Clear old values first. Incomplete observations must not retain
        # scores from a previous calculation.
        for fieldname in score_fields:
            self.set(fieldname, None)

        for fieldname, value in result.get("component_scores", {}).items():
            if fieldname in score_fields:
                self.set(fieldname, value)

        self.tews_score = result.get("total")
        self.calculated_triage_color = colour

        if self.manual_priority_override:
            if not (self.override_reason or "").strip():
                frappe.throw(
                    frappe._("A reason is required when manually overriding triage priority.")
                )
            if self.triage_color not in VALID_TRIAGE_COLOURS:
                frappe.throw(
                    frappe._("Select a valid triage colour for the manual override.")
                )
        else:
            # The final colour follows the server calculation unless
            # an explicitly documented manual override is active.
            self.triage_color = colour

    def before_submit(self):
        """A colour is needed to submit. Emergency signs, SpO2 under 92 and a documented
        manual override already give one; otherwise every required observation must be entered."""
        if self.triage_color:
            return

        missing = calculate_tews(self.form_type, self).get("missing_fields", [])
        if missing:
            meta = frappe.get_meta(self.doctype)
            labels = [meta.get_label(fieldname) or fieldname for fieldname in missing]
            frappe.throw(
                frappe._("Missing fields: {0}. Complete them before submitting.").format(", ".join(labels)),
                title=frappe._("Missing Fields"),
            )

        frappe.throw(
            frappe._("This assessment cannot be submitted because no triage colour could be determined.")
        )

    def on_submit(self):
        self.create_vital_signs_from_assessment()
        self.update_patient_triage_state()
        self.publish_critical_alert()

    def validate_body_measurements(self):
        """Blood pressure, weight and height: not recorded is empty, bad values are refused, BMI is calculated."""
        for fieldname, (low, high, unit) in BODY_LIMITS.items():
            value = flt(self.get(fieldname))
            if value <= 0:
                self.set(fieldname, None)
                continue
            if value < low or value > high:
                label = frappe.get_meta(self.doctype).get_label(fieldname)
                frappe.throw(frappe._("{0} must be between {1} and {2} {3}.").format(label, low, high, unit))

        systolic, diastolic = flt(self.get("sbp")), flt(self.get("bp_diastolic"))
        if systolic > 0 and diastolic > 0 and diastolic >= systolic:
            frappe.throw(frappe._("Diastolic blood pressure must be lower than systolic."))

        weight, height = flt(self.get("weight")), flt(self.get("height"))
        self.bmi = round(weight / ((height / 100) ** 2), 1) if weight > 0 and height > 0 else None

    def copy_body_measurements_to_vital_signs(self):
        """Carry the extra measurements into the generated Vital Signs record."""
        name = self.get("vital_signs_record")
        if not name or not frappe.db.exists("Vital Signs", name):
            return
        meta = frappe.get_meta("Vital Signs")
        values = {}
        for target, value in (
            ("bp_diastolic", self.get("bp_diastolic")),
            ("weight", self.get("weight")),
            ("height", round(flt(self.get("height")) / 100, 3)),  # Vital Signs stores metres
            ("bmi", self.get("bmi")),
        ):
            if value and meta.has_field(target):
                values[target] = value
        if flt(self.get("sbp")) > 0 and flt(self.get("bp_diastolic")) > 0 and meta.has_field("bp"):
            values["bp"] = "%d/%d" % (flt(self.get("sbp")), flt(self.get("bp_diastolic")))
        if values:
            frappe.db.set_value("Vital Signs", name, values, update_modified=False)

    def create_vital_signs_from_assessment(self):
        result = self._create_vital_signs_core()
        self.copy_body_measurements_to_vital_signs()
        return result

    def _create_vital_signs_core(self):
        """Create one standard Vital Signs record directly from this assessment."""
        if self.vital_signs_record:
            return

        if not self.patient:
            frappe.throw(frappe._("A patient is required to create Vital Signs."))

        vs = frappe.new_doc("Vital Signs")
        vs.naming_series = "HLC-VTS-.YYYY.-"
        vs.patient = self.patient
        vs.company = self.company
        vs.signs_date = self.arrival_date or today()
        vs.signs_time = self.arrival_time

        vs.rw_triage_color = self.triage_color
        vs.rw_triage_category = map_triage_color_to_opd_priority(self.triage_color)
        vs.rw_chief_complaint = self.chief_complaint

        # Read measurements directly from the unified assessment.
        vs.rw_spo2 = self.spo2
        vs.rw_pain_score = self.pain_score
        vs.temperature = self.temperature
        vs.pulse = self.hr
        vs.respiratory_rate = self.rr

        if self.sbp is not None:
            vs.bp_systolic = self.sbp

        vs.rw_tews_score = self.tews_score
        vs.rw_form_type = self.form_type
        vs.rw_triage_assessment = self.name

        if self.muac is not None:
            vs.rw_muac = self.muac

        if self.triage_notes:
            vs.rw_triage_notes = self.triage_notes

        if self.patient_oriented:
            vs.rw_oriented = 1

        vs.flags.ignore_permissions = True
        vs.insert()

        self.db_set("vital_signs_record", vs.name, update_modified=False)

        frappe.msgprint(
            frappe._("Vital Signs {0} created.").format(vs.name),
            alert=True,
        )

    def update_patient_triage_state(self):
        """The patient carries the colour of their newest submitted assessment only."""
        newer = frappe.db.exists(
            "Triage Assessment",
            {
                "patient": self.patient,
                "docstatus": 1,
                "creation": [">", self.creation],
                "name": ["!=", self.name],
            },
        )
        if newer:
            return

        frappe.db.set_value(
            "Patient",
            self.patient,
            {
                "rw_triage_color": self.triage_color,
                "rw_last_triage_date": self.arrival_date or today(),
                "rw_active_triage_assessment": self.name,
            },
            update_modified=False,
        )

    def publish_critical_alert(self):
        if self.triage_color not in ("RED", "ORANGE"):
            return

        frappe.publish_realtime(
            "triage_alert",
            {
                "patient_name": self.patient_name,
                "color": self.triage_color,
                "mrn": self.medical_record_number,
                "tews": self.tews_score,
                "arrival_time": str(self.arrival_time),
                "form_type": self.form_type,
            },
        )
