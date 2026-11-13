import frappe
from frappe import _
from frappe.model.document import Document

from healthcare.healthcare.queue_api import cancel_queue_entry, complete_open_entries, create_queue_entry


class InternalOrientation(Document):
	def validate(self):
		if self.orientation_from == self.orientation_to:
			frappe.throw(_("Orientation From and Orientation To must be different."), title=_("Orientation"))
		for fieldname in ("orientation_from", "orientation_to"):
			unit = self.get(fieldname)
			if unit and frappe.db.get_value("Healthcare Service Unit", unit, "is_group"):
				frappe.throw(
					_("{0} is a group. Choose a service unit where patients are seen.").format(unit),
					title=_("Orientation"),
				)

	def on_submit(self):
		# The patient leaves the unit they came from and joins the queue of the unit they go to.
		complete_open_entries(self.patient, self.orientation_from, self.date)
		entry = create_queue_entry(
			patient=self.patient,
			service_unit=self.orientation_to,
			queue_date=self.date,
			priority=self.priority,
			internal_orientation=self.name,
		)
		self.db_set("queue", entry.name)

	def on_cancel(self):
		cancel_queue_entry(self.queue)
