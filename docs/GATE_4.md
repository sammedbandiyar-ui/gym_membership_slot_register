# Gate 4 — RCA, Integration, Final Validation & Release

S6→S7 · Sprint 3 · weeks 12–14 · 10 marks · CO5. Prepared 2026-10-06.
Software package prepared; college release/clearance is **HUMAN EVIDENCE PENDING**.

## RCA and regression

See DEFECT_LOG.md. Actual setup issue D-001: the initial default Python environment could not
import Flask. Installing and running in an explicit local virtual environment resolved it.
The first 40-test application run passed; no fictional functional failure is invented to make
an RCA look more impressive. The suite is rerun for final regression evidence. Negative tests
are deliberate invalid inputs, not claims of previously discovered defects.

## End-to-end validation

`evidence/verify_http.py` starts Flask against a temporary database, uses cookie-bearing HTTP
requests with real CSRF tokens, checks all three roles, creates and edits slots, repairs a blocked
member, and proves a rule change without code. All 24 assertions passed in the packaged run.
It shuts down its own server. `http_results.json` and `server_log.txt` are raw evidence.
Manual browser usability, actual stakeholder acceptance and faculty observation remain pending.

## Final KPI comparison

| KPI | Target from Gate 1 | Observed packaged evidence |
|---|---|---|
| Reason completeness | 100% of fixed blocked fixture records | 1/1 record; all 6 expected IDs present |
| Enforcement depth | 100% of R01–R13 in both layers | 13/13 individually tested; full suite passed |
| Decision speed | Each of 100 local evaluations <2000 ms | See exact measured mean/max in kpi_results.json |
| Last-place concurrency | Exactly one of two succeeds | test_concurrent_last_place passed |
| Transaction atomicity | No partial failed writes | test_transaction_rollback and admin rollback passed |
| Role/ownership | All defined forbidden test actions blocked | Role, CSRF, cancellation and live HTTP checks passed |
| Automated suite | Zero failures/errors | 43 tests passed |
| Live HTTP | All scripted assertions pass | 24/24 passed |
| Rule change | Same request changes outcome by data edit only | daily limit 1 -> 2, blocked -> confirmed |

Counts describe tested cases, not an unbounded correctness proof. No production throughput or
field KPI is asserted. The final measured timestamp and environment are stored with evidence.

## Technical report and final Integration Map

COLLEGE_REPORT.md joins Gate 0–4, sources, requirements, implementation, results, limits and
handover. INTEGRATION_MAP.md contains final file/symbol/test pointers for every subject.
START_HERE.txt is the release runbook. Snapshot DB is dated; fresh initialization creates tomorrow's demo.

## Four-member ownership (proposed, not verified contribution)

| Member placeholder | Engine | Required individual demonstration |
|---|---|---|
| Member 1 — name/USN pending | E1 Data & Integrity | Trace a FK, explain a trigger, run bypass refusal and rollback |
| Member 2 — name/USN pending | E2 Logic & Rule | Trace overlap comparisons, all reasons, O(b+r), dated parameter |
| Member 3 — name/USN pending | E3 Interface & Access | Trace request/session/CSRF/role, show each screen and direct request check |
| Member 4 — name/USN pending | E4 Testing & Validation | Explain FR-to-test link, run suite/KPI, defend RCA and evidence limits |

All members must understand integration and explain code they submit. Actual authorship,
contributions, individual viva and version-control history are **HUMAN EVIDENCE PENDING**.

## Rule-change test procedure

At fresh state, admin sets max_daily_bookings=1 for tomorrow. `aarav` books #2, then attempts #5:
R13. Admin changes only the stored value to 2, keeping validity dates. Same request for #5 succeeds.
Inspect booking.policy_snapshot to see the decision's original policy. No Python, SQL schema or HTML
source is edited. Existing confirmed bookings are not cancelled when the parameter becomes stricter.

Assessment A1 RCA (2); A2 regression (1); A3 integrated E2/E1/E3 verified by E4 (2);
A4 KPI comparison (1); A5 report/map/individual ownership (3, individual demonstration pending);
B1 data-only rule change (1). Total 10. Three/four-engine wording still requires mentor confirmation.
