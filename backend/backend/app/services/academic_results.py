"""Term-aware academic result helpers."""
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.academic_term import AcademicTerm
from app.models.course_result import CourseResult
from app.models.enrollment import Enrollment
from app.models.semester_gpa import SemesterGPA
from app.models.student_cgpa import StudentCGPA


def completed_term_keys(db: Session) -> set[tuple[str, int]]:
    return {
        (term.academic_year, term.semester)
        for term in db.query(AcademicTerm).filter(AcademicTerm.status == "Completed").all()
    }


def term_status(db: Session, academic_year: str, semester: int) -> str:
    term = db.query(AcademicTerm).filter(
        AcademicTerm.academic_year == academic_year,
        AcademicTerm.semester == semester,
    ).first()
    # Fail closed: unconfigured terms remain progress data and cannot publish.
    return term.status if term else "Active"


def finalized_term_keys_for_student(db: Session, student_id: int, current_semester: int) -> set[tuple[str, int]]:
    """Completed terms visible as final results for one student.

    The student's profile semester is the active boundary.  Academic term
    records are shared by multiple cohorts, so a global "Completed" status
    must not finalize the current semester for a newer student.
    """
    return {
        (row.academic_year, row.semester)
        for row in db.query(Enrollment.academic_year, Enrollment.semester)
        .filter(
            Enrollment.student_id == student_id,
            Enrollment.semester < current_semester,
        )
        .all()
    }


def completed_cgpa_for_student(db: Session, student_id: int, current_semester: int) -> tuple[float, int]:
    """Return CGPA and completed credits without trusting stale cached CGPA."""
    finalized = finalized_term_keys_for_student(db, student_id, current_semester)
    rows = [row for row in db.query(CourseResult).filter(CourseResult.student_id == student_id).all()
            if (row.academic_year, row.semester) in finalized]
    credits = sum(int(row.credit_hours or 0) for row in rows if (row.letter_grade or "").upper() != "F")
    quality_points = sum(float(row.quality_points or 0) for row in rows)
    return (round(quality_points / credits, 2) if credits else 0.0, credits)


def recalculate_student_completed_results(db: Session, student_id: int) -> StudentCGPA:
    """Rebuild SGPA/CGPA exclusively from explicitly completed terms."""
    completed = completed_term_keys(db)
    grouped: dict[tuple[str, int], list[CourseResult]] = defaultdict(list)
    for row in db.query(CourseResult).filter(CourseResult.student_id == student_id).all():
        if (row.academic_year, row.semester) in completed:
            grouped[(row.academic_year, row.semester)].append(row)

    # Do not delete historical SGPA rows when a term is reopened. The API
    # publication boundary hides them until the registrar completes the term
    # again, preserving recoverable academic history.

    total_credits = 0
    total_quality_points = 0.0
    passed = failed = 0
    for (academic_year, semester), rows in grouped.items():
        credits = sum(int(row.credit_hours or 0) for row in rows)
        quality_points = sum(float(row.quality_points or 0) for row in rows)
        earned = sum(int(row.credit_hours or 0) for row in rows if (row.letter_grade or "").upper() != "F")
        gpa = round(quality_points / credits, 2) if credits else 0.0
        sgpa = db.query(SemesterGPA).filter(
            SemesterGPA.student_id == student_id,
            SemesterGPA.academic_year == academic_year,
            SemesterGPA.semester == semester,
        ).first()
        values = dict(total_credit_hours=credits, earned_credit_hours=earned,
                      total_grade_points=quality_points, semester_gpa=gpa,
                      academic_status="Good Standing" if gpa >= 2 else "Academic Warning",
                      remarks="Finalized completed term", updated_at=datetime.utcnow())
        if sgpa:
            for key, value in values.items():
                setattr(sgpa, key, value)
        else:
            db.add(SemesterGPA(student_id=student_id, academic_year=academic_year, semester=semester, **values))
        total_credits += earned
        total_quality_points += quality_points
        passed += sum(1 for row in rows if (row.letter_grade or "").upper() != "F")
        failed += sum(1 for row in rows if (row.letter_grade or "").upper() == "F")

    cgpa = round(total_quality_points / total_credits, 2) if total_credits else 0.0
    record = db.query(StudentCGPA).filter(StudentCGPA.student_id == student_id).first()
    values = dict(total_completed_credit_hours=total_credits, total_grade_points=total_quality_points,
                  overall_cgpa=cgpa, total_passed_courses=passed, total_failed_courses=failed,
                  academic_status="Good Standing" if cgpa >= 2 else "Academic Warning",
                  last_calculated=datetime.utcnow())
    if record:
        for key, value in values.items():
            setattr(record, key, value)
    else:
        record = StudentCGPA(student_id=student_id, **values)
        db.add(record)
    return record
