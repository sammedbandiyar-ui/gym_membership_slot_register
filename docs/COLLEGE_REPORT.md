# Gym Membership and Slot Register — Technical Report

FitZone Gym · Tilakwadi, Belagavi (fictional demonstration gym)
Foundation Integration Course · Theme 1 — Rule-Checked Records Register
Four-member mini project · Prepared 6 October 2026
Student names/USNs, division, team number, mentor and actual approval: **HUMAN EVIDENCE PENDING**.

## Gate 0 — Problem definition and integration objective

The system records gym membership eligibility and limited-capacity slot bookings. It addresses
a proposed manual-register risk: an invalid booking may be accepted or rejected without a full
explanation. Students request/cancel, coordinators inspect and administrators maintain data.
The scope is a local teaching system with fictional data, not gym attendance or payment management.
GATE_0.md documents stakeholders, AS-IS/TO-BE diagrams, scope, feasibility, risks and Integration Map v1.

Official sources: uploaded orientation PPT slides 1–30, especially 4–8, 11–15 and 27–30; uploaded
Word handbook Part A, Theme 1 Part B and Theme 1 Gate 0–4 sheets in Part C; user's complete brief.
Both official files were read before building. SOURCE_RECONCILIATION.md records conflicts. Four
engines follow the current PPT; the old Word sheet's three-engine wording requires confirmation.
CO1 is addressed by the problem/scope/integration analysis; real need validation remains pending.

## Gate 1 — Requirements and rule baseline

GATE_1.md provides FR-01–FR-13, NFR-01–NFR-07, all acceptance criteria, role stories, traceability,
R01–R13 and numeric/time boundaries. All admission rules are hard. An eligible student must be
active, complete, have active membership covering today and the slot, have no hold, choose an
active future slot with capacity, avoid duplicates/overlaps, and obey an effective daily limit.

The central acceptance criterion is both protection and explanation: any failure blocks admission,
and all known failures appear by ID/name/message on screen and in the stored decision. Missing
configuration fails closed. No soft warnings are invented. CO2 is evidenced by these traceable,
measurable criteria. Stakeholder acceptance of the proposed policies remains pending.

## Gate 2 — Architecture, design and trade-offs

E1 Data & Integrity owns schema.sql and db.py. Six tables are account, student, membership,
gym_slot, booking and rule_value. Primary/foreign keys, NOT NULL, UNIQUE, CHECK, simple indexes
and readable triggers protect the records. Dates/times are canonical; current occupancy is a
COUNT of confirmed bookings rather than a separately updated total.

E2 Logic & Rule owns rules.py. RuleEngine uses simple lists, a hand-written interval scan and
an explicit loop that collects all failed checks. Intervals are half-open: end equal to another
start is allowed. Runtime in Python is O(b+r), for b prior bookings and r rule checks. Complexity
claims exclude SQL execution. Class responsibilities and reuse visibly demonstrate OOP.

E3 Interface & Access owns Flask routes, Jinja HTML and CSS. Login uses hashed passwords and a
signed session; every POST needs CSRF. Role and ownership checks are server-side. Browser fields
never decide the student's identity, booking count or confirmation status. No JavaScript is needed.

E4 Testing & Validation owns requirements/test traceability, isolated fixtures, tests, KPI, RCA,
version-control guidance and the report. It is an actual executable verification contribution,
not merely a fourth folder. Software Engineering still influences all gates and engines.

Booking transaction: lock writer -> read/evaluate -> insert confirmed or rejected -> database
rechecks confirmation -> commit. Any error rolls back. A second writer sees updated capacity.
Rejected attempts retain their complete reason list and the applicable policy snapshot. The
SQLite trigger stops at the first DB failure; Python supplies all user-facing reasons.

GATE_2.md contains architecture and ER diagrams, contracts, database details and enforcement map.
CO3 is evidenced by explicit boundaries and design choices. Mentor confirmation of the stricter
Word algorithm wording and assessment adaptation is pending.

## Gate 3 — Implementation and measured results

The runnable implementation was created, Flask installed in a local virtual environment, SQLite
initialized and fictional sample data inserted. The 43-case suite actually ran successfully.
The server was started and checked with 24 actual HTTP assertions spanning all three roles.
Direct SQL attempts refused invalid confirmation, full capacity, orphans and invalid capacity.
Every admission rule was independently invalidated and checked in Python and SQLite.

Evidence includes test_results.txt, environment.json, db_bypass_results.txt, http_results.json,
server_log.txt and captured HTML responses. Tests are rerunnable and do not mutate working data.
All five subject areas connect to the same booking path in INTEGRATION_MAP.md. CO4 is supported
by runnable code plus actual outputs, not a claimed demo. Real team Git history is pending.

## Gate 4 — RCA, validation, limitations and handover

D-001 records the observed missing-Flask setup failure and explicit virtual-environment remedy.
The first functional suite passed; no artificial application defect or historic regression story
was invented. Final regression outputs are included. The parameter change from daily limit 1 to 2
changes the outcome without code edits, demonstrated both by test and live HTTP.

Final KPI values are in kpi_results.json: 100 timed local evaluator calls, 1/1 multi-failure fixture
with the complete six-reason set, and 13/13 admission guards exercised in both layers by the test
suite. Gate 4 compares these to targets. These are synthetic test measurements, not field results.
Authentication/network costs are not included in evaluator timing.

Limitations: no real stakeholder interview, manual browser acceptance, permanent administrative
audit, password-reset UI, deployment hardening or actual admission monitoring. Existing confirmations
are historical booking-time decisions, not continuously revalidated permissions. A database file
owner can alter schema; this is outside form/ordinary SQL bypass protection. SQLite foreign keys
must be enabled for each connection. Python and SQL rule copies require paired regression tests.

Handover: START_HERE.txt gives exact setup, credentials and faculty sequence. Source files, schema,
tests, snapshot data, evidence, gate files, study guides and speeches are packaged together. The
four-member assignment is proposed in GATE_4.md; names, actual ownership, individual viva, mentor
marks, signatures and Gate 0–4 clearance remain **HUMAN EVIDENCE PENDING**.

CO5 is evidenced by test design/execution, measured results, actual setup RCA and transparent
reporting. Software completion does not imply academic clearance. Students must explain and
review every part they submit, as required by PPT slide 30.
