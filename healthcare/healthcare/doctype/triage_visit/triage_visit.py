# Copyright (c) 2026, Rwanda EMR and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, today


class TriageVisit(Document):
	def before_save(self):
		self.calculate_bmi()

	def on_submit(self):
		self.create_vital_signs()

	def calculate_bmi(self):
		if self.height and self.weight and self.height > 0:
			self.bmi = round(self.weight / (self.height**2), 1)

	def create_vital_signs(self):
		if self.linked_vital_signs:
			return

		vs = frappe.new_doc("Vital Signs")
		vs.naming_series = "HLC-VTS-.YYYY.-"
		vs.patient = self.patient
		vs.company = self.company
		vs.signs_date = self.signs_date or today()
		vs.signs_time = self.signs_time or now_datetime().strftime("%H:%M:%S")
		vs.temperature = self.temperature
		vs.pulse = self.pulse
		vs.respiratory_rate = self.respiratory_rate
		vs.bp_systolic = self.bp_systolic
		vs.bp_diastolic = self.bp_diastolic
		vs.tongue = self.tongue
		vs.abdomen = self.abdomen
		vs.reflexes = self.reflexes
		vs.height = self.height
		vs.weight = self.weight
		vs.bmi = self.bmi
		vs.vital_signs_note = self.vital_signs_note
		vs.flags.ignore_permissions = True
		vs.insert()

		frappe.db.set_value("Triage Visit", self.name, "linked_vital_signs", vs.name)
		frappe.msgprint(f"Vital Signs record {vs.name} created automatically.", alert=True)
