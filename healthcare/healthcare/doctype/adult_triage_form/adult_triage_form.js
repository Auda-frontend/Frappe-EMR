var FORM_TYPE    = "adult";
var DOCTYPE_NAME = "Adult Triage Form";

// ── ALARM FIELDS ─────────────────────────────────────────────────────────────
var ALARM_FIELDS = [
    "alarm_not_breathing",
    "alarm_obstructed_breathing",
    "alarm_severe_resp_distress",
    "alarm_cardiac_arrest",
    "alarm_hemorrhage_uncontrolled",
    "alarm_stab_gunshot",
    "alarm_lethargic",
    "alarm_weak_fast_pulse",
    "alarm_cap_refill_3sec",
    "alarm_cold_hands",
    "alarm_convulsion",
    "alarm_coma",
    "alarm_hypoglycemia",
    "alarm_purpuric_rash",
    "alarm_burn_face_inhalation"
];

// Very Urgent Signs — checked when TEWS = 0-4
// If ANY checked → ORANGE
var YELLOW_FIELDS = [
    "yellow_focal_neuro",
    "yellow_altered_mental",
    "yellow_chest_pain",
    "yellow_poisoning",
    "yellow_coughing_blood",
    "yellow_diabetic_high",
    "yellow_aggression",
    "yellow_acute_sob",
    "yellow_severe_pain",
    "yellow_burn_20_urgent",
    "yellow_fracture_open",
    "yellow_threatened_limb",
    "yellow_eye_injury",
    "yellow_large_joint_disloc",
    "yellow_severe_mechanism",
    "yellow_abdominal_trauma"
];

// Urgent Signs — checked when TEWS = 0-2 and no yellow signs
// If ANY checked → YELLOW
var GREEN_FIELDS = [
    "green_cant_drink",
    "green_very_pale",
    "green_resp_distress",
    "green_diabetic_high",
    "green_malnutrition",
    "green_moderate_pain",
    "green_disloc_finger_toe",
    "green_fracture_closed",
    "green_burn_no_urgency"
];

// ── TEWS SCORING — matched exactly to physical form image ────────────────────

function score_mobility(v) {
    // Score 0: Walking
    // Score +1: With help / Wheelchair
    // Score +2: Stretcher OR Immobile (both in the same +2 column)
    var map = {
        "Walking":                0,
        "With help / Wheelchair": 1,
        "Stretcher":              2,
        "Immobile":               2
    };
    return (map[v] !== undefined) ? map[v] : 0;
}

function score_rr(v) {
    // Score -2: <9
    // Score  0: 9-14
    // Score +1: 15-20
    // Score +2: 21-29
    // Score +3: >29
    v = v || 0;
    if (v < 9)   return 2;
    if (v <= 14) return 0;
    if (v <= 20) return 1;
    if (v <= 29) return 2;
    return 3;
}

function score_hr(v) {
    // Score -2: <41
    // Score -1: 41-50
    // Score  0: 51-100
    // Score +1: 101-110
    // Score +2: 111-129
    // Score +3: >129
    v = v || 0;
    if (v < 41)   return 2;
    if (v <= 50)  return 1;
    if (v <= 100) return 0;
    if (v <= 110) return 1;
    if (v <= 129) return 2;
    return 3;
}

function score_sbp(v) {
    // Score -3: <71
    // Score -2: 71-80
    // Score -1: 81-100
    // Score  0: 101-199
    // Score +2: >199  (no +1, no +3)
    v = v || 0;
    if (v < 71)   return 3;
    if (v <= 80)  return 2;
    if (v <= 100) return 1;
    if (v <= 199) return 0;
    return 2;
}

function score_temp(v) {
    // Score -2: <35
    // Score  0: 35-38.4
    // Score +2: >38.5  (no -1, no +1, no +3)
    v = v || 36;
    if (v < 35)    return 2;
    if (v <= 38.4) return 0;
    return 2;
}

function score_avpu(v) {
    // Score -2: Confused
    // Score  0: Alert
    // Score +1: React to Voice
    // Score +2: React to pain
    // Score +3: Unresponsive
    var map = {
        "Alert":         0,
        "Confused":      2,
        "Voice":         1,
        "Pain":          2,
        "Unresponsive":  3
    };
    return (map[v] !== undefined) ? map[v] : 0;
}

// ── TEWS CALCULATOR ───────────────────────────────────────────────────────────
function calc_tews(frm) {
    var d   = frm.doc;
    var mob = score_mobility(d.mobility || "");
    var rr  = score_rr(d.rr);
    var hr  = score_hr(d.hr);
    var sbp = score_sbp(d.sbp);
    var tmp = score_temp(d.temperature);
    var av  = score_avpu(d.avpu || "");
    var tr  = d.trauma ? 1 : 0;

    var total = mob + rr + hr + sbp + tmp + av + tr;

    // Write individual scores back to read-only fields
    frm.set_value("mobility_score", mob);
    frm.set_value("rr_score",       rr);
    frm.set_value("hr_score",       hr);
    frm.set_value("sbp_score",      sbp);
    frm.set_value("temp_score",     tmp);
    frm.set_value("avpu_score",     av);
    frm.set_value("trauma_score",   tr);
    frm.set_value("tews_score",     total);

    return total;
}

// ── DEHYDRATION SPECIAL RULE ──────────────────────────────────────────────────
// Severe Dehydration triggers RED only when ≥ 2 of these 3 sub-fields are checked
function check_dehydration_alarm(frm) {
    var count = 0;
    if (frm.doc.dehydration_skin_pinch)  count++;
    if (frm.doc.dehydration_lethargy)    count++;
    if (frm.doc.dehydration_sunken_eyes) count++;
    return count >= 2;
}

// ── TRIAGE COLOR DECISION FLOW ────────────────────────────────────────────────

function assign_color(frm) {

    // ── SECTION 1: Emergency Signs ────────────────────────────────────────
    for (var i = 0; i < ALARM_FIELDS.length; i++) {
        if (frm.doc[ALARM_FIELDS[i]]) {
            set_color(frm, "RED");
            notify_nurse(frm, "RED",
                "Emergency sign present. Patient requires immediate resuscitation.");
            return;
        }
    }

    if (check_dehydration_alarm(frm)) {
        set_color(frm, "RED");
        notify_nurse(frm, "RED",
            "Severe dehydration (≥ 2 signs). Patient requires immediate resuscitation.");
        return;
    }

    // ── SECTION 2: TEWS ───────────────────────────────────────────────────
    var t  = frm.doc.tews_score || 0;
    var o2 = frm.doc.spo2;

    if (t >= 7 || (o2 && o2 < 92)) {
        set_color(frm, "RED");
        notify_nurse(frm, "RED",
            "TEWS = " + t +
            (o2 && o2 < 92 ? " / SpO\u2082 = " + o2 + "%" : "") +
            ". Patient requires immediate resuscitation.");
        return;
    }

    if (t >= 5) {
        set_color(frm, "ORANGE");
        notify_nurse(frm, "ORANGE",
            "TEWS = " + t + ". Patient must be seen in less than 10 minutes.");
        return;
    }

    // TEWS = 0-4: proceed to Very Urgent Signs
    // ── SECTION 3: Very Urgent Signs ─────────────────────────────────────
    var has_yellow = false;
    for (var j = 0; j < YELLOW_FIELDS.length; j++) {
        if (frm.doc[YELLOW_FIELDS[j]]) {
            has_yellow = true;
            break;
        }
    }

    if (has_yellow) {
        set_color(frm, "ORANGE");
        notify_nurse(frm, "ORANGE",
            "Very urgent complaint present. Patient must be seen in less than 10 minutes.");
        return;
    }

    if (t >= 3) {
        // TEWS 3-4 with no very urgent signs → YELLOW
        set_color(frm, "YELLOW");
        notify_nurse(frm, "YELLOW",
            "TEWS = " + t + " with no very urgent complaints. " +
            "Patient to be seen within 60 minutes.");
        return;
    }

    // TEWS 0-2 with no very urgent signs: proceed to Urgent Signs
    // ── SECTION 4: Urgent Signs ───────────────────────────────────────────
    var has_green = false;
    for (var k = 0; k < GREEN_FIELDS.length; k++) {
        if (frm.doc[GREEN_FIELDS[k]]) {
            has_green = true;
            break;
        }
    }

    if (has_green) {
        set_color(frm, "YELLOW");
        notify_nurse(frm, "YELLOW",
            "Urgent complaint present. Patient to be seen within 60 minutes.");
        return;
    }

    // No signs found in any section → GREEN
    set_color(frm, "GREEN");
    notify_nurse(frm, "GREEN",
        "No urgent signs detected. Patient to be seen within 4 hours.");
}

// ── SET COLOR ON THE FORM ─────────────────────────────────────────────────────
function set_color(frm, color) {
    var bg = {
        "RED":    "#dc2626",
        "ORANGE": "#ea580c",
        "YELLOW": "#ca8a04",
        "GREEN":  "#16a34a"
    };

    frm.set_value("triage_color", color);

    var fd = frm.fields_dict["triage_color"];
    if (fd && fd.wrapper) {
        $(fd.wrapper)
            .find("input, select, .form-control, .control-input")
            .css({
                "background-color": bg[color],
                "color":            "#ffffff",
                "font-weight":      "bold"
            });
    }

    frm.refresh_field("triage_color");
}

// ── NURSE NOTIFICATION ────────────────────────────────────────────────────────
function notify_nurse(frm, color, message) {
    var icons = {
        "RED":    "\uD83D\uDD34",
        "ORANGE": "\uD83D\uDFE0",
        "YELLOW": "\uD83D\uDFE1",
        "GREEN":  "\uD83D\uDFE2"
    };
    var times = {
        "RED":    "Immediate Resuscitation",
        "ORANGE": "Seen in < 10 minutes",
        "YELLOW": "Seen within 60 minutes",
        "GREEN":  "Seen within 4 hours"
    };
    var indicator = {
        "RED":    "red",
        "ORANGE": "orange",
        "YELLOW": "yellow",
        "GREEN":  "green"
    };

    // Always update the dashboard headline
    // frm.dashboard.set_headline_alert(
    //     icons[color] + " <b>" + color + " \u2014 " + times[color] + "</b>: " +
    //     message + " <b>You may now proceed to the orientation desk.</b>",
    //     indicator[color]
    // );

    // For RED and ORANGE: also show a prominent pop-up alert
    if (color === "RED" || color === "ORANGE") {
        frappe.show_alert({
            message: icons[color] + " <b>" + color + " \u2014 " +
                     times[color] + "</b><br>" + message +
                     "<br><br>\u26A0\uFE0F <b>Proceed immediately to orientation desk.</b>",
            indicator: indicator[color]
        }, 12);
    }
}

// ── APPLY EXISTING COLOR ON FORM LOAD ────────────────────────────────────────
function restore_color_display(frm) {
    if (frm.doc.triage_color) {
        set_color(frm, frm.doc.triage_color);
        var times = {
            "RED":    "Immediate Resuscitation",
            "ORANGE": "Seen in < 10 minutes",
            "YELLOW": "Seen within 60 minutes",
            "GREEN":  "Seen within 4 hours"
        };
        var icons = {
            "RED":    "\uD83D\uDD34",
            "ORANGE": "\uD83D\uDFE0",
            "YELLOW": "\uD83D\uDFE1",
            "GREEN":  "\uD83D\uDFE2"
        };
        var indicator = {
            "RED": "red", "ORANGE": "orange",
            "YELLOW": "yellow", "GREEN": "green"
        };
        frm.dashboard.set_headline_alert(
            icons[frm.doc.triage_color] +
            " <b>" + frm.doc.triage_color + " \u2014 " +
            times[frm.doc.triage_color] + "</b>",
            indicator[frm.doc.triage_color]
        );
    }
}

// ── FRAPPE EVENT HANDLERS ─────────────────────────────────────────────────────
frappe.ui.form.on(DOCTYPE_NAME, {

    // ── LIFECYCLE ─────────────────────────────────────────────────────────
    onload: function(frm) {
        if (frm.is_new() && frappe.route_options) {
            var ro = frappe.route_options;
            if (ro.triage_assessment && !frm.doc.triage_assessment) {
                frm.set_value("triage_assessment", ro.triage_assessment);
            } else if (ro.parent_triage && !frm.doc.parent_triage) {
                frm.set_value("parent_triage", ro.parent_triage);
            }
        }
    },

    refresh: function(frm) {
        // Lock all score fields — calculated automatically, not entered manually
        var score_fields = [
            "mobility_score", "rr_score", "hr_score", "sbp_score",
            "temp_score", "avpu_score", "trauma_score", "tews_score"
        ];
        score_fields.forEach(function(f) {
            frm.set_df_property(f, "read_only", 1);
        });

        // Restore color display if form already has a color saved
        restore_color_display(frm);
    },

    after_save: function(frm) {
        if (frm.doc.triage_assessment || frm.doc.parent_triage) {
            frappe.call({
                method: "frappe.client.get",
                args: { doctype: DOCTYPE_NAME, name: frm.doc.name },
                callback: function(r) {
                    if (r.message) {
                        frappe.call({
                            method: "healthcare.healthcare.doctype.adult_triage_form.adult_triage_form.sync_to_parent_triage",
                            args: { form_data: r.message },
                            error: function(err) {
                                frappe.msgprint(__("Sync to parent triage failed."));
                                console.error(err);
                            }
                        });
                    }
                },
                error: function(err) {
                    frappe.msgprint(__("Could not fetch form data for sync."));
                    console.error(err);
                }
            });
        }
    },

    // ── VITALS — recalculate TEWS then assign color ───────────────────────
    mobility: function(frm) {
        calc_tews(frm);
        assign_color(frm);
    },
    rr: function(frm) {
        calc_tews(frm);
        assign_color(frm);
    },
    hr: function(frm) {
        calc_tews(frm);
        assign_color(frm);
    },
    sbp: function(frm) {
        calc_tews(frm);
        assign_color(frm);
    },
    temperature: function(frm) {
        calc_tews(frm);
        assign_color(frm);
    },
    avpu: function(frm) {
        calc_tews(frm);
        assign_color(frm);
    },
    trauma: function(frm) {
        calc_tews(frm);
        assign_color(frm);
    },
    spo2: function(frm) {
        // SpO2 affects color directly — no TEWS recalc needed
        assign_color(frm);
    },

    // ── SECTION 1: ALARM CHECKBOXES ──────────────────────────────────────
    alarm_not_breathing: function(frm) {
        assign_color(frm);
    },
    alarm_obstructed_breathing: function(frm) {
        assign_color(frm);
    },
    alarm_severe_resp_distress: function(frm) {
        assign_color(frm);
    },
    alarm_cardiac_arrest: function(frm) {
        assign_color(frm);
    },
    alarm_hemorrhage_uncontrolled: function(frm) {
        assign_color(frm);
    },
    alarm_stab_gunshot: function(frm) {
        assign_color(frm);
    },
    alarm_lethargic: function(frm) {
        assign_color(frm);
    },
    alarm_weak_fast_pulse: function(frm) {
        assign_color(frm);
    },
    alarm_cap_refill_3sec: function(frm) {
        assign_color(frm);
    },
    alarm_cold_hands: function(frm) {
        assign_color(frm);
    },
    alarm_convulsion: function(frm) {
        assign_color(frm);
    },
    alarm_coma: function(frm) {
        assign_color(frm);
    },
    // Dehydration: each sub-field triggers the ≥2 check
    dehydration_skin_pinch: function(frm) {
        assign_color(frm);
    },
    dehydration_lethargy: function(frm) {
        assign_color(frm);
    },
    dehydration_sunken_eyes: function(frm) {
        assign_color(frm);
    },
    alarm_hypoglycemia: function(frm) {
        assign_color(frm);
    },
    alarm_purpuric_rash: function(frm) {
        assign_color(frm);
    },
    alarm_burn_face_inhalation: function(frm) {
        assign_color(frm);
    },

    // ── SECTION 3: VERY URGENT SIGNS (checked when TEWS = 0-4) ──────────
    // Any checked → ORANGE
    yellow_focal_neuro: function(frm) {
        assign_color(frm);
    },
    yellow_altered_mental: function(frm) {
        assign_color(frm);
    },
    yellow_chest_pain: function(frm) {
        assign_color(frm);
    },
    yellow_poisoning: function(frm) {
        assign_color(frm);
    },
    yellow_coughing_blood: function(frm) {
        assign_color(frm);
    },
    yellow_diabetic_high: function(frm) {
        assign_color(frm);
    },
    yellow_aggression: function(frm) {
        assign_color(frm);
    },
    yellow_acute_sob: function(frm) {
        assign_color(frm);
    },
    yellow_severe_pain: function(frm) {
        assign_color(frm);
    },
    yellow_burn_20_urgent: function(frm) {
        assign_color(frm);
    },
    yellow_fracture_open: function(frm) {
        assign_color(frm);
    },
    yellow_threatened_limb: function(frm) {
        assign_color(frm);
    },
    yellow_eye_injury: function(frm) {
        assign_color(frm);
    },
    yellow_large_joint_disloc: function(frm) {
        assign_color(frm);
    },
    yellow_severe_mechanism: function(frm) {
        assign_color(frm);
    },
    yellow_abdominal_trauma: function(frm) {
        assign_color(frm);
    },

    // ── SECTION 4: URGENT SIGNS (checked when TEWS = 0-2, no yellow signs)
    // Any checked → YELLOW
    green_cant_drink: function(frm) {
        assign_color(frm);
    },
    green_very_pale: function(frm) {
        assign_color(frm);
    },
    green_resp_distress: function(frm) {
        assign_color(frm);
    },
    green_diabetic_high: function(frm) {
        assign_color(frm);
    },
    green_malnutrition: function(frm) {
        assign_color(frm);
    },
    green_moderate_pain: function(frm) {
        assign_color(frm);
    },
    green_disloc_finger_toe: function(frm) {
        assign_color(frm);
    },
    green_fracture_closed: function(frm) {
        assign_color(frm);
    },
    green_burn_no_urgency: function(frm) {
        assign_color(frm);
    }
});