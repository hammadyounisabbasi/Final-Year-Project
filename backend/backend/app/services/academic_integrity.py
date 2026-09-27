"""Read-only, evidence-grounded Academic Integrity queries.

The service deliberately does not create cases, alter marks, or infer misconduct.
It reports stored evidence and deterministic relationship/mark inconsistencies only.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.models.course import Course
from app.models.course_result import CourseResult
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.exam import Assessment, AssessmentAttempt, AssessmentResponse
from app.models.grade import Grade
from app.models.student import Student
from app.models.submission import Submission
from app.models.teacher import Teacher
from app.core.config import settings
from app.services.gradebook_records import build_gradebook_snapshot


HIGH_SIMILARITY = 75.0
REVIEW_SIMILARITY = 40.0
TEXT_EXTENSIONS = {".txt", ".md", ".py", ".js", ".ts", ".java", ".c", ".cpp", ".sql", ".html", ".css", ".json", ".csv"}


def _iso(value):
    return value.isoformat() if value else None


def _name(person) -> str:
    return f"{person.first_name} {person.last_name}".strip()


def _normalise(value: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", (value or "").casefold())).strip()


def _safe_submission_text(submission: Submission) -> tuple[str, str | None]:
    """Return analyzable text without exposing a local filesystem path."""
    parts = [submission.response_text or ""]
    if submission.file_path and submission.file_path != "inline":
        root = settings.UPLOAD_DIR.parent
        candidate = (root / submission.file_path).resolve()
        try:
            candidate.relative_to(root.resolve())
            if candidate.exists() and candidate.suffix.casefold() in TEXT_EXTENSIONS:
                parts.append(candidate.read_text(encoding="utf-8", errors="ignore")[:15000])
            elif not candidate.exists():
                return "\n".join(parts).strip(), "Stored file is missing from the server."
            else:
                return "\n".join(parts).strip(), "File content preview is unavailable for this file type."
        except (OSError, ValueError):
            return "\n".join(parts).strip(), "Stored file could not be read safely."
    text = "\n".join(parts).strip()
    return text, None if text else "No readable submission text is stored."


def _similarity_matches(db: Session, submission: Submission) -> list[dict]:
    siblings = (db.query(Submission).options(joinedload(Submission.student))
                .filter(Submission.assignment_id == submission.assignment_id).all())
    texts = {row.submission_id: _normalise(_safe_submission_text(row)[0]) for row in siblings}
    current = texts.get(submission.submission_id, "")
    if len(current.split()) < 20:
        return []
    matches = []
    for other in siblings:
        if other.submission_id == submission.submission_id:
            continue
        other_text = texts.get(other.submission_id, "")
        if len(other_text.split()) < 20:
            continue
        ratio = SequenceMatcher(None, current, other_text).ratio()
        if ratio >= 0.82:
            matches.append({
                "submission_id": other.submission_id,
                "student_id": other.student_id,
                "student_name": _name(other.student),
                "roll_number": other.student.roll_number,
                "similarity_percent": round(ratio * 100, 1),
                "scope": "Same-assignment student submissions only",
            })
    return sorted(matches, key=lambda row: row["similarity_percent"], reverse=True)


def _submission_state(row: Submission) -> tuple[str, str]:
    score = row.plagiarism_score
    if score is not None and score >= HIGH_SIMILARITY:
        return "High Similarity", "high"
    if score is not None and score >= REVIEW_SIMILARITY:
        return "Review Suggested", "review"
    if not row.file_hash and not (row.response_text or "").strip() and row.file_path == "inline":
        return "Evidence Incomplete", "high"
    if row.verified:
        return "Verified", "info"
    if score is not None or row.ai_feedback:
        return "Evidence Available", "info"
    return "Normal", "info"


def integrity_warnings(db: Session) -> list[dict]:
    warnings: list[dict] = []

    grades = (db.query(Grade).options(
        joinedload(Grade.enrollment).joinedload(Enrollment.student),
        joinedload(Grade.enrollment).joinedload(Enrollment.course),
        joinedload(Grade.teacher),
    ).all())
    assignments = db.query(Assignment).all()
    assignment_lookup: dict[tuple, list[Assignment]] = {}
    for item in assignments:
        key = (item.course_id, item.academic_year, item.semester, _normalise(item.title))
        assignment_lookup.setdefault(key, []).append(item)

    assessments = db.query(Assessment).all()
    assessment_lookup = {(item.course_id, item.academic_year, item.semester, _normalise(item.title)): item for item in assessments}
    assessment_by_id = {item.assessment_id: item for item in assessments}
    submission_pairs = set(db.query(Submission.assignment_id, Submission.student_id).distinct().all())
    attempts = (db.query(AssessmentAttempt).options(
        joinedload(AssessmentAttempt.assessment).joinedload(Assessment.course), joinedload(AssessmentAttempt.student)).all())
    attempt_lookup = {(item.assessment_id, item.student_id): item for item in attempts}
    enrollment_lookup = {row.enrollment_id: row for row in db.query(Enrollment).all()}
    response_totals = {attempt_id: float(total or 0) for attempt_id, total in db.query(
        AssessmentResponse.attempt_id, func.sum(AssessmentResponse.awarded_marks)).group_by(AssessmentResponse.attempt_id).all()}
    grade_counts = {enrollment_id: count for enrollment_id, count in db.query(
        Grade.enrollment_id, func.count(Grade.grade_id)).group_by(Grade.enrollment_id).all()}

    for grade in grades:
        enrollment = grade.enrollment
        if not enrollment:
            warnings.append(_warning("GRADE_ENROLLMENT_MISSING", "High Priority Review", "Grade references no available enrollment.", "grade", grade.grade_id))
            continue
        common = {
            "student_id": enrollment.student_id,
            "student_name": _name(enrollment.student),
            "roll_number": enrollment.student.roll_number,
            "course_id": enrollment.course_id,
            "course": f"{enrollment.course.course_code} — {enrollment.course.course_title}",
            "teacher_id": grade.graded_by,
            "teacher_name": _name(grade.teacher) if grade.teacher else None,
        }
        if grade.obtained_marks < 0 or grade.total_marks < 0 or grade.obtained_marks > grade.total_marks:
            warnings.append(_warning("MARK_INVALID_RANGE", "High Priority Review", f"Recorded marks {grade.obtained_marks:g}/{grade.total_marks:g} are outside valid bounds.", "grade", grade.grade_id, **common))
        if grade.academic_year and grade.academic_year != enrollment.academic_year:
            warnings.append(_warning("GRADE_YEAR_MISMATCH", "High Priority Review", "Grade academic year does not match its enrollment.", "grade", grade.grade_id, **common))
        if grade.semester and grade.semester != enrollment.semester:
            warnings.append(_warning("GRADE_SEMESTER_MISMATCH", "High Priority Review", "Grade semester does not match its enrollment.", "grade", grade.grade_id, **common))

        online_assessment_id = None
        if grade.title.startswith("OnlineAssessment:"):
            parts = grade.title.split(":", 2)
            online_assessment_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            raw_title = parts[2] if len(parts) > 2 else grade.title
        else:
            raw_title = grade.title.split(":")[-1] if grade.title.startswith("Gradebook:") else grade.title
        key = (enrollment.course_id, grade.academic_year or enrollment.academic_year, grade.semester or enrollment.semester, _normalise(raw_title))
        if grade.assessment_type == "Assignment" and assignment_lookup.get(key):
            assignment = assignment_lookup[key][0]
            if (assignment.assignment_id, enrollment.student_id) not in submission_pairs:
                warnings.append(_warning("ASSIGNMENT_SUBMISSION_MISSING", "High Priority Review", "A linked assignment grade exists, but no matching submission is stored.", "grade", grade.grade_id, assignment_id=assignment.assignment_id, **common))
        assessment = assessment_by_id.get(online_assessment_id) if online_assessment_id else assessment_lookup.get(key)
        if assessment:
            attempt = attempt_lookup.get((assessment.assessment_id, enrollment.student_id))
            if not attempt:
                warnings.append(_warning("ASSESSMENT_ATTEMPT_MISSING", "High Priority Review", "A linked assessment grade exists, but no attempt is stored.", "grade", grade.grade_id, assessment_id=assessment.assessment_id, **common))
            elif abs(float(attempt.obtained_marks) - float(grade.obtained_marks)) > 0.001:
                warnings.append(_warning("AUTO_SCORE_RECORDED_MISMATCH", "High Priority Review", f"Attempt score is {attempt.obtained_marks:g}/{attempt.total_marks:g}, while the linked grade is {grade.obtained_marks:g}/{grade.total_marks:g}.", "grade", grade.grade_id, assessment_id=assessment.assessment_id, attempt_id=attempt.attempt_id, **common))

    for attempt in attempts:
        enrollment = enrollment_lookup.get(attempt.enrollment_id)
        common = {"student_id": attempt.student_id, "student_name": _name(attempt.student), "roll_number": attempt.student.roll_number,
                  "course_id": attempt.assessment.course_id, "course": attempt.assessment.course.course_code if attempt.assessment.course else None,
                  "assessment_id": attempt.assessment_id, "attempt_id": attempt.attempt_id}
        if attempt.obtained_marks < 0 or attempt.total_marks < 0 or attempt.obtained_marks > attempt.total_marks:
            warnings.append(_warning("ATTEMPT_MARK_INVALID_RANGE", "High Priority Review", f"Attempt marks {attempt.obtained_marks:g}/{attempt.total_marks:g} are outside valid bounds.", "attempt", attempt.attempt_id, **common))
        calculated = response_totals.get(attempt.attempt_id, 0.0)
        if attempt.status != "In Progress" and abs(float(calculated) - float(attempt.obtained_marks)) > 0.001:
            warnings.append(_warning("AUTO_SCORE_MISMATCH", "High Priority Review", f"Stored attempt score is {attempt.obtained_marks:g}; response total is {float(calculated):g}.", "attempt", attempt.attempt_id, **common))
        if not enrollment or enrollment.student_id != attempt.student_id or enrollment.course_id != attempt.assessment.course_id:
            warnings.append(_warning("ATTEMPT_ENROLLMENT_MISMATCH", "High Priority Review", "Attempt student/course does not align with its enrollment evidence.", "attempt", attempt.attempt_id, **common))

    results = (db.query(CourseResult).options(joinedload(CourseResult.student), joinedload(CourseResult.course), joinedload(CourseResult.teacher)).all())
    for result in results:
        enrollment = enrollment_lookup.get(result.enrollment_id)
        common = {"student_id": result.student_id, "student_name": _name(result.student), "roll_number": result.student.roll_number,
                  "course_id": result.course_id, "course": f"{result.course.course_code} — {result.course.course_title}",
                  "teacher_id": result.teacher_id, "teacher_name": _name(result.teacher) if result.teacher else None}
        if not enrollment or enrollment.student_id != result.student_id or enrollment.course_id != result.course_id:
            warnings.append(_warning("RESULT_ENROLLMENT_MISMATCH", "High Priority Review", "Course result does not align with its enrollment/student/course relationship.", "result", result.result_id, **common))
        elif enrollment.semester != result.semester or enrollment.academic_year != result.academic_year:
            warnings.append(_warning("RESULT_TERM_MISMATCH", "High Priority Review", "Course result semester/year does not match its enrollment.", "result", result.result_id, **common))
        if result.total_marks is not None and (result.total_marks < 0 or result.total_marks > 100):
            warnings.append(_warning("RESULT_TOTAL_INVALID", "High Priority Review", f"Course result total {result.total_marks:g} is outside the configured 0–100 result scale.", "result", result.result_id, **common))
        if result.published:
            grade_count = grade_counts.get(result.enrollment_id, 0)
            if grade_count == 0:
                warnings.append(_warning("PUBLISHED_RESULT_EVIDENCE_INCOMPLETE", "Review Suggested", "Published result has no component Grade rows in the current database.", "result", result.result_id, **common))
        if enrollment:
            snapshot = build_gradebook_snapshot(db, enrollment)
            for component in snapshot["components"]:
                if component["status"] != "CONFLICT":
                    continue
                online_evidence = component.get("online_evidence", [])
                warnings.append(_warning(
                    "GRADE_SOURCE_CONFLICT",
                    "High Priority Review",
                    component["message"],
                    "result",
                    result.result_id,
                    evidence_type="gradebook_component",
                    component_id=component["component_id"],
                    manual_grade_ids=component.get("manual_grade_ids", []),
                    assessment_ids=[item["assessment_id"] for item in online_evidence],
                    attempt_ids=[item["attempt_id"] for item in online_evidence if item.get("attempt_id")],
                    **common,
                ))
            for check in snapshot["checks"]:
                if check["status"] in {"missing", "unavailable"}:
                    warnings.append(_warning(
                        "GRADEBOOK_EVIDENCE_INCOMPLETE",
                        "Review Suggested",
                        check["message"],
                        "result",
                        result.result_id,
                        evidence_type=check["type"],
                        **common,
                    ))
                elif check["status"] == "conflict":
                    warnings.append(_warning(
                        "GRADE_SOURCE_CONFLICT",
                        "High Priority Review",
                        check["message"],
                        "result",
                        result.result_id,
                        evidence_type=check["type"],
                        **common,
                    ))
    return warnings


def _warning(code: str, severity: str, message: str, record_type: str, record_id: int, **extra) -> dict:
    return {"code": code, "severity": severity, "message": message, "record_type": record_type, "record_id": record_id, **extra}


def overview(db: Session) -> dict:
    warnings = integrity_warnings(db)
    total_submissions = db.query(func.count(Submission.submission_id)).scalar() or 0
    scored = db.query(func.count(Submission.submission_id)).filter(Submission.plagiarism_score.isnot(None)).scalar() or 0
    high = db.query(func.count(Submission.submission_id)).filter(Submission.plagiarism_score >= HIGH_SIMILARITY).scalar() or 0
    verified = db.query(func.count(Submission.submission_id)).filter(Submission.verified.is_(True)).scalar() or 0
    ungraded = db.query(func.count(Submission.submission_id)).filter(Submission.graded.is_(False), Submission.submission_status != "Draft").scalar() or 0
    warning_students = len({row.get("student_id") for row in warnings if row.get("student_id")})
    scores = [float(value) for (value,) in db.query(Submission.plagiarism_score).filter(Submission.plagiarism_score.isnot(None)).all()]
    distribution = {"0–25": 0, "26–50": 0, "51–75": 0, "76–100": 0}
    for score in scores:
        distribution["0–25" if score <= 25 else "26–50" if score <= 50 else "51–75" if score <= 75 else "76–100"] += 1
    warning_types = Counter(row["code"] for row in warnings)
    departments = [{"id": row.department_id, "name": row.department_name} for row in db.query(Department).order_by(Department.department_name)]
    courses = [{"id": row.course_id, "code": row.course_code, "title": row.course_title} for row in db.query(Course).order_by(Course.course_code)]
    teachers = [{"id": row.teacher_id, "name": _name(row), "employee_id": row.employee_id} for row in db.query(Teacher).order_by(Teacher.first_name, Teacher.last_name)]
    return {
        "definitions": {
            "high_similarity": f"Stored plagiarism_score ≥ {HIGH_SIMILARITY:g}; this is a review signal, not a misconduct decision.",
            "pending_review": "Submitted/under-review submissions that are not verified or graded.",
            "data_warnings": "Deterministic mark, attempt, enrollment, term, or supporting-evidence inconsistencies.",
        },
        "stats": {
            "total_assignments": db.query(func.count(Assignment.assignment_id)).scalar() or 0,
            "total_submissions": total_submissions,
            "similarity_scored": scored,
            "high_similarity": high,
            "verified_submissions": verified,
            "ungraded_submissions": ungraded,
            "data_warnings": len(warnings),
            "students_needing_review": warning_students,
        },
        "charts": {
            "similarity_distribution": [{"label": key, "count": value} for key, value in distribution.items()],
            "warning_categories": [{"code": key, "count": value} for key, value in warning_types.most_common()],
        },
        "filters": {"departments": departments, "courses": courses, "teachers": teachers},
        "limitations": [
            "Stored similarity scores are unavailable for submissions where plagiarism_score is null.",
            "Live comparison is limited to readable submissions for the same assignment; it is not an internet plagiarism search.",
            "A Grade row can only be linked to an assignment or online assessment when its stored title identifies that record.",
        ],
    }


def list_submissions(db: Session, *, search: str = "", department_id: int | None = None, course_id: int | None = None,
                     teacher_id: int | None = None, semester: int | None = None, review_state: str = "",
                     grading_status: str = "", min_similarity: float | None = None, max_similarity: float | None = None,
                     sort_by: str = "submitted_at", sort_order: str = "desc", page: int = 1, page_size: int = 20) -> dict:
    query = (db.query(Submission).join(Assignment).join(Student, Submission.student_id == Student.student_id)
             .join(Course, Assignment.course_id == Course.course_id).join(Teacher, Assignment.teacher_id == Teacher.teacher_id)
             .options(joinedload(Submission.assignment).joinedload(Assignment.course).joinedload(Course.department),
                      joinedload(Submission.assignment).joinedload(Assignment.teacher), joinedload(Submission.student)))
    if search:
        like = f"%{search.strip().casefold()}%"
        query = query.filter(or_(func.lower(Student.first_name + " " + Student.last_name).like(like), func.lower(Student.roll_number).like(like),
                                 func.lower(Assignment.title).like(like), func.lower(Course.course_code).like(like), func.lower(Course.course_title).like(like),
                                 func.lower(Teacher.first_name + " " + Teacher.last_name).like(like)))
    if department_id: query = query.filter(Course.department_id == department_id)
    if course_id: query = query.filter(Assignment.course_id == course_id)
    if teacher_id: query = query.filter(Assignment.teacher_id == teacher_id)
    if semester: query = query.filter(Assignment.semester == semester)
    if grading_status == "graded": query = query.filter(Submission.graded.is_(True))
    if grading_status == "ungraded": query = query.filter(Submission.graded.is_(False))
    if min_similarity is not None: query = query.filter(Submission.plagiarism_score >= min_similarity)
    if max_similarity is not None: query = query.filter(Submission.plagiarism_score <= max_similarity)
    if review_state == "high": query = query.filter(Submission.plagiarism_score >= HIGH_SIMILARITY)
    elif review_state == "review": query = query.filter(Submission.plagiarism_score >= REVIEW_SIMILARITY, Submission.plagiarism_score < HIGH_SIMILARITY)
    elif review_state == "verified": query = query.filter(Submission.verified.is_(True))
    elif review_state == "unscored": query = query.filter(Submission.plagiarism_score.is_(None))
    total = query.count()
    sort_map = {"submitted_at": Submission.submitted_at, "similarity": Submission.plagiarism_score,
                "student": Student.first_name, "course": Course.course_code, "assignment": Assignment.title,
                "marks": Submission.teacher_marks}
    column = sort_map.get(sort_by, Submission.submitted_at)
    rows = query.order_by(column.asc() if sort_order == "asc" else column.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for row in rows:
        state, severity = _submission_state(row)
        items.append({
            "submission_id": row.submission_id, "student_id": row.student_id, "student_name": _name(row.student), "roll_number": row.student.roll_number,
            "assignment_id": row.assignment_id, "assignment": row.assignment.title, "course_id": row.assignment.course_id,
            "course_code": row.assignment.course.course_code, "course_title": row.assignment.course.course_title,
            "department": row.assignment.course.department.department_name if row.assignment.course.department else None,
            "teacher_id": row.assignment.teacher_id, "teacher": _name(row.assignment.teacher), "semester": row.assignment.semester,
            "submitted_at": _iso(row.submitted_at), "similarity_score": row.plagiarism_score, "ai_score": row.ai_score,
            "verified": bool(row.verified), "graded": bool(row.graded), "teacher_marks": row.teacher_marks,
            "total_marks": row.assignment.total_marks, "submission_status": row.submission_status, "review_state": state, "severity": severity,
        })
    return {"items": items, "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": math.ceil(total / page_size) if total else 0}}


def submission_detail(db: Session, submission_id: int) -> dict:
    row = (db.query(Submission).options(joinedload(Submission.student).joinedload(Student.department),
            joinedload(Submission.assignment).joinedload(Assignment.course).joinedload(Course.department),
            joinedload(Submission.assignment).joinedload(Assignment.teacher)).filter_by(submission_id=submission_id).first())
    if not row:
        raise HTTPException(404, "Submission not found")
    assignment, student = row.assignment, row.student
    enrollment = db.query(Enrollment).filter_by(student_id=student.student_id, course_id=assignment.course_id,
                                                 academic_year=assignment.academic_year, semester=assignment.semester).first()
    content, content_error = _safe_submission_text(row)
    matches = _similarity_matches(db, row)
    duplicate_hashes = []
    if row.file_hash:
        duplicate_hashes = [{"submission_id": other.submission_id, "student_name": _name(other.student), "roll_number": other.student.roll_number}
                            for other in db.query(Submission).options(joinedload(Submission.student)).filter(
                                Submission.file_hash == row.file_hash, Submission.submission_id != row.submission_id).all()]
    state, severity = _submission_state(row)
    warnings = []
    if row.teacher_marks is not None and (row.teacher_marks < 0 or row.teacher_marks > assignment.total_marks):
        warnings.append(_warning("SUBMISSION_MARK_INVALID_RANGE", "High Priority Review", "Teacher marks are outside assignment bounds.", "submission", row.submission_id))
    if not enrollment:
        warnings.append(_warning("SUBMISSION_ENROLLMENT_MISSING", "High Priority Review", "No matching course/year/semester enrollment was found.", "submission", row.submission_id))
    return {
        "submission": {"submission_id": row.submission_id, "title": row.submission_title, "file_name": row.file_name,
                       "file_size": row.file_size, "file_type": row.file_type, "file_hash": row.file_hash,
                       "submitted_at": _iso(row.submitted_at), "is_late": bool(row.is_late), "attempt": row.submission_attempt,
                       "status": row.submission_status, "verified": bool(row.verified), "graded": bool(row.graded),
                       "teacher_marks": row.teacher_marks, "teacher_feedback": row.teacher_feedback,
                       "ai_score": row.ai_score, "ai_feedback": row.ai_feedback, "plagiarism_score": row.plagiarism_score,
                       "content_preview": content[:12000] if content else None, "content_status": content_error or "Readable evidence available."},
        "student": {"student_id": student.student_id, "name": _name(student), "roll_number": student.roll_number,
                    "registration_number": student.registration_number, "department": student.department.department_name if student.department else None,
                    "semester": student.semester, "section": student.section},
        "assignment": {"assignment_id": assignment.assignment_id, "title": assignment.title, "description": assignment.description,
                       "type": assignment.assignment_type, "course_id": assignment.course_id, "course_code": assignment.course.course_code,
                       "course_title": assignment.course.course_title, "teacher_id": assignment.teacher_id, "teacher": _name(assignment.teacher),
                       "total_marks": assignment.total_marks, "due_date": _iso(assignment.due_date), "academic_year": assignment.academic_year,
                       "semester": assignment.semester, "section": assignment.section},
        "enrollment": None if not enrollment else {"enrollment_id": enrollment.enrollment_id, "status": enrollment.enrollment_status,
                                                     "academic_year": enrollment.academic_year, "semester": enrollment.semester, "section": enrollment.section},
        "integrity": {"review_state": state, "severity": severity, "internal_similarity_matches": matches,
                      "duplicate_file_hash_matches": duplicate_hashes, "warnings": warnings,
                      "similarity_scope": "Stored score provenance is not recorded. Live matches compare readable same-assignment student submissions only; no internet search is performed."},
    }


def list_warnings(db: Session, *, severity: str = "", code: str = "", student_id: int | None = None,
                  teacher_id: int | None = None, course_id: int | None = None, page: int = 1, page_size: int = 20) -> dict:
    rows = integrity_warnings(db)
    if severity: rows = [row for row in rows if row["severity"].casefold() == severity.casefold()]
    if code: rows = [row for row in rows if row["code"] == code]
    if student_id: rows = [row for row in rows if row.get("student_id") == student_id]
    if teacher_id: rows = [row for row in rows if row.get("teacher_id") == teacher_id]
    if course_id: rows = [row for row in rows if row.get("course_id") == course_id]
    total = len(rows)
    start = (page - 1) * page_size
    return {"items": rows[start:start + page_size], "pagination": {"page": page, "page_size": page_size, "total": total,
                                                                       "total_pages": math.ceil(total / page_size) if total else 0}}


def student_integrity(db: Session, student_id: int) -> dict:
    student = db.query(Student).options(joinedload(Student.department)).filter_by(student_id=student_id).first()
    if not student: raise HTTPException(404, "Student not found")
    submissions = db.query(Submission).filter_by(student_id=student_id).order_by(Submission.submitted_at.desc()).all()
    attempts = (db.query(AssessmentAttempt).options(joinedload(AssessmentAttempt.assessment).joinedload(Assessment.course))
                .filter_by(student_id=student_id).order_by(AssessmentAttempt.started_at.desc()).all())
    results = (db.query(CourseResult).options(joinedload(CourseResult.course)).filter_by(student_id=student_id)
               .order_by(CourseResult.created_at.desc()).all())
    warnings = [row for row in integrity_warnings(db) if row.get("student_id") == student_id]
    return {"student": {"student_id": student_id, "name": _name(student), "roll_number": student.roll_number,
                         "department": student.department.department_name if student.department else None},
            "summary": {"submissions": len(submissions), "similarity_scored": sum(row.plagiarism_score is not None for row in submissions),
                        "high_similarity": sum(row.plagiarism_score is not None and row.plagiarism_score >= HIGH_SIMILARITY for row in submissions),
                        "assessment_attempts": len(attempts), "course_results": len(results), "data_warnings": len(warnings)},
            "submissions": [{"submission_id": row.submission_id, "assignment": row.assignment.title, "submitted_at": _iso(row.submitted_at),
                              "similarity_score": row.plagiarism_score, "graded": bool(row.graded), "teacher_marks": row.teacher_marks} for row in submissions],
            "attempts": [{"attempt_id": row.attempt_id, "assessment": row.assessment.title, "course": row.assessment.course.course_code,
                           "status": row.status, "started_at": _iso(row.started_at), "submitted_at": _iso(row.submitted_at),
                           "score": row.obtained_marks, "total_marks": row.total_marks, "violations": row.fullscreen_violations,
                           "auto_submit_reason": row.auto_submit_reason} for row in attempts],
            "results": [{"result_id": row.result_id, "course": row.course.course_code, "academic_year": row.academic_year,
                          "semester": row.semester, "total_marks": row.total_marks, "published": bool(row.published), "verified": bool(row.verified)} for row in results],
            "warnings": warnings}


def teacher_integrity(db: Session, teacher_id: int) -> dict:
    teacher = db.query(Teacher).options(joinedload(Teacher.department)).filter_by(teacher_id=teacher_id).first()
    if not teacher: raise HTTPException(404, "Teacher not found")
    assignments = db.query(Assignment).filter_by(teacher_id=teacher_id).all()
    assignment_ids = [row.assignment_id for row in assignments]
    submissions = db.query(Submission).filter(Submission.assignment_id.in_(assignment_ids)).all() if assignment_ids else []
    warnings = [row for row in integrity_warnings(db) if row.get("teacher_id") == teacher_id]
    return {"teacher": {"teacher_id": teacher_id, "name": _name(teacher), "employee_id": teacher.employee_id,
                         "department": teacher.department.department_name if teacher.department else None},
            "summary": {"assignments": len(assignments), "submissions_received": len(submissions),
                        "graded_submissions": sum(bool(row.graded) for row in submissions),
                        "ungraded_submissions": sum(not bool(row.graded) for row in submissions), "data_warnings": len(warnings)},
            "warnings": warnings,
            "note": "This is an evidence-verification view, not a teacher performance or misconduct score."}
