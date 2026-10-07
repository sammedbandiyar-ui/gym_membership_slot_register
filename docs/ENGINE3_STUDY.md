# Engine 3 Study — Interface & Access

Owner: Member 3 (name/USN pending). Read app.py and templates/.

## Basic questions

**What is Flask doing?** Routing HTTP requests, managing sessions and rendering HTML from Python data.

**Why three roles?** Students book/cancel, coordinators review, admins maintain rules and records.

**What is server-side validation?** Python checks the submitted request even if browser checks were removed.

**Where are passwords stored?** As Werkzeug-generated hashes in account.password_hash, not plaintext.

## Apply questions

**Trace POST /book/2.** Check CSRF -> role -> session student ID -> db.book -> render confirmation or all reasons.

**How is cancellation ownership checked?** SQL matches booking ID, current student ID and confirmed status together.

**How is an admin value validated?** Parse date/integer, check range/order, write transactionally; DB constraints also apply.

**Show coordinator access.** Members and decisions succeed; /admin/rules returns 403.

## Analyze questions

**Can posting student_id=1 bypass the blocked student's status?** No; the route takes identity from the logged-in account.

**What does CSRF prevent?** A forged cross-site mutation without the session's form token. It does not replace role checks.

**Why return 409 for a blocked booking?** The request is understood but conflicts with the current booking rules.

**What happens on restart?** Default signing key changes, so sessions need login again; an environment key can persist them.

## Decision questions

**Why no JavaScript?** Server-rendered forms meet the requirements and are easier to understand and test.

**Why not hide unavailable buttons as protection?** Hiding buttons is not authorization; direct POST requests still need all checks.

**Why Flask's development server?** This is a local classroom demo; public deployment is outside this package's scope.

**How does registration work?** /register creates only a student account and profile; admin activates membership before booking.

## 2–3 minute speech (about 280 words)

My engine is Interface and Access. It connects the user to the rule and database engines using
Flask routes, HTML templates and CSS. There is no JavaScript framework, external service or cloud
component. The application runs locally and keeps the request flow easy to explain.

The three roles have different responsibilities. A student sees their own profile, membership
and slots, submits a booking, reads every rejection reason and cancels their own confirmation.
A coordinator sees members, availability and booking decisions. An admin also edits membership,
student status and holds, creates or edits slots, sets capacity and maintains dated rule values.

Login compares the submitted password with a stored hash. A signed session identifies the
account. On each request, the server reloads the account and checks its role. Mutating forms
also include a CSRF token. The server verifies that token before the route can change data.
These checks are complementary: a correct token does not grant an admin role.

For a booking request, the server derives the student ID from the session. It ignores any
student ID or decision status someone tries to add to the form. The booking service then runs
all eligibility checks inside a transaction. I render either the confirmation or the complete
reason list. A rule refusal returns HTTP 409, while an unauthorized role receives 403.

For admin forms, dates, times, flags and numeric values are validated again on the server.
Database constraints are the final guard. Templates escape displayed values to avoid treating
profile text as executable HTML.

I will demonstrate all three roles, a direct request refusal and an admin data edit. Automated
live HTTP checks exercised these flows against a running Flask server. Manual usability review
and other operating-system checks remain pending, so I will not claim those were already done.
