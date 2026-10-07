# Engine 2 Study — Logic & Rule

Owner: Member 2 (name/USN pending). Read rules.py, especially RuleEngine.

## Basic questions

**What does RuleEngine return?** allowed, reasons, policy and checked; db.book adds booking_id.

**What is a reason?** A dictionary with a stable rule ID, readable name and friendly message.

**What demonstrates OOP?** A RuleEngine instance has one responsibility and a connection; the class is reused by service/tests.

**Are rules hard-coded?** Rule meanings are code; editable numeric daily limit and validity period are table data.

## Apply questions

**Trace 06:00–07:00 against 06:30–07:30.** 06:00 < 07:30 and 06:30 < 07:00: overlap.

**Trace 06:00–07:00 against 07:00–08:00.** Second comparison is false: adjacency is allowed.

**Which failures does blocked/#4 return?** R01, R02, R03, R05, R06, R09 — six named reasons.

**How do you change behavior without code?** Admin changes max_daily_bookings from 1 to 2 for the slot's date.

## Analyze questions

**Why not return on first failure?** The student would fix one issue only to discover another; FR-05 needs the full set.

**Why check membership on the slot date too?** A membership valid today may expire before a future booking.

**What if no policy applies?** R12 blocks; the engine does not invent a fallback limit or assert R13 against an unknown value.

**What is the complexity?** O(b+r) Python time and space, with b previous confirmations and r=13 checks; SQL costs are extra.

## Decision questions

**Why a linear interval scan?** Small per-student records, clear comparisons and simple viva explanation; a tree adds complexity.

**Did you build a custom list structure?** No. We built the overlap algorithm and full-check evaluator using Python lists.

**Does that satisfy the handbook?** The PPT allows an algorithm; Word's stricter non-trivial wording requires mentor confirmation.

**Why maintain Python and SQL checks?** Python explains all failures; database guards ordinary writes that bypass Python. Tests keep them aligned.

## 2–3 minute speech (about 280 words)

My engine is Logic and Rule. It answers a simple question: may this student reserve this slot,
and if not, exactly why? I implemented it in the RuleEngine class in rules.py. The class receives
a database connection but does not write the final decision. That separation makes it reusable
from the booking service and from tests.

The engine reads the student profile, membership, selected slot, previous confirmed bookings
and the policy for the slot date. It checks active status, profile completeness, active membership,
start and end dates, hold status, slot status and start time, capacity, duplicate booking,
overlap, policy availability and the daily limit.

All thirteen checks have IDs and names. The evaluator does not stop after the first failure.
It loops through the complete check list and collects a reason for every failed condition.
An empty reason list means allowed. For the blocked demonstration student choosing the full
slot, six different reasons appear together and are stored in the decision history.

My hand-built algorithm is the interval overlap scan. It visits each previous confirmation.
Two different slots overlap when they are on the same date, the old start is before the new
end, and the new start is before the old end. Adjacent periods are allowed. For b existing
bookings and r checks, the Python work is O(b plus r); the database queries have additional cost.

I chose this scan because the student's booking list is small and its comparisons are easy
to verify on paper. I will trace an overlapping pair and an adjacent pair, then run the unit test.
Finally I will show the daily limit changing in the rule table. The next decision changes
without editing code. The mentor must still confirm the older handbook's algorithm wording.
