var FORM_TYPE    = "maternity";
var DOCTYPE_NAME = "Maternity Triage Form";

// ── ALARM FIELDS ─────────────────────────────────────────────────────────────
// Maternity has all adult base alarms PLUS maternity-specific ones under "Other"
var ALARM_FIELDS = [
    // Airway / Breathing — same as adult
    "alarm_not_breathing",
    "alarm_obstructed_breathing",
    "alarm_severe_resp_distress",
    // Circulation — same as adult
    "alarm_cardiac_arrest",
    "alarm_hemorrhage_uncontrolled",
    "alarm_stab_gunshot",             // Stab/gunshot wound to neck or chest
    "alarm_lethargic",
    "alarm_weak_fast_pulse",
    "alarm_cap_refill_3sec",
    "alarm_cold_hands",
    // Convulsion / Coma — same as adult
    "alarm_convulsion",
    "alarm_coma",
    // Dehydration handled separately via check_dehydration_alarm()
    // Other — maternity-specific (under "Other" section on the form)
    "alarm_prolapsed_cord",           // Prolapsed cord
    "alarm_no_fetal_movement",        // No fetal movement
    "alarm_bandel_ring",              // Bandel ring
    "alarm_abnormal_ctg",             // Abnormal CTG
    "alarm_stab_gunshot_maternity",   // Stab/gunshot wound (repeated under Other)
    "alarm_imminent_birth"            // Imminent birth
];

// ── VERY URGENT SIGNS (YELLOW section) ───────────────────────────────────────
// Maternity yellow signs are COMPLETELY DIFFERENT from adult/child/infant.
// Two sub-groups: Maternal/Fetal AND Medical/Trauma on pregnancy.
// If ANY checked → ORANGE
var YELLOW_FIELDS = [
    // Maternal / Fetal
    "yellow_multipara_active_labour",   // Multi-pares in active labour
    "yellow_uterine_contraction",       // Detectable uterine contraction
    "yellow_rom",                       // Rupture of membranes - ROM
    "yellow_decreased_fetal_movements", // Decreased fetal movements
    "yellow_bleeding_spotting",         // Bleeding > than spotting
    "yellow_preterm_labour",            // Preterm labor < 37 weeks
    "yellow_contraction_planned_cs",    // Active contraction on planned C-section
    "yellow_preeclampsia",              // Signs of Pre-eclampsia
    // Medical / Trauma on pregnancy
    "yellow_altered_mental",            // Altered mental status - acute (< 1 day)
    "yellow_burn_20_urgent",            // Burn over 20% with urgent signs
    "yellow_poisoning",                 // Poisoning / Overdose
    "yellow_fracture_open",             // Fracture open (with skin break)
    "yellow_large_joint_disloc",        // Dislocation of large joint
    "yellow_major_trauma",              // Major trauma
    "yellow_coughing_blood",            // Coughing or vomiting blood
    "yellow_abdominal_trauma_severe_pain" // Abdominal trauma / Severe pain (> 7)
];

// ── URGENT SIGNS (GREEN section) ─────────────────────────────────────────────
// Maternity green signs are COMPLETELY DIFFERENT from adult/child/infant.
// Two sub-groups: Maternal/Fetal AND Medical/Trauma on pregnancy.
// If ANY checked → YELLOW
var GREEN_FIELDS = [
    // Maternal / Fetal
    "green_active_labor",               // Active labor
    "green_miscarriage",                // Miscarriage
    "green_malpresentation",            // Malpresentation
    "green_planned_cs_multiple",        // Planned on C-section / Multiple gestation
    "green_rom_above_6hr",              // Rupture of membranes above 6 hours
    // Medical / Trauma on pregnancy
    "green_cant_drink",                 // Unable to drink or vomits everything
    "green_known_diabetes",             // Unwell with known diabetes
    "green_malnutrition",               // Severe malnutrition / wasting
    "green_fracture_closed_moderate_pain", // Fracture-closed / Moderate pain (5-6)
    "green_burn_no_urgency"             // Burn without urgent signs
];

// ── TEWS SCORING — Maternity form ────────────────────────────────────────────
//
// Maternity TEWS is IDENTICAL to adult TEWS — same table, same ranges,
// same columns including SBP. Confirmed from both the PDF text and the image.
//
// Physical form column layout (same as adult):
// SCORE  | 3    | 2        | 1      | 0       | 1              | 2             | 3
// -------|------|----------|--------|---------|----------------|---------------|------------
// Mob    |      |          |        | Walking | With help/WC   | Stretcher/Imm |
// RR     |      | <9       |        | 9-14    | 15-20          | 21-29         | >29
// HR     |      | <41      | 41-50  | 51-100  | 101-110        | 111-129       | >129
// SBP    | <71  | 71-80    | 81-100 | 101-199 |                | >199          |
// Temp   |      | <35      |        | 35-38.4 |                | >38.5         |
// AVUP   |      | Confused |        | Alert   | React to Voice | React to pain | Unresponsive
// Trauma |      |          |        | No      | Yes            |               |

function score_mobility(v) {
    // Score 0: Walking
    // Score +1: With help / Wheelchair
    // Score +2: Stretcher OR Immobile (both in same column)
    var map = {
        "Walking":                0,
        "With help / Wheelchair": 1,
        "Stretcher":              2,
        "Immobile":               2
    };
    return (map[v] !== undefined) ? map[v] : 0;
}

function score_rr(v) {
    // Score 2 (left): <9
    // Score 0:        9-14
    // Score +1:       15-20
    // Score +2:       21-29
    // Score +3:       >29
    v = v || 0;
    if (v < 9)   return 2;
    if (v <= 14) return 0;
    if (v <= 20) return 1;
    if (v <= 29) return 2;
    return 3;
}

function score_hr(v) {
    // Score 2 (left): <41
    // Score 1 (left): 41-50
    // Score 0:        51-100
    // Score +1:       101-110
    // Score +2:       111-129  (form prints "11-129" which is a typo for 111-129)
    // Score +3:       >129
    v = v || 0;
    if (v < 41)   return 2;
    if (v <= 50)  return 1;
    if (v <= 100) return 0;
    if (v <= 110) return 1;
    if (v <= 129) return 2;
    return 3;
}

function score_sbp(v) {
    // Score 3 (left): <71
    // Score 2 (left): 71-80
    // Score 1 (left): 81-100
    // Score 0:        101-199
    // Score +2:       >199  (no +1 or +3 for SBP)
    v = v || 0;
    if (v < 71)   return 3;
    if (v <= 80)  return 2;
    if (v <= 100) return 1;
    if (v <= 199) return 0;
    return 2;
}

function score_temp(v) {
    // Score 2 (left): <35
    // Score 0:        35-38.4
    // Score +2:       >38.5  (no +1 or +3 for Temp)
    v = v || 36;
    if (v < 35)    return 2;
    if (v <= 38.4) return 0;
    return 2;
}

function score_avpu(v) {
    // Score 2 (left): Confused
    // Score 0:        Alert
    // Score +1:       React to Voice
    // Score +2:       React to pain
    // Score +3:       Unresponsive
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
    var sbp = score_sbp(d.sbp);   // Maternity includes SBP — same as adult
    var tmp = score_temp(d.temperature);
    var av  = score_avpu(d.avpu || "");
    var tr  = d.trauma ? 1 : 0;

    var total = mob + rr + hr + sbp + tmp + av + tr;

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

    // No signs in any section → GREEN
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
        // Maternity includes sbp_score (same as adult)
        var score_fields = [
            "mobility_score", "rr_score", "hr_score", "sbp_score",
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
                            method: "healthcare.healthcare.doctype.maternity_triage_form.maternity_triage_form.sync_to_parent_triage",
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
    // Maternity includes sbp — same as adult
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
        assign_color(frm);
    },

    // ── SECTION 1: ALARM CHECKBOXES ──────────────────────────────────────
    // Adult base alarms
    alarm_not_breathing:              function(frm) { assign_color(frm); },
    alarm_obstructed_breathing:       function(frm) { assign_color(frm); },
    alarm_severe_resp_distress:       function(frm) { assign_color(frm); },
    alarm_cardiac_arrest:             function(frm) { assign_color(frm); },
    alarm_hemorrhage_uncontrolled:    function(frm) { assign_color(frm); },
    alarm_stab_gunshot:               function(frm) { assign_color(frm); },
    alarm_lethargic:                  function(frm) { assign_color(frm); },
    alarm_weak_fast_pulse:            function(frm) { assign_color(frm); },
    alarm_cap_refill_3sec:            function(frm) { assign_color(frm); },
    alarm_cold_hands:                 function(frm) { assign_color(frm); },
    alarm_convulsion:                 function(frm) { assign_color(frm); },
    alarm_coma:                       function(frm) { assign_color(frm); },
    // Dehydration sub-fields
    dehydration_skin_pinch:           function(frm) { assign_color(frm); },
    dehydration_lethargy:             function(frm) { assign_color(frm); },
    dehydration_sunken_eyes:          function(frm) { assign_color(frm); },
    // Maternity-specific alarms
    alarm_prolapsed_cord:             function(frm) { assign_color(frm); },
    alarm_no_fetal_movement:          function(frm) { assign_color(frm); },
    alarm_bandel_ring:                function(frm) { assign_color(frm); },
    alarm_abnormal_ctg:               function(frm) { assign_color(frm); },
    alarm_stab_gunshot_maternity:     function(frm) { assign_color(frm); },
    alarm_imminent_birth:             function(frm) { assign_color(frm); },

    // ── SECTION 3: VERY URGENT SIGNS → ORANGE ────────────────────────────
    // Maternal / Fetal
    yellow_multipara_active_labour:     function(frm) { assign_color(frm); },
    yellow_uterine_contraction:         function(frm) { assign_color(frm); },
    yellow_rom:                         function(frm) { assign_color(frm); },
    yellow_decreased_fetal_movements:   function(frm) { assign_color(frm); },
    yellow_bleeding_spotting:           function(frm) { assign_color(frm); },
    yellow_preterm_labour:              function(frm) { assign_color(frm); },
    yellow_contraction_planned_cs:      function(frm) { assign_color(frm); },
    yellow_preeclampsia:                function(frm) { assign_color(frm); },
    // Medical / Trauma on pregnancy
    yellow_altered_mental:              function(frm) { assign_color(frm); },
    yellow_burn_20_urgent:              function(frm) { assign_color(frm); },
    yellow_poisoning:                   function(frm) { assign_color(frm); },
    yellow_fracture_open:               function(frm) { assign_color(frm); },
    yellow_large_joint_disloc:          function(frm) { assign_color(frm); },
    yellow_major_trauma:                function(frm) { assign_color(frm); },
    yellow_coughing_blood:              function(frm) { assign_color(frm); },
    yellow_abdominal_trauma_severe_pain:function(frm) { assign_color(frm); },

    // ── SECTION 4: URGENT SIGNS → YELLOW ─────────────────────────────────
    // Maternal / Fetal
    green_active_labor:                 function(frm) { assign_color(frm); },
    green_miscarriage:                  function(frm) { assign_color(frm); },
    green_malpresentation:              function(frm) { assign_color(frm); },
    green_planned_cs_multiple:          function(frm) { assign_color(frm); },
    green_rom_above_6hr:                function(frm) { assign_color(frm); },
    // Medical / Trauma on pregnancy
    green_cant_drink:                   function(frm) { assign_color(frm); },
    green_known_diabetes:               function(frm) { assign_color(frm); },
    green_malnutrition:                 function(frm) { assign_color(frm); },
    green_fracture_closed_moderate_pain:function(frm) { assign_color(frm); },
    green_burn_no_urgency:              function(frm) { assign_color(frm); }
});