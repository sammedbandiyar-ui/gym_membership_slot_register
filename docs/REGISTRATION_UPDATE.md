# Registration and gym UI update

## Gate 0 — Scope
FitZone Gym, Tilakwadi, Belagavi is fictional branding. Student self-registration is now in scope. Official college source files remain unchanged.

## Gate 1 — FR-14
A visitor can create a student account using full name, unique username, phone and matching passwords (8–128 characters). New users sign in immediately; membership must be activated by Admin before booking. Duplicate account/profile writes roll back together. No public role selection.

## Gate 2 — Implementation
app.register validates and hashes passwords, creates account and student within one transaction. Student ID / USN is no longer collected or shown. A generated internal reference fills the legacy database column to preserve existing databases; no migration is required. CSRF applies to registration. register.html/login.html and a simple responsive stylesheet provide the public forms.

## Gate 3 — Evidence
Tests: test_registration_login_and_activation, test_registration_duplicates_rollback, test_registration_validation_and_csrf. Live HTTP adds five registration/sign-in/activation checks. Full updated totals: 43 tests and 24 HTTP checks.

## Gate 4 — Upgrade and ownership
Existing databases remain compatible. Preserve gym.db during an upgrade; no reinitialization. Historical first-run logs describe the prior version. Latest test_results.txt and http_results.json describe this revision. HUMAN EVIDENCE PENDING remains applicable to academic approvals and real stakeholders.

