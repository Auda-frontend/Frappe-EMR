def execute():
	"""Re-sync Triage Visit with Adult/Child/Maternity form sections and desk links."""
	from healthcare.healthcare.triage_visit_setup import install_triage_visit

	install_triage_visit()
