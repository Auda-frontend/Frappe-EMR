// Unified Rwanda Triage Assessment form.
// Server-side Python remains authoritative for TEWS and triage colour.

frappe.ui.form.on("Triage Assessment", {
    onload(frm) {
        if (frm.is_new() && frappe.route_options) {
            const ro = frappe.route_options;

            if (ro.patient && !frm.doc.patient) {
                frm.set_value("patient", ro.patient);
            }
            if (ro.company && !frm.doc.company) {
                frm.set_value("company", ro.company);
            }
        }

        if (frm.is_new()) {
            if (!frm.doc.arrival_date) {
                frm.set_value("arrival_date", frappe.datetime.get_today());
            }
            if (!frm.doc.arrival_time) {
                frm.set_value("arrival_time", frappe.datetime.now_time());
            }
        }
    },

    refresh(frm) {
        set_mobility_options(frm);
        set_triage_colour_editability(frm);
        update_triage_priority_alert(frm);
        toggle_notification_fields(frm);
        update_triage_indicator(frm);

        if (frm.doc.vital_signs_record) {
            frm.add_custom_button(__("Open Vital Signs"), () => {
                frappe.set_route(
                    "Form",
                    "Vital Signs",
                    frm.doc.vital_signs_record
                );
            }, __("Workflow"));
        }

        if (!frm.is_new() && !frm.doc.patient_oriented) {
            if (frm.doc.docstatus === 1) {
                frm.add_custom_button(__("Orient patient"), () => rw_triage_open_orientation(frm), __("Workflow"));
            }
        }
    },

    patient(frm) {
        if (!frm.doc.patient) return;

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Patient",
                name: frm.doc.patient
            },
            callback(r) {
                if (!r.message) return;

                const p = r.message;
                const updates = [
                    ["patient_name", p.patient_name],
                    ["patient_gender", p.sex],
                    ["medical_record_number", p.name],
                    ["is_maternity", (p.sex || "").toLowerCase() === "female" ? (p.rw_is_maternity || 0) : 0]
                ];

                if (p.dob) {
                    const today = frappe.datetime.nowdate();
                    updates.push(["date_of_birth", p.dob]);
                    updates.push([
                        "patient_age",
                        moment(today).diff(moment(p.dob), "years")
                    ]);
                    updates.push([
                        "patient_age_months",
                        moment(today).diff(moment(p.dob), "months")
                    ]);
                }

                if (!frm.doc.company && p.default_company) {
                    updates.push(["company", p.default_company]);
                }

                Promise.all(
                    updates.map(([field, value]) => frm.set_value(field, value))
                ).then(() => {
                    if (!frm.doc.arrival_date) {
                        frm.set_value("arrival_date", frappe.datetime.nowdate());
                    }
                    if (!frm.doc.arrival_time) {
                        frm.set_value("arrival_time", frappe.datetime.now_time());
                    }

                    set_form_type_from_demographics(frm);
                    set_mobility_options(frm);
                });
            }
        });
    },

    is_maternity(frm) {
        set_form_type_from_demographics(frm);
        set_mobility_options(frm);
    },

    patient_age(frm) {
        set_form_type_from_demographics(frm);
        set_mobility_options(frm);
    },

    patient_age_months(frm) {
        set_form_type_from_demographics(frm);
        set_mobility_options(frm);
    },

    form_type(frm) {
        set_mobility_options(frm);
    },

    weight(frm) {
        rw_update_bmi(frm);
    },

    height(frm) {
        rw_update_bmi(frm);
    },

    before_submit(frm) {
        rw_check_required_before_submit(frm);
    },

    triage_color(frm) {
        toggle_notification_fields(frm);
        update_triage_priority_alert(frm);
        update_triage_indicator(frm);
    },

    manual_priority_override(frm) {
        set_triage_colour_editability(frm);
        toggle_notification_fields(frm);
    }
});


function set_form_type_from_demographics(frm) {
    if (frm.doc.is_maternity) {
        frm.set_value("form_type", "Maternity");
        return;
    }

    const months = frm.doc.patient_age_months;
    const years = frm.doc.patient_age;

    if (months !== undefined && months !== null && months !== "") {
        if (Number(months) <= 36) {
            frm.set_value("form_type", "Infant");
        } else if (Number(months) <= 144) {
            frm.set_value("form_type", "Child");
        } else {
            frm.set_value("form_type", "Adult");
        }
        return;
    }

    if (years !== undefined && years !== null && years !== "") {
        if (Number(years) <= 3) {
            frm.set_value("form_type", "Infant");
        } else if (Number(years) <= 12) {
            frm.set_value("form_type", "Child");
        } else {
            frm.set_value("form_type", "Adult");
        }
    }
}


function set_mobility_options(frm) {
    if (!frm.fields_dict.mobility) return;

    const childOrInfant = ["Child", "Infant"].includes(frm.doc.form_type);
    const options = childOrInfant
        ? [
            { value: "", label: "" },
            { value: "0", label: __("0 - Normal for age") },
            { value: "2", label: __("2 - Unable to move as normal") },
        ]
        : [
            { value: "", label: "" },
            { value: "0", label: __("0 - Walking") },
            { value: "1", label: __("1 - With help / wheelchair") },
            { value: "2", label: __("2 - Stretcher / immobile") },
        ];

    frm.set_df_property("mobility", "options", options);

    const current = frm.doc.mobility;
    if (current !== undefined && current !== null && current !== "") {
        if (!options.some((o) => o.value === String(current))) {
            frm.set_value("mobility", "");
        }
    }
}


function set_triage_colour_editability(frm) {
    if (frm.fields_dict.triage_color) {
        frm.set_df_property(
            "triage_color",
            "read_only",
            !frm.doc.manual_priority_override
        );
    }
}


function update_triage_priority_alert(frm) {
    // One banner only: the triage colour and the care this patient needs.
    const info = {
        RED: { colour: "red", text: __("RED - Emergency: this patient needs immediate care.") },
        ORANGE: { colour: "orange", text: __("ORANGE - Urgent: this patient needs urgent care.") },
        YELLOW: { colour: "yellow", text: __("YELLOW - Non-urgent: this patient needs prompt care.") },
        GREEN: { colour: "green", text: __("GREEN - Routine: this patient can be seen in turn.") },
    }[frm.doc.triage_color];

    if (frm.dashboard.clear_headline) {
        frm.dashboard.clear_headline();
    }
    if (!info) return;

    let text = info.text;
    if (frm.doc.patient_oriented) {
        text += " " + __("Patient already oriented.");
    }
    frm.dashboard.set_headline_alert(text, info.colour);
}


function toggle_notification_fields(frm) {
    const critical = ["RED", "ORANGE"].includes(frm.doc.triage_color);

    ["notified_color", "notified_at", "doctor_name", "doctor_attended_at"]
        .forEach((field) => {
            if (frm.fields_dict[field]) {
                frm.toggle_display(field, critical);
            }
        });

    if (frm.fields_dict.override_reason) {
        frm.toggle_display(
            "override_reason",
            !!frm.doc.manual_priority_override
        );
    }
}


function update_triage_indicator(frm) {
    const colours = { RED: "red", ORANGE: "orange", YELLOW: "yellow", GREEN: "green" };
    const colour = frm.doc.triage_color;

    if (colour && colours[colour]) {
        const score = frm.doc.tews_score !== undefined && frm.doc.tews_score !== null
            ? " - TEWS " + frm.doc.tews_score
            : "";
        frm.page.set_indicator(__(colour) + score, colours[colour]);
    } else {
        frm.page.set_indicator(__("Not yet assessed"), "gray");
    }
}


function rw_triage_open_orientation(frm) {
    // Orient from the triage nursing station, with the priority set from the triage colour.
    const priorities = { RED: "Emergency", ORANGE: "Urgent", YELLOW: "Non-urgent", GREEN: "Routine" };
    const values = { patient: frm.doc.patient, triage_assessment: frm.doc.name };
    const priority = priorities[frm.doc.triage_color];
    if (priority) {
        values["priority"] = priority;
    }

    const tries = [
        { healthcare_service_unit_name: ["like", "%Nursing Station%"], is_group: 0 },
        { service_unit_type: "Triage", is_group: 0 },
    ];
    const find_unit = (i) => {
        if (i >= tries.length) return Promise.resolve(null);
        return frappe.db
            .get_value("Healthcare Service Unit", tries[i], "name")
            .then((res) => (res.message && res.message.name) || find_unit(i + 1));
    };

    find_unit(0).then((unit) => {
        if (unit) {
            values.orientation_from = unit;
        }
        frappe.new_doc("Internal Orientation", values);
    });
}


function rw_update_bmi(frm) {
    // Preview only. The server recalculates BMI on every save.
    const weight = flt(frm.doc.weight);
    const height = flt(frm.doc.height);
    const bmi = weight > 0 && height > 0 ? flt(weight / Math.pow(height / 100, 2), 1) : null;
    frm.set_value("bmi", bmi);
}


// Observations that must be entered before an assessment can be submitted.
// The server enforces the same rule (tews.py); this only highlights the gaps early.
// Not required: SpO2, diastolic BP, trauma (a tick box). SBP is scored on adult and maternity only.
const RW_REQUIRED_ALWAYS = ["mobility", "rr", "hr", "temperature", "avpu"];
const RW_REQUIRED_ALL = RW_REQUIRED_ALWAYS.concat(["sbp"]);
const RW_NUMERIC_REQUIRED = ["rr", "hr", "temperature", "sbp"];
const RW_SPO2_RED_BELOW = 92; // same value as SPO2_RED_BELOW in tews.py


function rw_missing_required(frm) {
    // An emergency sign, SpO2 under 92 or a documented override already gives a colour.
    const emergency = Object.keys(frm.fields_dict).some((name) => {
        const field = frm.fields_dict[name];
        return name.startsWith("alarm_") && field.df.fieldtype === "Check"
            && field.disp_status !== "None" && frm.doc[name];
    });
    const low_spo2 = flt(frm.doc.spo2) > 0 && flt(frm.doc.spo2) < RW_SPO2_RED_BELOW;
    if (emergency || low_spo2 || frm.doc.manual_priority_override) {
        return [];
    }

    const adult_like = ["Adult", "Maternity"].includes(frm.doc.form_type);
    const required = RW_REQUIRED_ALWAYS.concat(adult_like ? ["sbp"] : []);
    return required.filter((name) => {
        const value = frm.doc[name];
        if (RW_NUMERIC_REQUIRED.includes(name)) {
            return !(flt(value) > 0);
        }
        return value === undefined || value === null || String(value).trim() === "";
    });
}


function rw_mark_missing(frm, missing) {
    RW_REQUIRED_ALL.forEach((name) => {
        const field = frm.fields_dict[name];
        if (field && field.$wrapper) {
            field.$wrapper.toggleClass("has-error", missing.includes(name));
        }
    });
}


function rw_check_required_before_submit(frm) {
    const missing = rw_missing_required(frm);
    rw_mark_missing(frm, missing);
    if (!missing.length) return;

    frappe.validated = false;
    const labels = missing.map((name) => __(frm.fields_dict[name].df.label || name));
    frappe.msgprint({
        title: __("Missing Fields"),
        indicator: "red",
        message: __("Missing fields: {0}. Complete them before submitting.", [labels.join(", ")]),
    });
    frm.scroll_to_field(missing[0]);
}


// A field loses its red mark as soon as it is filled in.
RW_REQUIRED_ALL.forEach((name) => {
    frappe.ui.form.on("Triage Assessment", name, (frm) => {
        const field = frm.fields_dict[name];
        if (field && field.$wrapper) {
            field.$wrapper.removeClass("has-error");
        }
    });
});
