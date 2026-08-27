// Copyright (c) 2016, ESS LLP and contributors
// For license information, please see license.txt
{% include 'healthcare/healthcare/doctype/patient_encounter/patient_encounter_rw_opd.js' %}

frappe.ui.form.on('Patient Encounter', {
	onload: function(frm) {
		if (frm.doc.patient) {
			prefill_consultation_history(frm);
			prefill_chief_complaints(frm);
		}
	},

	setup: function(frm) {
		frm.get_field('diagnosis').grid.editable_fields = [
			{fieldname: 'diagnosis', columns: 2},
			{fieldname: 'code', columns: 1},
			{fieldname: 'title', columns: 3},
			{fieldname: 'uri', columns: 3},
			{fieldname: 'case_status', columns: 1},
			{fieldname: 'diagnosis_type', columns: 2}
		];
		frm.get_field('drug_prescription').grid.editable_fields = [
			{fieldname: 'drug_presentation', columns: 3},
			{fieldname: 'per_dose_amount', columns: 2},
			{fieldname: 'unit', columns: 1},
			{fieldname: 'frequency', columns: 2},
			{fieldname: 'duration', columns: 1},
			{fieldname: 'quantity_prescribed', columns: 1},
			{fieldname: 'patient_instructions', columns: 2}
		];
		frm.get_field('lab_test_prescription').grid.editable_fields = [
			{fieldname: 'lab_test_code', columns: 3},
			{fieldname: 'lab_test_name', columns: 3},
			{fieldname: 'date_time', columns: 2},
			{fieldname: 'clinical_information', columns: 4}
		];
		frm.get_field('rapid_tests').grid.editable_fields = [
			{fieldname: 'rapid_test', columns: 3},
			{fieldname: 'test_name', columns: 2},
			{fieldname: 'date_time', columns: 2},
			{fieldname: 'result_value', columns: 2},
			{fieldname: 'result', columns: 2}
		];
		frm.get_field('imaging').grid.editable_fields = [
			{fieldname: 'imaging_study', columns: 3},
			{fieldname: 'study_name', columns: 3},
			{fieldname: 'study_date_time', columns: 3},
			{fieldname: 'clinical_indication', columns: 3}
		];
		frm.get_field('procedure_prescription').grid.editable_fields = [
			{fieldname: 'procedure', columns: 3},
			{fieldname: 'procedure_name', columns: 3},
			{fieldname: 'referring_practitioner', columns: 2},
			{fieldname: 'date', columns: 2},
			{fieldname: 'to_be_done_in_theatre', columns: 2}
		];
		frm.get_field('therapies').grid.editable_fields = [
			{fieldname: 'therapy_type', columns: 8},
			{fieldname: 'no_of_sessions', columns: 2}
		];
		frm.get_field('systematic_physical_examination').grid.editable_fields = [
			{fieldname: 'exam_type', columns: 2},
			{fieldname: 'status', columns: 2},
			{fieldname: 'abnormalities_summary', columns: 4},
			{fieldname: 'short_notes', columns: 4}
		];
		frm.get_field('consumables').grid.editable_fields = [
			{fieldname: 'item_code', columns: 2},
			{fieldname: 'date', columns: 1},
			{fieldname: 'quantity', columns: 1},
			{fieldname: 'uom', columns: 1},
			{fieldname: 'comment', columns: 2}
		];
		frm.get_field('procedure_consumables').grid.editable_fields = [
			{fieldname: 'item', columns: 2},
			{fieldname: 'item_name', columns: 2},
			{fieldname: 'quantity', columns: 1},
			{fieldname: 'uom', columns: 1},
			{fieldname: 'invoice_separately', columns: 2}
		];
		frm.get_field('prosthetics_orthotics').grid.editable_fields = [
			{fieldname: 'item', columns: 2},
			{fieldname: 'date', columns: 2},
			{fieldname: 'quantity', columns: 2},
			{fieldname: 'provision_type', columns: 2}
		];
		frm.get_field('general_followup').grid.editable_fields = [
			{fieldname: 'date', columns: 2},
			{fieldname: 'programmed_visit', columns: 1},
			{fieldname: 'rdv', columns: 2},
			{fieldname: 'complaint_diagnosis', columns: 3},
			{fieldname: 'visit_completed', columns: 1}
		];
	},

	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			if (frm.doc.docstatus === 1) {
				if(!['Discharge Scheduled', 'Admission Scheduled', 'Admitted'].includes(frm.doc.inpatient_status)) {
					frm.add_custom_button(__('Schedule Admission'), function() {
						schedule_inpatient(frm);
					});
				}
			}

			frm.add_custom_button(__("Refer Patient"), function() {
				create_patient_referral(frm);
			},__("Create"));

			frm.add_custom_button(__('Patient History'), function() {
				if (frm.doc.patient) {
					frappe.route_options = {'patient': frm.doc.patient};
					frappe.set_route('patient_history');
				} else {
					frappe.msgprint(__('Please select Patient'));
				}
			},__('View'));

			if (frm.doc.docstatus === 1 && frm.doc.inpatient_status === 'Admitted') {
				frm.add_custom_button(__('Schedule Discharge'), function() {
					schedule_discharge(frm);
				});
			}
		}

		frm.set_query('patient', function() {
			return {
				filters: {'status': 'Active'}
			};
		});

		frm.set_query('lab_test_code', 'lab_test_prescription', function() {
			return {
				filters: {
					is_billable: 1
				}
			};
		});

		frm.set_query('rapid_test', 'rapid_tests', function() {
			return {
				filters: {
					is_billable: 1
				}
			};
		});

		wire_connections_buttons(frm);
	},

	patient: function(frm) {
		frm.events.set_patient_info(frm);
	},

	practitioner: function(frm) {
		if (!frm.doc.practitioner) {
			frm.set_value('practitioner_name', '');
		}
	},

	height_cm: function(frm) {
		calculate_bmi(frm);
	},

	weight_kg: function(frm) {
		calculate_bmi(frm);
	},

	systole: function(frm) {
		calculate_bp_status(frm);
	},

	diastole: function(frm) {
		calculate_bp_status(frm);
	},

	set_patient_info: async function(frm) {
		if (frm.doc.patient) {
			frappe.call({
				method: 'healthcare.healthcare.doctype.patient.patient.get_patient_detail',
				args: {
					patient: frm.doc.patient
				},
				callback: function(data) {
					let age = '';
					if (data.message.dob) {
						age = calculate_age(data.message.dob);
					}
					let values = {
						'patient_age': age,
						'patient_name':data.message.patient_name,
						'patient_sex': data.message.sex,
						'inpatient_record': data.message.inpatient_record,
						'inpatient_status': data.message.inpatient_status
					};
					frm.set_value(values);
				}
			});
		} else {
			let values = {
				'patient_age': '',
				'patient_name':'',
				'patient_sex': '',
				'inpatient_record': '',
				'inpatient_status': ''
			};
			frm.set_value(values);
		}
	}
});

var wire_connections_buttons = function(frm) {
	if (frm.fields_dict.internal_orientation) {
		frm.fields_dict.internal_orientation.$input.on('click', function() {
			frappe.set_route('patient-orientation');
		});
	}
	if (frm.fields_dict.clinical_procedure) {
		frm.fields_dict.clinical_procedure.$input.on('click', function() {
			create_procedure(frm);
		});
	}
	if (frm.fields_dict.nutrition_referral) {
		frm.fields_dict.nutrition_referral.$input.on('click', function() {
			frappe.msgprint(__('Nutrition referral workflow is not implemented yet.'));
		});
	}
};

var prefill_consultation_history = function(frm) {
	frappe.db.get_doc('Patient', frm.doc.patient).then((patient) => {
		const map = {
			any_allergies: 'allergies',
			medications: 'medication',
			past_medical_history: 'medical_history',
			surgical_history: 'surgical_history',
		};
		Object.keys(map).forEach((enc_field) => {
			if (!frm.doc[enc_field] && patient[map[enc_field]]) {
				frm.set_value(enc_field, patient[map[enc_field]]);
			}
		});
	});
};

var prefill_chief_complaints = function(frm) {
	if (!frm.doc.chief_complaints && frm.doc.rw_chief_complaint) {
		frm.set_value('chief_complaints', frm.doc.rw_chief_complaint);
	}
	if (!frm.doc.history_present_illness) {
		frm.set_value('history_present_illness', frm.doc.rw_history_present_illness || frm.doc.chief_complaints || '');
	}
};

var calculate_bmi = function(frm) {
	let height = frm.doc.height_cm;
	let weight = frm.doc.weight_kg;
	if (!height || !weight) {
		frm.set_value('bmi', null);
		frm.set_value('bmi_status', '');
		return;
	}
	let height_m = height / 100;
	let bmi = weight / (height_m * height_m);
	bmi = Math.round(bmi * 100) / 100;
	frm.set_value('bmi', bmi);
	let status = '';
	if (bmi < 18.5) {
		status = __('Underweight');
	} else if (bmi < 25) {
		status = __('Normal');
	} else if (bmi < 30) {
		status = __('Overweight');
	} else {
		status = __('Obese');
	}
	frm.set_value('bmi_status', status);
};

var calculate_bp_status = function(frm) {
	let systole = frm.doc.systole;
	let diastole = frm.doc.diastole;
	if (!systole || !diastole) {
		frm.set_value('bp_status', '');
		return;
	}
	let status = '';
	if (systole < 120 && diastole < 80) {
		status = __('Normal');
	} else if (systole < 130 && diastole < 80) {
		status = __('Elevated');
	} else if (systole < 140 && diastole < 90) {
		status = __('High (Stage 1)');
	} else {
		status = __('High (Stage 2)');
	}
	frm.set_value('bp_status', status);
};

var schedule_inpatient = function(frm) {
	let service_unit_type = "";
	var dialog = new frappe.ui.Dialog({
		title: 'Patient Admission',
		fields: [
			{fieldtype: 'Link', label: 'Medical Department', fieldname: 'medical_department', options: 'Medical Department', reqd: 1},
			{fieldtype: 'Link', label: 'Healthcare Practitioner (Primary)', fieldname: 'primary_practitioner', options: 'Healthcare Practitioner', reqd: 1},
			{fieldtype: 'Link', label: 'Healthcare Practitioner (Secondary)', fieldname: 'secondary_practitioner', options: 'Healthcare Practitioner'},
			{fieldtype: 'Link', label: 'Nursing Checklist Template', fieldname: 'admission_nursing_checklist_template', options: 'Nursing Checklist Template'},
			{fieldtype: 'Column Break'},
			{fieldtype: 'Date', label: 'Admission Ordered For', fieldname: 'admission_ordered_for', default: 'Today'},
			{fieldtype: 'Link', label: 'Service Unit Type', fieldname: 'service_unit_type', options: 'Healthcare Service Unit Type'},
			{fieldtype: 'Int', label: 'Expected Length of Stay', fieldname: 'expected_length_of_stay'},
			{fieldtype: 'Section Break'},
			{fieldtype: 'Long Text', label: 'Admission Instructions', fieldname: 'admission_instruction'}
		],
		primary_action_label: __('Order Admission'),
		primary_action : function() {
			var args = {
				patient: frm.doc.patient,
				admission_encounter: frm.doc.name,
				referring_practitioner: frm.doc.practitioner,
				company: frm.doc.company,
				medical_department: dialog.get_value('medical_department'),
				primary_practitioner: dialog.get_value('primary_practitioner'),
				secondary_practitioner: dialog.get_value('secondary_practitioner'),
				admission_ordered_for: dialog.get_value('admission_ordered_for'),
				admission_service_unit_type: dialog.get_value('service_unit_type'),
				expected_length_of_stay: dialog.get_value('expected_length_of_stay'),
				admission_instruction: dialog.get_value('admission_instruction'),
				admission_nursing_checklist_template: dialog.get_value('admission_nursing_checklist_template')
			}
			frappe.call({
				method: 'healthcare.healthcare.doctype.inpatient_record.inpatient_record.schedule_inpatient',
				args: {
					args: args
				},
				callback: function(data) {
					if (!data.exc) {
						frm.reload_doc();
					}
				},
				freeze: true,
				freeze_message: __('Scheduling Patient Admission')
			});
			frm.refresh_fields();
			dialog.hide();
		}
	});

	dialog.set_values({
		'medical_department': frm.doc.medical_department,
		'primary_practitioner': frm.doc.practitioner,
	});

	dialog.fields_dict['service_unit_type'].get_query = function() {
		return {
			filters: {
				'inpatient_occupancy': 1,
				'allow_appointments': 0
			}
		};
	};

	dialog.fields_dict["service_unit_type"].df.onchange = () => {
		if (dialog.get_value("service_unit_type") && dialog.get_value("service_unit_type") != service_unit_type) {
			service_unit_type = dialog.get_value("service_unit_type");
			frappe.db.get_value("Healthcare Service Unit Type", {name: dialog.get_value("service_unit_type")}, ["is_billable", "item"])
			.then(r => {
				if (r.message.is_billable && !r.message.item) {
					frappe.msgprint({
						message: __("Selected service unit type doesn't have any item linked"),
						title: __("Warning"),
						indicator: "orange",
					});
				}
			})
		}
	};

	dialog.show();
	dialog.$wrapper.find('.modal-dialog').css('width', '800px');
};

var schedule_discharge = function(frm) {
	var dialog = new frappe.ui.Dialog ({
		title: 'Inpatient Discharge',
		fields: [
			{fieldtype: 'Date', label: 'Discharge Ordered Date', fieldname: 'discharge_ordered_date', default: 'Today', read_only: 1},
			{fieldtype: 'Date', label: 'Followup Date', fieldname: 'followup_date'},
			{fieldtype: 'Link', label: 'Nursing Checklist Template', options: 'Nursing Checklist Template', fieldname: 'discharge_nursing_checklist_template'},
			{fieldtype: 'Column Break'},
			{fieldtype: 'Small Text', label: 'Discharge Instructions', fieldname: 'discharge_instructions'},
			{fieldtype: 'Section Break', label:'Discharge Summary'},
			{fieldtype: 'Long Text', label: 'Discharge Note', fieldname: 'discharge_note'}
		],
		primary_action_label: __('Order Discharge'),
		primary_action : function() {
			var args = {
				patient: frm.doc.patient,
				discharge_encounter: frm.doc.name,
				discharge_practitioner: frm.doc.practitioner,
				discharge_ordered_date: dialog.get_value('discharge_ordered_date'),
				followup_date: dialog.get_value('followup_date'),
				discharge_instructions: dialog.get_value('discharge_instructions'),
				discharge_note: dialog.get_value('discharge_note'),
				discharge_nursing_checklist_template: dialog.get_value('discharge_nursing_checklist_template')
			}
			frappe.call ({
				method: 'healthcare.healthcare.doctype.inpatient_record.inpatient_record.schedule_discharge',
				args: {args},
				callback: function(data) {
					if(!data.exc){
						frm.reload_doc();
					}
				},
				freeze: true,
				freeze_message: 'Scheduling Inpatient Discharge'
			});
			frm.refresh_fields();
			dialog.hide();
		}
	});

	dialog.show();
	dialog.$wrapper.find('.modal-dialog').css('width', '800px');
};

let create_procedure = function(frm) {
	if (!frm.doc.patient) {
		frappe.throw(__('Please select patient'));
	}
	frappe.route_options = {
		'patient': frm.doc.patient,
		'medical_department': frm.doc.medical_department,
		'company': frm.doc.company
	};
	frappe.new_doc('Clinical Procedure');
};

let calculate_age = function(birth) {
	let ageMS = Date.parse(Date()) - Date.parse(birth);
	let age = new Date();
	age.setTime(ageMS);
	let years =  age.getFullYear() - 1970;
	return `${years} ${__('Years(s)')} ${age.getMonth()} ${__('Month(s)')} ${age.getDate()} ${__('Day(s)')}`;
};

let create_patient_referral = function(frm) {
	var dialog = new frappe.ui.Dialog ({
		title: "Patient Referral",
		size: "large",
		fields: [
			{
				label: "References",
				fieldname: "references",
				fieldtype: "Table",
				is_editable_grid: true,
				data: [],
				fields: [
					{
						"fieldname": "refer_to",
						"fieldtype": "Link",
						"label": "Refer To",
						"options": "Healthcare Practitioner",
						"in_list_view": 1,
						"reqd": 1,
						get_query: function () {
							return {
								filters: {
									name: ["!=", frm.doc.practitioner]
								},
							};
						},
					},
					{
						"fieldname": "appointment_type",
						"fieldtype": "Link",
						"label": "Appointment Type",
						"options": "Appointment Type",
						"in_list_view": 1,
						"reqd": 1,
					},
					{
						"fieldname": "referral_note",
						"fieldtype": "Long Text",
						"label": "Referral Note",
						"in_list_view": 1,
					},
				],
			},
		],
		primary_action_label: __("Refer"),
		primary_action : function() {
			if (dialog.get_value("references").length>0) {
				frappe.call({
					method: "healthcare.healthcare.doctype.patient_encounter.patient_encounter.create_patient_referral",
					freeze: true,
					args: {
						encounter: frm.doc.name,
						references: dialog.get_value("references"),
					},
					callback: function(r) {
						if (r && !r.exc) {
							dialog.hide();
							frm.reload_doc();
							frappe.show_alert({
								message: __("Patient referral requests created successfully"),
								indicator: "success"
							});
						}
					}
				});
				frm.refresh_fields();
			}
		}
	});

	dialog.show();
};
