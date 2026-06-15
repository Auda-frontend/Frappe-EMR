# -*- coding: utf-8 -*-
"""Server-side triage assessment and form sync."""

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, now_datetime, today

from healthcare.healthcare.rwanda_triage.scoring import (
	FORM_TYPE_DOCTYPE,
	map_triage_color_to_opd_priority,
)


class TriageAssessment(Document):
	def validate(self):
		if not self.nurse_name:
			self.nurse_name = frappe.session.user

	def on_submit(self):
		self.create_vital_signs_from_assessment()
		self.update_patient_triage_state()
		self.publish_critical_alert()

	def create_vital_signs_from_assessment(self):
		if self.vital_signs_record:
			return

		child = self.get_linked_form_doc()
		if not child:
			frappe.throw(
				frappe._(
					"No age-specific triage form is linked. Create and save the {0} form before submitting."
				).format(self.form_type)
			)

		vs = frappe.new_doc("Vital Signs")
		vs.naming_series = "HLC-VTS-.YYYY.-"
		vs.patient = self.patient
		vs.company = self.company
		vs.signs_date = self.arrival_date or today()
		vs.signs_time = self.arrival_time

		color = self.triage_color or child.get("triage_color")
		vs.rw_triage_color = color
		vs.rw_triage_category = map_triage_color_to_opd_priority(color)
		vs.rw_chief_complaint = self.chief_complaint
		vs.rw_spo2 = child.get("spo2") or self.spo2
		vs.rw_pain_score = child.get("pain_score") or self.pain_score
		vs.temperature = child.get("temperature")
		vs.pulse = child.get("hr")
		vs.respiratory_rate = child.get("rr")
		if child.get("sbp"):
			vs.bp_systolic = child.get("sbp")
		vs.rw_tews_score = child.get("tews_score") or self.tews_score
		vs.rw_form_type = self.form_type
		vs.rw_triage_assessment = self.name
		if self.muac:
			vs.rw_muac = self.muac
		if self.triage_notes:
			vs.rw_triage_notes = self.triage_notes
		if self.patient_oriented:
			vs.rw_oriented = 1

		vs.flags.ignore_permissions = True
		vs.insert()

		self.db_set("vital_signs_record", vs.name, update_modified=False)
		frappe.msgprint(frappe._("Vital Signs {0} created.").format(vs.name), alert=True)

	def get_linked_form_doc(self):
		if not self.form_type:
			return None
		meta = FORM_TYPE_DOCTYPE.get(self.form_type)
		if not meta:
			return None
		doctype, fieldname = meta
		ref = self.get(fieldname)
		if not ref:
			return None
		return frappe.get_doc(doctype, ref)

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


def push_form_results_to_assessment(doc, method=None):
	"""Age-specific form on_update → parent Triage Assessment."""
	if not doc.get("triage_assessment"):
		return
	updates = {
		"triage_color": doc.get("triage_color"),
		"tews_score": doc.get("tews_score"),
		"spo2": doc.get("spo2"),
		"pain_score": doc.get("pain_score"),
	}
	frappe.db.set_value("Triage Assessment", doc.triage_assessment, updates, update_modified=True)

	if doc.get("patient") and doc.get("triage_color"):
		frappe.db.set_value(
			"Patient",
			doc.patient,
			"rw_triage_color",
			doc.triage_color,
			update_modified=False,
		)

	# Link back on assessment if empty
	form_type_link = {
		"Adult Triage Form": ("Adult", "adult_triage_form"),
		"Child Triage Form": ("Child", "child_triage_form"),
		"Infant Triage Form": ("Infant", "infant_triage_form"),
		"Maternity Triage Form": ("Maternity", "maternity_triage_form"),
	}
	if doc.doctype in form_type_link:
		ftype, field = form_type_link[doc.doctype]
		assessment = frappe.get_doc("Triage Assessment", doc.triage_assessment)
		if not assessment.get(field):
			assessment.db_set(field, doc.name, update_modified=False)
		if not assessment.form_type:
			assessment.db_set("form_type", ftype, update_modified=False)
