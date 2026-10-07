# Defect Log and Root Cause Analysis

## Gate 0 — Evidence policy

Only actual observed failures are defects here. Hypothetical risks and deliberate invalid-input
cases are not represented as historical bugs. Do not copy the hall-ticket example's date bug.

## Gate 1 — Severity and acceptance

High: prevents running or permits an invalid booking. Medium: incomplete reason or wrong role/data.
Low: presentation issue. Each actual major defect needs symptom, investigation, cause, fix and retest.

## Gate 2 — Risks addressed by design (not discovered defects)

Last-place race -> transaction + trigger. First-failure-only response -> full reason collection.
Stale occupancy -> derive COUNT. Form bypass -> server and DB checks. These were design concerns,
not claims that a previous version failed. Store future actual team defects below with real dates.

## Gate 3 — Actual issue D-001

| Field | Actual observation |
|---|---|
| Date | 2026-10-06 |
| Severity / category | High setup blocker / environment |
| Symptom | `python app.py --init-db` raised ModuleNotFoundError: No module named 'flask' |
| Investigation | Default Python and supplied runtime Python initially lacked Flask; an initial user-site installation did not make it available to the later invocation |
| Root cause supported by evidence | The interpreter used to run the application did not have a visible Flask dependency. The precise persistence behavior of that initial user-site install was not established |
| Fix | Created workspace .venv; installed requirements with .venv/bin/python -m pip; used that exact interpreter to initialize/run/test |
| Prevention | START_HERE documents virtual environment and interpreter-specific installation commands; no bare pip guidance |
| Actual retest | Database initialization succeeded; 43 tests and 24 real HTTP checks passed |
| Status | Resolved for the recorded virtual environment |

The original application test run passed all 40 tests. The registration revision passes 43 tests. No functional defect was observed in that run.
This is not proof there are no unknown bugs. Human acceptance and other OS validation are pending.

## Gate 4 — Regression and future log

The final rerun results live in evidence/test_results.txt and http_results.json. A regression run
rechecks behavior; it need not falsely claim an earlier failing functional test.

For real future defects, fill: ID; date; symptom; reproducible steps; expected/actual; affected FR;
engine; investigation; root cause; exact fix; regression test; observed result; owner and reviewer.
All future entries and student-authored RCA are **HUMAN EVIDENCE PENDING** until performed.
