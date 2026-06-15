from frappe import _
from frappe.model.document import Document
from frappe.realtime import publish_realtime
import frappe


class Triage(Document):
	def on_submit(self):
		"""Update Patient record with triage results and publish notifications"""
		
		# Update Patient with triage metadata
		patient = frappe.get_doc("Patient", self.patient)
		patient.custom_triage_color = self.rw_triage_category
		patient.custom_last_triage_date = self.signs_date
		patient.custom_active_triage = self.name
		patient.save(ignore_permissions=True)

		# Publish realtime alerts for RED and ORANGE
		if self.rw_triage_category in ("RED", "ORANGE"):
			# Publish to specific role group (nurses and physicians)
			alert_data = {
				"doctype": "Triage",
				"name": self.name,
				"patient": self.patient,
				"patient_name": frappe.db.get_value("Patient", self.patient, "patient_name"),
				"color": self.rw_triage_category,
				"triage_time": self.signs_date + " " + self.signs_time if self.signs_time else self.signs_date,
				"timestamp": frappe.datetime.now()
			}
			
			# Publish to specific users/roles
			publish_realtime(
				event="triage_alert",
				message=alert_data,
				room="triage_alerts"
			)

		# Record notification metadata
		if self.rw_triage_category in ("RED", "ORANGE"):
			self.rw_notified_color = self.rw_triage_category
			self.rw_notified_at = frappe.datetime.now()
			self.save(ignore_permissions=True)


@frappe.whitelist()
def get_patient_triage_info(patient):
	"""Get current triage info for a patient"""
	try:
		patient_doc = frappe.get_doc("Patient", patient)
		return {
			"custom_triage_color": patient_doc.custom_triage_color,
			"custom_last_triage_date": patient_doc.custom_last_triage_date,
			"custom_active_triage": patient_doc.custom_active_triage,
			"is_maternity": patient_doc.rw_is_maternity
		}
	except:
		return {}


@frappe.whitelist()
def get_triage_form_type(patient):
	"""Determine which triage form type to use based on patient age"""
	try:
		dob = frappe.db.get_value("Patient", patient, "dob")
		is_maternity = frappe.db.get_value("Patient", patient, "rw_is_maternity")
		
		if not dob:
			return "Adult"  # Default
		
		age_years = (frappe.datetime.get_today() - dob).days // 365
		
		if is_maternity:
			return "Maternity"
		elif age_years >= 16:
			return "Adult"
		elif age_years >= 5:
			return "Child"
		else:
			return "Infant"
	except:
		return "Adult"
