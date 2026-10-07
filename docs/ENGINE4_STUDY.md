# Engine 4 Study — Testing & Validation

Owner: Member 4 (name/USN pending). Read tests.py, TESTING.md and evidence/.

## Basic questions

**What does this engine produce?** Test design/code, execution evidence, KPI measurements, RCA, traceability and report.

**What is an acceptance criterion?** An observable pass/fail condition for a requirement, such as 20/20 blocking another booking.

**What is regression testing?** Rerun tests after changes to detect broken behavior that previously worked.

**What is RCA?** Explain the actual symptom, investigation, root cause, fix and observed retest.

## Apply questions

**Run the suite.** `python tests.py`; it writes actual results and exits nonzero if tests fail.

**Link an FR to a test.** FR-05 -> test_all_reasons_stored_and_shown -> exact six-ID set in HTML and stored JSON.

**How do you test concurrency?** Two connections/threads request the last place; assert exactly one success.

**How do you measure latency?** Time 100 evaluator calls with perf_counter, report mean/max and dataset size.

## Analyze questions

**Does 100% reason completeness mean all production records?** No. It means 1/1 fixed multi-failure fixture records in that measurement.

**Are test-client checks real network requests?** No; verify_http.py separately starts Flask and uses actual localhost HTTP.

**What defect actually occurred?** Missing Flask in the runtime interpreter; explicit virtual-environment installation resolved it.

**Can tests prove no bugs remain?** No. They provide evidence for specified scenarios; human acceptance remains pending.

## Decision questions

**Why temporary databases?** Repeatable isolation and no damage to the demo or student records.

**Why not invent a functional defect for the report?** That would be false evidence. Report the actual setup issue and honest passing first run.

**Why is Engine 4 separate?** The current PPT assigns one engine per member, with tests/report/version control owned by Member 4.

**Can we claim gate clearance?** Only the mentor can decide after observation; all such claims remain HUMAN EVIDENCE PENDING.

## 2–3 minute speech (about 280 words)

My engine is Testing and Validation. I connect the requirements to evidence that can be rerun.
The main executable is tests.py. The documentation records functional requirements, measurable
limits, acceptance criteria, traceability, defect analysis and the final report.

The suite contains forty-three tests. It covers the valid path and failures such as inactive students,
missing details, membership dates, holds, capacity, duplicate and overlapping bookings. It also
checks foreign keys, invalid values, direct database inserts and updates, role restrictions,
CSRF, cancellation, rollback and simultaneous requests for the last available place.

Each test uses a fresh temporary database copied from a fictional baseline. This keeps results
repeatable and avoids changing the working register. One test deliberately invalidates each of
the thirteen admission rules, confirms the Python reason and attempts direct SQL. This supports
our claim that each booking rule has protection in both logic and the database.

I also run verify_http.py. It starts the actual Flask application and makes real HTTP requests
with cookies and form tokens. Twenty-four checks cover all three roles and the rule change from
one to two bookings per day. HTML responses and server logs are saved as evidence; they are
not screenshots or a claim of manual usability testing.

Our KPI reports identify their denominators. Reason completeness uses one known multi-failure
record with six expected reasons. Timing uses one hundred local rule evaluations on the small
synthetic dataset. These are not real-world gym measurements.

The actual setup issue was a missing Flask dependency in the chosen interpreter. We resolved
it with an explicit virtual environment and reran successfully. We did not invent another bug.
Finally, real interviews, mentor approvals, individual ownership and multi-week commits remain
pending. My job is to make the evidence clear and reproducible, not to replace those human tasks.
