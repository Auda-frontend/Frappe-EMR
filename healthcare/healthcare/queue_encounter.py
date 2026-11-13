"""What the Patient Encounter needs for the queue: the link to its Queue entry, and permission to
finish a visit after the consultation has been submitted."""
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# "Complete visit" changes these fields on an encounter that is already submitted. Frappe only allows
# that for fields flagged "Allow on Submit", and otherwise stops with "Not allowed to change ...
# after submission".
FIELDS_CHANGED_AFTER_SUBMIT = (
	"consultation_status",
	"rw_opd_visit_status",
	"rw_visit_completed_at",
)


def ensure_queue_encounter_field():
	"""Set up the queue link and the after-submit rules. Safe to run on every migrate."""
	create_custom_fields(
		{
			"Patient Encounter": [
				{
					"fieldname": "rw_queue",
					"fieldtype": "Link",
					"label": "Queue entry",
					"options": "Queue",
					"read_only": 1,
					"no_copy": 1,
					"hidden": 1,
					"insert_after": "rw_queue_number",
				}
			]
		},
		update=True,
	)
	allow_visit_completion_after_submit()


def allow_visit_completion_after_submit():
	from healthcare.healthcare.rwanda_opd import set_encounter_field_property

	for fieldname in FIELDS_CHANGED_AFTER_SUBMIT:
		set_encounter_field_property(fieldname, "allow_on_submit", "1", property_type="Check")
