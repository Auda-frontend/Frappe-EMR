var FORM_TYPE    = "infant";
var DOCTYPE_NAME = "Infant Triage Form";

// ── ALARM FIELDS ─────────────────────────────────────────────────────────────
// Infant alarm signs are identical to child form
var ALARM_FIELDS = [
    "alarm_not_breathing_weak",       // Not breathing or weak breathing
    "alarm_central_cyanosis",         // Central cyanosis
    "alarm_obstructed_breathing",     // Obstructed breathing
    "alarm_severe_resp_distress",     // Severe respiratory distress
    "alarm_cardiac_arrest",           // Cardiac arrest
    "alarm_pulse_low_absent",         // Pulse low or absent
    "alarm_hemorrhage_uncontrolled",  // Hemorrhage uncontrolled
    "alarm_lethargic",                // Lethargic
    "alarm_weak_fast_pulse",          // Pulse weak and fast
    "alarm_cap_refill_3sec",          // Cap refill ≥ 3 sec
    "alarm_cold_hands",               // Cold hand plus
    "alarm_convulsion",               // Convulsion
    "alarm_coma",                     // Coma
    "alarm_hypoglycemia",             // Hypoglycemia
    "alarm_purpuric_rash",            // Purpuric rash
    "alarm_burn_face_inhalation"      // Burn face/inhalation
];

// ── VERY URGENT SIGNS (YELLOW section) ───────────────────────────────────────
// Infant yellow signs are COMPLETELY DIFFERENT from adult and child.
// If ANY checked → ORANGE
var YELLOW_FIELDS = [
    "yellow_more_sleep",          // More sleep than normal
    "yellow_focal_neuro",         // Focal neurological deficit — acute (< 1 day)
    "yellow_inconsolable_cry",    // Inconsolable crying / severe pain (pain > 7)
    "yellow_floppy_irritable",    // Floppy, irritable, or restless
    "yellow_chest_pain",          // Chest pain
    "yellow_poisoning",           // Poisoning / Overdose
    "yellow_tiny_baby",           // Tiny baby (younger than 2 months)
    // Trauma
    "yellow_burn_10_urgent",      // Burn over 10% or urgent signs — NOTE: 10% not 20%
    "yellow_fracture_open",       // Fracture open (with skin break)
    "yellow_threatened_limb",     // Threatened limb (no pulse or pale)
    "yellow_eye_injury",          // Eye injury
    "yellow_large_joint_disloc",  // Dislocation of large joint (not finger/toe)
    "yellow_severe_mechanism"     // Severe mechanism — fall > child's height, RTA
];

// ── URGENT SIGNS (GREEN section) ─────────────────────────────────────────────
// Infant green signs are COMPLETELY DIFFERENT from adult and child.
// If ANY checked → YELLOW
var GREEN_FIELDS = [
    "green_pitting_oedema",       // Pitting oedema of both feet or face
    "green_cant_drink",           // Unable to drink or vomits everything
    "green_severe_pallor",        // Severe pallor
    "green_resp_distress",        // Some respiratory distress
    "green_known_diabetes",       // Unwell with known diabetes
    "green_malnutrition",         // Severe malnutrition / wasting
    // Diarrhoea sub-signs — any of these counts
    "green_diarrhea_vomiting",    // Diarrhoea and/or vomiting
    "green_dv_sunken_eyes",       // — Sunken eyes
    "green_dv_dry_mouth",         // — Dry mouth
    "green_dv_decreased_urine",   // — Decreased urine output
    "green_dv_skin_pinch_slow",   // — Skin pinch slow < 2 sec
    // Trauma
    "green_disloc_finger_toe",    // Dislocation finger or toe
    "green_fracture_closed",      // Fracture closed
    "green_burn_no_urgency",      // Burn without urgent signs
    "green_moderate_pain"         // Moderate pain (5-6)
];

// ── TEWS SCORING — Infant form (0-3 years) ───────────────────────────────────
//
// Physical form column layout:
// SCORE  | 3    | 2     | 1     | 0       | 1       | 2       | 3
// -------|------|-------|-------|---------|---------|---------|--------
// Mob    |      |       |       | Normal  | Unable  |         |
//        |      |       |       | for age | to move |         |
// RR     | <20  | 20-25 |       | 26-39   | 40-49   |         | 50 or >
// HR     | <70  | 70-79 |       | 80-130  | 131-159 |         | 160 or >
// Temp   |      | <35   |       | 35-38.4 |         | 38.4+   |
// AVUP   |      | Conf  |       | Alert   | Voice   | Pain    | Unresponsive
// Trauma |      |       |       | No      | Yes     |         |

// NOTE: Infant form has NO SBP (blood pressure) row

function score_mobility(v) {
    // Score 0: Normal for age
    // Score +1: Unable to move as normal
    var map = {
        "Normal for age":           0,
        "Unable to move as normal": 1
    };
    return (map[v] !== undefined) ? map[v] : 0;
}

function score_rr(v) {
    // Score 3 (left): < 20
    // Score 2 (left): 20-25
    // Score 0:        26-39
    // Score +1:       40-49
    // Score +3:       50 or >
    // NOTE: no score 1 on left, no score 2 on right for infant RR
    v = v || 0;
    if (v < 20)  return 3;
    if (v <= 25) return 2;
    if (v <= 39) return 0;
    if (v <= 49) return 1;
    return 3;
}

function score_hr(v) {
    // Score 3 (left): < 70
    // Score 2 (left): 70-79
    // Score 0:        80-130
    // Score +1:       131-159
    // Score +3:       160 or >
    // NOTE: no score 1 on left, no score 2 on right for infant HR
    v = v || 0;
    if (v < 70)   return 3;
    if (v <= 79)  return 2;
    if (v <= 130) return 0;
    if (v <= 159) return 1;
    return 3;
}

// NO score_sbp for infant form — no blood pressure row

function score_temp(v) {
    // Score 2 (left): < 35
    // Score 0:        35-38.4
    // Score +2:       38.4 or >
    // Same as adult and child
    v = v || 36;
    if (v < 35)    return 2;
    if (v <= 38.4) return 0;
    return 2;
}

function score_avpu(v) {
    // Score 2 (left): Confused
    // Score 0:        Alert
    // Score +1:       Reactive to Voice
    // Score +2:       Reacts to Pain
    // Score +3:       Unresponsive
    // Same as adult and child
    var map = {
        "Alert":        0,
        "Confused":     2,
        "Voice":        1,
        "Pain":         2,
        "Unresponsive": 3
    };
    return (map[v] !== undefined) ? map[v] : 0;
}

// ── TEWS CALCULATOR ───────────────────────────────────────────────────────────
function calc_tews(frm) {
    var d   = frm.doc;
    var mob = score_mobility(d.mobility || "");
    var rr  = score_rr(d.rr);
    var hr  = score_hr(d.hr);
    // NO sbp for infant form
    var tmp = score_temp(d.temperature);
    var av  = score_avpu(d.avpu || "");
    var tr  = d.trauma ? 1 : 0;

    var total = mob + rr + hr + tmp + av + tr;

    frm.set_value("mobility_score", mob);
    frm.set_value("rr_score",       rr);
    frm.set_value("hr_score",       hr);
    frm.set_value("temp_score",     tmp);
    frm.set_value("avpu_score",     av);
    frm.set_value("trauma_score",   tr);
    frm.set_value("tews_score",     total);

    return total;
}

// ── DEHYDRATION SPECIAL RULE ──────────────────────────────────────────────────
// Severe Dehydration → RED only when ≥ 2 of these 3 sub-fields are checked
function check_dehydration_alarm(frm) {
    var count = 0;
    if (frm.doc.dehydration_skin_pinch)  count++;
    if (frm.doc.dehydration_lethargy)    count++;
    if (frm.doc.dehydration_sunken_eyes) count++;
    return count >= 2;
}

// ── TRIAGE COLOR DECISION FLOW ────────────────────────────────────────────────
//
// SECTION 1 — Emergency Signs
//   Any alarm checked?              → RED    (stop)
//   ≥2 dehydration sub-fields?      → RED    (stop)
//
// SECTION 2 — TEWS
//   TEWS ≥ 7 OR SpO2 < 92%?        → RED    (stop)
//   TEWS = 5 or 6?                  → ORANGE (stop)
//   TEWS = 0-4                      → continue to Section 3
//
// SECTION 3 — Very Urgent Signs (TEWS = 0-4 only)
//   Any very urgent sign checked?   → ORANGE (stop)
//   None checked AND TEWS = 3-4?   → YELLOW (stop)
//   None checked AND TEWS = 0-2    → continue to Section 4
//
// SECTION 4 — Urgent Signs (TEWS = 0-2, no very urgent signs)
//   Any urgent sign checked?        → YELLOW (stop)
//   None checked?                   → GREEN  (stop)

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
            "Severe dehydration (\u2265 2 signs). Patient requires immediate resuscitation.");
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

    frm.dashboard.set_headline_alert(
        icons[color] + " <b>" + color + " \u2014 " + times[color] + "</b>: " +
        message + " <b>You may now proceed to the orientation desk.</b>",
        indicator[color]
    );

    if (color === "RED" || color === "ORANGE") {
        frappe.show_alert({
            message: icons[color] + " <b>" + color + " \u2014 " +
                     times[color] + "</b><br>" + message +
                     "<br><br>\u26A0\uFE0F <b>Proceed immediately to orientation desk.</b>",
            indicator: indicator[color]
        }, 12);
    }
}

// ── RESTORE COLOR ON FORM LOAD ────────────────────────────────────────────────
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
        // Lock all score fields — calculated automatically
        // NOTE: no sbp_score field on infant form
        var score_fields = [
            "mobility_score", "rr_score", "hr_score",
            "temp_score", "avpu_score", "trauma_score", "tews_score"
        ];
        score_fields.forEach(function(f) {
            frm.set_df_property(f, "read_only", 1);
        });

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
                            method: "healthcare.healthcare.doctype.infant_triage_form.infant_triage_form.sync_to_parent_triage",
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
    // NOTE: no sbp trigger — infant form has no blood pressure field
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
        assign_color(frm);
    },

    // ── SECTION 1: ALARM CHECKBOXES ──────────────────────────────────────
    alarm_not_breathing_weak:      function(frm) { assign_color(frm); },
    alarm_central_cyanosis:        function(frm) { assign_color(frm); },
    alarm_obstructed_breathing:    function(frm) { assign_color(frm); },
    alarm_severe_resp_distress:    function(frm) { assign_color(frm); },
    alarm_cardiac_arrest:          function(frm) { assign_color(frm); },
    alarm_pulse_low_absent:        function(frm) { assign_color(frm); },
    alarm_hemorrhage_uncontrolled: function(frm) { assign_color(frm); },
    alarm_lethargic:               function(frm) { assign_color(frm); },
    alarm_weak_fast_pulse:         function(frm) { assign_color(frm); },
    alarm_cap_refill_3sec:         function(frm) { assign_color(frm); },
    alarm_cold_hands:              function(frm) { assign_color(frm); },
    alarm_convulsion:              function(frm) { assign_color(frm); },
    alarm_coma:                    function(frm) { assign_color(frm); },
    dehydration_skin_pinch:        function(frm) { assign_color(frm); },
    dehydration_lethargy:          function(frm) { assign_color(frm); },
    dehydration_sunken_eyes:       function(frm) { assign_color(frm); },
    alarm_hypoglycemia:            function(frm) { assign_color(frm); },
    alarm_purpuric_rash:           function(frm) { assign_color(frm); },
    alarm_burn_face_inhalation:    function(frm) { assign_color(frm); },

    // ── SECTION 3: VERY URGENT SIGNS → ORANGE ────────────────────────────
    yellow_more_sleep:             function(frm) { assign_color(frm); },
    yellow_focal_neuro:            function(frm) { assign_color(frm); },
    yellow_inconsolable_cry:       function(frm) { assign_color(frm); },
    yellow_floppy_irritable:       function(frm) { assign_color(frm); },
    yellow_chest_pain:             function(frm) { assign_color(frm); },
    yellow_poisoning:              function(frm) { assign_color(frm); },
    yellow_tiny_baby:              function(frm) { assign_color(frm); },
    yellow_burn_10_urgent:         function(frm) { assign_color(frm); },
    yellow_fracture_open:          function(frm) { assign_color(frm); },
    yellow_threatened_limb:        function(frm) { assign_color(frm); },
    yellow_eye_injury:             function(frm) { assign_color(frm); },
    yellow_large_joint_disloc:     function(frm) { assign_color(frm); },
    yellow_severe_mechanism:       function(frm) { assign_color(frm); },

    // ── SECTION 4: URGENT SIGNS → YELLOW ─────────────────────────────────
    green_pitting_oedema:          function(frm) { assign_color(frm); },
    green_cant_drink:              function(frm) { assign_color(frm); },
    green_severe_pallor:           function(frm) { assign_color(frm); },
    green_resp_distress:           function(frm) { assign_color(frm); },
    green_known_diabetes:          function(frm) { assign_color(frm); },
    green_malnutrition:            function(frm) { assign_color(frm); },
    green_diarrhea_vomiting:       function(frm) { assign_color(frm); },
    green_dv_sunken_eyes:          function(frm) { assign_color(frm); },
    green_dv_dry_mouth:            function(frm) { assign_color(frm); },
    green_dv_decreased_urine:      function(frm) { assign_color(frm); },
    green_dv_skin_pinch_slow:      function(frm) { assign_color(frm); },
    green_disloc_finger_toe:       function(frm) { assign_color(frm); },
    green_fracture_closed:         function(frm) { assign_color(frm); },
    green_burn_no_urgency:         function(frm) { assign_color(frm); },
    green_moderate_pain:           function(frm) { assign_color(frm); }
});