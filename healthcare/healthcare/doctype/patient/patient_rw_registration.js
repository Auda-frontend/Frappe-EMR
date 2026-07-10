// Rwanda patient registration desk UX (Phase A)

const RW_HIDDEN_FORM_TABS = [
	"dashboard_tab",
	"address_and_contact_tab",
	"medical_history_tab",
];

const RW_MEDICAL_HISTORY_FIELDS = [
	"medical_history_tab",
	"allergy_medical_and_surgical_history",
	"allergies",
	"medication",
	"column_break_20",
	"medical_history",
	"surgical_history",
	"risk_factors",
	"tobacco_past_use",
	"tobacco_current_use",
	"alcohol_past_use",
	"alcohol_current_use",
	"column_break_32",
	"surrounding_factors",
	"other_risk_factors",
];

const RW_UNKNOWN_ID_PREFIX = "RW-UNK-";
const RW_RELATIVE_ROLES = ["father", "mother"];
const RW_RELATIVE_UNKNOWN_TAGS = { father: "F", mother: "M" };
const RW_DEFAULT_OPEN_SECTION = "rw_sb_identification";
const RW_DEFAULT_COLLAPSED_SECTIONS = [
	"rw_sb_insurance",
	"rw_sb_social",
	"rw_sb_father",
	"rw_sb_mother",
];

const RW_INSURANCE_DETAIL_FIELDS = [
	"rw_col_insurance",
	"custom_insurance_provider",
	"rw_insurance_member_number",
	"rw_is_main_insurer",
	"rw_main_insured_name",
	"rw_main_insured_insurance_number",
];

const RW_STRAY_COLUMN_BREAKS = ["column_break_14", "column_break_25"];

frappe.ui.form.on("Patient", {
	refresh(frm) {
		rw_patient_hide_extra_tabs(frm);
		rw_patient_hide_stray_column_breaks(frm);
		rw_patient_setup_insurance_visibility(frm);
		rw_patient_setup_manual_flags(frm);
		rw_patient_setup_identification_visibility(frm);
		RW_RELATIVE_ROLES.forEach((role) => rw_patient_setup_relative_identification(frm, role));
		rw_patient_setup_section_defaults(frm);
		rw_patient_setup_registration_desk(frm);
	},

	rw_go_manual(frm) {
		rw_patient_setup_manual_flags(frm);
	},

	rw_set_dob_manually(frm) {
		rw_patient_setup_manual_flags(frm);
	},

	rw_identification_type(frm) {
		rw_patient_handle_identification_type_change(frm);
	},

	rw_patient_id_set(frm) {
		rw_patient_setup_identification_visibility(frm);
	},

	rw_patient_insured(frm) {
		rw_patient_setup_insurance_visibility(frm);
		if (frm.doc.rw_patient_insured === "No") {
			[
				"custom_insurance_provider",
				"rw_insurance_member_number",
				"rw_main_insured_name",
				"rw_main_insured_insurance_number",
			].forEach((f) => frm.set_value(f, null));
			frm.set_value("rw_mark_special_case", 0);
			frm.set_value("rw_is_main_insurer", 1);
		}
	},

	rw_is_main_insurer(frm) {
		rw_patient_toggle_main_insured_fields(frm);
	},

	rw_national_id(frm) {
		if (frm.doc.rw_national_id && frm.is_new()) {
			rw_patient_check_duplicate_nin(frm);
		}
	},

	rw_father_id_type(frm) {
		rw_patient_handle_relative_id_type_change(frm, "father");
	},

	rw_mother_id_type(frm) {
		rw_patient_handle_relative_id_type_change(frm, "mother");
	},
});

function rw_patient_hide_stray_column_breaks(frm) {
	// Stock Marley column breaks between demographics fields — keep hidden so Identification stays 2-col.
	RW_STRAY_COLUMN_BREAKS.forEach((fieldname) => {
		if (frm.fields_dict[fieldname]) {
			frm.set_df_property(fieldname, "hidden", 1);
		}
	});
}

function rw_patient_setup_section_defaults(frm) {
	if (!frm.layout || !frm.layout.sections) {
		return;
	}

	// Clear saved collapse state so Identification opens by default on each visit.
	[
		"rw-patient-identification-section",
		"rw-patient-insurance-section",
		"rw-patient-social-section",
		"rw-patient-father-section",
		"rw-patient-mother-section",
	].forEach((css_class) => localStorage.removeItem(`${css_class}-closed`));

	frm.layout.sections.forEach((section) => {
		if (!section.df || !section.df.collapsible) {
			return;
		}
		if (section.df.fieldname === RW_DEFAULT_OPEN_SECTION) {
			section.collapse(false);
		} else if (RW_DEFAULT_COLLAPSED_SECTIONS.includes(section.df.fieldname)) {
			section.collapse(true);
		}
	});
}

function rw_patient_hide_extra_tabs(frm) {
	[...RW_HIDDEN_FORM_TABS, ...RW_MEDICAL_HISTORY_FIELDS].forEach((fieldname) => {
		if (frm.fields_dict[fieldname]) {
			frm.set_df_property(fieldname, "hidden", 1);
		}
	});
}

function rw_patient_is_system_unknown_id(value) {
	return !!(value && String(value).startsWith(RW_UNKNOWN_ID_PREFIX));
}

function rw_patient_is_system_relative_unknown_id(value, role) {
	const tag = RW_RELATIVE_UNKNOWN_TAGS[role];
	if (!tag || !value) {
		return false;
	}
	return String(value).startsWith(`${RW_UNKNOWN_ID_PREFIX}${tag}-`);
}

function rw_patient_handle_relative_id_type_change(frm, role) {
	const id_type_field = `rw_${role}_id_type`;
	const id_number_field = `rw_${role}_id_number`;
	const id_type = frm.doc[id_type_field] || "UNKNOWN";

	if (id_type === "UNKNOWN") {
		if (!frm.doc[id_number_field] || rw_patient_is_system_relative_unknown_id(frm.doc[id_number_field], role)) {
			rw_patient_generate_relative_unknown_id(frm, role);
		}
	} else if (rw_patient_is_system_relative_unknown_id(frm.doc[id_number_field], role)) {
		frm.set_value(id_number_field, null);
	}

	rw_patient_setup_relative_identification(frm, role);
}

function rw_patient_generate_relative_unknown_id(frm, role) {
	frappe.call({
		method: "healthcare.healthcare.rwanda_registration.generate_rw_relative_unknown_identification_number",
		args: { role },
		callback(r) {
			if (r.message) {
				frm.set_value(`rw_${role}_id_number`, r.message);
			}
		},
	});
}

function rw_patient_setup_relative_identification(frm, role) {
	const id_type_field = `rw_${role}_id_type`;
	const id_number_field = `rw_${role}_id_number`;
	const id_type = frm.doc[id_type_field] || "UNKNOWN";
	const is_unknown = id_type === "UNKNOWN";

	if (frm.fields_dict[id_number_field]) {
		frm.set_df_property(
			id_number_field,
			"label",
			is_unknown ? __("Identification Number (system generated)") : __("Identification Number")
		);
		frm.set_df_property(id_number_field, "read_only", is_unknown);
	}

	if (is_unknown && !frm.doc[id_number_field]) {
		rw_patient_generate_relative_unknown_id(frm, role);
	}
}

function rw_patient_handle_identification_type_change(frm) {
	const id_type = frm.doc.rw_identification_type || "UNKNOWN";

	if (id_type === "UNKNOWN") {
		if (!frm.doc.rw_national_id || rw_patient_is_system_unknown_id(frm.doc.rw_national_id)) {
			rw_patient_generate_unknown_id(frm);
		}
	} else if (rw_patient_is_system_unknown_id(frm.doc.rw_national_id)) {
		frm.set_value("rw_national_id", null);
	}

	rw_patient_setup_identification_visibility(frm);
}

function rw_patient_generate_unknown_id(frm) {
	frappe.call({
		method: "healthcare.healthcare.rwanda_registration.generate_rw_unknown_identification_number",
		callback(r) {
			if (r.message) {
				frm.set_value("rw_national_id", r.message);
			}
		},
	});
}

function rw_patient_setup_registration_desk(frm) {
	if (!frm.fields_dict.rw_reg_search_help) {
		return;
	}

	if (frm.is_new()) {
		frm.set_intro(
			__(
				"Search for an existing patient first (UPID, full name, NIN, or phone) to avoid duplicates."
			),
			"blue"
		);

		frm.add_custom_button(__("Find Existing Patient"), () => rw_patient_open_search_dialog(frm), __("Registration"));

		if (frappe.model.can_create("Patient")) {
			frm.add_custom_button(__("Generate Temporary UPID"), () => rw_patient_generate_temp_upid(frm), __("Registration"));
		}
	} else {
		frm.set_intro();
		rw_patient_workflow_buttons(frm);
	}

	if (frm.doc.rw_patient_insured === "Yes" && !frm.is_new()) {
		frm.add_custom_button(__("Check Eligibility"), () => rw_patient_check_eligibility(frm), __("Registration"));
	}
}

function rw_patient_workflow_buttons(frm) {
	const group = __("Workflow");
	frm.add_custom_button(__("Record triage"), () => {
		frappe.route_options = { patient: frm.doc.name };
		frappe.new_doc("Triage Assessment");
	}, group);
	frm.add_custom_button(__("Patient orientation"), () => frappe.set_route("patient-orientation"), group);
	frm.add_custom_button(__("Department queue"), () => frappe.set_route("department-queue"), group);
}

function rw_patient_setup_insurance_visibility(frm) {
	const insured = frm.doc.rw_patient_insured === "Yes";
	RW_INSURANCE_DETAIL_FIELDS.forEach((fieldname) => {
		if (frm.fields_dict[fieldname]) {
			frm.toggle_display(fieldname, insured);
		}
	});
	rw_patient_toggle_main_insured_fields(frm);
}

function rw_patient_setup_manual_flags(frm) {
	const go_manual = !!frm.doc.rw_go_manual;
	const set_dob = !!frm.doc.rw_set_dob_manually;

	if (frm.fields_dict.rw_upid) {
		frm.set_df_property("rw_upid", "read_only", !go_manual && !frm.doc.rw_upid_is_temporary);
	}
	["rw_upid_is_temporary", "rw_upid_source"].forEach((fieldname) => {
		if (frm.fields_dict[fieldname]) {
			frm.toggle_display(fieldname, go_manual || frm.doc.rw_upid_is_temporary);
		}
	});
	if (frm.fields_dict.dob) {
		frm.set_df_property("dob", "read_only", !set_dob);
	}
}

function rw_patient_setup_identification_visibility(frm) {
	const id_type = frm.doc.rw_identification_type || "UNKNOWN";
	const is_unknown = id_type === "UNKNOWN";
	const show_nid_app = id_type === "NID_APPLICATION_NUMBER";
	const show_upid_field = id_type === "UPID" || !!frm.doc.rw_go_manual || !!frm.doc.rw_upid_is_temporary;
	const show_id_number = ["NID", "PASSPORT", "REFUGEE_ID", "UNKNOWN"].includes(id_type);

	frm.toggle_display("rw_nid_application_number", show_nid_app);
	frm.toggle_display("rw_upid", show_upid_field);
	frm.toggle_display("rw_national_id", show_id_number);

	if (frm.fields_dict.rw_national_id) {
		const labels = {
			NID: __("Identification Number (NID/NIN)"),
			PASSPORT: __("Identification Number (Passport)"),
			REFUGEE_ID: __("Identification Number (Refugee ID)"),
			UNKNOWN: __("Identification Number (system generated)"),
		};
		frm.set_df_property(
			"rw_national_id",
			"label",
			labels[id_type] || labels.UNKNOWN
		);
		frm.set_df_property("rw_national_id", "read_only", is_unknown);
	}

	if (frm.is_new() && is_unknown && !frm.doc.rw_national_id) {
		rw_patient_generate_unknown_id(frm);
	}

	if (frm.doc.rw_patient_id_set) {
		if (frm.fields_dict.rw_national_id) {
			frm.set_df_property("rw_national_id", "reqd", show_id_number);
		}
		if (frm.fields_dict.rw_upid) {
			frm.set_df_property("rw_upid", "reqd", show_upid_field && id_type === "UPID");
		}
		if (frm.fields_dict.rw_nid_application_number) {
			frm.set_df_property("rw_nid_application_number", "reqd", show_nid_app);
		}
	} else {
		["rw_national_id", "rw_upid", "rw_nid_application_number"].forEach((fieldname) => {
			if (frm.fields_dict[fieldname]) {
				frm.set_df_property(fieldname, "reqd", 0);
			}
		});
	}
}

function rw_patient_toggle_main_insured_fields(frm) {
	const show_main = frm.doc.rw_patient_insured === "Yes" && !frm.doc.rw_is_main_insurer;
	frm.toggle_display("rw_main_insured_name", show_main);
	frm.toggle_display("rw_main_insured_insurance_number", show_main);
	if (frm.doc.rw_is_main_insurer) {
		frm.set_value("rw_main_insured_name", null);
		frm.set_value("rw_main_insured_insurance_number", null);
	}
}

function rw_patient_open_search_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __("Find Existing Patient"),
		fields: [
			{
				fieldtype: "Small Text",
				fieldname: "search_text",
				label: __("Name or partial ID"),
				description: __("Full name, first name, last name, UID, NIN, or UPID"),
			},
			{ fieldtype: "Column Break" },
			{ fieldtype: "Data", fieldname: "national_id", label: __("National ID (NIN)") },
			{ fieldtype: "Data", fieldname: "upid", label: __("UPID") },
			{ fieldtype: "Data", fieldname: "phone", label: __("Phone") },
			{ fieldtype: "Data", fieldname: "insurance_member", label: __("Insurance member number") },
		],
		primary_action_label: __("Search"),
		primary_action(values) {
			if (!values.search_text && !values.national_id && !values.upid && !values.phone && !values.insurance_member) {
				frappe.msgprint(__("Enter at least one search criterion."));
				return;
			}
			frappe.call({
				method: "healthcare.healthcare.rwanda_registration.search_patients_rw",
				args: {
					search_text: values.search_text,
					national_id: values.national_id,
					upid: values.upid,
					phone: values.phone,
					insurance_member: values.insurance_member,
					limit_page_length: 20,
				},
				freeze: true,
				callback(r) {
					rw_patient_show_search_results(frm, d, r.message || []);
				},
			});
		},
	});
	d.show();
}

function rw_patient_show_search_results(frm, dialog, rows) {
	if (!rows.length) {
		frappe.msgprint(__("No matching patients found. You may continue with new registration."));
		return;
	}

	const html = `
		<div class="rw-patient-search-results" style="max-height:320px;overflow:auto;">
			<table class="table table-bordered table-sm">
				<thead>
					<tr>
						<th>${__("Name")}</th>
						<th>${__("NIN")}</th>
						<th>${__("UPID")}</th>
						<th>${__("Phone")}</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					${rows
						.map(
							(row) => `
						<tr>
							<td>${frappe.utils.escape_html(row.patient_name || row.name)}</td>
							<td>${frappe.utils.escape_html(row.rw_national_id || "")}</td>
							<td>${frappe.utils.escape_html(row.rw_upid || "")}</td>
							<td>${frappe.utils.escape_html(row.mobile || row.phone || "")}</td>
							<td><button class="btn btn-xs btn-primary rw-open-patient" data-name="${frappe.utils.escape_html(
								row.name
							)}">${__("Open")}</button></td>
						</tr>`
						)
						.join("")}
				</tbody>
			</table>
		</div>`;

	const result_dialog = new frappe.ui.Dialog({
		title: __("Search Results ({0})", [rows.length]),
		fields: [{ fieldtype: "HTML", fieldname: "results_html" }],
		primary_action_label: __("Continue New Registration"),
		primary_action() {
			result_dialog.hide();
		},
	});

	result_dialog.fields_dict.results_html.$wrapper.html(html);
	result_dialog.fields_dict.results_html.$wrapper.find(".rw-open-patient").on("click", function () {
		const name = $(this).data("name");
		result_dialog.hide();
		dialog.hide();
		frappe.set_route("Form", "Patient", name);
	});
	result_dialog.show();
}

function rw_patient_check_duplicate_nin(frm) {
	frappe.call({
		method: "healthcare.healthcare.rwanda_registration.search_patients_rw",
		args: { national_id: frm.doc.rw_national_id, limit_page_length: 1 },
		callback(r) {
			const rows = r.message || [];
			if (rows.length && rows[0].name !== frm.doc.name) {
				frappe.msgprint({
					title: __("Duplicate NIN"),
					indicator: "orange",
					message: __("National ID is already registered to patient {0}.", [
						`<a href="/app/patient/${rows[0].name}">${rows[0].patient_name || rows[0].name}</a>`,
					]),
				});
			}
		},
	});
}

function rw_patient_generate_temp_upid(frm) {
	frappe.call({
		method: "healthcare.healthcare.rwanda_registration.generate_rw_temp_upid",
		callback(r) {
			if (r.message) {
				frm.set_value("rw_upid", r.message);
				frm.set_value("rw_upid_is_temporary", 1);
				frm.set_value("rw_upid_source", "Local Temporary");
			}
		},
	});
}

function rw_patient_check_eligibility(frm) {
	if (!frm.doc.name) {
		frappe.msgprint(__("Save the patient before checking eligibility."));
		return;
	}
	if (!frm.doc.rw_insurance_member_number) {
		frappe.msgprint(__("Enter the insurance member / policy number first."));
		return;
	}
	frappe.call({
		method: "healthcare.healthcare.rwanda_registration.check_insurance_eligibility",
		args: { patient: frm.doc.name },
		freeze: true,
		callback(r) {
			if (r.message) {
				frm.reload_doc();
				frappe.show_alert({
					message: r.message.message || __("Eligibility check recorded."),
					indicator: r.message.valid ? "green" : "orange",
				});
			}
		},
	});
}
