// Queue list: today's open entries, with a button on every open entry.
//
//   Waiting     -> "Proceed": calls queue_api.proceed (Waiting -> In Service, one user only) and opens
//                  the next screen for the service unit's type.
//   In Service  -> "Open": goes back to the screen that was opened for this entry.
//
// The service unit's TYPE is the routing key: "Consultation" units open a Patient Encounter and
// "Triage" units open a Triage Assessment.
const QUEUE_UNIT_ROUTES = {
	Consultation: {
		// Created on the server, once per queue entry and already linked to it. Opening an entry that
		// is already in service goes back to the same encounter.
		open: (entry) =>
			frappe
				.xcall("healthcare.healthcare.queue_api.get_or_create_encounter", { queue: entry.name })
				.then((encounter) => {
					frappe.set_route("Form", "Patient Encounter", encounter);
					return true;
				}),
	},
	Triage: {
		open: (entry, reopen) => {
			if (reopen) {
				// Nothing is linked to this entry, so a second click must not create another document.
				frappe.show_alert({ message: __("This patient is already in service."), indicator: "orange" });
			} else {
				frappe.new_doc("Triage Assessment", { patient: entry.patient });
			}
			return Promise.resolve(true);
		},
	},
};

const QUEUE_STATUS_COLORS = {
	Waiting: "blue",
	"In Service": "orange",
	Completed: "green",
	Cancelled: "red",
	"No Show": "grey",
};

// Opens the screen for a queue entry. Resolves to true when a screen was opened.
function open_queue_entry(entry, reopen) {
	return frappe.db
		.get_value("Healthcare Service Unit", entry.service_unit, "service_unit_type")
		.then((res) => {
			const unit_type = res.message && res.message.service_unit_type;
			const route = QUEUE_UNIT_ROUTES[unit_type];
			return route ? route.open(entry, reopen) : false;
		});
}

frappe.listview_settings["Queue"] = {
	add_fields: ["status", "priority", "patient", "patient_name", "service_unit", "counter"],
	hide_name_column: true,

	onload(listview) {
		// Queue entries are created by Internal Orientation only, so there is no Add button.
		if (listview.page.btn_primary) {
			listview.page.btn_primary.hide();
		}
	},

	filters: [
		["status", "in", ["Waiting", "In Service"]],
		["queue_date", "=", frappe.datetime.get_today()],
	],

	get_indicator(doc) {
		return [__(doc.status), QUEUE_STATUS_COLORS[doc.status] || "grey", "status,=," + doc.status];
	},

	button: {
		show(doc) {
			return doc.status === "Waiting" || doc.status === "In Service";
		},
		get_label(doc) {
			return doc && doc.status === "In Service" ? __("Open") : __("Proceed");
		},
		get_description(doc) {
			const name = doc.patient_name || doc.patient;
			return doc.status === "In Service" ? __("Open {0}", [name]) : __("Call {0}", [name]);
		},
		action(doc) {
			const entry = { name: doc.name, patient: doc.patient, service_unit: doc.service_unit };
			const done = (opened) => {
				if (!opened) {
					frappe.show_alert({
						message: __("{0} is now in service.", [doc.patient_name || doc.patient]),
						indicator: "green",
					});
					if (cur_list) {
						cur_list.refresh();
					}
				}
			};
			if (doc.status === "In Service") {
				open_queue_entry(entry, true).then(done);
				return;
			}
			frappe.call({
				method: "healthcare.healthcare.queue_api.proceed",
				args: { queue: doc.name },
				freeze: true,
				callback(r) {
					if (r.message) {
						open_queue_entry(
							{ name: doc.name, patient: r.message.patient, service_unit: r.message.service_unit },
							false
						).then(done);
					}
				},
			});
		},
	},
};
