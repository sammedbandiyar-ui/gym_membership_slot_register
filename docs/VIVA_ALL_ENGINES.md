# Viva — All Four Engines and Five Subjects

Use the four ENGINE*_STUDY.md guides for each owner's questions and 2–3 minute speech.
Practice with unseen inputs; memorizing these answers is not a substitute for explaining the code.

## Basic questions

**What is the theme question?** Where is this rule checked, and what stops someone skipping it?

**Answer it for this project.** Forms guide input, Python rechecks and reports all failures, and database triggers/constraints refuse invalid confirmed writes.

**What are the four engines?** Data & Integrity; Logic & Rule; Interface & Access; Testing & Validation.

**Where are all five subjects?** DBMS in schema/transactions, programming and algorithm in rules, Web in Flask/templates, SE in requirements/tests/RCA, OOP in RuleEngine and reusable test fixtures.

**What are the gates and marks?** Gate 0 problem 5; Gate 1 requirements 10; Gate 2 design 10; Gate 3 build/test 15; Gate 4 RCA/integration/release 10. Total 50.

## Apply questions

**Trace an allowed booking through every engine.** E3 authenticates and validates; E1 opens transaction; E2 returns allowed; E1 DB rechecks and commits; E3 displays; E4 verifies the path.

**Trace a rejection.** E2 collects every failed check; E1 stores a rejected row and policy snapshot; E3 shows each reason; E4 compares expected and stored/displayed IDs.

**Show one parameter as data.** rule_value.max_daily_bookings with value and inclusive valid_from/valid_to; lookup uses slot date.

**Show a boundary.** Slot #1 begins at 19/20; one eligible booking succeeds; 20/20 rejects another.

**Explain one SQL query.** Count confirmed booking rows for a slot; cancelled and rejected records consume no capacity.

## Analyze questions

**Where could two users collide?** Both request the final place. BEGIN IMMEDIATE serializes read/check/write; triggers independently enforce capacity.

**Why is only client validation insufficient?** A user can send a POST directly or disable form restrictions.

**What is not protected by the schema?** Web roles/CSRF and hostile owners changing the file/schema; ordinary DB connections need foreign_keys=ON.

**Can a correct rule engine still be unsafe?** Yes, without a transaction two checks may both see a free place; without DB guards direct SQL bypasses it.

**Where could copies drift?** Python and SQL rule predicates; the paired depth test exercises every named rule in both layers.

**What was actually measured?** 43 automated tests, 24 real HTTP assertions and local evaluator timings. No field survey or faculty approval.

## Decision questions

**Why four engines when the Word says three?** The user required the current PPT's four-engine structure. We flagged the assessment conflict for mentor confirmation.

**Why an algorithm instead of a custom tree?** The PPT allows a hand-built algorithm; a linear interval scan is appropriate for a small booking history. Word's stricter wording is pending clarification.

**Why not seven tables for an audit?** booking itself preserves rejected/confirmed/cancelled decisions and policy snapshots; permanent admin change auditing is out of scope.

**Why not automatically cancel after every admin change?** The brief concerns eligibility at booking. Automatic revocation would add policy and history complexity; confirm this explicit boundary with the mentor.

**Would you deploy this publicly unchanged?** No. It is a local classroom demo with shared sample credentials and a development server.

**Can you submit it as your own fourteen-week history?** No. AI assistance and the single-session baseline are disclosed; real student work and mentor evidence must follow.

## Gate 0 -> Gate 4 rehearsal

1. Gate 0: state the rule, affected stakeholder and AS-IS uncertainty.
2. Gate 1: choose an FR and show its acceptance criterion and exact test.
3. Gate 2: draw four-engine flow and trace a table relationship and interval comparison.
4. Gate 3: run the app, demonstrate every failing reason and direct DB refusal.
5. Gate 4: explain actual RCA, rerun regression, change a data parameter and defend KPI denominators.

## One-minute joint opening

Our project is the Gym Membership and Slot Register under Theme 1. A student can reserve a
fixed gym period only after all eligibility conditions pass. We show every failed rule, rather
than making the student discover one problem at a time. We use Python Flask, SQLite and plain
HTML/CSS. The four engines belong to four proposed team members: data integrity, rule logic,
interface access and testing validation. OOP is visible in the reusable RuleEngine class.
We will show a valid booking, the capacity boundary, an overlapping booking, a multi-reason
rejection and a database bypass refusal. Then we will change a limit in the rule table and
show a different outcome without editing code. The source documents conflict on three versus
four engines, so we preserved the current PPT and flagged mentor confirmation. Our supplied
software test evidence is real; academic approvals and actual team history remain pending.
