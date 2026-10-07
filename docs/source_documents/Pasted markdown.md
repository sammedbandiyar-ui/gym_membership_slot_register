I am a final-year BCA student doing a 4-member mini project under the Foundation Integration Course.

I have uploaded the official college mini-project PPT and Word documents containing:

- the four themes,
- the four engines,
- the five subject areas,
- Gate 0 to Gate 4 requirements,
- assessment sheets,
- examples,
- evidence expectations,
- viva expectations.

**Read the uploaded official documents completely before building anything.**

Treat the uploaded college documents as the primary source of truth.

If the PPT and Word file conflict, do not silently choose one. Clearly flag the conflict for mentor confirmation. In particular, preserve the current PPT’s **four-engine structure** even if the older Word gate sheets mention three engines.

---

# PROJECT

**Project Title:** Gym Membership and Slot Register\
**Theme:** Theme 1 — Rule-Checked Records Register\
**Organization:** Department of BCA, KLE Technological University, Belagavi\
**Team Size:** 4 members

Build the **complete integrated runnable project for all four engines**, not only documentation.

Use:

- Python Flask
- SQLite
- HTML
- CSS
- very little JavaScript

Keep the project beginner-friendly, small, easy to run, and easy to explain in viva.

Do not use React, Node.js, Django, external APIs, cloud services, OTP, payment gateways, advanced frameworks, or unnecessary architecture.

---

# SIMPLE PROJECT IDEA

The system should manage:

- gym members,
- membership validity,
- gym time slots,
- slot capacity,
- slot bookings,
- booking eligibility,
- rejection reasons,
- coordinator/admin management.

A **slot** means a fixed gym time period, such as:

- 6:00 AM–7:00 AM
- 7:00 AM–8:00 AM
- 4:00 PM–5:00 PM
- 5:00 PM–6:00 PM

The system should record who booked each slot and whether the slot is full.

---

# MAIN RULE

A student can book a gym slot only if:

1. the student is active,
2. required profile details are complete,
3. gym membership is active and not expired,
4. the selected slot has available capacity,
5. the student does not already have a conflicting or duplicate booking,
6. there is no restriction or hold.

If any condition fails:

- the booking must be blocked,
- the system must show **all failing reasons**, not just the first one,
- important invalid data must also be prevented at the database level where possible.

This project must clearly answer the Theme 1 question:

**“Where is this rule checked, and what stops someone skipping it?”**

---

# USERS

Use three simple roles:

**Student**

- login
- view profile
- view membership status
- view available gym slots
- book a slot
- cancel own booking
- view booking status and rejection reasons

**Coordinator**

- view members
- view bookings
- view full/open slots
- review booking decisions

**Admin**

- manage student status/hold
- manage membership validity
- create/edit gym slots
- set slot capacity
- manage rule values
- view records

---

# KEEP DATABASE SIMPLE

Prefer about 6 tables:

- `account`
- `student`
- `membership`
- `gym_slot`
- `booking`
- `rule_value`

Add another table only if genuinely required.

Use simple:

- primary keys
- foreign keys
- NOT NULL
- UNIQUE
- CHECK constraints
- simple indexes
- transactions where required
- parameterized SQL queries

Avoid unnecessary stored procedures or advanced database features.

---

# MANDATORY FIVE SUBJECT AREAS

The uploaded official PPT requires all five foundational subject areas to be visibly demonstrated in one integrated project.

Do not skip any of them.

## 1. Database Management Systems

Demonstrate through **Engine 1 — Data & Integrity**.

Include:

- tables
- primary keys
- foreign keys
- relationships
- constraints
- transactions
- queries
- data validation
- prevention of invalid records at database level
- one example where an invalid booking/decision is refused even if the form is bypassed

Keep the DBMS code easy to explain.

## 2. Data Structures & Programming

Demonstrate through **Engine 2 — Logic & Rule**.

Include:

- the main eligibility/booking rule
- collect all failing reasons
- one simple hand-built structure or algorithm
- explain why it was chosen
- include a simple complexity note

Keep this as easy as possible while still satisfying the college requirement.

A simple approach such as iterating through a list of rule checks and collecting failure messages is acceptable if it genuinely satisfies the official requirement.

## 3. Web Technologies

Demonstrate through **Engine 3 — Interface & Access**.

Include:

- Flask routes
- login
- role-based access
- Student screens
- Coordinator screens
- Admin screens
- forms
- requests
- server-side validation
- error messages

The server must re-check important rules so a direct request cannot bypass them.

## 4. Software Engineering & SDLC

Demonstrate through **Engine 4 — Testing & Validation**.

Include:

- requirements
- FR IDs
- measurable NFRs
- acceptance criteria
- use cases/user stories
- traceability
- test cases
- unit tests
- integration tests
- defect log
- root cause analysis
- regression testing
- KPI measurement
- final report
- version-control evidence guidance

Do not fabricate real multi-week commits, mentor approvals, stakeholder interviews, or actual gate clearance. Clearly mark those as **human evidence pending**.

## 5. Object-Oriented Programming

OOP must be visible in the integrated project.

Use simple beginner-friendly Python classes/modules with:

- clear responsibilities
- reuse
- basic error handling

Avoid advanced inheritance or design patterns.

A simple `RuleEngine` class is acceptable if it fits the project naturally.

---

# FOUR ENGINES

Build all four engines completely.

## Engine 1 — Data & Integrity

Responsibility:

- database schema
- keys
- constraints
- integrity
- queries
- transactions
- storing decisions safely

Suggested files:

- `schema.sql`
- `db.py`

## Engine 2 — Logic & Rule

Responsibility:

- booking eligibility
- membership validity checks
- slot capacity check
- duplicate/conflict check
- collect all reasons
- algorithm/structure

Suggested file:

- `rules.py`

## Engine 3 — Interface & Access

Responsibility:

- Flask application
- login
- roles
- pages
- forms
- requests
- server-side validation

Suggested files:

- `app.py`
- `templates/`
- `static/`

## Engine 4 — Testing & Validation

Responsibility:

- test plan
- automated tests
- defect log
- RCA
- regression tests
- KPI
- report

Suggested files:

- `tests.py`
- `docs/TESTING.md`
- `docs/DEFECT_LOG.md`
- `docs/COLLEGE_REPORT.md`

---

# IMPORTANT SLOT RULES

Keep slot logic simple.

A slot should have:

- slot ID
- date or day
- start time
- end time
- maximum capacity
- current bookings
- active/inactive status

The system must:

- prevent booking a full slot,
- prevent duplicate booking of the same slot,
- prevent conflicting bookings if two slots overlap,
- prevent booking without valid membership,
- allow cancellation,
- update availability correctly.

Do not make scheduling more advanced than necessary.

---

# GATE 0 TO GATE 4

Structure all project documentation in the **exact Gate 0 → Gate 1 → Gate 2 → Gate 3 → Gate 4 order** from the uploaded college documents.

## Gate 0

Include:

- problem statement
- stakeholders
- AS-IS workflow
- TO-BE workflow
- scope
- out-of-scope
- feasibility
- risks
- Integration Map v1
- one-sentence governing rule

## Gate 1

Include:

- functional requirements with IDs
- measurable non-functional requirements
- acceptance criteria
- use cases/user stories
- traceability
- rule IDs
- conditions
- failure messages
- hard rules vs soft rules
- boundary acceptance criteria for numeric rules such as slot capacity

## Gate 2

Include:

- four-engine architecture
- ER diagram
- keys
- relationships
- constraints
- interface contracts
- inputs
- outputs
- errors
- algorithm/workflow
- complexity note
- Integration Map v2
- rule parameters stored as data
- enforcement location: form / logic / database

Explicitly note that the older handbook may mention three engines, while the current orientation PPT uses four engines. Flag this for mentor confirmation.

## Gate 3

Include:

- all four engines implemented
- tests for each engine
- integration tests
- KPI results
- database-bypass rejection demonstration
- blocked booking showing every failing rule by name

Do not invent real Git commit history.

## Gate 4

Include:

- RCA
- regression testing
- end-to-end validation
- final KPI
- technical report
- final Integration Map
- individual ownership
- rule-change test where a parameter changes in data and behavior changes without editing code

---

# REQUIRED PROJECT STRUCTURE

Create the actual runnable project, preferably:

`gym_membership_slot_register/`

- `app.py`
- `db.py`
- `rules.py`
- `schema.sql`
- `tests.py`
- `requirements.txt`
- `README.md`
- `START_HERE.txt`
- `templates/`
- `static/`
- `docs/`
- `evidence/`

Keep the number of source files small.

---

# SAMPLE DATA

Create fictional sample users for demonstration.

Include at least:

- one student who can successfully book,
- one student with expired/inactive membership,
- one student with incomplete details or restriction,
- one nearly full/full slot,
- one available slot,
- Coordinator account,
- Admin account.

Use clear demo credentials and document them in `START_HERE.txt`.

---

# TESTS

Test at least:

- valid booking
- inactive student
- incomplete profile
- expired membership
- membership not started yet
- restricted student
- available slot
- exact capacity boundary
- full slot
- duplicate booking
- conflicting booking
- invalid foreign key
- invalid capacity
- cancellation
- role access
- direct database bypass attempt
- rule parameter change without code modification

Include boundary tests such as:

- capacity 19/20 → allowed
- capacity 20/20 → blocked

---

# INTEGRATION MAP

Create a clear Integration Map showing:

- all five subject areas,
- corresponding engine,
- actual files,
- actual functions/classes/tables/tests,
- what to demonstrate at each gate.

---

# VIVA PREPARATION

Create:

- `ENGINE1_STUDY.md`
- `ENGINE2_STUDY.md`
- `ENGINE3_STUDY.md`
- `ENGINE4_STUDY.md`
- `VIVA_ALL_ENGINES.md`

Each should contain:

- Basic questions
- Apply questions
- Analyze questions
- Decision questions

Keep answers short and beginner-friendly.

Also create a 2–3 minute speech for each engine.

---

# BUILD AND VERIFY

Do not stop at planning or documentation.

Actually:

1. create all project files,
2. install/check dependencies,
3. create the SQLite database,
4. insert sample data,
5. run the test suite,
6. fix errors,
7. rerun tests,
8. start the Flask application,
9. verify Student flow,
10. verify Coordinator flow,
11. verify Admin flow,
12. verify valid booking,
13. verify blocked booking with all reasons,
14. verify full-slot rejection,
15. verify duplicate/conflicting booking rejection,
16. verify database-level protections,
17. verify all five subject areas are represented.

Do not claim anything was tested unless you actually ran it.

---

# FINAL PACKAGE

When everything is complete, package the entire project into:

**`Gym_Membership_and_Slot_Register_COMPLETE.zip`**

The ZIP must contain all source code, templates, static files, database setup files, tests, documentation, Gate 0–4 evidence files, Integration Map, viva guides, and README.

Include:

**`START_HERE.txt`**

with:

- software required
- exact setup commands
- exact virtual environment commands
- exact dependency installation command
- exact database initialization command
- exact command to start website
- local URL
- Student login
- Coordinator login
- Admin login
- exact faculty demonstration sequence

---

# IMPORTANT INTEGRITY RULE

Do not fabricate:

- real stakeholder interviews,
- mentor approval,
- gate clearance,
- actual signatures,
- multi-week Git commits,
- real-world KPI data that was not measured.

Mark such items clearly as:

**HUMAN EVIDENCE PENDING**