/*
(c) ESS 2015-16
*/
frappe.listview_settings['Lab Test'] = {
	add_fields: ['name', 'status', 'invoiced'],
	filters: [['docstatus', '=', '0']],
	get_indicator: function (doc) {
		if (doc.status === 'Draft') {
			return [__('Pending'), 'orange', 'status, =, Draft'];
		} else if (doc.status === 'Approved') {
			return [__('Approved'), 'green', 'status, =, Approved'];
		} else if (doc.status === 'Rejected') {
			return [__('Rejected'), 'orange', 'status, =, Rejected'];
		} else if (doc.status === 'Completed') {
			return [__('Completed'), 'green', 'status, =, Completed'];
		} else if (doc.status === 'Cancelled') {
			return [__('Cancelled'), 'red', 'status, =, Cancelled'];
		}
	},
	onload: function (listview) {
		rw_lab_hide_add(listview);
	},
	refresh: function (listview) {
		rw_lab_hide_add(listview);
	}
};

// Lab tests are ordered from the encounter, so the list has no Add button and no manual create.
function rw_lab_hide_add(listview) {
	if (listview.page.clear_primary_action) {
		listview.page.clear_primary_action();
	}
	if (listview.page.btn_primary) {
		listview.page.btn_primary.hide();
	}
}

var create_multiple_dialog = function (listview) {
	var dialog = new frappe.ui.Dialog({
		title: 'Create Multiple Lab Tests',
		width: 100,
		fields: [
			{ fieldtype: 'Link', label: 'Patient', fieldname: 'patient', options: 'Patient', reqd: 1 },
			{
				fieldtype: 'Select', label: 'Invoice / Patient Encounter', fieldname: 'doctype',
				options: '\nSales Invoice\nPatient Encounter', reqd: 1
			},
			{
				fieldtype: 'Dynamic Link', fieldname: 'docname', options: 'doctype', reqd: 1,
				get_query: function () {
					return {
						filters: {
							'patient': dialog.get_value('patient'),
							'docstatus': 1
						}
					};
				}
			}
		],
		primary_action_label: __('Create'),
		primary_action: function () {
			frappe.call({
				method: 'healthcare.healthcare.doctype.lab_test.lab_test.create_multiple',
				args: {
					'doctype': dialog.get_value('doctype'),
					'docname': dialog.get_value('docname')
				},
				callback: function (data) {
					if (!data.exc) {
						if (!data.message) {
							frappe.msgprint(__('No Lab Tests created'));
						}
						listview.refresh();
					}
				},
				freeze: true,
				freeze_message: __('Creating Lab Tests...')
			});
			dialog.hide();
		}
	});

	dialog.show();
};
