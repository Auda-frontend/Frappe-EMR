"""Healthcare workspace links for the queue flow. Safe to run on every migrate."""
import frappe

# (label shown on the workspace, DocType it opens)
QUEUE_LINKS = (
	("Queue Management", "Queue"),
	("Internal Orientation", "Internal Orientation"),
)


def ensure_queue_workspace_links():
	"""Add Queue and Internal Orientation to the Consultation card of the Healthcare workspace."""
	if not frappe.db.exists("Workspace", "Healthcare"):
		return

	ws = frappe.get_doc("Workspace", "Healthcare")
	existing = {row.link_to for row in ws.links if row.link_to}
	missing = [(label, doctype) for label, doctype in QUEUE_LINKS if doctype not in existing]
	if not missing:
		return

	# Place the new links right after Patient Encounter, inside the Consultation card.
	anchor = next((i for i, row in enumerate(ws.links) if row.link_to == "Patient Encounter"), None)
	if anchor is None:
		# The card layout is not what we expect, so leave the workspace untouched.
		return

	for label, doctype in missing:
		ws.append(
			"links",
			{
				"label": label,
				"link_type": "DocType",
				"link_to": doctype,
				"type": "Link",
				"hidden": 0,
				"is_query_report": 0,
				"onboard": 0,
			},
		)
	new_rows = ws.links[-len(missing):]
	rows = list(ws.links[: len(ws.links) - len(missing)])
	rows[anchor + 1 : anchor + 1] = new_rows
	ws.links = rows
	# Rows are ordered by idx, so renumber them to match the new order.
	for position, row in enumerate(ws.links, start=1):
		row.idx = position

	ws.save(ignore_permissions=True)
