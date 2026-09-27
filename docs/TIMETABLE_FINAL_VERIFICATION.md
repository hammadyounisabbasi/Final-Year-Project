# Admin Timetable Creator: final correction verification

Verification uses the real Admin page in visible Chrome, the actual FastAPI routes,
and an authenticated in-memory backup of the university database. External AI calls
are disabled in acceptance tests to exercise safe offline behavior. Production
table counts are also read directly before and after; no production approval is sent.

Final runs completed successfully: **31 regression tests passed**, the full Chrome
acceptance script exited successfully, and `pip check` reported no broken requirements.
Scanned-PDF and PNG extraction were also run using only the normal `venv` packages,
without adding the test dependency directory to Python's import path.

## Root causes

- The frontend discarded the backend conversation state, losing active facts and edits.
- The old General generator made one one-hour row per course, substituted optional
  teacher defaults, and did not validate weekly credits or global resource conflicts.
- The word `PDF` selected download intent even when the request was file-based generation.
- Attachment review was mandatory, sent messages did not retain attachment cards,
  and resetting the live `FileList` could discard the second and third upload.
- PDF extraction never tried OCR. Spreadsheet extraction removed empty cells,
  shifting table relationships. OCR headers could lose spaces and fail recognition.
- PyMuPDF, RapidOCR, and NumPy existed only in the test dependency directory, not in
  the application's virtual environment. Required runtime packages are now installed.
- Department inference could mistake regeneration wording for a department and let
  old System department mentions override a new target or imply a reference curriculum.
- System candidate validation did not independently enforce final weekly coverage.

## Exact files changed in this pass

| File | Change |
|---|---|
| `backend/backend/app/services/timetable_conversation.py` | New DB-independent structured input, grounded provider extraction, LangGraph conversation, scheduler, validator, edits and partial regeneration. |
| `backend/backend/app/services/timetable_agent.py` | Safe default mode, intent correction, current-scope precedence, mode separation, final validation; obsolete General generator removed. |
| `backend/backend/app/services/timetable_constraints.py` | Practical-room checks, weekly-minute coverage, multi-semester targets, precise database blockers. |
| `backend/backend/app/services/timetable_documents.py` | Scanned-page OCR, OCR row reconstruction, empty spreadsheet cells preserved, expanded archive limits. |
| `backend/backend/app/api/admin.py` | DB-independent attachment facts, safe extraction errors, final coverage recheck at approval. |
| `backend/backend/app/schemas/admin.py` | Bounded conversation-state transport. |
| `requirements.txt` | PyMuPDF runtime dependency. |
| `frontend/Admin_dashboard/timetable-chat.js` | Persistent state, visible sent attachments, safe multi-file processing, current-row downloads, separated approval controls and lazy System options. |
| `frontend/Admin_dashboard/timetable-chat.css` | Cohort headings and attachment wrapping. |
| `frontend/Admin_dashboard/ai-timetable-creator.html` | Conversational and System-scope labels. |
| `tests/api/test_timetable_agent.py` | Updated acceptance expectations, thread-safe authentication fixture, current-System-scope regression. |
| `tests/api/test_timetable_conversation.py` | Conversation, evidence grounding, constraints, credit, global conflict, and edit regressions. |
| `tests/api/timetable_final_browser.py` | Reproducible current Admin browser acceptance workflow and artifacts. |
| `tests/api/TIMETABLE_TESTING.md` | Pointer to this current verification workflow. |
| `docs/TIMETABLE_FINAL_VERIFICATION.md` | This report. |

The pre-existing unrelated working-tree changes were not reverted. No schema,
authentication, Student portal, Teacher portal, exam, or assignment implementation
was changed in this pass. Runtime dependency installation affects `venv/` only.

## Requested verification results

| # | Requested result | Verified evidence |
|---|---|---|
| 1 | Root causes | Listed above, including failures reproduced through the browser. |
| 2 | Exact changed files | Listed above. |
| 3 | Missing-detail conversation | Exact Cybersecurity request asks for semester, course credits and assigned teachers; no immediate preview. |
| 4 | Chat-provided generation | Exact CYB-101 / CSC-101 / MTH-101 fixture produces 10 sessions with the supplied titles and teacher mappings. |
| 5 | Credit hours | 3 + 4 + 3 credits produce 600 weekly minutes. Missing coverage is rejected. |
| 6 | Conflicts | Teacher, room, cohort, cross-semester conflicts and corrupted previews are rejected; valid generated previews pass global validation. |
| 7 | PDF attachment visibility | File card appears before send and remains in the sent user message. |
| 8 | PDF content extraction | A misleadingly named PDF supplies actual course/teacher table content for generation. |
| 9 | Scanned PDF | Image-only PDF goes through OCR and generates a validated timetable. |
| 10 | Image upload/read | PNG, JPG, JPEG and WebP fixtures produce visible cards, OCR text and generated previews. See OCR accuracy limits below. |
| 11 | DOCX | Paragraphs and course-table fixture extracted and scheduled in the browser. |
| 12 | CSV | Course-table and room-list fixtures extracted; CSV participates in the combined-file flow. |
| 13 | XLSX | Course table and separate teacher-assignment workbook extracted and scheduled. Blank-cell regression preserves column positions. |
| 14 | Multiple attachments | `teachers.xlsx`, `courses.pdf`, `rooms.csv` merge into 13 sessions across two semesters. |
| 15 | Follow-up edits | Move CYB-101 to Tuesday, then change “its teacher” to Dr. Farhan; unchanged attachment text cannot undo the edit. |
| 16 | Partial regeneration | Semester 1 rows remain exactly unchanged while Semester 2 is regenerated. Day-only regeneration preserves all other days. |
| 17 | Actual browser PDF | Download event succeeds; saved PDF opens. Export request equals the latest preview rows, all latest row values appear, and a separate download contains all eight semesters. First cohort page visually inspected. |
| 18 | Database counts | Source database and isolated copy retain the counts below. |
| 19 | System mode | Existing CS coverage detected; signed replacement preview and approval controls shown without saving. Missing Software Engineering records block generation. Switching to General clears approval controls. |
| 20 | Remaining limitations | Listed below; no claims of unrestricted natural-language or perfect OCR accuracy. |

| Model | Before | After |
|---|---:|---:|
| ClassSchedule | 218 | 218 |
| StudentTimetable | 4,164 | 4,164 |
| Course | 42 | 42 |
| Teacher | 100 | 100 |
| Enrollment | 1,464 | 1,464 |

These values were checked both in the source database opened read-only and in the
in-memory test copy. Approval persistence and replay/concurrency protection are
tested separately on disposable copies, never on the source database.

## Scheduling policy and limits

One credit equals 60 weekly contact minutes. Sessions are one hour. Lab sessions
occur only when practical hours are explicitly supplied or the course itself is
identified as a lab; credit count alone does not create a lab requirement.
Labs must be identified as labs. Default optional values are Section A, Monday–Friday, 09:00–17:00, and
temporary rooms only when no rooms were supplied. Supplied names, codes, mappings
and room choices are retained. General mode returns `changes: []` and no approval token.

- Local OCR may omit spaces in names or misread low-quality content. Extracted text
  remains editable; arbitrary scans and handwritten documents are not proven accurate.
- Provider failover is verified with controlled responses; grounded prose extraction
  is tested with controlled model output. Live cloud-provider success is not claimed.
- Scheduling uses bounded search, an 18-hour teacher workload cap, and, in General
  mode, a maximum of three consecutive hours. It can request relaxed constraints
  rather than find every theoretically feasible timetable.
- Natural edits support named-course moves, teacher changes with contextual pronouns,
  day availability and scoped regeneration. Ambiguous edits need clarification;
  unrestricted ChatGPT-level understanding is not claimed.
- Room capacity, equipment and detailed production availability are not represented
  by dedicated database tables. System mode uses verified recorded room names and
  existing schedules, and never creates missing inventory or teacher records.
- Browser verification used an authenticated copy of the real database. No production
  timetable was approved or published during this pass.

## Reproduce and inspect

## Capacity-scheduler follow-up

The General/Test capacity failure reported after the final correction pass was
caused by the input parser, not a real room, teacher, or timetable limitation.
Its day-range pattern matched across line breaks, so a bulleted list beginning
with Monday and Tuesday was interpreted as `Monday-Tuesday`. The scheduler then
received only two days (12 slots) for 16 required one-hour sessions.

`timetable_conversation.py` now confines ranges to one line, recognizes
`Available Rooms/Labs`, accepts course codes separated by a dash or whitespace,
and gives four-credit courses four teaching hours unless the source explicitly
provides practical hours. The General/Test planner now uses MRV backtracking,
with a 100,000-node bound, rather than committing greedy first-fit placements.
Hard constraints are section, teacher and room overlap, valid supplied slots,
credit coverage, explicit practical hours, explicit required rooms and teacher
unavailability. Room preference, distribution, daily course repetition and
consecutive teaching remain candidate-order preferences.

The exact Cybersecurity fixture has 16 sessions over Monday-Friday, uses only
the six supplied one-hour slots, includes ICT-101, and validates with no teacher,
room or section conflict. It passes unchanged when course input order is
reversed, ICT-101 is first, or Programming Fundamentals is last. General/Test
tests use a database object that raises if accessed; the scheduler therefore
cannot inherit production schedules or write production data.

Ollama is configured for `qwen2.5:1.5b` with a 90-second cold-model timeout,
15-minute keep-alive and a bounded 768-token response. The application provider
manager completed an actual local request after this change. A provider outage
still leaves deterministic General/Test extraction and scheduling available.

## Agent and retrieval architecture follow-up

The General/Test graph is now `understand → retrieve knowledge → plan request →
respond`. The planner records requested cohorts plus hard and soft scheduling
goals without exposing private reasoning. `timetable_knowledge.py` provides a
provider-isolated embedding interface and a local deterministic embedding index
for extracted timetable text. References are chunked at roughly 900 characters
with 140-character overlap, deduplicated by SHA-256, and retain source filename,
type, session, category, timestamp and chunk identity.

Retrieval is top-k cosine similarity with duplicate removal and optional metadata
filters. It runs only for requests that can benefit from context. It can fill
missing General/Test fields, but cannot overwrite current explicit input or
reviewed structured facts. System-mode retrieval is supporting context only:
the live Department, Course and Teacher records remain authoritative and the
existing approval transaction is the only persistence path.

New regression coverage uses unseen Geoinformatics courses, two sections, a
shared teacher, a file-named reference, and a later provenance-cited teacher
question.

```powershell
venv/Scripts/python.exe -m pip install -r requirements.txt
venv/Scripts/python.exe -m unittest discover -s tests/api -p 'test_timetable*.py' -v
venv/Scripts/python.exe tests/api/timetable_final_browser.py
```

The browser harness also needs the test-only Playwright package and Chrome. Generated
fixtures, screenshots, downloaded PDFs and machine-readable counts are in
`tmp/timetable-final/`; the detailed result is `tmp/timetable-final/report.json`.
The regression output is in `tmp/timetable-all-tests.log`.
