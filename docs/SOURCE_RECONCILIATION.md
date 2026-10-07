# College source reconciliation — mentor confirmation required

Read in full before implementation: uploaded 30-slide Student Orientation PPT (including notes),
Word handbook Parts A–C and Quick Reference (all four themes and twenty gate sheets), and
Pasted markdown.md (the project brief). Source copies and text extracts are in source_documents/.
PPT slides carry 30 September 2026. This package was prepared 6 October 2026, not across fourteen weeks.

## Gate 0 — Authority, theme and ownership

- PPT slides 1, 5, 8, 29: four engines, four members. Word Part A and all gate identity blocks:
  three engines, three member fields; Software Engineering explicitly not an engine.
- **Resolution for this build:** preserve four engines and Member 4 (Testing & Validation), as
  instructed by the user. **MENTOR CONFIRMATION PENDING** for use of adapted printed sheets.
- Title is explicitly listed as Theme 1 title 14 in Word Part B and PPT slide 11.
- PPT slide 4 lists DBMS, Data Structures & Programming, Web, SE/SDLC, OOP. Word Part A combines
  Programming/OOP and separately lists DSA. Map all concepts; do not drop OOP or programming.
- Stakeholder meetings and problem incidence in the worked examples belong to those examples,
  not this project. Their counts (14 hall tickets, etc.) are not our evidence.

## Gate 1 — Requirement decisions

- Both sources require all failing reasons and numerical boundaries for Theme 1.
- Word B1/B2/B3 adds hard/soft rule classification and validity periods; retained here.
- Proposed local policy: max_daily_bookings=2 (editable, dated), membership valid today and on the
  slot date, IST scheduling, future start only, no midnight-crossing slots. Confirm with mentor/user.
- Soft rules: none; no invented warning requirement. R01–R13 are hard booking checks.
- Existing confirmations are booking-time decisions. Later status/hold changes do not revoke
  them. Actual admission control is out of scope. **MENTOR CONFIRMATION PENDING** on this policy.

## Gate 2 — Architecture and algorithm conflict

| Issue | Current PPT | Word handbook | Implemented handling |
|---|---|---|---|
| Engine count | Four, slides 5/13/28 | Three, Part A and Gate 2 A1 | Four; flag mentor sign-off |
| SE role | Engine 4 | Cross-cutting, not an engine | Engine 4 owns tests/report; SE also spans gates |
| Algorithm | One hand-built structure OR algorithm, slide 4/5 | Five-area table says non-trivial structure; engine row allows structure OR algorithm | Hand-built interval scan plus all-reasons evaluation; justify complexity; mentor confirms sufficiency |
| Rule validity | Table and applies-from date, slide 15 | Table with validity period, Gate 2 B1 | Inclusive valid_from/valid_to, no overlaps, fail closed when missing |

The algorithm does meaningful work: it compares half-open time intervals, excludes the same slot,
filters dates and returns every overlap. It does not claim Python's list is a student-built data
structure. If the mentor requires a custom structure beyond an algorithm, this remains a rubric
clarification rather than a claim of compliance with a stricter interpretation.

## Gate 3 — Assessment and measured evidence

Word Gate 3 A1–A3 assigns 2 marks to each of three engines; the PPT requires all four working.
Keep the published 15-mark total and original row IDs. Add Engine 4 evidence as a supplemental
unscored row; mentor decides distribution. Do not invent a fourth 2-mark allocation.
Word Gate 3 A5 requires multi-week commits by all members: **HUMAN EVIDENCE PENDING**.
Theme 1 KPI interpretations agree: all reasons, logic+database, rule change without code.

Other-theme differences were read but do not govern this project: Word Theme 2 uses indexed
measurements at three sizes and top-10 relevance >=70%; PPT slides 17–18 uses a 20-search fixed
set and search accuracy >=80%, with a top-5 example. These should also be clarified if switching
from Theme 1; no search-system KPI is imported into this register.

## Gate 4 — Release is not college clearance

Word Gate 4 A3 refers to three integrated engines; use four in the evidence pointer and flag
mentor confirmation. Both sources use Gate 0–4 marks 5/10/10/15/10 = 50 and stages S0–S7.
No actual gate decision, faculty mark, signature, interview, fourteen-week timeline or individual
viva is asserted. The generated requirements/design are this session's baseline, not historical
pre-code student submissions. PPT slide 30 requires dated documents and an AI-use log; see
HUMAN_EVIDENCE.md. Personal student explanations remain necessary.
