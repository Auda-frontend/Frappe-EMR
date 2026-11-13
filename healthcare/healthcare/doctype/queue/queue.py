import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, today

from healthcare.healthcare.queue_api import get_open_entries, take_counter


class Queue(Document):
	def before_insert(self):
		# Entries come only from Internal Orientation, never from the Add button or an import.
		if not self.flags.from_orientation:
			frappe.throw(
				_("Queue entries are created by submitting an Internal Orientation."), title=_("Queue")
			)
		self.queue_date = getdate(self.queue_date or today())
		self.status = "Waiting"
		self.arrived_at = now_datetime()
		# Takes the counter lock, which also serialises the duplicate check in validate().
		self.counter = take_counter(self.service_unit, self.queue_date)

	def validate(self):
		if self.is_new():
			existing = get_open_entries(self.patient, self.service_unit, self.queue_date)
			if existing:
				frappe.throw(
					_("{0} is already in the queue at {1} (entry {2}).").format(
						self.patient_name or self.patient, self.service_unit, existing[0]
					),
					title=_("Queue"),
				)
