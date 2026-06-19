# -*- coding: utf-8 -*-
"""Sync age-specific triage form results to Triage Assessment / legacy Triage."""

import frappe

from healthcare.healthcare.rwanda_triage.scoring import sync_form_results_to_assessment

FORM_LINK_FIELD = {
	"Adult Triage Form": ("Adult", "adult_triage_form", "rw_adult_triage_form"),
	"Child Triage Form": ("Child", "child_triage_form", "rw_child_triage_form"),
	"Infant Triage Form": ("Infant", "infant_triage_form", "rw_infant_triage_form"),
	"Maternity Triage Form": ("Maternity", "maternity_triage_form", "rw_maternity_triage_form"),
}


def _as_doc(doc):
	if isinstance(doc, dict):
		return frappe._dict(doc)
	return doc


def sync_triage_form_to_parent(doc, method=None):
	"""Hook handler for all age-specific triage forms."""
	doc = _as_doc(doc)
	if not doc:
		return

	parent_triage = doc.get("parent_triage")
	assessment_name = doc.get("triage_assessment")
	if not parent_triage and not assessment_name:
		return

	meta = FORM_LINK_FIELD.get(doc.doctype)
	if not meta:
		return

	form_type, assessment_field, legacy_field = meta

	try:
		if assessment_name:
			parent_doc = frappe.get_doc("Triage Assessment", assessment_name)
			sync_form_results_to_assessment(parent_doc, doc)
			parent_doc.set(assessment_field, doc.name)
			if not parent_doc.form_type:
				parent_doc.form_type = form_type
			parent_doc.flags.ignore_permissions = True
			parent_doc.save()
			return

		parent_doc = frappe.get_doc("Triage", parent_triage)

		if doc.get("rr"):
			parent_doc.respiratory_rate = doc.rr
		if doc.get("hr"):
			parent_doc.pulse = doc.hr
		if doc.get("sbp"):
			parent_doc.bp_systolic = doc.sbp
		if doc.get("temperature"):
			parent_doc.temperature = doc.temperature
		if doc.get("spo2") is not None:
			parent_doc.rw_spo2 = doc.spo2
		if doc.get("tews_score") is not None:
			parent_doc.rw_tews_score = doc.tews_score
		if doc.get("pain_score") is not None:
			parent_doc.rw_pain_score = doc.pain_score
		if doc.get("avpu"):
			parent_doc.vital_signs_note = f"AVPU: {doc.avpu}"
		if doc.get("triage_color"):
			parent_doc.rw_triage_category = doc.triage_color

		parent_doc.set(legacy_field, doc.name)
		parent_doc.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"{doc.doctype} Sync Error")
