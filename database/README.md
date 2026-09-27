# ACOS Database Architecture & Relational Schema

> **Comprehensive SQLite Relational Database Engine with 25 Normalized Schemas, 15 Versioned Migrations, Triggers, Views, and Seed Data**

---

## 📌 Overview

The **Autonomous Campus Operating System (ACOS)** database layer is designed for high relational integrity, Zero-Trust data isolation, and comprehensive campus management. Utilizing **SQLite 3** managed through **SQLAlchemy 2.0 ORM** and declarative SQL scripts, the database maintains complete academic records, financial transactions, attendance metrics, AI audit logs, and security tracking.

---

## 🏛️ Directory Structure

```
database/
├── README.md                      # Database documentation (this file)
├── university.db                  # Active SQLite database file
│
├── schema/                        # 25 Modular SQL Schema DDL Scripts
│   ├── 00_create_database.sql     # Database settings, pragmas, and foreign keys
│   ├── 01_users.sql               # User credentials, roles, and status
│   ├── 02_departments.sql         # Departments, faculties, and codes
│   ├── 03_students.sql            # Student demographic & enrollment details
│   ├── 04_teachers.sql            # Faculty profiles, designations & emails
│   ├── 05_courses.sql             # Course catalog, credit hours, prerequisites
│   ├── 06_enrollments.sql         # Course-student registrations & sections
│   ├── 07_attendance.sql          # Class attendance records & session statuses
│   ├── 08_grades.sql              # Sessional, midterm, and final grades
│   ├── 09_assignments.sql         # Assignment briefs, deadlines, max marks
│   ├── 10_submissions.sql         # Student submissions, scores, teacher feedback
│   ├── 11_fee_records.sql         # Fee vouchers, challans, dues & payments
│   ├── 12_documents.sql           # Verified student certificates & transcripts
│   ├── 13_library.sql             # Books catalog, issued books, due dates
│   ├── 14_hostels.sql             # Hostel rooms, allocations, wardens
│   ├── 15_transport.sql           # Transport routes, bus stops, fee passes
│   ├── 16_notifications.sql       # Campus notices, circulars & audience scope
│   ├── 17_research.sql            # ORIC publications, grants & research projects
│   ├── 18_security.sql            # Security logs, visitor passes & incidents
│   ├── 19_ai_agents.sql           # AI agent registrations, capabilities & telemetry
│   ├── 20_audit.sql               # Immutable Zero-Trust audit trails
│   ├── 21_course_results.sql      # Computed course GPAs, marks & letter grades
│   ├── 22_semester_gpa.sql        # Semester-wise GPA calculations
│   ├── 23_student_cgpa.sql        # Cumulative CGPA & earned credit tracking
│   └── 24_admin.sql               # Admin user profiles & designations
│
├── migrations/                    # 15 Versioned Schema Evolution Migrations
│   ├── v4_class_schedules.sql     # Schedule & timetable table additions
│   ├── v5_assignments_submissions.sql # Assignment submission schema enhancements
│   ├── v6_submission_response.sql # Assignment feedback and response columns
│   ├── v7_assignment_section.sql  # Section-specific assignment filtering
│   ├── v8_attendance.sql          # Attendance status & date integrity
│   ├── v9_academic_terms.sql      # Academic semester terms & calendars
│   ├── v10_academic_calendar_integrity.sql # Calendar date constraints
│   ├── v11_student_academic_progress_repair.sql # GPA/CGPA computation repair
│   ├── v12_current_cohort_academic_years.sql   # Cohort year normalization
│   ├── v13_online_assessments.sql # Online quiz/exam questions & answers
│   ├── v14_student_timetable.sql  # Normalized student timetable mapping
│   └── v15_timetable_coverage.sql # Timetable slots & teacher room coverage
│
├── seed/                          # Comprehensive Realistic Seed SQL Data
│   ├── 1_admins.sql               # Default admin accounts
│   ├── 2_departments.sql          # CS, IT, SE, EE, BBA departments
│   ├── 3_teachers.sql             # Faculty seed profiles & credentials
│   ├── 4_students.sql             # Student seed profiles across cohorts
│   ├── 5_courses.sql              # Core & elective course catalog
│   ├── 6_enrollments.sql          # Student course enrollment mappings
│   ├── 8_course_results.sql       # Graded course results & GPA points
│   ├── 9_semester_gpa.sql         # Semester GPA history records
│   ├── 10_student_cgpa.sql        # Cumulative CGPA summaries
│   ├── assignments.sql            # Sample assignments & submissions
│   ├── attendance.sql             # Historical lecture attendance data
│   ├── grades.sql                 # Sessional & midterm grade records
│   ├── hostels.sql                # Hostel allocation records
│   ├── library.sql                # Library inventory & issued books
│   └── notifications.sql          # University notices & circulars
│
├── triggers/                      # Automated Database Integrity Triggers
│   ├── 22_triggers.sql            # GPA recalculation & audit logging triggers
│   ├── 22_triggers.sql            # Canonical corrected trigger set
│   └── 22_triggers_legacy.sql     # Historical reference only
│
├── views/                         # Pre-compiled Analytical SQL Views
│   └── 21_views.sql               # Student transcripts, course statistics, attendance %
│
└── backups/                       # Snapshot backups of active databases
```

---

## 🔗 Key Entity Relationships

```
              ┌───────────────┐
              │  departments  │
              └───────┬───────┘
                      │
        ┌─────────────┴─────────────┐
        │ 1:N                       │ 1:N
        ▼                           ▼
 ┌──────────────┐            ┌──────────────┐
 │   teachers   │            │   students   │
 └──────┬───────┘            └──────┬───────┘
        │                           │
        │ 1:N                       │ 1:N
        ▼                           ▼
 ┌──────────────┐            ┌──────────────┐
 │   courses    │◄───────────┤ enrollments  │
 └──────┬───────┘    M:N     └──────┬───────┘
        │                           │
   ┌────┴───────────────────────────┴────┐
   │ 1:N                                 │ 1:N
   ▼                                     ▼
┌──────────────┐                      ┌──────────────┐
│ assignments  │                      │  attendance  │
└──────┬───────┘                      └──────────────┘
       │
       │ 1:N
       ▼
┌──────────────┐
│ submissions  │
└──────────────┘
```

---

## 📊 Core Data Entities & Descriptions

| Entity / Table | Description | Key Fields |
|---|---|---|
| `users` | Core credentials and role identifiers | `id`, `username`, `email`, `password_hash`, `role`, `is_active` |
| `students` | Student demographic and academic profiles | `id`, `user_id`, `reg_no`, `roll_no`, `name`, `department_id`, `semester` |
| `teachers` | Faculty members and department affiliations | `id`, `user_id`, `employee_id`, `name`, `department_id`, `designation` |
| `departments` | Academic faculties and departments | `id`, `code`, `name`, `faculty_name` |
| `courses` | Course catalog with credit weightages | `id`, `code`, `name`, `credit_hours`, `department_id` |
| `enrollments` | Active semester course registrations | `id`, `student_id`, `course_id`, `teacher_id`, `semester`, `section` |
| `attendance` | Daily lecture attendance records | `id`, `enrollment_id`, `date`, `status` (Present/Absent/Late/Excused) |
| `assignments` | Course coursework created by teachers | `id`, `course_id`, `teacher_id`, `title`, `deadline`, `max_marks` |
| `submissions` | Student assignment work and marks | `id`, `assignment_id`, `student_id`, `submission_file`, `obtained_marks` |
| `course_results` | Final grades and computed GPA points | `id`, `student_id`, `course_id`, `marks`, `gpa`, `letter_grade` |
| `semester_gpa` | Aggregated semester performance | `id`, `student_id`, `semester`, `gpa`, `credits_earned` |
| `student_cgpa` | Cumulative GPA across all semesters | `id`, `student_id`, `cgpa`, `total_credits_earned`, `academic_standing` |
| `fee_records` | Student financial invoices and dues | `id`, `student_id`, `challan_no`, `amount`, `status`, `due_date` |
| `library` | Digital library books and borrow logs | `id`, `title`, `author`, `isbn`, `available_copies` |
| `audit_logs` | Immutable Zero-Trust security trails | `id`, `user_id`, `action`, `resource`, `timestamp`, `ip_address` |

---

## 🛠️ Database Setup & Provisioning

To initialize, migrate, and seed the SQLite database from scratch:

```bash
# Run the automated provisioning script from repository root
python scripts/setup_database.py
```

This executes:
1. All DDL schemas in `database/schema/` in numerical order.
2. All migrations in `database/migrations/`.
3. All triggers in `database/triggers/` and views in `database/views/`.
4. Comprehensive seed datasets from `database/seed/`.

---

## 🔐 Default Test Credentials

All seed accounts share the default password:
- **Default Password**: `UOH@2025`

### Sample Accounts:
- **Student Usernames**: `hamza.ali24`, `ahmed.raza24`, `usman.khan24`, `bilal.raja24`, `zain.abidin24`
- **Teacher Emails / Usernames**: `ahmad.malik@uoh.edu.pk`, `usman.ali@uoh.edu.pk`, `sara.khan@uoh.edu.pk`
- **Admin**: `admin`
> **Current source of truth:** `database/university.db` is generated and Git-ignored. Build it with `python scripts/setup_database.py`. Empty historical placeholders were removed; `triggers/22_triggers.sql` is the corrected canonical trigger set and `22_triggers_legacy.sql` is retained only for reference.
