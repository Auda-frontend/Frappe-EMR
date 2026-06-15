# -*- coding: utf-8 -*-
from frappe.model.document import Document
import frappe


class AdultTriageForm(Document):
    def on_update(self):
        sync_to_parent_triage(self)


@frappe.whitelist()
def sync_to_parent_triage(doc, method=None):
    """Synchronize Adult Triage Form data to parent Triage or Triage Assessment record"""

    if not doc:
        return

    parent_triage = doc.parent_triage
    assessment_name = doc.triage_assessment

    if not parent_triage and not assessment_name:
        return

    try:
        if assessment_name:
            parent_doc = frappe.get_doc("Triage Assessment", assessment_name)

            if doc.triage_color:
                parent_doc.triage_color = doc.triage_color
            if doc.tews_score:
                parent_doc.tews_score = doc.tews_score
            if doc.spo2:
                parent_doc.spo2 = doc.spo2
            if doc.pain_score:
                parent_doc.pain_score = doc.pain_score

            parent_doc.adult_triage_form = doc.name
            parent_doc.form_type = parent_doc.form_type or "Adult"

            parent_doc.flags.ignore_permissions = True
            parent_doc.save()

        else:
            parent_doc = frappe.get_doc("Triage", parent_triage)

            if doc.rr:
                parent_doc.respiratory_rate = doc.rr
            if doc.hr:
                parent_doc.pulse = doc.hr
            if doc.sbp:
                parent_doc.bp_systolic = doc.sbp
            if doc.temperature:
                parent_doc.temperature = doc.temperature
            if doc.spo2:
                parent_doc.rw_spo2 = doc.spo2

            if doc.tews_score:
                parent_doc.rw_tews_score = doc.tews_score
            if doc.pain_score:
                parent_doc.rw_pain_score = doc.pain_score

            if doc.avpu:
                parent_doc.vital_signs_note = f"AVPU: {doc.avpu}"

            if doc.triage_color:
                parent_doc.rw_triage_category = doc.triage_color

            parent_doc.rw_adult_triage_form = doc.name

            parent_doc.save(ignore_permissions=True)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Adult Triage Form Sync Error")