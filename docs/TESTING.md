# Testing and Validation Plan

## Gate 0 — Validation purpose

Prove that ineligible bookings are blocked with complete explanations and that valid bookings
respect capacity. Test fixtures are fictional; real user validation is **HUMAN EVIDENCE PENDING**.

## Gate 1 — Test basis

Gate 1's FR table is the requirements-to-tests traceability matrix. Targets are local decision
speed <2000 ms, complete reason set, all 13 checks enforced twice, no overcapacity under two
concurrent requests, no partial writes and correct role/ownership boundaries.

## Gate 2 — Strategy and isolation

Unit: hand-built interval scan and evaluator cases. DB integration: schema constraints, direct
SQL, rollback, capacity counts. HTTP integration: Flask test client checks forms/roles/CSRF and
business decisions. End-to-end: real running server + stdlib urllib, three roles and changed data.

Each GymTests case copies a fresh seeded baseline into a temporary directory. The suite never
opens the student's working gym.db. Fixtures: 22 students, 5 slots, 20 initial confirmed bookings,
including 19/20 and 1/1 slots. IDs are known only within those fixtures. KPI runs its own isolated DB.

## Gate 3 — Test cases

| Test group / method | Input / precondition | Expected |
|---|---|---|
| test_valid_booking | Active student 1, available #2 | confirmed, empty reasons |
| test_inactive_student | active=0 | R01 |
| test_incomplete_profile | empty phone | R02 |
| test_expired_membership | student 2 expired | R05 |
| test_inactive_membership / test_missing_membership | inactive / absent row | R03 / R03,R04,R05 |
| test_membership_not_started | starts tomorrow | R04 |
| test_membership_slot_date_covered / test_membership_exact_boundary | ends today / covers tomorrow inclusively | R05 / allowed |
| test_restricted_student | hold=1 | R06 |
| test_available_slot | empty #2 | R09 absent |
| test_capacity_19_20_and_20_20 | last place then retry | first allowed, second R09 |
| test_full_slot | #4 1/1 | R09 |
| test_duplicate | second same slot | R10 |
| test_conflicting_booking | #2 then overlapping #3 | R11 |
| test_adjacent_slots_allowed | #1 then #2 | both allowed |
| test_conflict_algorithm_unit | overlap, adjacency, another date | only actual overlap ID |
| test_all_reasons_stored_and_shown | blocked student on #4 | exact R01,R02,R03,R05,R06,R09 stored/shown |
| test_invalid_foreign_key | rejected row for missing student | FK exception |
| test_invalid_capacity | 0,-1,201,1.5 | CHECK exception |
| test_invalid_dates_times | bad date, 25:00, reversed interval | CHECK exception |
| test_cancellation_reopens_capacity / test_cancel_ownership | own / another student's ID | reopen / no update |
| test_roles_and_private_history | student/coordinator/admin routes | role-specific access and data |
| test_csrf_and_wrong_password | no token, wrong password | refuse |
| test_direct_request_rechecks_rules | forged student_id/status form data | authenticated blocked student still refused |
| test_direct_database_bypass / test_database_update_bypass | direct invalid confirmed INSERT / promotion UPDATE | R01 exception |
| test_all_rules_database_depth | each R01–R13 independently invalidated | Python reason + database refusal |
| test_rule_parameter_change | daily limit 1 then 2 | second booking blocked then allowed |
| test_policy_period_overlap_and_missing | duplicate period / no policy | DB exception / R12 |
| test_capacity_reduction_and_time_edit | below occupancy / move booked slot | refusal; equal occupancy allowed |
| test_transaction_rollback | successful first statement then invalid capacity | no partial booking |
| test_concurrent_last_place | two threads, separate DB connections, one free place | exactly one success |
| test_admin_forms / test_admin_invalid_input_no_partial_write | valid edits / bad membership status | saved / both updates rolled back |
| test_inactive_and_past_slots | inactive / past date | R07 / R08 |
| test_missing_slot_rollback | slot 999 | ValueError, no open transaction |
| test_rejection_shape_constraint | rejected row with [] | CHECK exception |
| test_html_escape_and_sql_injection | script-looking name, SQL-looking username | HTML escaped; no login bypass |

Run `python tests.py`. The actual output is evidence/test_results.txt. This plan is not the result.
Run `python evidence/db_bypass_demo.py` for visible direct-SQL exceptions.
Run `python evidence/verify_http.py` for actual server requests and captured HTML.

## Gate 4 — Regression and KPI protocol

After any schema or rule edit, rerun the full suite; paired Python/SQL logic can drift. Record
actual failure, cause and fix before declaring a regression resolved. Do not invent a failing run.
The final suite and HTTP outputs in evidence are from executed commands, not assumed passes.

KPI protocol: after seeding, evaluate eligible student 1/slot 2 100 times with perf_counter; report
mean/max milliseconds. Separately compare the blocked fixture's complete expected ID set against
actual reasons. Denominator is one multi-failure record, not six independent records. The 13-rule
depth claim is supported by the isolated Python+SQL cases in the successful suite. Environment is
recorded in environment.json. Authentication hashing and network latency are outside this KPI.

Remaining human acceptance: keyboard/mobile/browser usability, actual faculty observation,
stakeholder criteria, mentor approval and supported OS testing beyond the recorded Linux run.
