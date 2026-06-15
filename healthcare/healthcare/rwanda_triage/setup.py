# -*- coding: utf-8 -*-
"""Install Rwanda TEWS triage assessment system (aligned with existing OPD on Vital Signs)."""

import json
import os

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.modules.import_file import import_file_by_path


def install_rwanda_triage_system():
	"""Idempotent: doctypes, custom fields, desk links. Keeps Triage Visit for legacy records."""
	from .doctype_builder import generate_all_doctype_json

	app_path = frappe.get_app_path("healthcare")
	generate_all_doctype_json(app_path)
	_import_all_triage_doctypes(app_path)
	create_custom_fields(get_rwanda_triage_custom_fields(), update=True)
	_ensure_workspace_links()
	frappe.db.commit()
	frappe.clear_cache()


def _import_all_triage_doctypes(app_path):
	folders = [
		"triage_assessment",
		"adult_triage_form",
		"child_triage_form",
		"infant_triage_form",
		"maternity_triage_form",
	]
	for folder in folders:
		path = os.path.join(app_path, "healthcare", "doctype", folder, f"{folder}.json")
		if os.path.exists(path):
			import_file_by_path(path, force=True, ignore_version=True)


def get_rwanda_triage_custom_fields():
	"""Patient + Vital Signs extensions — uses rw_ prefix (existing app convention)."""
	return {
		"Patient": [
			{
				"fieldname": "rw_is_maternity",
				"fieldtype": "Check",
				"label": "Is Maternity Patient",
				"insert_after": "sex",
				"description": "Tick at registration for pregnant patients — routes to Maternity triage form.",
			},
			{
				"fieldname": "rw_triage_color",
				"fieldtype": "Select",
				"label": "Triage Color",
				"options": "RED\nORANGE\nYELLOW\nGREEN",
				"read_only": 1,
				"insert_after": "rw_is_maternity",
				"in_list_view": 1,
			},
			{
				"fieldname": "rw_last_triage_date",
				"fieldtype": "Date",
				"label": "Last Triage Date",
				"read_only": 1,
				"insert_after": "rw_triage_color",
			},
			{
				"fieldname": "rw_active_triage_assessment",
				"fieldtype": "Link",
				"label": "Active Triage Assessment",
				"options": "Triage Assessment",
				"read_only": 1,
				"insert_after": "rw_last_triage_date",
			},
		],
		"Vital Signs": [
			{
				"fieldname": "rw_triage_color",
				"fieldtype": "Select",
				"label": "TEWS Triage Color",
				"options": "RED\nORANGE\nYELLOW\nGREEN",
				"read_only": 1,
				"insert_after": "rw_triage_category",
				"in_list_view": 1,
			},
			{
				"fieldname": "rw_tews_score",
				"fieldtype": "Int",
				"label": "TEWS Score",
				"read_only": 1,
				"insert_after": "rw_triage_color",
			},
			{
				"fieldname": "rw_form_type",
				"fieldtype": "Select",
				"label": "Form Type Used",
				"options": "Adult\nChild\nInfant\nMaternity",
				"read_only": 1,
				"insert_after": "rw_tews_score",
			},
			{
				"fieldname": "rw_triage_assessment",
				"fieldtype": "Link",
				"label": "Triage Assessment",
				"options": "Triage Assessment",
				"read_only": 1,
				"insert_after": "rw_form_type",
			},
		],
	}


def _ensure_workspace_links():
	ws_name = "Healthcare"
	if not frappe.db.exists("Workspace", ws_name):
		return
	ws = frappe.get_doc("Workspace", ws_name)
	if not any(l.link_to == "Triage Assessment" for l in (ws.links or [])):
		ws.append(
			"links",
			{
				"label": "Triage Assessment",
				"link_type": "DocType",
				"link_to": "Triage Assessment",
				"type": "Link",
				"hidden": 0,
				"onboard": 1,
			},
		)
		ws.save(ignore_permissions=True)


@frappe.whitelist()
def install_rwanda_triage_system_api():
	frappe.only_for(("System Manager", "Healthcare Administrator"))
	install_rwanda_triage_system()
	return {"ok": True, "message": "Rwanda triage system installed. Hard-refresh desk."}
