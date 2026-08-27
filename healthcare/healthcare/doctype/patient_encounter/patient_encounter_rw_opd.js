// Rwanda consultation form (Patient Encounter)

const RW_VISIT_STATUS_COLORS = {
	Waiting: "blue",
	"In Consultation": "yellow",
	Completed: "green",
	Cancelled: "red",
};

const RW_CLINICAL_FIELDS = [
	"rw_history_present_illness",
	"rw_physical_examination_notes",
	"rw_clinical_impression",
	"symptoms",
	"diagnosis",
	"drug_prescription",
	"lab_test_prescription",
	"procedure_prescription",
	"rw_visit_outcome",
	"rw_discharge_summary",
	"rw_patient_instructions",
];

frappe.ui.form.on("Patient Encounter", {
	refresh(frm) {
		rw_consultation_setup_desk(frm);
	},

	onload(frm) {
		if (frm.doc.patient) {
			rw_consultation_pull_history(frm);
			rw_consultation_prefill_hpi(frm);
		}
		rw_consultation_load_triage_summary(frm);
	},
});

function rw_consultation_setup_desk(frm) {
	if (!frm.fields_dict.rw_opd_visit_status) {
		return;
	}

	const status = frm.doc.rw_opd_visit_status || "Waiting";
	const in_consultation = status === "In Consultation";
	const is_locked = status === "Waiting" || status === "Completed" || frm.doc.docstatus === 1;

	if (RW_VISIT_STATUS_COLORS[status]) {
		frm.dashboard.add_indicator(__("Visit: {0}", [status]), RW_VISIT_STATUS_COLORS[status]);
	}
	if (frm.doc.rw_triage_category === "Emergency") {
		frm.dashboard.add_indicator(__("Critical patient"), "red");
	}

	const intro = [];
	if (frm.doc.rw_oriented_service) intro.push(__("Service: {0}", [frm.doc.rw_oriented_service]));
	if (frm.doc.rw_oriented_department) intro.push(__("Dept: {0}", [frm.doc.rw_oriented_department]));
	if (frm.doc.rw_queue_number) intro.push(__("Queue #{0}", [frm.doc.rw_queue_number]));
	if (frm.doc.rw_patient_upid) intro.push(__("UPID: {0}", [frm.doc.rw_patient_upid]));
	if (intro.length) frm.set_intro(intro.join(" · "), "blue");

	if (status === "Waiting") {
		frm.set_intro(
			__(
				"Patient is waiting in the department queue. Click <b>Proceed to attend</b> before entering clinical notes."
			),
			"orange"
		);
	}

	rw_consultation_toggle_clinical_fields(frm, is_locked && !in_consultation);

	if (frm.is_new() || frm.doc.docstatus === 2) {
		return;
	}

	const group = __("Consultation");

	if (frm.doc.rw_triage) {
		frm.add_custom_button(__("View triage"), () => frappe.set_route("Form", "Vital Signs", frm.doc.rw_triage), group);
	}

	if (status === "Waiting") {
		frm.add_custom_button(__("Proceed to attend"), () => rw_consultation_start(frm), group);
	}

	if (in_consultation && frm.doc.docstatus === 0) {
		frm.add_custom_button(
			__("Submit consultation"),
			() => {
				if (!frm.doc.diagnosis || !frm.doc.diagnosis.length) {
					frappe.msgprint({
						title: __("Diagnosis required"),
						indicator: "red",
						message: __("Add at least one diagnosis before submitting."),
					});
					frm.scroll_to_field("diagnosis");
					return;
				}
				frm.save("Submit");
			},
			group
		);
	}

	if (in_consultation && frm.doc.docstatus === 1 && status !== "Completed") {
		frm.add_custom_button(__("Complete visit"), () => rw_consultation_complete(frm), group);
	}

	frm.add_custom_button(__("Department queue"), () => {
		frappe.route_options = {
			medical_department: frm.doc.rw_oriented_department || frm.doc.medical_department,
			oriented_service: frm.doc.rw_oriented_service,
		};
		frappe.set_route("department-queue");
	}, __("Workflow"));
}

function rw_consultation_toggle_clinical_fields(frm, read_only) {
	RW_CLINICAL_FIELDS.forEach((fieldname) => {
		if (frm.fields_dict[fieldname]) {
			frm.set_df_property(fieldname, "read_only", read_only ? 1 : 0);
		}
	});
}

function rw_consultation_start(frm) {
	frappe.call({
		method: "healthcare.healthcare.rwanda_opd.start_consultation",
		args: { encounter: frm.doc.name },
		freeze: true,
		callback() {
			frm.reload_doc();
		},
	});
}

function rw_consultation_complete(frm) {
	if (!frm.doc.rw_visit_outcome) {
		frappe.msgprint({
			title: __("Visit outcome required"),
			indicator: "orange",
			message: __("Select a visit outcome before completing the visit."),
		});
		frm.scroll_to_field("rw_visit_outcome");
		return;
	}
	frappe.call({
		method: "healthcare.healthcare.rwanda_opd.complete_consultation",
		args: { encounter: frm.doc.name },
		freeze: true,
		callback() {
			frm.reload_doc();
			frappe.show_alert({ message: __("Visit completed"), indicator: "green" });
		},
	});
}

function rw_consultation_pull_history(frm) {
	if (!frm.doc.patient) return;
	frappe.db.get_doc("Patient", frm.doc.patient).then((patient) => {
		const map = {
			rw_allergies: "allergies",
			rw_current_medication: "medication",
			rw_past_medical_history: "medical_history",
			rw_surgical_history: "surgical_history",
			rw_tobacco_past_use: "tobacco_past_use",
			rw_tobacco_current_use: "tobacco_current_use",
			rw_alcohol_past_use: "alcohol_past_use",
			rw_alcohol_current_use: "alcohol_current_use",
			rw_other_risk_factors: "other_risk_factors",
		};
		Object.keys(map).forEach((enc_field) => {
			if (!frm.doc[enc_field] && patient[map[enc_field]]) {
				frm.set_value(enc_field, patient[map[enc_field]]);
			}
		});
	});
}

function rw_consultation_prefill_hpi(frm) {
	if (frm.doc.rw_history_present_illness || !frm.doc.rw_chief_complaint) return;
	frm.set_value("rw_history_present_illness", frm.doc.rw_chief_complaint);
}

function rw_consultation_load_triage_summary(frm) {
	if (!frm.fields_dict.rw_triage_vitals_html || !frm.doc.name || frm.is_new()) return;
	frappe.call({
		method: "healthcare.healthcare.rwanda_consultation.get_consultation_triage_summary",
		args: { encounter: frm.doc.name },
		callback(r) {
			if (r.message && r.message.html) {
				frm.fields_dict.rw_triage_vitals_html.$wrapper.html(r.message.html);
			}
		},
	});
}
