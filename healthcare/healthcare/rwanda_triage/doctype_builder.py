# -*- coding: utf-8 -*-
"""Build DocType JSON fixtures for Rwanda triage forms."""

from __future__ import annotations

import json
import os

from .form_definitions import (
    FORM_META,
    TRIAGE_ASSESSMENT_FIELDS,
    build_form_fields,
)


def _permissions(roles):
	return [{"role": role, "read": 1, "write": 1, "create": 1, "delete": 1 if role == "Nursing User" else 0, "submit": 1 if role == "Physician" else 0, "print": 1, "email": 1, "export": 1, "report": 1, "share": 1} for role in roles]


def _build_doctype(name, fields, naming_series, is_submittable=True):
	field_order = [f["fieldname"] for f in fields]
	if naming_series:
		fields = [{"fieldname": "naming_series", "fieldtype": "Select", "label": "Series", "options": naming_series, "reqd": 1}] + fields
		field_order = ["naming_series"] + field_order
	return {
		"actions": [],
		"autoname": "naming_series:" if naming_series else "",
		"creation": "2026-06-09 12:00:00.000000",
		"doctype": "DocType",
		"engine": "InnoDB",
		"field_order": field_order,
		"fields": fields if not naming_series else fields,
		"is_submittable": 1 if is_submittable else 0,
		"links": [],
		"modified": "2026-06-09 12:00:00.000000",
		"modified_by": "Administrator",
		"module": "Healthcare",
		"name": name,
		"naming_rule": "By \"Naming Series\" field" if naming_series else "",
		"owner": "Administrator",
		"permissions": _permissions(["Nursing User", "Physician", "System Manager"]),
		"sort_field": "modified",
		"sort_order": "DESC",
		"track_changes": 1,
	}


def write_doctype_json(app_path, folder, doc):
	path = os.path.join(app_path, "healthcare", "doctype", folder, f"{folder}.json")
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w") as f:
		json.dump(doc, f, indent=1)
		f.write("\n")
	return path


def generate_all_doctype_json(app_path=None):
	if not app_path:
		import frappe
		app_path = frappe.get_app_path("healthcare")

	written = []
	# Triage Assessment
	ta_fields = list(TRIAGE_ASSESSMENT_FIELDS)
	ta_doc = _build_doctype("Triage Assessment", ta_fields, "TRIAGE-.YYYY.-")
	written.append(write_doctype_json(app_path, "triage_assessment", ta_doc))

	for name, meta in FORM_META.items():
		fields = build_form_fields(meta["form_type"])
		doc = _build_doctype(name, fields, meta["naming_series"])
		written.append(write_doctype_json(app_path, meta["prefix"], doc))

	return written
