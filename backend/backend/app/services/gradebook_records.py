"""Deterministic Gradebook evidence validation and online-score projection.

AssessmentAttempt is the authoritative online score. Grade rows remain the
manual Gradebook source only when no matching online assessment exists.
"""
from __future__ import annotations

import math
import re
from datetime import datetime

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.course_result import CourseResult
from app.models.enrollment import Enrollment
from app.models.exam import Assessment, AssessmentAttempt, AssessmentQuestion, AssessmentResponse
from app.models.grade import Grade
from app.models.gradebook import GradebookComponent, GradebookSetting
from app.models.submission import Submission
from app.services.gradebook import calculate_component_marks


FINAL_ATTEMPT_STATUSES = ("Submitted", "Auto Submitted")
ACTIVE_ASSESSMENT_STATUSES = ("Published", "Closed")
EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
VERIFIED = "VERIFIED"
CONFLICT = "CONFLICT"


def _tokens(value: str | None) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (value or "").casefold()))


def _assessment_type(component: GradebookComponent) -> str | None:
    if component.category in ("Midterm", "Final"):
        return component.category
    if "quiz" in _tokens(component.name) or "quizzes" in _tokens(component.name):
        return "Quiz"
    return None


def _component_manual_rows(db: Session, enrollment: Enrollment, component: GradebookComponent) -> list[Grade]:
    rows = (db.query(Grade)
            .filter(
                Grade.enrollment_id == enrollment.enrollment_id,
                Grade.title.like(f"Gradebook:{component.component_id}:%"),
            ).all())

    def item_index(row: Grade) -> int:
        parts = row.title.split(":", 3)
        return int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 10**9

    return sorted(rows, key=lambda row: (item_index(row), row.grade_id))


def _manual_component(component: GradebookComponent, rows: list[Grade]) -> dict:
    scores = [float(row.obtained_marks) for row in rows]
    valid = (
        len(rows) == component.item_count
        and all(math.isfinite(score) and 0 <= score <= component.item_total_marks for score in scores)
    )
    value = None
    if valid:
        try:
            value = calculate_component_marks(component, scores)
        except ValueError:
            valid = False
    return {
        "present": bool(rows),
        "valid": valid,
        "scores": scores,
        "grade_ids": [row.grade_id for row in rows],
        "value": value,
    }


def _assessment_attempt_evidence(db: Session, enrollment: Enrollment, assessment: Assessment) -> dict:
    attempt = (db.query(AssessmentAttempt)
               .filter(
                   AssessmentAttempt.assessment_id == assessment.assessment_id,
                   AssessmentAttempt.student_id == enrollment.student_id,
               ).first())
    base = {
        "assessment_id": assessment.assessment_id,
        "assessment": assessment.title,
        "assessment_type": assessment.assessment_type,
        "assessment_total": assessment.total_marks,
        "attempt_id": attempt.attempt_id if attempt else None,
        "attempt_status": attempt.status if attempt else "Not Attempted",
        "obtained_marks": attempt.obtained_marks if attempt else None,
        "total_marks": attempt.total_marks if attempt else None,
        "submitted_at": attempt.submitted_at.isoformat() if attempt and attempt.submitted_at else None,
        "auto_submitted": bool(attempt and attempt.status == "Auto Submitted"),
        "auto_submit_reason": attempt.auto_submit_reason if attempt else None,
    }
    if attempt is None:
        return {**base, "status": "missing", "message": "No valid online attempt found"}
    if attempt.enrollment_id != enrollment.enrollment_id:
        return {**base, "status": "conflict", "message": "Attempt enrollment does not match the selected enrollment"}
    if attempt.status not in FINAL_ATTEMPT_STATUSES or attempt.submitted_at is None:
        return {**base, "status": "incomplete", "message": "Online attempt is not submitted"}
    if not all(math.isfinite(float(value)) for value in (attempt.obtained_marks, attempt.total_marks)):
        return {**base, "status": "conflict", "message": "Online attempt contains a non-finite score"}
    if attempt.total_marks <= 0 or attempt.obtained_marks < 0 or attempt.obtained_marks > attempt.total_marks:
        return {**base, "status": "conflict", "message": "Online attempt marks are outside valid bounds"}
    question_total = float(db.query(func.sum(AssessmentQuestion.marks)).filter(
        AssessmentQuestion.assessment_id == assessment.assessment_id).scalar() or 0)
    response_total = float(db.query(func.sum(AssessmentResponse.awarded_marks)).filter(
        AssessmentResponse.attempt_id == attempt.attempt_id).scalar() or 0)
    if abs(question_total - float(assessment.total_marks)) > 0.001 or abs(question_total - float(attempt.total_marks)) > 0.001:
        return {**base, "status": "conflict", "message": "Assessment, question, and attempt totals do not agree"}
    if abs(response_total - float(attempt.obtained_marks)) > 0.001:
        return {**base, "status": "conflict", "message": "Attempt score does not equal its response evidence"}
    return {**base, "status": "verified", "message": "Submitted online attempt and response score are verified"}


def _online_component(db: Session, enrollment: Enrollment, component: GradebookComponent) -> dict:
    assessment_type = _assessment_type(component)
    if assessment_type is None:
        return {"managed": False, "assessment_type": None, "status": None, "evidence": []}
    assessments = (db.query(Assessment)
                   .filter(
                       Assessment.course_id == enrollment.course_id,
                       Assessment.academic_year == enrollment.academic_year,
                       Assessment.semester == enrollment.semester,
                       Assessment.section == enrollment.section,
                       Assessment.assessment_type == assessment_type,
                       Assessment.status.in_(ACTIVE_ASSESSMENT_STATUSES),
                   )
                   .order_by(Assessment.start_at.asc(), Assessment.assessment_id.asc())
                   .all())
    if not assessments:
        return {
            "managed": False,
            "assessment_type": assessment_type,
            "status": EVIDENCE_INCOMPLETE,
            "evidence": [],
            "message": f"No online {assessment_type} assessment is configured for this course term and section",
        }
    evidence = [_assessment_attempt_evidence(db, enrollment, item) for item in assessments]
    if len(assessments) > component.item_count:
        return {
            "managed": True,
            "assessment_type": assessment_type,
            "status": CONFLICT,
            "evidence": evidence,
            "scores": [],
            "value": None,
            "message": f"{len(assessments)} online assessments map to {component.item_count} configured item slots",
        }
    conflicts = [item for item in evidence if item["status"] == "conflict"]
    if conflicts:
        return {
            "managed": True,
            "assessment_type": assessment_type,
            "status": CONFLICT,
            "evidence": evidence,
            "scores": [],
            "value": None,
            "message": conflicts[0]["message"],
        }
    verified = [item for item in evidence if item["status"] == "verified"]
    if len(assessments) != component.item_count or len(verified) != len(assessments):
        return {
            "managed": True,
            "assessment_type": assessment_type,
            "status": EVIDENCE_INCOMPLETE,
            "evidence": evidence,
            "scores": [],
            "value": None,
            "message": f"Verified {len(verified)} of {component.item_count} required online {assessment_type} attempts",
        }
    scores = [round(float(item["obtained_marks"]) / float(item["total_marks"]) * component.item_total_marks, 4)
              for item in evidence]
    return {
        "managed": True,
        "assessment_type": assessment_type,
        "status": VERIFIED,
        "evidence": evidence,
        "scores": scores,
        "value": calculate_component_marks(component, scores),
        "message": f"{len(scores)} online {assessment_type} score(s) verified",
    }


def _lab_check(db: Session, enrollment: Enrollment, components: list[GradebookComponent]) -> dict | None:
    lab_components = [item for item in components if "lab" in _tokens(item.name) or "labs" in _tokens(item.name)]
    if not lab_components:
        return None
    assignments = (db.query(Assignment)
                   .filter(
                       Assignment.course_id == enrollment.course_id,
                       Assignment.academic_year == enrollment.academic_year,
                       Assignment.semester == enrollment.semester,
                       Assignment.assignment_type == "Lab",
                       Assignment.status.in_(("Published", "Closed", "Archived")),
                       or_(Assignment.section == enrollment.section, Assignment.section.is_(None)),
                   ).all())
    if not assignments:
        return {
            "type": "lab_completion",
            "status": "unavailable",
            "component_ids": [item.component_id for item in lab_components],
            "evidence_ids": [],
            "message": "No published Lab assignment evidence is available for this configured course term",
        }
    submissions = (db.query(Submission)
                   .filter(
                       Submission.assignment_id.in_([item.assignment_id for item in assignments]),
                       Submission.student_id == enrollment.student_id,
                       Submission.submission_status != "Draft",
                   ).order_by(Submission.submitted_at.desc()).all())
    if not submissions:
        return {
            "type": "lab_completion",
            "status": "missing",
            "component_ids": [item.component_id for item in lab_components],
            "evidence_ids": [],
            "assignment_ids": [item.assignment_id for item in assignments],
            "message": "Lab assignments are configured, but no submitted Lab evidence was found for this student",
        }
    return {
        "type": "lab_completion",
        "status": "verified",
        "component_ids": [item.component_id for item in lab_components],
        "evidence_ids": [item.submission_id for item in submissions],
        "assignment_ids": sorted({item.assignment_id for item in assignments}),
        "message": "Submitted Lab evidence was found",
    }


def build_gradebook_snapshot(db: Session, enrollment: Enrollment, setting: GradebookSetting | None = None) -> dict:
    setting = setting or db.query(GradebookSetting).filter_by(
        course_id=enrollment.course_id,
        academic_year=enrollment.academic_year,
        semester=enrollment.semester,
    ).first()
    if setting is None:
        return {
            "status": EVIDENCE_INCOMPLETE,
            "enrollment_id": enrollment.enrollment_id,
            "student_id": enrollment.student_id,
            "course_id": enrollment.course_id,
            "academic_year": enrollment.academic_year,
            "semester": enrollment.semester,
            "checks": [],
            "components": [],
            "category_totals": {"Sessional": 0.0, "Midterm": 0.0, "Final": 0.0},
            "total": 0.0,
            "message": "Grade Book Settings are not configured for this enrollment term",
        }

    component_records = []
    category_totals = {"Sessional": 0.0, "Midterm": 0.0, "Final": 0.0}
    checks = []
    has_conflict = False
    has_incomplete = False
    quiz_records = []
    for component in setting.components:
        manual = _manual_component(component, _component_manual_rows(db, enrollment, component))
        online = _online_component(db, enrollment, component)
        status = VERIFIED if manual["valid"] else EVIDENCE_INCOMPLETE
        source = "manual_gradebook"
        value = manual["value"]
        message = "Manual Gradebook evidence is complete" if manual["valid"] else "Manual Gradebook evidence is incomplete"
        if online["managed"]:
            source = "online_assessment"
            status = online["status"]
            value = online.get("value")
            message = online["message"]
            if online["status"] == VERIFIED and manual["present"]:
                expected = online.get("scores") or []
                if not manual["valid"] or len(expected) != len(manual["scores"]) or any(
                    abs(left - right) > 0.001 for left, right in zip(expected, manual["scores"])
                ):
                    status = CONFLICT
                    value = None
                    message = "GRADE_SOURCE_CONFLICT: manual Gradebook values differ from the authoritative online score"
        elif online.get("assessment_type") == "Quiz":
            quiz_records.append((component, online))

        if source == "online_assessment" and online.get("assessment_type") == "Quiz":
            quiz_records.append((component, online))
        if status == CONFLICT:
            has_conflict = True
        elif source == "online_assessment" and status != VERIFIED:
            has_incomplete = True
        if value is not None and status != CONFLICT:
            category_totals[component.category] += float(value)
        component_records.append({
            "component_id": component.component_id,
            "category": component.category,
            "name": component.name,
            "item_count": component.item_count,
            "item_total_marks": component.item_total_marks,
            "component_total_marks": component.total_marks,
            "source": source,
            "read_only": source == "online_assessment",
            "status": status,
            "synchronized_scores": online.get("scores", []) if source == "online_assessment" else [],
            "synchronized_value": value if source == "online_assessment" else None,
            "manual_grade_ids": manual["grade_ids"],
            "online_evidence": online.get("evidence", []),
            "message": message,
        })

    for component, online in quiz_records:
        evidence_ids = [item["attempt_id"] for item in online.get("evidence", []) if item.get("attempt_id")]
        check_status = "verified" if online.get("status") == VERIFIED else "conflict" if online.get("status") == CONFLICT else "missing"
        checks.append({
            "type": "quiz_completion",
            "status": check_status,
            "component_id": component.component_id,
            "evidence_ids": evidence_ids,
            "message": online.get("message", "Quiz evidence is unavailable"),
        })
    lab = _lab_check(db, enrollment, setting.components)
    if lab:
        checks.append(lab)
        if lab["status"] != "verified":
            has_incomplete = True

    status = CONFLICT if has_conflict or any(item["status"] == "conflict" for item in checks) else (
        EVIDENCE_INCOMPLETE if has_incomplete or any(item["status"] in ("missing", "unavailable") for item in checks)
        else VERIFIED
    )
    rounded = {key: round(value, 2) for key, value in category_totals.items()}
    if status == VERIFIED:
        message = "Configured Gradebook evidence is verified."
    elif status == CONFLICT:
        message = "A manual and online score conflict requires review; no ambiguous overwrite is allowed."
    else:
        message = "Available marks may be saved, but some configured supporting evidence is incomplete."
    return {
        "status": status,
        "enrollment_id": enrollment.enrollment_id,
        "student_id": enrollment.student_id,
        "course_id": enrollment.course_id,
        "academic_year": enrollment.academic_year,
        "semester": enrollment.semester,
        "checks": checks,
        "components": component_records,
        "category_totals": rounded,
        "total": round(sum(rounded.values()), 2),
        "message": message,
    }


def synchronize_course_result(db: Session, enrollment: Enrollment, teacher_id: int) -> tuple[dict, CourseResult | None]:
    snapshot = build_gradebook_snapshot(db, enrollment)
    if snapshot["status"] == CONFLICT:
        return snapshot, None
    result = db.query(CourseResult).filter_by(enrollment_id=enrollment.enrollment_id).first()
    if result and result.locked:
        return {**snapshot, "status": CONFLICT, "message": "The CourseResult is locked and was not synchronized."}, None
    if result is None:
        result = CourseResult(
            enrollment_id=enrollment.enrollment_id,
            student_id=enrollment.student_id,
            course_id=enrollment.course_id,
            teacher_id=teacher_id,
            semester=enrollment.semester,
            academic_year=enrollment.academic_year,
            credit_hours=enrollment.course.credit_hours,
            published=0,
            verified=0,
            locked=0,
        )
        db.add(result)
    totals = snapshot["category_totals"]
    result.teacher_id = teacher_id
    result.sessional_marks = totals["Sessional"]
    result.midterm_marks = totals["Midterm"]
    result.final_marks = totals["Final"]
    result.total_marks = snapshot["total"]
    result.percentage = snapshot["total"]
    result.updated_at = datetime.utcnow()
    return snapshot, result
