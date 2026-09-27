# Timetable module verification

> Current conversational acceptance workflow and verified results:
> [Final correction report](../../docs/TIMETABLE_FINAL_VERIFICATION.md).
> Run `tests/api/timetable_final_browser.py` for the current Admin UI. The older
> publication harness and notes below describe the preceding implementation.

## Changed files

Existing files updated:

- `backend/backend/app/main.py`
- `backend/backend/app/api/admin.py`
- `backend/backend/app/api/student.py` (timetable reader only)
- `backend/backend/app/api/teacher.py` (timetable reader only)
- `backend/backend/app/schemas/admin.py`
- `backend/backend/app/services/ai_providers.py`
- `backend/backend/app/services/timetable_creator.py`
- `backend/backend/app/services/timetable_documents.py`
- `requirements.txt`
- `frontend/Admin_dashboard/ai-timetable-creator.html`
- `frontend/Student_dashboard/timetable.html` (publication refresh)
- `frontend/Teacher_dashboard/teacher-schedule.js` (publication refresh)

Files added:

- `backend/backend/app/services/timetable_agent.py`
- `backend/backend/app/services/timetable_constraints.py`
- `backend/backend/app/services/timetable_approval.py`
- `frontend/Admin_dashboard/timetable-chat.js`
- `frontend/Admin_dashboard/timetable-chat.css`
- `tests/api/test_timetable_agent.py`
- `tests/api/timetable_browser_flow.py`
- `tests/api/TIMETABLE_TESTING.md`
- `tmp/.gitignore` (keeps local runtime/test artifacts out of version control)

## Running verification

Run from the project root:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests/api -p test_timetable_agent.py -v
```

The suite takes a read-only SQLite backup of `database/university.db` into memory.
It never publishes test changes to the source database or creates university
fixtures. Tests cover read-only planning, explicit approval, signed preview
integrity, duplicate/replay rejection, historical replacements, both portal
queries, independent resource conflicts, workload ranking, missing sessions,
repair routing, document extraction, and provider failover.

For the browser flow, install test-only dependencies and use the existing Chrome:

```powershell
python -m pip install playwright pymupdf
python tests/api/timetable_browser_flow.py
```

This script opens Chrome, starts temporary servers on ports 8765 and 8766,
authenticates as an existing Admin with a short-lived test token, and uses only
the in-memory database copy. It checks desktop/tablet/mobile layouts, generated
preview, PDF download, rejection, regeneration, confirmation/cancellation,
approval, PDF extraction review, and local image OCR. Screenshots and generated
PDFs go to the ignored `tmp/` directory. No real passwords are required or logged.
The browser check also signs in to the actual Student and Teacher timetable pages
and verifies that an approved schedule is visibly rendered for its enrolled student
and selected teacher.

# Implementation boundaries

- `timetable_agent.py`: LangChain typed extraction and compiled LangGraph
  understand/read/plan/validate/repair/review workflow. No write node.
- `timetable_constraints.py`: reusable database snapshot, capability matching,
  year-specific workload ranking, independent booking checks, and bounded
  deterministic scheduling. Existing enrolled courses supply IDs and credit hours.
- `timetable_approval.py`: 30-minute, Admin-bound signed preview proof and database
  revision check. Approval revalidates under SQLite `BEGIN IMMEDIATE`; replacements
  retain cancelled schedule rows. Schema is unchanged.
- `timetable_documents.py`: real PDF/DOCX/TXT extraction, local RapidOCR image
  processing, evidence review, and text-based ReportLab weekly grids.
- The existing `AIProviderManager` retains Groq → Gemini → Hugging Face → Ollama
  order. Invalid typed responses can fall through to the next provider. No model
  has database write access.

No dedicated room-capacity, equipment, teacher availability, or capability table
exists. The planner uses recorded teaching rooms, active bookings, course ownership,
matching taught course titles and recorded specialization. Its conservative policy
is at most 18 scheduled hours and 6 scheduled courses per teacher per academic year.
Unknown courses/teachers and unsupported extracted requirements require review;
uploads do not create capability records. Cross-department requests require real
matching course/enrollment mappings. An empty department returns a clear no-data
result instead of inventing records. Scanned PDFs with no extractable text request
a clearer reference; image uploads support local OCR.

Startup no longer runs automatic timetable migrations, expansion, or normalization.
Existing timetable maintenance scripts remain available for deliberate maintenance.
Student timetables use matching enrollments and canonical schedules. Teacher views
default to the latest recorded active academic year. Open portals refresh on a
same-origin publication signal, focus, and a 30-second visible-tab interval.

Live provider check in this environment: configured Ollama timed out and the
deterministic fallback completed without writes. Other provider failures/order are
covered with controlled failures in the integration suite; cloud success was not
claimed.

## Additional production hardening

- Both generation and chat enforce `document_reviewed=true` for nonempty reference
  text. Malformed history is rejected by typed request validation.
- Oversized extracted references are rejected explicitly rather than silently cut.
- Explicit chat department/semester requests override stale filter selections.
  Database-derived acronyms are disambiguated using recorded department codes.
- Known time windows are enforced; contradictory windows require clarification.
  Unknown explicit course/teacher lists cannot broaden generation when AI is offline.
- Signed approval binds to the database revision taken before planning. Changes to
  students, departments, enrollments, teachers, courses, or schedules during planning
  prevent signing. Approval still rechecks the revision under the write lock.
- OCR initializes once per process and serializes inference to bound resource use.
- The integration fixture uses separate SQLite connections to a shared, memory-only
  backup so concurrent portal requests do not reuse a single DBAPI cursor.

These checks cover this timetable module. Deployment still needs the existing
application's HTTPS, authentication secret management, database backups, and AI
provider configuration. No cloud-provider availability or schema facts are invented.

Simultaneous approval is regression-tested: one request commits and the competing
request receives 409, with no duplicate insert. Expected SQLite writer contention
returns a clear retry response; other database operation failures return 503 after
rollback. For hosted Admin pages, API calls default to the same origin; deployments
can set `window.TIMETABLE_API_BASE_URL` before loading `timetable-chat.js`. Local
localhost development retains the existing port-8000 backend.
