# Engine 1 Study — Data & Integrity

Owner: Member 1 (name/USN pending). Read schema.sql and db.py with this guide.

## Basic questions

**What is a primary key?** A unique identifier for one row, such as booking.id.

**Why six tables?** Identity, profile, membership, slot, decision and policy each have a separate responsibility.

**What is a foreign key?** A reference to an existing parent, such as booking.student_id -> student.id.

**Where is current bookings stored?** It is not a column: count confirmed booking rows for the slot.

## Apply questions

**How do you stop a duplicate?** A partial unique index permits only one confirmed student/slot pair.

**How do you show a bypass refusal?** Run `python evidence/db_bypass_demo.py`; direct SQL raises IntegrityError.

**What happens during cancellation?** Change confirmed to cancelled, record timestamp, derive availability again.

**Where is the transaction?** db.book begins IMMEDIATE before evaluation, then inserts and commits or rolls back.

## Analyze questions

**What if two students see one free place?** Only one writer holds the lock; the next reevaluates after the first commits.

**Why not only CHECK for capacity?** Capacity needs counts from other rows; SQLite CHECK cannot contain a subquery.

**Can an old approval remain after membership is disabled?** Yes; eligibility is a booking-time decision. New attempts fail.

**Can someone with file access defeat this?** Yes, by altering the database/schema. These guards protect ordinary writes, not the file owner.

## Decision questions

**Why SQLite?** A local, small teaching project needs no separate server and still supports transactions/constraints.

**Why use triggers despite keeping it simple?** Cross-table booking integrity must survive skipping Flask and Python.

**Why not delete cancelled bookings?** Keep the decision history and allow a later new confirmation without losing the old record.

**Why snapshot the policy?** A later limit change should not rewrite the policy recorded for the original decision.

## 2–3 minute speech (about 290 words; pause for the demonstration)

My engine is Data and Integrity. Its job is to store the register correctly and refuse invalid
confirmed bookings even when someone skips the web form. The main files are schema.sql and db.py.

There are six tables. Account stores login information and role. Student stores the profile,
active status and hold. Membership stores its active flag and validity dates. Gym slot stores
the date, start and end times, capacity and active status. Booking stores confirmed, rejected
or cancelled decisions. Rule value stores the daily limit and its validity period.

Primary keys identify records. Foreign keys stop references to missing students or slots.
Required fields use NOT NULL, flags and numeric ranges use CHECK, and a partial unique index
prevents two confirmed bookings for the same student and slot. Cancelled and rejected history
can still remain. The current booking count is calculated from confirmed rows, so there is no
separate counter that can become inconsistent.

The important transaction starts before the rule engine reads the records. BEGIN IMMEDIATE
allows one SQLite writer at a time. We evaluate the rules, store the decision and commit. If an
error occurs, we roll back. Therefore two requests cannot both take the final available place.

The database also checks confirmed inserts and updates with readable triggers. We need these
because membership validity, capacity and overlap involve other rows and tables. A CHECK alone
cannot perform those queries. The Python engine gives every reason to the user; the database
only needs one failure to refuse an invalid write.

I will demonstrate a direct SQL attempt using db_bypass_demo.py, then show the exact-capacity
and rollback tests. Our protection assumes the schema is intact and foreign keys are enabled.
A person who owns the database file can alter it, so we do not claim to prevent that. This is
booking integrity, not a complete security system or gym attendance system.
