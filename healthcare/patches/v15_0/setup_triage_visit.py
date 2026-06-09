def execute():
	"""Ensure Triage Visit doctype, print format, and workspace links are installed."""
	from healthcare.healthcare.triage_visit_setup import install_triage_visit

	install_triage_visit()
