# Gate 1 — Requirements Baseline

S1 · weeks 3–4 · 10 marks · CO2. Prepared 2026-10-06.
This is a proposed baseline; historical approval and stakeholder sign-off are **HUMAN EVIDENCE PENDING**.

## Functional requirements, needs, acceptance and tests

| ID | Stakeholder need / requirement | Measurable acceptance criterion | Implementation | Test in tests.GymTests |
|---|---|---|---|---|
| FR-01 | All users: login and role isolation | Correct password opens assigned role; wrong password does not; unauthorized protected action returns 403 | login, roles in app.py | test_roles_and_private_history; test_csrf_and_wrong_password |
| FR-02 | Student: see profile and membership | Own USN, phone, status, hold and membership dates visible; no other student's history | dashboard, bookings | test_roles_and_private_history; live Student dashboard check |
| FR-03 | All roles: see slot availability | Display date, times, capacity and confirmed count; rejected/cancelled rows do not count | db.slot_rows | test_available_slot; test_cancellation_reopens_capacity |
| FR-04 | Student: eligible booking | All R01–R13 pass, exactly one confirmed row written | db.book, RuleEngine.evaluate | test_valid_booking; test_membership_exact_boundary |
| FR-05 | Student/coordinator: understand rejection | Every failing ID/name/message on screen and stored; no capacity consumed | evaluate, decision.html, booking.reasons | test_all_reasons_stored_and_shown |
| FR-06 | Student: no duplicate/overlap | Same slot blocked; any overlapping same-date slot blocked; adjacent slots allowed | find_conflicts, booking triggers | test_duplicate; test_conflicting_booking; test_adjacent_slots_allowed |
| FR-07 | Student: cancel own booking | Only own confirmed ID changes to cancelled; one place reopens; repeat has no effect | db.cancel, cancel_booking | test_cancel_ownership; test_cancellation_reopens_capacity |
| FR-08 | Coordinator: review members and decisions | Read all member/status rows, open/full slots, decision reasons; no admin writes | members, bookings, dashboard | test_roles_and_private_history; live Coordinator checks |
| FR-09 | Admin: update profile/status/hold/membership | Valid edits saved together; invalid membership value rolls both edits back | edit_member | test_admin_forms; test_admin_invalid_input_no_partial_write |
| FR-10 | Admin: create/edit slots and capacity | Capacity integer 1–200; positive duration; occupied slots cannot move in time or shrink below occupancy | edit_slot, slot_update | test_admin_forms; test_invalid_capacity; test_capacity_reduction_and_time_edit |
| FR-11 | Admin: change dated rule data | Limit 1 blocks second daily booking, limit 2 permits it; no code edits; no overlapping policy periods | edit_rules, rule_value | test_rule_parameter_change; test_policy_period_overlap_and_missing |
| FR-12 | Faculty/admin: integrity beyond form | Direct invalid confirmed SQL insert/update refused; orphans and invalid values refused | schema.sql | test_direct_database_bypass; test_database_update_bypass; test_invalid_foreign_key |
| FR-13 | Team/faculty: reproducible evaluation | Test runner fails nonzero on failure; writes actual logs; live server checks reproducible | tests.py, evidence/verify_http.py | Complete suite; live HTTP report |

| FR-14 | Visitor: register and sign in | Unique username/USN create student-only account; admin activates membership before booking; duplicate writes roll back | app.register, register.html | test_registration_login_and_activation; test_registration_duplicates_rollback; test_registration_validation_and_csrf |

## NFRs and KPI targets

| ID | Requirement / target | Measurement and scope |
|---|---|---|
| NFR-01 | Decision latency <2000 ms for each of 100 evaluations | perf_counter, local 22-student/5-slot synthetic seed; RuleEngine only, not network/login |
| NFR-02 | All expected reasons in 100% of blocked test records | Fixed multi-failure fixture; expected set compared with actual, plus individual rule tests |
| NFR-03 | 100% of 13 hard admission rules enforced in logic AND database | Isolated failures of each R01–R13; direct confirmed INSERT rejected |
| NFR-04 | No overcapacity in two concurrent last-place attempts | Two connections/threads compete at 19/20; exactly one succeeds |
| NFR-05 | No partial record changes on failed transaction | Failure during two-statement write restores prior state |
| NFR-06 | All tested role/ownership restrictions enforced | Student private history, admin forbidden, coordinator read only, own cancellation |
| NFR-07 | One-command test execution, exit code 0 only if passing | python tests.py on supported environment |

These are project-local acceptance targets, not field measurements. No real-user speed or user
satisfaction is asserted. Limits were documented during this build, not retrospectively dated to week 3.

## Rule catalogue

Every rule below is **hard: block**. Database messages show the rule ID/name; Python adds the
friendly message. Missing student/slot IDs are invalid requests (404), not partial decisions.

| ID | Name and passing condition | Exact failure message |
|---|---|---|
| R01 | Student active: active=1 | Student account is inactive. |
| R02 | Profile complete: existing required name/USN plus exactly 10 ASCII phone digits | A 10-digit phone number is required; contact admin. |
| R03 | Membership active: exists and active=1 | Membership is missing or inactive. |
| R04 | Membership started: starts_on <= today AND slot date | Membership has not started (or is missing). |
| R05 | Membership valid through slot: ends_on >= today AND slot date | Membership expired or does not cover the slot date (or is missing). |
| R06 | No hold: hold=0 | A restriction or hold is present. |
| R07 | Slot active: active=1 | Slot is inactive. |
| R08 | Slot not started: slot date/time strictly after current IST minute | Slot has already started. |
| R09 | Capacity available: confirmed count < capacity | Slot is full. |
| R10 | No duplicate: no confirmed same student/slot | You already booked this slot. |
| R11 | No overlap: no OTHER confirmed same-date interval intersects | This slot overlaps an existing booking. |
| R12 | Policy available: one dated policy covers slot date | No rule value covers this slot date; contact admin. |
| R13 | Daily limit: confirmed same-day count < applicable value | Daily booking limit reached. |

R13 is not evaluated as a failure when policy is missing, because no limit is known; R12 blocks.
Missing membership yields R03/R04/R05, explicitly showing all missing eligibility checks.
Soft rules (warn only): none in this version. Status badges are information, not a separate rule.

## Numeric and time boundary acceptance

| Boundary | Expected |
|---|---|
| Occupancy 19, capacity 20 | Allowed if other checks pass; becomes 20 |
| Occupancy 20, capacity 20 | Block R09; remains 20 |
| Capacity 0 / 1 / 200 / 201 / fractional | Refuse / accept if occupancy allows / accept / refuse / refuse |
| Daily limit 1, count 0 / count 1 | Allow / block R13 |
| Daily limit changes 1 to 2, count 1 | Same request becomes allowed |
| Policy value 0 / 1 / 10 / 11 | Invalid / valid / valid / invalid |
| Membership starts today, ends on slot date | Inclusive dates pass |
| Starts tomorrow / expires yesterday / ends before future slot | R04 / R05 / R05 |
| 06:00–07:00 vs 07:00–08:00 | Adjacent, no overlap |
| 06:00–07:00 vs 06:30–07:30 | Overlap, block |
| Start equals end; end earlier than start | Invalid slot |
| Policy validity exact first/last date | Covered inclusively |

## Use cases / user stories

UC-01 Student books: login -> profile -> select slot -> server checks every rule -> transaction
stores confirmed or rejected decision -> display all reasons -> review history. Alternate: missing
slot 404; occupied slot 409; database busy 503; stale/absent form token 400.

UC-02 Student cancels: choose own confirmed row -> POST -> update status -> capacity derived again.
Wrong owner or already cancelled ID returns 404. No hard delete.

UC-03 Coordinator reviews: login -> members -> slots -> decisions; can explain a rejection but
cannot override one or write admin fields.

UC-04 Admin maintains: login -> member form or slot form or rule form -> validate -> transaction
-> success message. Bad fields keep form and error visible; database constraints remain final guard.

Assessment: A1 FR table (2); A2 NFR table (1); A3 acceptance column (2); A4 stories (1);
A5 stakeholder need column (1); B1 rule catalogue (1); B2 hard/soft statement (1); B3 boundaries (1).
Weakest point: real stakeholder acceptance criteria are awaiting confirmation.
