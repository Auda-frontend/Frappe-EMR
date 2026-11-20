# -*- coding: utf-8 -*-
"""Authoritative server-side Rwanda Triage Assessment workflow."""

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


class TriageAssessment(Document):
    def validate(self):
        if not self.nurse_name:
            self.nurse_name = frappe.session.user

        self.set_authoritative_form_type()
        self.calculate_and_set_triage_result()


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
        if not self.triage_color:
            details = []

            if self.get("missing_fields"):
                details.extend(self.get("missing_fields"))

            frappe.throw(
                frappe._(
                    "This assessment cannot be submitted because no triage colour "
                    "could be determined. Complete the required observations first."
                )
            )

    def on_submit(self):
        self.create_vital_signs_from_assessment()
        self.update_patient_triage_state()
        self.publish_critical_alert()

    def create_vital_signs_from_assessment(self):
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
