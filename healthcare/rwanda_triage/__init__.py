"""Compatibility shim so `healthcare.rwanda_triage` resolves (bench execute / patches)."""

from healthcare.healthcare.rwanda_triage.setup import (  # noqa: F401
	get_rwanda_triage_custom_fields,
	install_rwanda_triage_system,
	install_rwanda_triage_system_api,
)
from healthcare.healthcare.rwanda_triage.scoring import (  # noqa: F401
	FORM_TYPE_DOCTYPE,
	map_triage_color_to_opd_priority,
	detect_form_type,
)
