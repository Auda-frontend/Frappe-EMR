# -*- coding: utf-8 -*-
"""Install Triage Visit doctype, print format, and desk links."""

import json
import os

import frappe
from frappe.modules.import_file import import_file_by_path


@frappe.whitelist()
def install_triage_visit():
	"""Sync Triage Visit + print format; add Healthcare workspace links."""
	_import_triage_visit_doctype()
	_import_triage_print_format()
	_ensure_workspace_links()
	frappe.db.commit()
	frappe.clear_cache(doctype="Triage Visit")
	return {"ok": True, "message": "Triage Visit installed"}


def _import_triage_visit_doctype():
	app_path = frappe.get_app_path("healthcare")
	path = os.path.join(app_path, "healthcare", "doctype", "triage_visit", "triage_visit.json")
	if not os.path.exists(path):
		frappe.throw(f"Triage Visit JSON not found: {path}")
	import_file_by_path(path, force=True, ignore_version=True)


def _import_triage_print_format():
	app_path = frappe.get_app_path("healthcare")
	path = os.path.join(app_path, "healthcare", "print_format", "triage_form", "triage_form.json")
	if os.path.exists(path):
		import_file_by_path(path, force=True, ignore_version=True)


def _ensure_workspace_links():
	"""Add Triage Visit to Healthcare workspace Consultation card."""
	ws_name = "Healthcare"
	if not frappe.db.exists("Workspace", ws_name):
		return

	ws = frappe.get_doc("Workspace", ws_name)
	links = ws.links or []

	if not any(l.link_to == "Triage Visit" for l in links if l.link_to):
		# Insert after Triage (Vital Signs) link
		insert_at = next(
			(i for i, l in enumerate(links) if getattr(l, "link_to", None) == "Vital Signs"),
			len(links),
		)
		ws.append(
			"links",
			{
				"label": "Triage Visit",
				"link_type": "DocType",
				"link_to": "Triage Visit",
				"type": "Link",
				"hidden": 0,
				"is_query_report": 0,
				"onboard": 0,
			},
		)
		# Move new link next to Vital Signs
		new_link = ws.links[-1]
		ws.links.pop()
		ws.links.insert(insert_at + 1, new_link)

	# Rename Vital Signs desk label for clarity
	for link in ws.links:
		if link.link_to == "Vital Signs" and link.label == "Triage":
			link.label = "Triage (Vital Signs)"

	ws.save(ignore_permissions=True)

	_update_desk_page_healthcare()


def _update_desk_page_healthcare():
	path = os.path.join(
		frappe.get_app_path("healthcare"),
		"healthcare",
		"desk_page",
		"healthcare",
		"healthcare.json",
	)
	if not os.path.exists(path):
		return

	with open(path) as f:
		data = json.load(f)

	links = json.loads(data.get("links") or "[]")
	if not any(l.get("name") == "Triage Visit" for l in links):
		links.insert(
			5,
			{
				"type": "doctype",
				"name": "Triage Visit",
				"label": "Triage Visit",
			},
		)
		data["links"] = json.dumps(links)
		with open(path, "w") as f:
			json.dump(data, f, indent=1)
			f.write("\n")
