# ACOS — Complete Project Guide and Thesis Reference

## Purpose and evidence base

Autonomous Campus Operating System (ACOS) is a research-oriented university ERP and decision-support prototype for the University of Haripur. Its central contribution is the combination of campus transactions with zero-trust, role-scoped, database-grounded AI. It implements separate student, teacher and administrator portals, academic records, attendance, assignments, online assessments, a library, timetable planning, and administrative/watchdog interfaces.

This guide follows a full workspace inventory of 355 files and a read of all human-readable source, SQL, configuration, test, and project-documentation files. Binary assets and generated artefacts were catalogued by type/purpose rather than treated as maintainable source: SQLite databases/backups, DOCX uploads, PDFs, logos/wireframes, Python bytecode, pytest caches, the venv and Git internals. `tree.txt` is a generated historical listing, not a source of truth. Runtime data is in `database/university.db`; SQL files are the reproducible design/history.

## Architecture and end-to-end operation

```text
Static browser UI (HTML/CSS/vanilla JavaScript)
  → JWT Bearer token → FastAPI REST application (:8000)
  → authenticated RBAC + Pydantic validation + services/SQLAlchemy
  → SQLite university.db (constraints, triggers, views)
  → scoped database context → AI providers/fallback response
```

`backend/backend/app/main.py` is the composition root. It initializes idempotent library and assessment schema checks, creates/mounts `backend/backend/uploads` at `/uploads`, registers auth/student/teacher/admin/exam/library routers, enables development CORS (`*`, no credentials), and exposes `/` and `/health`. Timetable normalization/migrations are deliberately not automatic, avoiding an unexpected publication or rewrite at startup.

### Authentication and authorization

Login pages send identifier/password to `POST /auth/login`. `services/auth_service.py` selects an active user by username/email and verifies a bcrypt/Passlib hash. `core/security.py` signs an expiring JWT with `sub` and role. `core/auth.py:get_current_user` decodes it and reloads the user, then every protected route resolves the matching Student/Teacher/Admin profile and filters data from that profile. The UI role selection is never the access-control boundary.

### Student and teacher flows

Student routes return only the caller's profile, courses/enrollments, attendance, timetable, published results/dashboard, fees, library data, notices and assignments. Students submit text/files against eligible assignments; attachment paths are stored under `uploads/student_submissions`. Teachers see only their profile, courses, rosters and schedules; they create schedules/assignments, mark roster attendance, inspect/review submissions, and manage assessments. Ownership helper functions in `api/student.py`, `api/teacher.py` and `api/exam.py` are the important server-side isolation mechanism.

### Online assessments

`api/exam.py` governs teacher creation/question import/publish/overview/results and student list/start/answer/save/submit/violation/result operations. It verifies teacher ownership and student enrollment, enforces deadlines, auto-grades as appropriate, and returns results subject to reveal policy. Migration v13 creates `Assessments`, `Assessment_Questions`, `Assessment_Attempts`, `Assessment_Responses`, and `Assessment_Target_Students`.

### Grounded AI research mechanism

Before a student or teacher chat, the backend verifies identity and deterministically gathers only permitted current records. `student_ai_context.py` builds identity/results/courses/timetable/attendance/assignments/fees/exams/advice facts; `teacher_ai_context.py` builds identity/courses/students/schedule/attendance/assignments/assessments/grades facts. Assistant services constrain prompt/history and call `AIProviderManager`: Groq → Gemini → Hugging Face → local Ollama. Failure falls back to a deterministic answer generated solely from the same facts. No LLM receives a database write tool. This makes the research claim measurable: authentication → scoped retrieval → constrained generation/fallback, instead of unrestricted model access.

### Timetable workflow

Admin UI `frontend/Admin_dashboard/ai-timetable-creator.html` and `timetable-chat.{js,css}` call `/admin/timetable-creator/*`. General chat parses supplied facts into a read-only proposal; system mode uses LangGraph (`understand → read_database → generate → validate → repair → review`) and actual course/enrollment/teacher data. `timetable_constraints.py` checks time, teacher, room, student, workload and coverage conflicts. References are transient: maximum 5 MB and 20,000 extracted characters, parsed from PDF/DOCX/TXT/CSV/XLSX or local OCR and explicitly reviewed.

Generation cannot write. `timetable_approval.py` signs an admin-bound preview with a 30-minute proof and DB revision. Approval starts `BEGIN IMMEDIATE`, rechecks proof/revision/constraints, cancels replacement rows, inserts active `Class_Schedules`, creates matching `Student_Timetable` rows, then commits atomically. Writer contention returns 409 and any error rolls back. PDF export is read-only. This is the critical human-in-the-loop safety boundary.

## Backend file map

| Area/files | Responsibility |
|---|---|
| `core/config.py`, `database.py`, `security.py`, `auth.py` | Environment settings; engine/session and foreign-key hook; password/JWT primitives; current-user dependency. |
| `models/*.py` | SQLAlchemy mapping for users, department, student, teacher, admin, course, enrollment, attendance, assignment, submission, grade, results/GPA/CGPA, term, schedule/timetable, and five assessment entities. `role.py` is empty/legacy. |
| `schemas/{auth,student,teacher,exam,ai_assistant,admin}.py` | Pydantic request/response contracts; timetable schemas validate scope/history/reference review/proposal/PDF payloads. |
| `api/auth.py` | `/auth/login`, `/auth/me`. |
| `api/student.py` | Attendance, assignment/submission, profile, courses, timetable, results/dashboard, fees/library/notices, student AI. |
| `api/teacher.py` | Profile/course/roster, attendance, schedule, assignment/submission review/AI evaluation, teacher AI. |
| `api/admin.py` | Admin profile, term completion gate and timetable options/analyze/generate/chat/document/approve/PDF. |
| `api/exam.py` | Online assessment lifecycle, attempts, proctoring events and gradebook marks. |
| `api/library.py` | Catalog/search/upload/sync/download/view/chat and analytics; admin-only mutations. |
| `services/academic_results.py` | Defines completed/finalized results and recalculates completed CGPA. |
| `services/ai_providers.py` | Provider abstraction, environment reload, HTTP calls and ordered fallback. |
| `services/{student,teacher}_ai_{context,assistant}.py` | Scoped fact extraction and deterministic/LLM responses. |
| `services/library_catalog.py`, `library_discovery.py` | Catalog/activity bookkeeping and cautious external discovery. |
| `services/timetable_{agent,conversation,creator,constraints,approval,documents,knowledge,normalizer}.py` | LangGraph system planning; general conversation parser/scheduler; database scope/draft; constraints; signed approval; extraction/PDF; local embeddings/retrieval; legacy repair. |
| `weekly_session_expander.py`, `*_migration.py` | Explicit maintenance helpers; do not run implicitly. |

For any new API field, change the ORM model, forward migration, clean schema, Pydantic schema, service/router, consumer UI, tests and API documentation together.

## Database: design and maintenance

`Users` is identity root; Students/Teachers/Admins reference it. Departments own student/teacher/course records. Enrollments link student/course/year/semester/section; attendance, grades and results derive from enrollment; assignments own submissions; Class_Schedules link course/teacher/term/section; Student_Timetable maps published schedules to matching enrollments. Results aggregate through `Semester_GPA` to `Student_CGPA`.

`database/schema/00_create_database.sql` sets DB pragmas. `01`–`24` create Users, Departments, Students, Teachers, Courses, Enrollments, Attendance, Grades, Assignments, Submissions, Fee_Records, Documents, Library/Issues, Hostels, Transport, Notifications, Research, Security, AI telemetry, Audit, Course_Results, Semester_GPA, Student_CGPA and Admins. Use the schema files as the fresh-build data model.

The executable migration history begins at `v4`; later files cover schedules, assignments/submissions, academic terms, assessments, library activity, timetable coverage, gradebook, and timetable integrity. Empty v1-v3 placeholders were removed. Never edit an applied migration: add a new forward-only migration.

Seed files 1–6 and 8–10 contain the demonstration identities, departments, courses/enrollments, and academic data. Former zero-byte seed placeholders were removed. `22_triggers.sql` is the corrected canonical set; `22_triggers_legacy.sql` is historical and is not applied by the builder.

### Adding future data safely

Back up `university.db` before any change; never hand-edit it while the API is active. Use routes/admin flows for operational data. For reproducible thesis data, add idempotent SQL to the appropriate seed file/new ordered seed, rebuild a disposable DB, validate foreign keys, then test.

1. Add a department first.
2. Add a User with a bcrypt hash and correct role, then its Student/Teacher/Admin profile referencing the user and department.
3. Add Courses before Enrollments; enrollment must use real student/course/year/semester/section and status `Enrolled`.
4. Publish schedules with teacher/admin APIs. Direct fixtures must satisfy all time/room/teacher conflicts and create matching Student_Timetable records.
5. Use grade/result workflow, then `PUT /admin/academic-terms/status` to complete a term; it blocks completion until every enrolled course has a published final result and recalculates affected CGPAs.
6. Create assignment before submission and course/enrollment before attendance. Use API file routes so ownership and upload paths remain valid.
7. Upload/sync library books through the library API; copying a PDF into the frontend `Books` folder does not catalog it.

## Frontend map

| Files | Purpose |
|---|---|
| `landing_page/{index.html,style.css,app.js,uoh-logo.png}` | Public landing presentation and brand. |
| `login_page/{student,teacher,admin}-login.html`, `login.{css,js}`, assets | Shared JWT login and role redirect. |
| `welcome/{student,teacher,admin}-home.html` | Role-specific navigation gateways. |
| `Student_dashboard/*` | `stu_dashboard.html` plus focused profile, courses, attendance, timetable, results, assignments, exams, fees, library, notices views. `student-attendance.js` and `student-assignments.js` support interaction. |
| `Teacher_dashboard/*` | Dashboard plus courses, students, schedule, attendance, assignments, assessments, gradebook and notices. `teacher-auth.js` guards session; the other `teacher-*.js` files are API-facing controllers. |
| `Admin_dashboard/dashboard*`, `admin-shell*` | Admin shell/navigation. `ai-timetable-creator.html` + `timetable-chat*` is the wired timetable client. Integrity/clerk/exam/finance/hostel/library/security/HR/faculty/student/communication pages are domain dashboards; verify APIs before treating a screen as live CRUD. `clerk-watchdogold.*` is legacy. |
| `shared/library.*`, `student-topbar.js` | Reusable library and student UI. |
| `Admin_dashboard/Books/*.pdf` | Static sample books, not catalog records. `_audit...py` checks links and `_fix...py` is a reviewed maintenance helper. |

Large dashboard HTML files bundle markup, CSS and scripts. Change a feature by first locating its `fetch()` API call, then updating contract/backend and loading/error/render states; do not only alter a hard-coded card. Timetable student/teacher pages refresh on publication/focus/visible-tab events.

## Tests, documents, configuration and artefacts

`tests/api/test_student_*`, `test_multiple_students.py`, `test_danish_malik_results.py` and `test_library.py` cover profile/course/result isolation and library behavior. `test_timetable_agent.py` and `test_timetable_conversation.py` cover planning; `timetable_browser_flow.py`/`timetable_final_browser.py` are browser acceptance harnesses; `TIMETABLE_TESTING.md` is their current boundary/limitations record. Backend `test_agent_suite.py` and `test_teacher_ai.py` test AI behavior. `backend/out.json` is generated output. Uploaded DOCX files are user/test artefacts and should be protected/backed up.

Root/component READMEs, `ARCHITECTURE.md`, `API_DESIGN.md`, `SETUP.md`, and `docs/` supply project/design/research evidence. `docs/Week_1` retains literature/research notes, threat checklist, architecture/API/agent protocol, ER/database/versioning, FAISS strategy, UX wireframes, milestone/status/risk logs. DOCX ER diagrams and wireframe images are thesis artefacts, not runtime code.

`.env` is secret-bearing and must never be committed; `.env.example` is the safe template. Root `requirements.txt` is the single runtime manifest and `requirements-dev.txt` adds testing tools. `CODE_OF_CONDUCT.md` and `LICENSE` contain the public terms. `scripts/setup_database.py` is the supported atomic SQLite builder.

## Deployment, upkeep and thesis framing

Use Python 3.12+, backend requirements, backend `.env`, and run `uvicorn app.main:app --reload` from `backend/backend`; serve frontend as static HTTP. Before release, replace default credentials, rotate secrets, restrict CORS, use HTTPS, apply upload validation/malware controls, store uploads outside source control, and back up database plus uploads together. SQLite is prototype-grade: migrate to a server DBMS for high concurrency.

Run `pytest tests/api/ -v` after backend changes; run agent suites after AI changes; run timetable unit/conversation/browser acceptance after planning changes. Key research evaluation measures are DB-grounded answer correctness, rejected unauthorized access, provider-failure completion, timetable conflict/coverage/workload satisfaction, approval race safety, and role-specific usability.

Known limitations to state honestly: permissive development CORS; some admin/watchdog screens are UI prototypes without CRUD APIs; cloud AI privacy/availability is external; capacity/equipment/teacher-availability tables do not exist; timetable claims beyond recorded data require review; scripts/licensing contain stale placeholders; and default seed credentials are demonstrations only. Update this guide in the same change set as every architectural, data, API, security, AI-provider, or deployment change.

## Appendix A — exhaustive file register

This appendix is intentionally literal. It records every relevant workspace file found during the audit, including empty, generated, binary, and legacy files. “Generated” means it is not a file to edit as application source; it must either be recreated from its owner source/data or retained as a protected operational artefact.

### Repository root and editor files

| File | Detailed purpose / maintenance rule |
|---|---|
| `.env` | Active root environment values. Secret-bearing; do not commit, print, or use as a thesis appendix. Prefer backend `.env.example` when preparing a new deployment. |
| `.gitignore` | Git exclusion policy for environments, caches, secrets and generated material. Update when a new generated/sensitive path is introduced. |
| `.vscode/settings.json` | VS Code chooses the `venv` environment manager/interpreter. Developer convenience only. |
| `README.MD` | Master narrative: scope, stack, portal capabilities, quick start, credentials, tests and project map. Update it after any material capability or setup change. |
| `ARCHITECTURE.md` | Detailed intended architecture/data-flow explanation. Use in thesis background but reconcile it with code when claims conflict. |
| `API_DESIGN.md` | Endpoint-level design reference. Update with new/changed routes, payloads, status codes and authorization rules. |
| `SETUP.md` | Environment/setup guidance. Update with version, install, database or deployment changes. |
| `CONTRIBUTING.md` | Proposed contributor workflow/conventions. Keep aligned with actual test and branching practice. |
| `CODE_OF_CONDUCT.md` | Contributor behavior and private reporting policy. |
| `LICENSE` | MIT License for the public source release. |
| `requirements.txt` | Pinned/root Python environment inventory. Regenerate/review after dependency changes; backend manifest is the normal app installer. |
| `Guide.md` | This living source-to-thesis/maintenance guide. Update alongside architecture/API/schema/security changes. |
| `tree.txt` | Generated repository tree snapshot (large, stale-prone). Regenerate rather than hand-maintain; never treat it as implementation. |

### AI folder

| File | Detailed purpose / maintenance rule |
|---|---|
| `ai/README.md` | Documents intended ACOS AI architecture, provider sequence, grounding and proposed folder layout. It is conceptual support for the live backend AI code. Update when providers, models, safety boundaries or agent capabilities change. |

The README refers to `agents`, `embeddings`, `models`, `prompts`, `rag`, `vector_db`, and `workflows`, but those directories/files are absent in this checkout. Do not cite them as implemented modules; current implementation is in `backend/backend/app/services`.

### Backend root, runtime and test files

| File | Detailed purpose / maintenance rule |
|---|---|
| `backend/README.md` | Backend-specific architecture, route and operation reference. Keep it synchronized with routers/services. |
| `backend/backend/.env` | Active backend settings/API keys. Keep private; replace values locally from `.env.example`. |
| `backend/backend/.env.example` | Safe settings template for database path, JWT and AI providers. Add a placeholder/documentation entry for every newly required environment variable. |
| `requirements.txt` | Canonical pinned runtime dependency manifest at the repository root. |
| `backend/backend/test.py` | Small local test/probe script. Treat as developer diagnostic rather than formal pytest coverage. |
| `backend/backend/test_agent_suite.py` | Student/teacher AI verification harness covering greeting, context grounding, conversations and provider fallback. Run after AI changes. |
| `backend/backend/test_teacher_ai.py` | Focused teacher-assistant test harness. Run after teacher context/assistant changes. |
| `backend/backend/out.json` | Captured/generated test/report output; inspect for diagnostics but regenerate rather than hand-edit. |
| `backend/backend/uploads/assignment_references/20260817180509653586.docx` | Uploaded assignment reference artefact. Protect as user content; its metadata/path are consumed by assignment workflows, not source control logic. |
| `backend/backend/uploads/student_submissions/20260820074146973944.docx` | Student upload artefact; protect/back up and do not edit as code. |
| `backend/backend/uploads/student_submissions/20260907073418158729.docx` | Student upload artefact; same rule. |
| `backend/backend/uploads/student_submissions/20260907082131695346.docx` | Student upload artefact; same rule. |
| `backend/backend/uploads/student_submissions/20260912101032270776.docx` | Student upload artefact; same rule. |
| `backend/backend/uploads/student_submissions/20260912101135570789.docx` | Student upload artefact; same rule. |
| `backend/backend/uploads/student_submissions/20260912101256189035.docx` | Student upload artefact; same rule. |
| `backend/backend/uploads/student_submissions/20260912101403412444.docx` | Student upload artefact; same rule. |

`backend/backend/__pycache__/test.cpython-312-pytest-9.1.1.pyc` and every `__pycache__/*.cpython-312.pyc` below are CPython-generated bytecode mirrors of the adjacent `.py` source. Delete/recreate them by running Python; never document or edit bytecode as source.

### Backend application entry/core files

| File | Detailed purpose / connections |
|---|---|
| `app/main.py` | FastAPI entry point. Defines lifespan, calls library/assessment schema checks, mounts uploads, CORS, includes routers and health endpoints. Run through Uvicorn. |
| `app/core/config.py` | `Settings` class, loading env configuration used by database/security/provider code. |
| `app/core/database.py` | SQLAlchemy engine/session lifecycle and foreign-key connection event. All router DB dependencies pass through it. |
| `app/core/security.py` | bcrypt hash/verify plus JWT sign/decode. Any auth algorithm/expiry change starts here and must be regression-tested. |
| `app/core/auth.py` | `get_current_user` Bearer dependency, token validation and user lookup. All protected APIs depend on it. |

### Backend model files

| File | Detailed purpose / principal relationship |
|---|---|
| `app/models/__init__.py` | Imports model classes to establish ORM metadata/relationships. Add new models here when required by initialization/import paths. |
| `academic_term.py` | Academic year/semester publication status and completion timestamp. Used by result/CGPA completion logic. |
| `admin.py` | Admin profile tied to a `User`; read by `/admin/profile`. |
| `assignment.py` | Teacher/course/year/semester/section assignment, deadline/marks/attachment metadata. Parent of submissions. |
| `attendance.py` | Student/course/teacher/term/date attendance record. Teacher attendance routes create/read it. |
| `class_schedule.py` | Scheduled course/teacher/day/time/room/year/semester/section/status row. Timetable planner publishes it. |
| `course.py` | Department course catalog, credit-hour, ownership/status data. Used by enrollment, timetable and results. |
| `course_result.py` | Final student-course outcome/publishing data feeding transcripts and GPA/CGPA. |
| `department.py` | Department identity/name/code. Parent for teachers/students/courses. |
| `enrollment.py` | Student-course registration within year/semester/section/status. The core roster and timetable coverage link. |
| `exam.py` | `Assessment`, question, attempt, response and target-student ORM models. Maps v13 assessment tables. |
| `grade.py` | Component marks, calculated grade/publish/lock state. Database triggers can derive course results. |

| `semester_gpa.py` | Per student/year/semester aggregate performance. |
| `student.py` | Student profile/demographic/academic/cohort/department attributes tied to User. |
| `student_cgpa.py` | Current/completed cumulative GPA, credits and standing. `academic_results.py` recalculates it. |
| `student_timetable.py` | Explicit enrollment/schedule/student mapping used for personalized timetable reads. |
| `submission.py` | Student response/file/marks/feedback/status record tied to assignment. |
| `teacher.py` | Teacher identity, department, employment and status profile tied to User. |
| `user.py` | Authentication root: username/email/password hash/role/active state; parent of role profiles. |

### Backend schema files

| File | Detailed purpose |
|---|---|
| `app/schemas/auth.py` | Login identifier/password request and bearer token response. |
| `app/schemas/student.py` | Student profile-update and assignment text-submission validation. |
| `app/schemas/teacher.py` | Teacher schedule/assignment/review/attendance entry payloads. |
| `app/schemas/exam.py` | Question, assessment creation, answer-save, submission and violation payloads. |
| `app/schemas/ai_assistant.py` | Student/teacher chat history/message, response/provider and greeting contracts. |
| `app/schemas/admin.py` | Academic-term status and timetable scope/history/reference/proposal/approval/PDF/chat contracts. |

### Backend API router files

| File | Detailed purpose and connected UI |
|---|---|
| `app/api/auth.py` | `/auth/login` and `/auth/me`; called by all login pages. |
| `app/api/student.py` | Student ownership resolver plus endpoints for dashboard pages, assignments/submissions/uploads, profile update, timetable/results/fees/library/notices and student AI. Consumed by Student dashboard pages. |
| `app/api/teacher.py` | Teacher ownership, file storage, schedule/attendance/assignment/submission evaluation/review, profile/course/roster and AI endpoints. Consumed by Teacher dashboard scripts/pages. |
| `app/api/admin.py` | Admin guard, profile/term status and secure timetable creator endpoints. Consumed primarily by Admin timetable client. |
| `app/api/exam.py` | Shared teacher/student online-exam endpoints and gradebook marks. Consumed by teacher assessments and student exams pages. |
| `app/api/library.py` | Member/admin guards and library catalog, upload, sync, download/view counts, search/chat/analytics. Consumed by shared library UI and library pages. |

### Backend service files

| File | Detailed purpose / change impact |
|---|---|
| `academic_results.py` | Finds completed/finalized terms, computes completed credits/CGPA and upserts Student_CGPA. Change only with result-policy tests. |
| `ai_providers.py` | Provider request normalization, direct HTTP provider classes and manager fallback. Add providers here plus env/example/docs/tests. |
| `auth_service.py` | User lookup/authentication logic. Security-sensitive; preserve active-state and hash validation. |
| `exam_migration.py` | Ensures online assessment schema. Called by lifespan; keep idempotent. |
| `library_catalog.py` | Ensures library structures, syncs files, produces catalog/summary and records activity. |
| `library_discovery.py` | URL safety, fetch/parser and public discovery result functions. Review SSRF/privacy rules before extension. |
| `student_ai_context.py` | Fine-grained student context queries and dynamic context assembly. New student AI facts must be authorized here first. |
| `student_ai_assistant.py` | Student prompt/fallback response and provider invocation. |
| `student_timetable_migration.py` | Explicit normalized timetable schema maintenance helper; not automatic at startup. |
| `teacher_ai_context.py` | Teacher identity/course/roster/schedule/attendance/assignment/assessment/grade fact queries. |
| `teacher_ai_assistant.py` | Teacher prompt/fallback response/provider interaction. |
| `timetable_agent.py` | Typed request plan, LangGraph state/nodes and general/system workflow invocations. No database write node. |
| `timetable_approval.py` | Proposal digest, revision, attachment and verification. Protect token expiry/user/revision binding. |
| `timetable_constraints.py` | Constraint snapshot, time conversion, conflict/coverage/workload validation and deterministic planning support. |
| `timetable_conversation.py` | General-mode input parser, facts expansion, overlap validation, deterministic schedule and conversation workflow. |
| `timetable_coverage_migration.py` | Explicit coverage schema helper. |
| `timetable_creator.py` | Scope inference, current schedule collection, serialization, analysis and draft validation. |
| `timetable_documents.py` | OCR lazy initialization; PDF/DOCX/text/tabular extraction and ReportLab PDF generation. |
| `timetable_knowledge.py` | Hash/SentenceTransformer embedding provider, chunk/index/retrieval and document relationship resolution. |
| `timetable_normalizer.py` | Detects and normalizes legacy timetable rows. Execute only as a deliberate maintenance action on a backup. |
| `weekly_session_expander.py` | Converts credit hours to expected weekly sessions and repairs coverage. Deliberate maintenance only. |

### Database schemas, migrations, seeds and analytics—individual register

`database/schema/00_create_database.sql` configures a new SQLite database. `01_users.sql` defines credentials/RBAC; `02_departments.sql` department master data; `03_students.sql` student profile; `04_teachers.sql` teacher profile; `05_courses.sql` catalog; `06_enrollments.sql` student-course registrations; `07_attendance.sql` attendance; `08_grades.sql` marks; `09_assignments.sql` coursework; `10_submissions.sql` submissions; `11_fee_records.sql` finance; `12_documents.sql` verified documents; `13_library.sql` catalog/issues; `14_hostels.sql` accommodation; `15_transport.sql` transport; `16_notifications.sql` notices; `17_research.sql` research/funding; `18_security.sql` security/session/threat logging; `19_ai_agents.sql` AI telemetry; `20_audit.sql` audit evidence; `21_course_results.sql` final course results; `22_semester_gpa.sql` term GPA; `23_student_cgpa.sql` cumulative GPA; `24_admin.sql` admin profile. Every one is the clean-install reference for its table and indexes.

The executable migration history starts at `database/migrations/v4_class_schedules.sql`; the former zero-byte v1-v3 placeholders were removed. Preserve applied migrations and add new forward-only files.

The numbered seed files 1–6 and 8–10 contain the demonstration identity, enrollment, and result graph. Former zero-byte seed placeholders were removed. Add future seed data in dependency order and never use a row ID that disagrees with its parent data.

`database/triggers/22_triggers.sql` is the corrected canonical trigger set. `22_triggers_legacy.sql` is retained only for historical comparison. `database/views/21_views.sql` contains the analytical read views; generated databases and backups are not committed.

### Frontend—individual register

`frontend/README.md` is the frontend guide. `landing_page/index.html` is public markup, `style.css` its responsive visual system, `app.js` its browser interactions, and `uoh-logo.png` its image asset. Login files `student-login.html`, `teacher-login.html`, `admin-login.html` are role-specific entry documents; `login.css` is shared styling, `login.js` is auth/token/redirect logic, `login-bg.jpg` background media and `uoh-logo.png` branding. Welcome files `student-home.html`, `teacher-home.html`, and `admin-home.html` are role gateways.

Student files: `stu_dashboard.html` is overview; `profile.html` profile; `my-courses.html` enrolled offerings; `attendance.html` display; `student-attendance.js` attendance controller; `timetable.html` schedule reader/refresh; `results.html` results and chart presentation; `assignments.html` assignment UI; `student-assignments.js` submission controller; `exams.html` assessment attempt UI; `fees.html` fee display; `library.html` catalog UI; `notices.html` notices. Each is a single-role client and should call `/student/*`, never privileged routes.

Teacher files: `tea-dashboard.html` overview; `my_courses.html` course UI; `teacher-courses.js` course controller; `students.html` roster UI; `teacher-students.js` roster controller; `classes_schedule.html` schedule UI; `teacher-schedule.js` schedule/published-refresh controller; `attendance.html` attendance UI; `teacher-attendance.js` roster/mark/history controller; `assignments.html` coursework UI; `teacher-assignments.js` create/review/upload/evaluate controller; `assessments.html` online exam UI; `gradebook.html` marks UI; `notices.html` notices UI; `teacher-auth.js` shared token/role guard. Maintain the matching `api/teacher.py` or `api/exam.py` contract whenever changing one.

Admin files: `dashboard.html`, `dashboard.css`, `dashboard.js` are overview presentation/logic; `admin-shell.css`/`admin-shell.js` are reusable shell navigation. `ai-timetable-creator.html`, `timetable-chat.css`, `timetable-chat.js` are the live timetable workflow. `academic-integrity.html`, `clerk-watchdog.html`, `exam-monitoring.html`, `finance-agent.html`, `hostel-agent.html`, `library-agent.html`, `security-agent.html`, `hr-administration.html`, `faculty-management.html`, `student-management.html`, `communication-notifications.html` are domain/watchdog dashboards; maintain a clear distinction between demo visualization and endpoint-backed actions. `coming-soon.html` is intentional placeholder. `clerk-watchdogold.html`, `clerk-watchdogold.css`, `clerk-watchdogold.js` are legacy baseline files. `_audit_admin_dashboard_links.py` audits navigational links and `_fix_admin_dashboard_links.py` attempts automated repairs—run only on a clean backup/review diff. `Books/Artificial Intelligence.pdf`, `C++_Programming.pdf`, `History of standard ML.pdf`, `Java programming.pdf`, `Python_Programming.pdf`, and `Web Engineering and Software Engineering.pdf` are static sample reading assets, not code nor library DB rows.

Shared files: `frontend/shared/library.css` styles library components; `library.js` implements catalog/search/chat/download/view interaction; `student-topbar.js` builds student top navigation/session behavior. Reuse these rather than duplicating token/UI logic.

### Tests, research docs and generated files—individual register

`tests/README.md` describes the test suite. `tests/api/test_student_profile.py`, `test_student_courses.py`, `test_student_results.py`, `test_multi_semester_results.py`, `test_multiple_students.py`, and `test_danish_malik_results.py` are database/API academic regression tests; `test_library.py` tests library routes; `test_timetable_agent.py` tests agent/constraints/approval; `test_timetable_conversation.py` tests general conversation parser/planner; `timetable_browser_flow.py` is an older end-to-end browser flow; `timetable_final_browser.py` is the current full UI acceptance harness; `TIMETABLE_TESTING.md` explains exact timetable verification. Corresponding `tests/api/__pycache__/*.pyc` files are generated bytecode only.

`docs/LIBRARY_IMPLEMENTATION.md` documents the library delivery. `docs/TIMETABLE_FINAL_VERIFICATION.md` records final timetable verification evidence. `docs/Week_1/Monday/litrature reviewed.md` and `research notes.md` are literature/research notes; `zero trust checklist.md` is security research checklist. `Tuesday/agent-communication-protocol.md`, `api-gateway-specification.md`, `architecture.md` are early protocol/design records. `Wednesday/database-design-document.docx` and `Er_diagram.docx` are binary design artefacts. `Thursday/faiss-indexing-strategy.md`, `full-er-diagram.docx`, `schema-changelog.md`, `schema-versioning-plan.md` are vector/database design records. `Friday/DEVELOPMENT_GUIDE.md`, `setup_environment.md`, `technology-integration-plan.md` capture early process/setup/stack planning. `Saturday/1_dashboard-wireframe.md`, `2_agent-pages-wireframes.md`, `3_responsive-design-guidelines.md`, `3_ui-component-inventory.md` document UX; `agent-pages-wireframes.png` and `dashboard-wireframe.png` are their visual assets. `Sunday/MILESTONES.md`, `PROJECT_STATUS.md`, `RESEARCH_LOG.md`, `RISKS.md` record progress, risks and research decisions. Cite them as design history, not necessarily final behavior.

`.pytest_cache/*` at root/backend and all `__pycache__` files are generated. `tmp/` is an ignored runtime/browser-test output folder; its contents are intentionally non-authoritative. `venv/` is the local dependency environment and must be rebuilt from requirements, never edited or included in a thesis/source release. `.git/` is repository metadata and is not project implementation.
> **Deployment-readiness update (2026-09-27):** `DEPLOYMENT.md`, `SETUP.md`, `.env.example`, the root requirements manifests, and `scripts/setup_database.py` are now authoritative. Earlier inventory notes describing empty license/conduct files, duplicate requirements, empty helper scripts, empty migrations/seeds, or the misspelled trigger filename are historical and no longer describe the current tree.
