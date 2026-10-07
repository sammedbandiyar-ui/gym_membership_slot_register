# Integration Map — v1, v2 and final

These are design maturity labels generated on 2026-10-06, not historical approved versions.

## Gate 0 — v1 concept map

DBMS -> E1 data and integrity; Data Structures & Programming -> E2 all-reason decisions and
interval comparison; Web -> E3 roles and HTTP; SE/SDLC -> E4 tests, requirements and report;
OOP -> reusable RuleEngine and modular responsibilities across integration.

## Gate 1 — requirements map

| Subject | FR / NFR anchor |
|---|---|
| DBMS | FR-03/04/07/10/12; NFR-03/04/05 |
| Data Structures & Programming | FR-04/05/06/11; NFR-01/02 |
| Web Technologies | FR-01/02/08/09/10/11; NFR-06 |
| SE & SDLC | FR-13; all FR acceptance criteria and NFR measurements |
| OOP | FR-04/05/06/13 reusable decisions and fixture class |

## Gate 2 — v2 concrete map

| Subject | Engine | Actual files and symbols | Tables / interface |
|---|---|---|---|
| DBMS | E1 | schema.sql; db.connect, book, cancel, slot_rows, init_database | account, student, membership, gym_slot, booking, rule_value; booking_insert/update, slot_update |
| Data Structures & Programming | E2 | rules.py: RuleEngine.evaluate, RuleEngine.find_conflicts | Interval list, named check list, failure list; allowed/reasons/policy contract |
| Web Technologies | E3 | app.py: create_app; register, login, roles, load_user_and_check_csrf, book_slot, edit_member, edit_slot, edit_rules; templates/*.html; static/style.css | Session-bound role and student ID, POST forms, 200/400/403/404/409/503 responses |
| SE & SDLC | E4 | tests.py: GymTests, measure_kpis; docs/GATE_0..4.md; evidence/verify_http.py | Requirement/test traceability, isolated fixtures, logs, honest approval status |
| OOP | E2 + E4, integration-wide modularity | RuleEngine.__init__/evaluate/find_conflicts; GymTests.setUp/tearDown; create_app encapsulates HTTP lifecycle | Instance owns a DB connection reference; reused from db.book and tests |

## Gate 3 — implemented demonstrations

| Subject | Exact tests / evidence | What to show |
|---|---|---|
| DBMS | test_invalid_foreign_key, test_all_rules_database_depth, test_transaction_rollback, test_concurrent_last_place | Direct insert refusal; show 19/20 boundary and atomic transaction |
| Data Structures & Programming | test_conflict_algorithm_unit, test_all_reasons_stored_and_shown, test_rule_parameter_change | Trace overlap condition and all six failures, no short circuit |
| Web Technologies | test_roles_and_private_history, test_admin_forms, test_direct_request_rechecks_rules; http_results.json | Login each role; admin forbidden to student; forged posted student ID ignored |
| SE & SDLC | test_results.txt, kpi_results.json, TESTING.md, DEFECT_LOG.md | Reproduce tests and explain measured denominators |
| OOP | test_conflict_algorithm_unit and test_valid_booking | Instantiate RuleEngine; reuse logic from service and tests; explain error propagation |

## Gate 4 — final ownership and defense

| Subject | Final artifact | Individual evidence still required |
|---|---|---|
| DBMS | E1 study guide, schema and bypass results | Member 1 explains keys, triggers, transaction boundary |
| Data Structures & Programming | E2 study guide, rules and complexity | Member 2 traces own algorithm on unseen input |
| Web Technologies | E3 study guide and HTTP captures | Member 3 explains session/CSRF/role/server validation |
| SE & SDLC | E4 guide, report, regression logs | Member 4 explains test design, actual RCA, real commits |
| OOP | VIVA_ALL_ENGINES.md and actual classes | Every member explains responsibility and reuse |

No subject is assigned to a disconnected toy program. A single booking passes E3 -> E1 -> E2 ->
E1 -> E3, while E4 verifies that entire path. Version-control history, real ownership and all
faculty decisions remain **HUMAN EVIDENCE PENDING**.
