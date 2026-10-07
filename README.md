# Gym Membership and Slot Register

FitZone Gym · Tilakwadi, Belagavi (fictional demonstration gym) · Foundation Integration Course.
Theme 1 — Rule-Checked Records Register. Four members, four engines, five subject areas.

Website: **FitZone Gym · Tilakwadi, Belagavi** (fictional demo). Register at `/register`, sign in, and contact Admin for membership activation. See [registration update](docs/REGISTRATION_UPDATE.md).

Start with **START_HERE.txt** for exact Windows/macOS/Linux setup commands, logins and faculty demo.
A local Flask + SQLite project with server-rendered HTML/CSS and a small JavaScript fees drawer. All data is fictional.

The responsive dashboard separates **Today** and **Tomorrow** using the current IST date,
with each day's slots ordered by start time. Later dates follow, and older dates are
available under **Past dates**. Dates update on page load or refresh; existing slot dates
and reservations are preserved. Cards show AM/PM times, session duration, occupancy and
availability. Closed, inactive and full slots cannot be booked from the dashboard.
Seven daily sessions are generated for today and tomorrow on dashboard visits: 07:00–08:30,
08:30–10:00, 10:00–11:30, 11:30–13:00, 16:00–17:30, 17:30–19:00 and 19:00–20:30.
Each defaults to 20 places. Admins manage repeating times/capacities under **Daily schedule**,
or use **Create slot** / **Manage slot** for a single date. Overrides survive refreshes.

Registration collects email, age and gender. Email is required for new accounts; existing accounts remain valid without an email address. All visible role labels use **Member**. The dashboard
shows membership start/end dates and days remaining. **About the gym** shows contact details;
**Membership fees** opens a side panel. Admins edit the contact details and all three fees
under **Gym settings**. Initial fees: 1 year ₹15,000; 6 months ₹8,000; 3 months ₹5,000.

On first start, `schedule.py` backs up an existing database to `backups/` beside the database,
then adds age/gender, two new tables (`daily_slot`, `gym_settings`) and schedule links.
Existing accounts and bookings are retained. Legacy future slots that do not match the new
timetable are deactivated and shown under **Inactive & previous schedule**; their booking
history is preserved. Booked recurring slots retain their original times when the template
changes. No database reset is needed. Internal legacy member-table/role identifiers remain
compatible with existing databases; they are not shown in the UI.

## Gate 0 — Problem and source authority

Read [Gate 0](docs/GATE_0.md) and [source reconciliation](docs/SOURCE_RECONCILIATION.md).
The uploaded PPT's four-engine structure is preserved. The Word handbook's three-engine
assessment references are flagged, not silently rewritten. No gate has been declared cleared.

## Gate 1 — Requirements

[Gate 1](docs/GATE_1.md) gives FRs, measurable NFRs, rule IDs, acceptance criteria and stakeholders.
A member must pass every applicable check; the interface displays every failed rule.

## Gate 2 — Design

[Gate 2](docs/GATE_2.md) contains the ER diagram, engine architecture, contracts, transactions,
complexity analysis and enforcement map. The original six tables plus two timetable/settings tables. `RuleEngine` provides OOP and a
hand-built interval scan. SQL triggers are required for cross-table checks that CHECK cannot express.

| Engine | Source | Responsibility |
|---|---|---|
| 1 — Data & Integrity | schema.sql, db.py, schedule.py | Eight tables, keys, triggers, parameterized queries, transactions |
| 2 — Logic & Rule | rules.py | RuleEngine, interval scan, all-reasons decisions |
| 3 — Interface & Access | app.py, templates/, static/ | Three roles, forms, CSRF, validation, HTTP |
| 4 — Testing & Validation | tests.py, evidence/, docs/ | Unit/integration tests, live HTTP, KPI, RCA, traceability |

## Gate 3 — Run and demonstrate

```bash
python -m venv .venv
# Activate as shown in START_HERE.txt
python -m pip install -r requirements.txt
python app.py --init-db
python tests.py
python app.py
```

Open http://127.0.0.1:5000. Demo usernames `aarav`, `expired`, `blocked`, `coordinator`, `admin`;
password for each: `DemoGym123!`. See [Gate 3](docs/GATE_3.md).

`--init-db` creates legacy demonstration fixtures and refuses to overwrite a database. The first dashboard visit applies the daily timetable described above.
Tests and live HTTP checks use temporary databases, leaving your main database untouched.
The dated snapshot in evidence is for reference; initialize fresh for use.

## Gate 4 — Validation and handover

See [Gate 4](docs/GATE_4.md), [report](docs/COLLEGE_REPORT.md), [testing](docs/TESTING.md),
[defect log](docs/DEFECT_LOG.md), [Integration Map](docs/INTEGRATION_MAP.md), and the study guides.

43 automated tests and 24 real HTTP checks passed in the packaged run. Raw evidence is in
`evidence/test_results.txt`, `http_results.json`, `kpi_results.json`, and `db_bypass_results.txt`.
HTML files are captured HTTP responses, not screenshots or evidence of manual browser testing.

### Practical limits

This is a local teaching demonstration, not an internet deployment. Passwords are hashed;
session signing keys are random at startup unless GYM_SECRET_KEY is supplied. Restarting logs
users out with the default key. No password-reset UI, admission scanning, attendance,
payments, notification system or permanent admin audit log is included.

Membership, holds and rule changes affect **new booking decisions**. Existing confirmations
are historical approvals, not automatically revoked; no claim is made about gym admission.
Time changes on slots with confirmed bookings and capacity reductions below occupancy are blocked.
Only the owner can cancel a reservation. Ask the owner to cancel before changing a booked slot's time.

Anyone who can alter the database file can also drop triggers: file ownership is a trust boundary.
Every ordinary connection must enable foreign keys. The database independently refuses invalid
confirmed bookings with schema intact; it is not an authorization system for hostile file owners.

**HUMAN EVIDENCE PENDING:** stakeholder study, mentor decisions, marks, signatures, personal
ownership demonstration, historical baselines and multi-week commits. AI assistance is disclosed.

