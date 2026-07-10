# Copyright (c) 2026, earthians Health Informatics Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, now_datetime, get_fullname


class MedicationDispensing(Document):
    def validate(self):
        """
        Enforces the status rules on every save:
        - Not Available lines cannot be invoiced or paid
        - Not invoiced lines cannot be paid
        """
        for line in self.dispensing_lines:

            # Rule 1: Not Available → force invoiced off, force paid = Not Paid
            if line.availability == "Not Available":
                if line.is_invoiced:
                    frappe.throw(
                        f"Medicine <b>{line.medicine_name}</b> is Not Available "
                        f"in stock and cannot be invoiced."
                    )
                if line.paid_status != "Not Paid":
                    frappe.throw(
                        f"Medicine <b>{line.medicine_name}</b> is Not Available "
                        f"and cannot be marked as paid."
                    )

            # Rule 2: Not invoiced → cannot be marked paid
            if not line.is_invoiced and line.paid_status == "Paid":
                frappe.throw(
                    f"Medicine <b>{line.medicine_name}</b> must be invoiced "
                    f"before it can be marked as Paid."
                )

        # Recalculate overall status on every save
        self.update_overall_status()

        # Recalculate totals on every save
        self.update_totals()

    def update_overall_status(self):
        """
        Recalculates and sets overall_status based on the current
        state of all dispensing lines.
        """
        available_lines = [
            l for l in self.dispensing_lines
            if l.availability == "Available"
        ]

        if not available_lines:
            self.overall_status = "Draft"
            return

        paid_count = sum(1 for l in available_lines if l.paid_status == "Paid")
        pending_count = sum(1 for l in available_lines if l.paid_status == "Pending")
        total_count = len(available_lines)

        if self.collected_status in ("Collected", "Outside"):
            self.overall_status = "Dispensed"
        elif paid_count == total_count:
            self.overall_status = "Fully Paid"
        elif paid_count > 0 or pending_count > 0:
            self.overall_status = "Partially Paid"
        elif any(l.is_invoiced for l in available_lines):
            self.overall_status = "Partially Paid"
        else:
            self.overall_status = "Ready for Billing"

    def update_totals(self):
        """
        Recalculates total_billable, insurance_amount, and copay_amount
        based on current Available lines and their item prices.
        """
        total = 0
        for line in self.dispensing_lines:
            if line.availability != "Available":
                continue
            item_price = frappe.db.get_value(
                "Item Price",
                {
                    "item_code": line.drug_code,
                    "price_list": "Standard Selling"
                },
                "price_list_rate"
            ) or 0
            total += item_price * (line.quantity or 1)

        self.total_billable = total
        coverage = self.insurance_coverage or 0
        self.insurance_amount = round((total * coverage) / 100, 0)
        self.copay_amount = total - self.insurance_amount

    def on_update(self):
        """
        When overall_status changes to Fully Paid:
        - Set pharmacy_queue_status = Waiting
        - Fire real-time notification to pharmacy workspace
        """
        if self.overall_status == "Fully Paid" \
                and self.pharmacy_queue_status == "Not in Queue":

            frappe.db.set_value(
                "Medication Dispensing",
                self.name,
                "pharmacy_queue_status",
                "Waiting",
                update_modified=False
            )

            # Real-time notification to pharmacy desk
            frappe.publish_realtime(
                event="pharmacy_queue_update",
                message={
                    "dispensing": self.name,
                    "patient": self.patient_name,
                    "visit_date": str(self.visit_date),
                    "medicines": len([
                        l for l in self.dispensing_lines
                        if l.availability == "Available"
                    ]),
                    "status": "Waiting"
                }
            )

            frappe.msgprint(
                f"Patient <b>{self.patient_name}</b> added to pharmacy queue.",
                alert=True,
                indicator="green"
            )

        # When collected — set collected_at and collected_by
        if self.collected_status in ("Collected", "Outside") \
                and not self.collected_at:

            frappe.db.set_value(
                "Medication Dispensing",
                self.name,
                {
                    "collected_at": now_datetime(),
                    "collected_by": frappe.session.user
                },
                update_modified=False
            )

# ═══════════════════════════════════════════════════════════════════════
# CALCULATE PRESCRIBED QUANTITY
# ═══════════════════════════════════════════════════════════════════════

def calculate_prescribed_quantity(row):
    """
    Calculates dispensing quantity from Drug Prescription.

    Example:
    Dosage: Once Daily
    Period: 5 Day

    Returns:
    quantity = 5
    """

    quantity = 1

    if row.period:
        try:
            days = int(str(row.period).split()[0])
            quantity = days
        except Exception:
            quantity = 1

    return quantity

# ═══════════════════════════════════════════════════════════════════════
# CALLED FROM PATIENT ENCOUNTER on_submit HOOK
# ═══════════════════════════════════════════════════════════════════════

def create_medication_dispensing(encounter, method=None):
    """
    Auto-creates one Medication Dispensing record when a
    Patient Encounter is submitted. Called from Patient Encounter
    controller's on_submit method.
    """
    # Don't create if no drugs prescribed
    if not encounter.drug_prescription:
        return

    # Don't create a duplicate for the same encounter
    existing = frappe.db.get_value(
        "Medication Dispensing",
        {"patient_encounter": encounter.name},
        "name"
    )
    if existing:
        return

    # Get patient's insurance info
    patient = frappe.get_doc("Patient", encounter.patient)
    insurance_provider = ""
    insurance_coverage = 0

    if patient.get("rw_insurance_provider"):
        ins = frappe.db.get_value(
            "Insurance Provider",
            patient.rw_insurance_provider,
            ["provider_name", "coverage_percentage"],
            as_dict=True
        )
        if ins:
            insurance_provider = ins.provider_name
            insurance_coverage = ins.coverage_percentage or 0

    # Build dispensing lines from drug prescription
    dispensing_lines = []

    for row in encounter.drug_prescription:
        if not row.drug_code:
            continue

        quantity = calculate_prescribed_quantity(row)

        # Check stock availability right now
        availability = check_stock_availability(
            row.drug_code,
            quantity
        )

        dispensing_lines.append({
            "medication": row.medication,
            "medicine_name": row.drug_name,
            "drug_code": row.drug_code,
            "dosage": row.dosage or "",
            "period": str(row.period) if row.period else "",
            "quantity": quantity,
            "availability": availability,
            "is_invoiced": 0,
            "paid_status": "Not Paid",
            "medication_request": row.get("medication_request") or "",
        })
    if not dispensing_lines:
        return

    # Calculate totals
    total_billable = calculate_total_billable(dispensing_lines)
    insurance_amt = round((total_billable * insurance_coverage) / 100, 0)
    copay_amt = total_billable - insurance_amt

    # Create the Medication Dispensing record
    disp = frappe.new_doc("Medication Dispensing")
    disp.patient = encounter.patient
    disp.patient_name = encounter.patient_name
    disp.patient_encounter = encounter.name
    disp.visit_date = encounter.encounter_date
    disp.insurance_provider = insurance_provider
    disp.insurance_coverage = insurance_coverage
    disp.total_billable = total_billable
    disp.insurance_amount = insurance_amt
    disp.copay_amount = copay_amt
    disp.overall_status = "Ready for Billing"
    disp.pharmacy_queue_status = "Not in Queue"
    disp.collected_status = "Not Collected"

    for line in dispensing_lines:
        disp.append("dispensing_lines", line)

    disp.insert(ignore_permissions=True)

    frappe.msgprint(
        f"Medication Dispensing record created: {disp.name}",
        alert=True,
        indicator="green"
    )


# ═══════════════════════════════════════════════════════════════════════
# STOCK AVAILABILITY CHECK
# ═══════════════════════════════════════════════════════════════════════

def check_stock_availability(item_code, qty_needed):
    """
    Checks if the item has enough stock in the pharmacy warehouse.
    Returns 'Available' or 'Not Available'.
    """
    pharmacy_warehouse = get_pharmacy_warehouse()
    if not pharmacy_warehouse:
        return "Not Available"

    available_qty = frappe.db.sql("""
        SELECT SUM(actual_qty)
        FROM `tabBin`
        WHERE item_code = %(item)s
        AND warehouse = %(warehouse)s
    """, {
        "item": item_code,
        "warehouse": pharmacy_warehouse
    })[0][0] or 0

    return "Available" if available_qty >= qty_needed else "Not Available"


def get_pharmacy_warehouse():
    """
    Returns the first warehouse with 'Pharmacy' in the name.
    Adjust this if your warehouse has a different naming convention.
    """
    result = frappe.db.get_value(
        "Warehouse",
        {"warehouse_name": ["like", "%Pharmacy%"]},
        "name"
    )
    return result


# ═══════════════════════════════════════════════════════════════════════
# CALCULATE TOTAL BILLABLE FROM DISPENSING LINES
# ═══════════════════════════════════════════════════════════════════════

def calculate_total_billable(lines):
    """
    Sums the selling price × quantity for all Available lines only.
    Unavailable lines are excluded from billing.
    """
    total = 0
    for line in lines:
        if line.get("availability") != "Available":
            continue
        item_price = frappe.db.get_value(
            "Item Price",
            {
                "item_code": line.get("drug_code"),
                "price_list": "Standard Selling"
            },
            "price_list_rate"
        ) or 0
        total += item_price * (line.get("quantity") or 1)
    return total


# ═══════════════════════════════════════════════════════════════════════
# LEGACY FUNCTIONS (Kept for backward compatibility)
# ═══════════════════════════════════════════════════════════════════════

def validate(doc, method=None):
    """
    Legacy validation function. Delegates to the document's validate method.
    """
    if hasattr(doc, 'validate'):
        doc.validate()


def on_update(doc, method=None):
    """
    Legacy on_update function. Delegates to the document's on_update method.
    """
    if hasattr(doc, 'on_update'):
        doc.on_update()


def update_overall_status(doc):
    """
    Legacy function. Delegates to the document's update_overall_status method.
    """
    if hasattr(doc, 'update_overall_status'):
        doc.update_overall_status()


def update_totals(doc):
    """
    Legacy function. Delegates to the document's update_totals method.
    """
    if hasattr(doc, 'update_totals'):
        doc.update_totals()