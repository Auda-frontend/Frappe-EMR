# eBuzima UI Restyle Notes

## Scope and current state

- Project checkout: Healthcare app at the repository root; Frappe app name is `healthcare`, app title is `Rwanda EMR`.
- This step maps the Patient Encounter (OPD consultation) customization sources only. No UI changes were made.
- The live site's database was not inspected. Manual database-only changes and deployed-site visibility may differ from this repository.
- The `docs/` directory and this notes file did not exist before this step.

## 1. Owning app, hooks, and patches

The eBuzima/Rwanda customizations are in this Healthcare fork, not a separate app folder. Relevant code is under `healthcare/healthcare/`; app configuration is in `healthcare/hooks.py`.

Relevant entries in `healthcare/hooks.py`:

- `app_include_js = "healthcare.bundle.js"` is active.
- `app_include_css` is commented out.
- `doctype_js` maps only `Sales Invoice` to `public/js/sales_invoice.js`; there is no Patient Encounter `doctype_js` registration.
- `doctype_list_js` is commented out; there is no Patient Encounter list hook there.
- Fixtures include all `Custom Field` and `Client Script` records, Healthcare-module `Print Format` and `DocType` records, plus a filtered DocType fixture.
- `after_install` calls the Rwanda OPD installer (which also runs the consultation installer).

Patient Encounter-related patches listed in `healthcare/patches.txt`:

- `migrate_rwanda_phase_b_opd`
- `migrate_rwanda_opd_workflow`
- `migrate_rwanda_queue_department_fix`
- `migrate_rwanda_consultation`

These patches re-run the corresponding installers and/or apply OPD workflow data fixes.

## 2. Patient Encounter scripts, styles, fields, and Property Setters

### Scripts

- `healthcare/healthcare/doctype/patient_encounter/patient_encounter.js`
  - Standard DocType form script. It includes the Rwanda OPD script below and also registers Patient Encounter handlers.
- `healthcare/healthcare/doctype/patient_encounter/patient_encounter_rw_opd.js`
  - Rwanda OPD form handlers for queue/consultation UX, patient history prefill, and triage summary.
- `healthcare/healthcare/doctype/patient_encounter/patient_encounter_list.js`
  - The sole Patient Encounter list script; adds status indicators and queue/orientation buttons.
- `healthcare/fixtures/client_script.json`
  - Exports Client Script records for Patient and Sales Invoice only; there is no Patient Encounter Client Script in this fixture.

### Styles and JSON

- No CSS file specific to Patient Encounter was found. The app's only CSS files are page-specific styles for patient history and patient progress.
- `healthcare/healthcare/doctype/patient_encounter/patient_encounter.json` defines the standard DocType and its standard fields/tabs.
- `healthcare/fixtures/custom_field.json` contains 58 Patient Encounter Custom Field records, including custom tabs and `rw_` fields.
- `healthcare/healthcare/fixtures/custom_fields.json` contains no Patient Encounter records.
- No Property Setter JSON was found.

### Runtime-generated customization

- `healthcare/healthcare/rwanda_opd.py` uses `create_custom_fields(..., update=True)` for OPD fields and calls `apply_opd_ui_labels()`.
- `healthcare/healthcare/rwanda_consultation.py` similarly creates/updates consultation fields; it also repositions follow-up fields and hides older fields/tabs.
- `rwanda_opd.py` creates or updates Property Setter records for field labels/visibility and adds a database Translation from `Patient Encounter` to `Consultation`.
- `rwanda_opd.py` also sets several custom fields as standard filters in the database.
- The source therefore persists custom fields through fixtures and installer code, and Property Setters/Translation through Python-created database records. Patches and after-install setup reapply relevant code-defined changes.

## 3. Tabs and their labels

### Standard DocType tabs

These are `Tab Break` fields in `healthcare/healthcare/doctype/patient_encounter/patient_encounter.json`:

| Fieldname | Label |
| --- | --- |
| `tab_consultation` | Consultation |
| `tab_investigation` | Investigation |
| `tab_final_diagnosis` | Final Diagnosis |
| `tab_treatment` | Treatment |
| `tab_consumables` | Consumables |
| `tab_followup` | General Followup |
| `tab_discharge` | Discharge |

### Custom tabs in the Custom Field fixture

These are `Custom Field` records in `healthcare/fixtures/custom_field.json`:

| Fieldname | Label |
| --- | --- |
| `custom_patient_details` | Patient Details |
| `rw_tab_visit` | Visit & triage |
| `rw_tab_medical_history` | Medical history |
| `rw_tab_consultation` | Consultation |
| `rw_tab_orders` | Orders |
| `rw_tab_discharge` | Discharge & follow-up |

### Additional code-defined tabs

- `healthcare/healthcare/rwanda_opd.py` also defines `rw_tab_visit`, `rw_tab_medical_history`, and `rw_tab_consultation`.
- `healthcare/healthcare/rwanda_consultation.py` creates `rw_tab_items` (Items), `rw_tab_tasks` (Tasks), `rw_tab_followup_detail` (Follow-up), and `rw_tab_history` (History).
- The OPD and consultation installers hide a number of earlier tabs/fields using Property Setters, including `custom_patient_details` and `rw_tab_consultation`. Actual visibility depends on installed database state and whether the installers/patches have run.

There are two distinct fields labelled “Consultation”: the standard `tab_consultation` from the DocType JSON and the custom `rw_tab_consultation` from the Rwanda Custom Field/code. The translation added by `apply_opd_ui_labels()` changes the DocType label `Patient Encounter` to `Consultation`; it does not cause the duplicate tab label.

## 4. Queue messages and buttons

In `healthcare/healthcare/doctype/patient_encounter/patient_encounter_rw_opd.js`, `rw_consultation_setup_desk()`:

- Builds an intro containing `Service: {0}` from `rw_oriented_service` (and may also include department, queue number, and UPID).
- For a Waiting visit, calls `frm.set_intro()` again with “Patient is waiting in the department queue. Click Proceed to attend before entering clinical notes.” That second call replaces the preceding intro in this code path; the source does not intentionally keep both messages visible simultaneously.
- Adds a Patient Encounter form “Department queue” button.

In `healthcare/healthcare/doctype/patient_encounter/patient_encounter_list.js`, the list `onload` adds both “Department queue” and “Patient orientation” buttons. No Patient Encounter form “Patient orientation” button was found.

## 5. Duplicate and potentially conflicting handlers

- `patient_encounter.js` includes `patient_encounter_rw_opd.js`; both files register `frappe.ui.form.on("Patient Encounter", ...)`.
- Both registrations include `onload` and `refresh`, but perform different work: the base file handles standard Patient Encounter form behavior and legacy prefill; the Rwanda file handles OPD status, workflow controls, Rwanda prefill, and triage summary. No identical handler body was found.
- `RW_VISIT_STATUS_COLORS` is declared in both the list script and the Rwanda form script. A runtime name collision cannot be confirmed from these source files alone because it depends on Frappe's script-loading scope.
- The Waiting-state intro replaces the previously set service intro in the Rwanda refresh function.
- No additional Patient Encounter hook or Client Script registration was found in this app's hooks/fixture search.

## 6. Answers and decisions recorded

- Authorized this step to create only this notes file; no UI implementation was authorized.
- Requested a separate read-only comparison with a live site and will provide the site context later. Until then, this map is repository-only and live state is unverified.
- Floating-button behavior: deferred until the form-restyle step.
- List “ID” means Encounter document ID.
- Use standard `service_unit` for service display/filtering, rather than Rwanda `rw_oriented_service`.
- Facility button: Omit the Ministry Of Health facility button from the restyle (confirmed by user).
- For a new Encounter before a patient is selected, keep the standard new-document title.

## Plan

Each area is intended as a separate, small implementation step. No application code has been changed as part of this plan.

1. **List columns and filters**
   - Files: `healthcare/healthcare/doctype/patient_encounter/patient_encounter.json`, `healthcare/fixtures/custom_field.json`, and `healthcare/healthcare/rwanda_opd.py`; add a new migration patch and `patches.txt` entry only if needed to update persisted filters on existing sites.
   - Work: Show the requested list columns, using the Encounter document ID and standard `service_unit`; restrict standard filters to ID, Patient, Full Name, and Service Unit. Stop the installer from re-enabling extra Rwanda filters.
   - Risk: **Medium–high**. Field list/filter properties are persisted and touched by both fixtures and installer code. Existing sites may need an idempotent patch.

2. **List header**
   - Files: `healthcare/healthcare/doctype/patient_encounter/patient_encounter_list.js` and this notes file.
   - Work: Show “Outpatient Consultation” as a list-scoped title and breadcrumb; keep the Department queue and Patient orientation list buttons; hide all list create actions, including the top Add primary action and empty-results create buttons. Omit the Ministry Of Health button. Do not change the DocType name or global Translation.
   - Risk: **Medium**. The breadcrumb label override depends on Frappe v15's rendered breadcrumb DOM; browser-verify it and confirm refresh/navigation do not restore the DocType label. Hiding create actions is client-side only and does not alter server permissions.

3. **Form header**
   - Files: `healthcare/healthcare/doctype/patient_encounter/patient_encounter.py`, `healthcare/healthcare/doctype/patient_encounter/patient_encounter.js`, `healthcare/healthcare/doctype/patient_encounter/patient_encounter_rw_opd.js`, and `healthcare/healthcare/doctype/patient_encounter/test_patient_encounter.py`.
   - Work: Keep the standard title for a new encounter until a patient is selected; make the saved Encounter title the patient's full name; preserve built-in navigation, print, menu, and Save behavior. The Save color is in step 8.
   - Risk: **High**. The backend currently stores a title containing both patient and practitioner; changing it affects document titles outside the form header and requires updating the existing title test.

4. **Tabs**
   - Files: `healthcare/healthcare/doctype/patient_encounter/patient_encounter.json`, `healthcare/fixtures/custom_field.json`, `healthcare/healthcare/rwanda_opd.py`, `healthcare/healthcare/rwanda_consultation.py`, and a new migration patch plus `patches.txt` entry for existing sites.
   - Work: Display, name, and order Patient Details, Consultation, Investigation, Final Diagnosis, Treatment, Consumables, General Followup, and Discharge. Hide or reposition the other tabs reversibly; do not delete tabs or fields.
   - Risk: **High**. Standard and custom tabs are defined in separate sources, and installers currently hide some custom tabs via Property Setters. The patch must apply the desired visibility/order on existing sites.

5. **Patient Details layout**
   - Files: `healthcare/healthcare/doctype/patient_encounter/patient_encounter.json`, `healthcare/fixtures/custom_field.json`, `healthcare/healthcare/rwanda_consultation.py`, and the scoped stylesheet in step 8.
   - Work: Reuse existing demographic fields, show the Patient Details tab, arrange its fields and Connections section, and style read-only fields. Do not create duplicate Connections controls.
   - Risk: **High / pending live-site comparison**. The current JS references `internal_orientation`, `clinical_procedure`, and `nutrition_referral`, but these controls are absent from the repository's DocType JSON and Custom Field fixture. Compare the supplied site's Customize Form/Custom Field state before deciding whether/how to expose or order them.

6. **Queue banner**
   - Files: `healthcare/healthcare/page/department_queue/department_queue.js`, `healthcare/healthcare/rwanda_opd.py`, and the scoped stylesheet in step 8.
   - Work: On the Department Queue page's empty state, show “No one waiting in this department” and a disabled “No one waiting” button. Use standard `service_unit` for queue service display/filter/query as requested.
   - Risk: **High / pending live-site comparison**. The current queue data path filters `rw_oriented_service`, whereas standard `service_unit` is a different field/type. Compare actual site values and queue behavior before changing the query; do not assume a mapping or backfill.

7. **Branding/navbar**
   - Files: `healthcare/hooks.py`, a new navbar asset/script only if supported Frappe branding settings cannot meet the design, and existing assets under `healthcare/public/images/`.
   - Work: Apply the approved branding across the entire Desk. Retain the current Healthcare icon/logo; do not add the Ministry Of Health facility button.
   - Risk: **High**. App-level branding affects all Desk pages, and a custom navbar script can depend on Frappe DOM details. No Ministry/eBuzima image assets were found in this repository; the approved choice is to retain the current Healthcare icon/logo without adding eBuzima text.

8. **Global CSS**
   - Files: a new `healthcare/public/css/ebuzima_ui.css` and `healthcare/hooks.py`.
   - Work: Load the stylesheet but scope page background, list card, form, field tint, and Save-button rules to Patient Encounter list/form only. Use the recorded colors `#0057a3`, `#f9fafa`, and `#c0c6cc`. Navbar styling from step 7 is separately approved for the entire Desk.
   - Risk: **Medium** if selectors remain scoped as specified; **high** if they leak to other Desk pages or depend on unstable markup.

### Decisions for this plan

- List ID means the Encounter document ID; list/service display and filtering use standard `service_unit`.
- “Outpatient Consultation” is list-view-only; do not replace the DocType name translation throughout the Desk.
- A saved Encounter's stored title should be the patient's full name. A new document retains the standard title until a patient is selected.
- The no-waiting message/button belongs on the Department Queue page empty state, not the Encounter form. Change queue service display/filter/query to standard `service_unit`.
- Compare the supplied live site before planning implementation of the Connections controls. The live-site context has not yet been supplied.
- Navbar scope is the entire Desk; retain the current Healthcare icon/logo without eBuzima text. Ministry Of Health facility button is omitted.
- Page/card/field CSS scope is limited to Patient Encounter list/form; the floating-button purpose remains deferred until the form-restyle step.
- List-header choice: use a list-JS-only title/breadcrumb override; keep both queue buttons; hide all list create actions. Do not change the DocType name or global Translation.

## List title and header implementation

- Changed `healthcare/healthcare/doctype/patient_encounter/patient_encounter_list.js`: the Patient Encounter list title and final breadcrumb now read “Outpatient Consultation”; the Department queue and Patient orientation buttons remain; all list create buttons are hidden in the UI. No DocType name, Translation, or Property Setter was changed.
- Validation: `node --check healthcare/healthcare/doctype/patient_encounter/patient_encounter_list.js` and `git diff --check` passed. Browser verification is still required for breadcrumb persistence and button visibility.
- Apply: run `bench build --app healthcare`, `bench clear-cache`, then hard-refresh the Encounter list in the browser.
- Undo: remove the four added statements from the list script; keep the recorded decision/plan history.

## Files touched in this step

- `docs/ui-restyle-notes.md` (created)

## Steps completed

- Read-only repository search and source mapping completed.
- No build, cache clear, migration, or browser verification was run; this was a documentation-only change.
- To undo this step, remove only `docs/ui-restyle-notes.md`.

## Tabs implementation

- Decisions: move Visit & triage and Medical history contents into Consultation; hide the duplicate Consultation tab while keeping HPI visible in standard Consultation; move `consultation_items` into Consumables; keep Final Diagnosis in its existing position; move Tasks into Investigation, Follow-up and Discharge & follow-up contents into General Followup, and History timeline into Consultation. Move and show `codification_table` (Medical Codes) in Consumables. Keep Patient Details hidden until its layout step. No fields or tab-break fields are deleted.
- Implementation: retain original tab-break Custom Fields as Tab Breaks; create distinct Section Break fields and re-anchor content to them. Keep the retained legacy breaks hidden at the end of the form. Reapply visibility, anchors, and field order through the consultation installer and an idempotent migration patch. The Orders tab break remains hidden and is anchored after `amended_from`; its table is separately moved.
- Apply: run `bench migrate`, then `bench clear-cache`; hard-refresh a Patient Encounter and check the tab order and moved field groups.
- Verify: validate the edited JSON/fixture, compile the changed Python files, and run `git diff --check`. Browser verification is required on the Healthcare v15 site; it was not run in this workspace.
- Undo: restore the changed JSON, fixture, installer, patch registration, and notes, then run `bench migrate` and the OPD installer to restore custom-field anchors and visibility. Because the tab migration updates the Encounter `field_order` Property Setter, restore `codification_table` to immediately after `submit_orders_on_save` and set its hidden Property Setter to `1` in the site console; preserve the rest of the current field order and clear the Encounter cache.

### Migration fieldtype correction

- The first tabs migration attempt failed because Frappe v15 does not allow an existing Custom Field's `fieldtype` to change from Tab Break to Section Break. No tab fieldtype changes are required or valid.
- Correction: keep the existing six tab-break fields as Tab Breaks, retain and hide them at the end of the form, and create new, separately named Section Break fields for the moved content. This preserves all existing field definitions and avoids bypassing Frappe validation.
- After applying the correction, retry `bench migrate`, then `bench clear-cache`; verify the Encounter tabs and moved field groups in the browser.

### Duplicate tab visibility correction

- User reported that the duplicate Consultation and Discharge & follow-up tabs still appeared after migration.
- Source cause: their fixture records declared `hidden: 0` and retained visible anchors; hiding relied on runtime Property Setters alone. The live site database was not inspected, so the precise runtime persistence/cache state is unverified.
- Correction: set both fixture records to `hidden: 1` and anchor them after `amended_from`; set the Consultation tab's installer definition the same way; add an idempotent patch that updates both existing Custom Field records, reapplies hidden Property Setters, and clears the Patient Encounter cache. Fieldtypes and data remain unchanged.
- Patient Details finding: its fixture has no insertion anchor and no fields are anchored to it. The installer currently hides it; demographic fields remain in standard Consultation. Requested Connections controls were not found in repository definitions and may be site/database-specific. Keep this for the separate Patient Details layout step; confirm the Connections fieldnames/targets before implementing them.
- Apply: run `bench migrate`, then `bench clear-cache`; hard-refresh the Encounter form and confirm only the intended tabs remain.
- Verify: validate fixture JSON, compile the Python patch/installer, and run `git diff --check`. Browser verification is still required.

### Patient Details layout

- User approved showing the existing `custom_patient_details` tab and moving the existing patient fields into it, in this order: Series, Date, Patient, UPID, Full Name, Gender, DOB, Age, Insurance, Catchment Area, Province, District.
- Mapping decision: show existing `patient_sector` as “Catchment Area”; the repository has no distinct Catchment Area field.
- Leave the existing Connections controls unchanged; their definitions may be site-specific and are not present in the repository.
- Implementation: show the Patient Details tab through the existing Property Setter helper, reorder the existing fields without changing fieldnames or fieldtypes, and set the `patient_sector` label through a Property Setter. A focused idempotent patch reapplies visibility, label, and field order to existing sites.
- Files changed: `healthcare/healthcare/rwanda_consultation.py`, `healthcare/patches.txt`, `healthcare/patches/v15_0/migrate_rwanda_patient_encounter_patient_details.py`, and this notes file.
- Apply: run `bench --site <site> migrate`, then `bench --site <site> clear-cache`; hard-refresh a Patient Encounter and verify that Patient Details is the first tab and contains the listed fields in order, with the existing Connections controls unchanged.
- Undo: revert the Patient Details edits in `healthcare/healthcare/rwanda_consultation.py`, remove `healthcare.patches.v15_0.migrate_rwanda_patient_encounter_patient_details` from `healthcare/patches.txt` and delete its patch file. On the site, restore the prior Patient Encounter `field_order` Property Setter, set the `custom_patient_details` hidden Property Setter to `1`, remove the `patient_sector` label Property Setter (or restore its previous value), then clear cache.
- Verification: run the focused Python syntax and order checks and `git diff --check`; browser verification and live migration remain outstanding.
