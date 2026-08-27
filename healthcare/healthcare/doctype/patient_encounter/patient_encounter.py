# -*- coding: utf-8 -*-
# Copyright (c) 2015, ESS LLP and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.model.document import Document


class PatientEncounter(Document):
	def validate(self):
		self.set_title()
		self.validate_therapies()

	def on_submit(self):
		if self.therapies:
			create_therapy_plan(self)
		self.db_set("status", "Completed")

	def on_cancel(self):
		self.db_set("status", "Cancelled")

	def set_title(self):
		self.title = _("{0} with {1}").format(
			self.patient_name or self.patient, self.practitioner_name or self.practitioner
		)[:100]

	def validate_therapies(self):
		if not self.therapies:
			return

		for therapy in self.therapies:
			if not therapy.no_of_sessions or therapy.no_of_sessions <= 0:
				frappe.throw(
					_("Row #{0} (Therapies): Number of Sessions should be at least 1").format(therapy.idx)
				)

	@frappe.whitelist()
	def add_clinical_note(self, note, note_type=None):
		clinical_note_doc = frappe.new_doc("Clinical Note")
		clinical_note_doc.patient = self.patient
		clinical_note_doc.reference_doc = "Patient Encounter"
		clinical_note_doc.reference_name = self.name
		clinical_note_doc.note = note
		clinical_note_doc.clinical_note_type = note_type
		clinical_note_doc.practitioner = self.practitioner
		clinical_note_doc.insert()

	@frappe.whitelist()
	def edit_clinical_note(self, note, note_name):
		clinical_note_doc = frappe.get_doc("Clinical Note", note_name)
		clinical_note_doc.note = note
		clinical_note_doc.save()

	@frappe.whitelist()
	def delete_clinical_note(self, note_name):
		if frappe.db.exists("Clinical Note", note_name):
			frappe.delete_doc("Clinical Note", note_name)

	@frappe.whitelist()
	def get_clinical_notes(self, patient):
		return frappe.get_all(
			"Clinical Note",
			{
				"patient": patient,
			},
			["posting_date", "note", "name", "practitioner", "user", "clinical_note_type"],
		)


def create_therapy_plan(encounter):
	if len(encounter.therapies):
		doc = frappe.new_doc("Therapy Plan")
		doc.patient = encounter.patient
		doc.start_date = encounter.encounter_date
		for entry in encounter.therapies:
			doc.append(
				"therapy_plan_details",
				{"therapy_type": entry.therapy_type, "no_of_sessions": entry.no_of_sessions},
			)
		doc.save(ignore_permissions=True)
		if doc.get("name"):
			encounter.db_set("therapy_plan", doc.name)
			frappe.msgprint(
				_("Therapy Plan {0} created successfully.").format(frappe.bold(doc.name)), alert=True
			)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_medications_query(doctype, txt, searchfield, start, page_len, filters):
	medication_name = filters.get("medication")

	medication_child = frappe.qb.DocType("Medication Linked Item")
	medication = frappe.qb.DocType("Medication")
	item = frappe.qb.DocType("Item")
	query = (
		frappe.qb.select(medication_child.brand, medication_child.manufacturer, medication_child.item)
		.from_(medication_child)
		.left_join(medication)
		.on(medication.name == medication_child.parent)
		.left_join(item)
		.on(item.name == medication_child.item)
		.where(item.disabled == 0)
	)
	if medication_name:
		query = query.where(medication.name == medication_name)

	data = query.run(as_dict=True)
	data_list = []
	for d in data:
		display_list = []
		if d.get("item"):
			display_list.append(d.get("item"))
		if d.get("brand"):
			display_list.append(d.get("brand"))
		if d.get("manufacturer"):
			display_list.append(d.get("manufacturer"))
		default_warehouse = frappe.get_cached_value("Stock Settings", None, "default_warehouse")
		if default_warehouse:
			actual_qty = frappe.db.get_value(
				"Bin", {"warehouse": default_warehouse, "item_code": d.get("item")}, "actual_qty"
			)
			display_list.append("<br>Actual Qty : " + (str(actual_qty) if actual_qty else "0"))
		data_list.append(display_list)
	res = tuple(tuple(sub) for sub in data_list)
	return res


@frappe.whitelist()
def get_medications(medication):
	return frappe.get_all("Medication Linked Item", {"parent": medication}, ["item"])


@frappe.whitelist()
def cancel_request(doctype, request):
	request_doc = frappe.get_doc(doctype, request)
	request_doc.cancel()


@frappe.whitelist()
def get_encounter_details(doc):
	doc = json.loads(doc)
	if doc.get("__islocal") == 0:
		doc = frappe.get_doc(doc.doctype, doc.docname)
	medication_requests = []
	service_requests = []
	filters = {"patient": doc.get("patient"), "docstatus": 1}
	medication_requests = frappe.get_all("Medication Request", filters, ["*"])
	service_requests = frappe.get_all("Service Request", filters, ["*"])
	status_codes = frappe.db.get_all(
		"Code Value",
		filters={
			"code_system": ["in", ["Request Status", "Medication Request Status"]],
		},
		fields=["name", "code_value", "display"],
	)
	status_code_map = get_value_map(status_codes)

	for service_request in service_requests:
		if service_request.template_dt == "Lab Test Template":
			lab_test = frappe.db.get_value("Lab Test", {"service_request": service_request.name}, "name")
			if lab_test:
				subject = frappe.db.get_value(
					"Patient Medical Record", {"reference_name": lab_test}, "subject"
				)
				if subject:
					service_request["lab_details"] = subject
	clinical_notes = frappe.get_all(
		"Clinical Note", {"patient": doc.get("patient")}, ["posting_date", "note"]
	)

	return medication_requests, service_requests, clinical_notes, status_code_map


def get_value_map(status_codes):
	"""return a map, for example, {"name": "x", "code_value": "", "display": "1"} to {"x": "1"}"""
	status_code_map = {
		list(d.values())[0]: list(d.values())[2]  # display is preferred over code_value
		if list(d.values())[2]
		else list(d.values())[1]
		for d in status_codes
	}
	return dict(status_code_map)


@frappe.whitelist()
def create_patient_referral(encounter, references):
	if isinstance(references, str):
		references = json.loads(references)

	encounter_doc = frappe.get_doc("Patient Encounter", encounter)
	for ref in references:
		order = frappe.get_doc(
			{
				"doctype": "Service Request",
				"order_date": encounter_doc.get("encounter_date"),
				"order_time": encounter_doc.get("encounter_time"),
				"company": encounter_doc.get("company"),
				"status": "draft-Request Status",
				"source_doc": "Patient Encounter",
				"order_group": encounter,
				"patient": encounter_doc.get("patient"),
				"practitioner": encounter_doc.get("practitioner"),
				"template_dt": "Appointment Type",
				"template_dn": ref.get("appointment_type"),
				"quantity": 1,
				"order_description": ref.get("referral_note"),
				"referred_to_practitioner": ref.get("refer_to"),
			}
		)
		order.insert(ignore_permissions=True, ignore_mandatory=True)
		order.submit()
