# Timetable Rebuild Plan

## Objective

Replace the hard-coded department timetable flow with a reusable, data-driven
generator that supports every department, selected semesters, review before
publication, and dynamic student and teacher timetable views.

## Scope and delivery order

1. **Audit the legacy path; retire it only after replacement verification**
   - Locate CS-specific constants, static courses, fixed teachers, and static
     timetable displays.
   - Audit database tables, relationships, read paths and production timetable
     records before designing a migration.
   - Preserve production timetable data through a reviewed migration where it
     is compatible with the new model.
   - Do not remove legacy endpoints/components until the replacement has
     generated, validated, published and displayed a complete timetable in both
     portals end-to-end.

2. **Create reusable timetable data model**
   - `AcademicTerm`: name, start/end dates, active state.
   - `Timetable`: department, semester, term, status (`draft`, `approved`,
     `published`), author and timestamps.
   - `TimetableCourse`: timetable, course, teacher, student cohort/semester,
     weekly sessions, session duration, preferred/eligible rooms and optional
     availability rules.
   - `TimetableSession`: timetable course, day, start time, end time, room.
   - Reuse existing Department, Course, Teacher, Student Enrollment and Room
     entities; do not duplicate their data.
   - Add a `TeacherAvailability` model/configuration if one does not already
     exist: teacher, day, available start/end time (including unavailable
     periods).
   - Add timetable configuration for working days, daily slot boundaries and
     slot length. The UI defaults to Monday-Friday, but the generator must not
     hard-code five days.

3. **Build admin setup wizard**
   - Choose department, academic term, and one or more semesters.
   - For every selected semester, add existing courses and select a teacher.
   - Default weekly sessions from credit hours: one credit = one weekly
     session, two = two, three = three. Admin configuration always overrides
     this default. Labs have independently configurable duration and session
     structure.
   - Validate prerequisites before generation: active teachers, rooms, courses,
     enrolled students, valid working hours and configured working days.

4. **Implement generation and validation service**
   - Generate sessions rather than storing a pre-rendered grid.
   - Enforce hard constraints: no overlapping teacher, room, or student cohort
     sessions; active teacher/course/room; valid durations and working hours.
   - Enforce teacher availability and room suitability: room type (classroom,
     computer lab, laboratory) plus capacity at least equal to the enrolled
     student count for the affected cohort.
   - Apply quality preferences: spread meetings across days, avoid excessive
     teacher daily load, honour availability and room capacity/type.
   - Return an actionable conflict report if no valid schedule is possible.

5. **Preview, manual edits, approval and publishing**
   - Display configured working days as rows with time-slot columns;
     Monday-Friday is the default.
   - Each session cell shows course, teacher, room and time.
   - Permit drag/drop or edit controls in draft mode, revalidating every edit.
   - Admin approves then publishes. Only published records appear in student
     and teacher portals.

6. **Portal integrations**
   - Student portal queries published sessions by the learner's department,
     enrolled semester and active term.
   - Teacher portal queries published sessions by authenticated teacher ID.
   - Both render the same timetable-grid component, filtered for their role.
   - Add print and export only after the primary views are working.

7. **AI Timetable Assistant rebuild**
   - Reuse the Library Assistant / Academic Assistant chat layout, styling,
     messages, empty state and responsive behavior.
   - Add attachment selection and drag/drop for CSV, DOCX and PDF.
   - Store file metadata safely, extract text/tables asynchronously and show
     extraction status/errors.
   - Scope questions and timetable recommendations to uploaded documents.
   - Show extracted courses, teachers, rooms and constraints for user review.
     The assistant is recommendation-only: it never writes timetable sessions.
     All scheduling goes through the same generator and validation service,
     followed by explicit admin approval.

8. **Verification**
   - Unit tests for clash detection, credit-hour defaults, generation and
     publishing rules.
   - API/component tests for setup, preview, approval and portal visibility.
   - End-to-end test with two departments, multiple semesters, shared rooms and
     shared teachers.
   - Verify desktop and mobile assistant upload/chat behavior.

## Key implementation decisions

- The canonical data is a list of `TimetableSession` records. Grid views are
  derived from those records, which keeps Student, Teacher and Admin views in
  sync.
- The generator must be constraint-based and deterministic/reproducible for a
  given input set; it must never silently create conflicting sessions.
- Credit hours provide a default weekly meeting count, not an inflexible rule;
  the explicit session configuration is authoritative.
- A preview remains a draft. Approval/publishing is the boundary that makes a
  timetable visible to students and teachers.

## First implementation checkpoint

After locating the project, audit the current UI/API/database flow first. Then
implement the model/migration layer, validation service and generator. Connect
the setup wizard, draft preview, editing/revalidation, approval/publishing,
student view, teacher view, assistant rebuild and document support in that
order. Retire legacy code only after a passing end-to-end replacement test.
