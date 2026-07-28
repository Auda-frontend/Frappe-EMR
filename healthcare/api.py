import frappe
from frappe.utils import nowdate, nowdatetime


# ═══════════════════════════════════════════════════════════════════════
# PATIENT ENCOUNTER — ON SUBMIT
# Creates Medication Dispensing + notifies billing desk
# ═══════════════════════════════════════════════════════════════════════

def on_encounter_submit(doc, method=None):
    """
    Fires when doctor submits a Consultation.
    1. Creates Medication Dispensing record
    2. Notifies cashier desk in real time
    3. Updates Internal Orientation if one exists
    """
    from your_app.doctype.medication_dispensing.medication_dispensing \
        import create_medication_dispensing

    # Step 1: Create Medication Dispensing
    create_medication_dispensing(doc)

    # Step 2: Notify cashier desk
    frappe.publish_realtime(
        event="billing_desk_alert",
        message={
            "patient":      doc.patient_name,
            "encounter":    doc.name,
            "date":         str(doc.encounter_date),
            "practitioner": doc.practitioner_name,
            "message":      "New patient ready for billing"
        }
    )

    # Step 3: Update Internal Orientation status if exists
    orientation = frappe.db.get_value(
        "Internal Orientation",
        {
            "patient": doc.patient,
            "to_department": ["like", "%Cashier%"],
            "status": ["in", ["Pending", "In Transit", "Arrived"]]
        },
        "name"
    )
    if orientation:
        frappe.db.set_value(
            "Internal Orientation",
            orientation,
            "workflow_state",
            "Arrived",
            update_modified=False
        )


# ═══════════════════════════════════════════════════════════════════════
# TRIAGE — ON SUBMIT
# Routes patient to correct department via Internal Orientation
# ═══════════════════════════════════════════════════════════════════════

def on_triage_submit(doc, method=None):
    """
    Fires when Triage is submitted.
    Creates Internal Orientation record based on triage color.
    RED/ORANGE → Emergency
    YELLOW/GREEN → OPD
    """
    color = doc.rw_triage_category

    destination = {
        "RED":    "Emergency",
        "ORANGE": "Emergency",
        "YELLOW": "OPD Consultation",
        "GREEN":  "OPD Consultation"
    }.get(color, "OPD Consultation")

    priority = {
        "RED":    "Immediate",
        "ORANGE": "Urgent",
        "YELLOW": "Semi-Urgent",
        "GREEN":  "Non-Urgent"
    }.get(color, "Non-Urgent")

    # Create Internal Orientation record
    orientation = frappe.new_doc("Internal Orientation")
    orientation.patient          = doc.patient
    orientation.from_department  = "Triage"
    orientation.to_department    = destination
    orientation.triage_record    = doc.name
    orientation.triage_color     = color
    orientation.priority         = priority
    orientation.oriented_by      = frappe.session.user
    orientation.oriented_at      = nowdatetime()
    orientation.workflow_state   = "Pending"
    orientation.insert(ignore_permissions=True)

    # Notify the destination department
    frappe.publish_realtime(
        event="department_queue_update",
        message={
            "patient":      doc.patient,
            "department":   destination,
            "color":        color,
            "priority":     priority,
            "orientation":  orientation.name,
            "message":      f"New {color} patient arriving from Triage"
        }
    )

    # Show alert to triage nurse
    frappe.msgprint(
        f"Patient oriented to <b>{destination}</b> "
        f"with priority <b>{priority}</b>.",
        alert=True,
        indicator="green" if color in ("GREEN", "YELLOW") else "red"
    )


# ═══════════════════════════════════════════════════════════════════════
# MEDICATION DISPENSING — ON FULLY PAID
# Notifies pharmacy desk and creates pharmacy orientation
# ═══════════════════════════════════════════════════════════════════════

def on_dispensing_fully_paid(doc, method=None):
    """
    Called when Medication Dispensing reaches Fully Paid state.
    Creates Internal Orientation to Pharmacy.
    """
    if doc.overall_status != "Fully Paid":
        return

    # Check if pharmacy orientation already exists
    existing = frappe.db.exists(
        "Internal Orientation",
        {
            "patient":        doc.patient,
            "to_department":  "Pharmacy",
            "triage_record":  ["!=", ""],
        }
    )
    if existing:
        return

    # Create orientation to pharmacy
    orientation = frappe.new_doc("Internal Orientation")
    orientation.patient         = doc.patient
    orientation.from_department = "Billing"
    orientation.to_department   = "Pharmacy"
    orientation.priority        = "Normal"
    orientation.oriented_by     = frappe.session.user
    orientation.oriented_at     = nowdatetime()
    orientation.workflow_state  = "Pending"
    orientation.notes           = (
        f"Medications paid. Dispensing ref: {doc.name}"
    )
    orientation.insert(ignore_permissions=True)

    # Notify pharmacy desk
    frappe.publish_realtime(
        event="pharmacy_queue_update",
        message={
            "patient":     doc.patient_name,
            "dispensing":  doc.name,
            "medicines":   len([
                l for l in doc.dispensing_lines
                if l.availability == "Available"
            ]),
            "message":     "Patient fully paid — ready for dispensing"
        }
    )