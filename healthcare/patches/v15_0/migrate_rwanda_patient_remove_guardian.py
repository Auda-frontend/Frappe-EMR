def execute():
	"""Remove guardian section; auto-ID for father/mother when identification type is UNKNOWN."""
	from healthcare.healthcare.rwanda_registration import install_rwanda_patient_registration

	install_rwanda_patient_registration()
