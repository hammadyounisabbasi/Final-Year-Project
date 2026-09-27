import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "backend"))

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.assignment import Assignment
from app.models.course_result import CourseResult
from app.models.enrollment import Enrollment
from app.models.exam import Assessment, AssessmentAttempt, AssessmentQuestion
from app.models.grade import Grade
from app.models.gradebook import GradebookSetting
from app.models.submission import Submission
from app.models.user import User
from app.services.academic_integrity import integrity_warnings


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def online_gradebook(tmp_path):
    database_copy = tmp_path / "online-gradebook.db"
    shutil.copy2(ROOT / "database" / "university.db", database_copy)
    engine = create_engine(f"sqlite:///{database_copy}", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    with Session() as session:
        enrollment = session.query(Enrollment).filter_by(course_id=25, academic_year="2024-2025", semester=5).first()
        assert enrollment is not None
        student_user = enrollment.student.user
        student_token = create_access_token({"sub": str(student_user.user_id), "role": "student"})
        enrollment_id = enrollment.enrollment_id
        student_id = enrollment.student_id
        section = enrollment.section

        session.query(Grade).filter_by(enrollment_id=enrollment_id).delete()
        session.query(CourseResult).filter_by(enrollment_id=enrollment_id).delete()
        session.query(Assessment).filter_by(course_id=25, academic_year="2024-2025", semester=5, section=section).delete()
        session.commit()

    teacher_login = client.post("/auth/login", json={"identifier": "usman.ali", "password": "UOH@2025"})
    other_login = client.post("/auth/login", json={"identifier": "ahmad.malik", "password": "UOH@2025"})
    assert teacher_login.status_code == other_login.status_code == 200
    teacher_token = teacher_login.json()["access_token"]
    other_token = other_login.json()["access_token"]

    components = [
        {"category": "Sessional", "name": "Quiz", "item_count": 1, "total_marks": 10},
        {"category": "Sessional", "name": "Lab", "item_count": 1, "total_marks": 10},
        {"category": "Sessional", "name": "Assignments", "item_count": 1, "total_marks": 5},
        {"category": "Midterm", "name": "Midterm", "item_count": 1, "total_marks": 25},
        {"category": "Final", "name": "Final", "item_count": 1, "total_marks": 50},
    ]
    saved = client.put("/teacher/gradebook/settings", headers=auth(teacher_token), json={
        "course_id": 25,
        "academic_year": "2024-2025",
        "semester": 5,
        "components": components,
    })
    assert saved.status_code == 200

    try:
        yield {
            "client": client,
            "Session": Session,
            "teacher": teacher_token,
            "other": other_token,
            "student": student_token,
            "enrollment_id": enrollment_id,
            "student_id": student_id,
            "section": section,
            "components": saved.json()["components"],
        }
    finally:
        app.dependency_overrides.clear()
        client.close()
        engine.dispose()


def create_assessment(Session, data, assessment_type="Quiz", title="Quiz 1", course_id=25,
                      academic_year="2024-2025", semester=5, section=None):
    with Session() as session:
        assessment = Assessment(
            course_id=course_id,
            teacher_id=3,
            academic_year=academic_year,
            semester=semester,
            section=section or data["section"],
            title=title,
            assessment_type=assessment_type,
            start_at=datetime.utcnow() - timedelta(minutes=5),
            end_at=datetime.utcnow() + timedelta(minutes=30),
            duration_minutes=30,
            total_marks=10,
            status="Published",
        )
        session.add(assessment)
        session.flush()
        question = AssessmentQuestion(
            assessment_id=assessment.assessment_id,
            question_text="Deterministic test question",
            option_a="Correct",
            option_b="Wrong B",
            option_c="Wrong C",
            option_d="Wrong D",
            correct_option="A",
            marks=10,
            position=1,
        )
        session.add(question)
        session.commit()
        return assessment.assessment_id, question.question_id


def create_lab_evidence(Session, data, with_submission):
    with Session() as session:
        assignment = Assignment(
            course_id=25,
            teacher_id=3,
            title="Lab Evidence",
            assignment_type="Lab",
            total_marks=10,
            semester=5,
            academic_year="2024-2025",
            section=data["section"],
            release_date=datetime.utcnow() - timedelta(days=2),
            due_date=datetime.utcnow() + timedelta(days=2),
            status="Published",
        )
        session.add(assignment)
        session.flush()
        if with_submission:
            session.add(Submission(
                assignment_id=assignment.assignment_id,
                student_id=data["student_id"],
                submission_title="Lab submission",
                file_name="inline",
                file_path="inline",
                response_text="Stored lab evidence",
                submission_status="Submitted",
            ))
        session.commit()


def submit_correct_attempt(data, assessment_id, question_id):
    client = data["client"]
    started = client.post(f"/student/exams/{assessment_id}/start", headers=auth(data["student"]))
    assert started.status_code == 200
    attempt_id = started.json()["attempt_id"]
    answer = client.patch(f"/student/attempts/{attempt_id}/answer", headers=auth(data["student"]), json={
        "question_id": question_id,
        "selected_option": "A",
    })
    assert answer.status_code == 200
    submitted = client.post(f"/student/attempts/{attempt_id}/submit", headers=auth(data["student"]), json={})
    assert submitted.status_code == 200
    return attempt_id


def test_online_quiz_submission_syncs_idempotently_and_keeps_provenance(online_gradebook):
    data = online_gradebook
    create_lab_evidence(data["Session"], data, with_submission=True)
    assessment_id, question_id = create_assessment(data["Session"], data)

    before = data["client"].get(
        "/teacher/gradebook/validate",
        headers=auth(data["teacher"]),
        params={"enrollment_id": data["enrollment_id"]},
    )
    assert before.status_code == 200
    assert before.json()["status"] == "EVIDENCE_INCOMPLETE"
    assert next(item for item in before.json()["checks"] if item["type"] == "quiz_completion")["status"] == "missing"
    assert next(item for item in before.json()["checks"] if item["type"] == "lab_completion")["status"] == "verified"

    attempt_id = submit_correct_attempt(data, assessment_id, question_id)
    validated = data["client"].get(
        "/teacher/gradebook/validate",
        headers=auth(data["teacher"]),
        params={"enrollment_id": data["enrollment_id"]},
    ).json()
    quiz = next(item for item in validated["components"] if item["name"] == "Quiz")
    assert validated["status"] == "VERIFIED"
    assert quiz["source"] == "online_assessment"
    assert quiz["read_only"] is True
    assert quiz["synchronized_scores"] == [10.0]
    assert quiz["synchronized_value"] == 10.0
    assert quiz["online_evidence"][0]["attempt_id"] == attempt_id
    assert quiz["online_evidence"][0]["attempt_status"] == "Submitted"

    with data["Session"]() as session:
        result = session.query(CourseResult).filter_by(enrollment_id=data["enrollment_id"]).one()
        assert result.sessional_marks == 10
        assert result.published == 0
        grade_count = session.query(Grade).filter(
            Grade.enrollment_id == data["enrollment_id"],
            Grade.title.like("Gradebook:%"),
        ).count()
        assert grade_count == 0

    repeated = data["client"].post(
        f"/student/attempts/{attempt_id}/submit",
        headers=auth(data["student"]),
        json={},
    )
    assert repeated.status_code == 200
    with data["Session"]() as session:
        assert session.query(CourseResult).filter_by(enrollment_id=data["enrollment_id"]).count() == 1
        assert session.query(Grade).filter(
            Grade.enrollment_id == data["enrollment_id"], Grade.title.like("Gradebook:%")
        ).count() == grade_count


def test_auto_submitted_quiz_is_valid_authoritative_evidence(online_gradebook):
    data = online_gradebook
    assessment_id, question_id = create_assessment(data["Session"], data)
    started = data["client"].post(f"/student/exams/{assessment_id}/start", headers=auth(data["student"]))
    assert started.status_code == 200
    attempt_id = started.json()["attempt_id"]
    answer = data["client"].patch(
        f"/student/attempts/{attempt_id}/answer",
        headers=auth(data["student"]),
        json={"question_id": question_id, "selected_option": "A"},
    )
    assert answer.status_code == 200
    submitted = data["client"].post(
        f"/student/attempts/{attempt_id}/submit",
        headers=auth(data["student"]),
        json={"auto_submit_reason": "timer", "fullscreen_violations": 0},
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "Auto Submitted"

    validation = data["client"].get(
        "/teacher/gradebook/validate",
        headers=auth(data["teacher"]),
        params={"enrollment_id": data["enrollment_id"]},
    ).json()
    quiz = next(item for item in validation["components"] if item["name"] == "Quiz")
    assert quiz["status"] == "VERIFIED"
    assert quiz["online_evidence"][0]["auto_submitted"] is True
    assert quiz["online_evidence"][0]["auto_submit_reason"] == "timer"
    assert quiz["synchronized_value"] == 10


def test_manual_save_uses_online_score_and_detects_manual_auto_conflict(online_gradebook):
    data = online_gradebook
    create_lab_evidence(data["Session"], data, with_submission=True)
    assessment_id, question_id = create_assessment(data["Session"], data)
    submit_correct_attempt(data, assessment_id, question_id)
    ids = {item["name"]: item["component_id"] for item in data["components"]}
    payload = {
        "enrollment_id": data["enrollment_id"],
        "components": [
            {"component_id": ids["Lab"], "scores": [8]},
            {"component_id": ids["Assignments"], "scores": [4]},
            {"component_id": ids["Midterm"], "scores": [20]},
            {"component_id": ids["Final"], "scores": [40]},
        ],
    }
    saved = data["client"].post("/teacher/gradebook/marks", headers=auth(data["teacher"]), json=payload)
    assert saved.status_code == 200
    assert saved.json()["total"] == 82
    assert saved.json()["validation"]["status"] == "VERIFIED"

    with data["Session"]() as session:
        quiz_component = ids["Quiz"]
        session.add(Grade(
            enrollment_id=data["enrollment_id"],
            assessment_type="Assignment",
            title=f"Gradebook:{quiz_component}:1:Quiz",
            obtained_marks=5,
            total_marks=10,
            percentage=50,
            graded_by=3,
            academic_year="2024-2025",
            semester=5,
        ))
        session.commit()

    validation = data["client"].get(
        "/teacher/gradebook/validate", headers=auth(data["teacher"]), params={"enrollment_id": data["enrollment_id"]}
    ).json()
    assert validation["status"] == "CONFLICT"
    quiz = next(item for item in validation["components"] if item["name"] == "Quiz")
    assert "GRADE_SOURCE_CONFLICT" in quiz["message"]
    blocked = data["client"].post("/teacher/gradebook/marks", headers=auth(data["teacher"]), json=payload)
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "GRADE_SOURCE_CONFLICT"
    with data["Session"]() as session:
        warning = next(item for item in integrity_warnings(session) if item["code"] == "GRADE_SOURCE_CONFLICT")
        assert warning["component_id"] == ids["Quiz"]
        assert warning["manual_grade_ids"] == quiz["manual_grade_ids"]
        assert warning["assessment_ids"] == [assessment_id]


def test_incomplete_attempt_multiple_assessments_and_missing_lab_are_not_silently_used(online_gradebook):
    data = online_gradebook
    create_lab_evidence(data["Session"], data, with_submission=False)
    assessment_id, _ = create_assessment(data["Session"], data)
    started = data["client"].post(f"/student/exams/{assessment_id}/start", headers=auth(data["student"]))
    assert started.status_code == 200
    validation = data["client"].get(
        "/teacher/gradebook/validate", headers=auth(data["teacher"]), params={"enrollment_id": data["enrollment_id"]}
    ).json()
    assert validation["status"] == "EVIDENCE_INCOMPLETE"
    assert next(item for item in validation["checks"] if item["type"] == "quiz_completion")["status"] == "missing"
    assert next(item for item in validation["checks"] if item["type"] == "lab_completion")["status"] == "missing"
    with data["Session"]() as session:
        assert session.query(CourseResult).filter_by(enrollment_id=data["enrollment_id"]).count() == 0

    component_ids = {item["name"]: item["component_id"] for item in data["components"]}
    saved_with_warning = data["client"].post(
        "/teacher/gradebook/marks",
        headers=auth(data["teacher"]),
        json={
            "enrollment_id": data["enrollment_id"],
            "components": [
                {"component_id": component_ids["Lab"], "scores": [8]},
                {"component_id": component_ids["Assignments"], "scores": [4]},
                {"component_id": component_ids["Midterm"], "scores": [20]},
                {"component_id": component_ids["Final"], "scores": [40]},
            ],
        },
    )
    assert saved_with_warning.status_code == 200
    assert saved_with_warning.json()["validation"]["status"] == "EVIDENCE_INCOMPLETE"
    with data["Session"]() as session:
        evidence_warnings = [
            item for item in integrity_warnings(session)
            if item["code"] == "GRADEBOOK_EVIDENCE_INCOMPLETE"
            and item.get("student_id") == data["student_id"]
            and item.get("course_id") == 25
        ]
        assert {item["evidence_type"] for item in evidence_warnings} == {
            "quiz_completion", "lab_completion"
        }

    create_assessment(data["Session"], data, title="Quiz 2")
    conflicted = data["client"].get(
        "/teacher/gradebook/validate", headers=auth(data["teacher"]), params={"enrollment_id": data["enrollment_id"]}
    ).json()
    assert conflicted["status"] == "CONFLICT"
    quiz = next(item for item in conflicted["components"] if item["name"] == "Quiz")
    assert "2 online assessments" in quiz["message"]


def test_validator_ignores_wrong_course_term_student_evidence_and_enforces_authorization(online_gradebook):
    data = online_gradebook
    create_assessment(data["Session"], data, course_id=31, title="Wrong course")
    create_assessment(data["Session"], data, academic_year="2023-2024", title="Wrong term")
    correct_assessment_id, _ = create_assessment(data["Session"], data, title="Wrong student attempt")
    with data["Session"]() as session:
        other_enrollment = session.query(Enrollment).filter(
            Enrollment.course_id == 25,
            Enrollment.academic_year == "2024-2025",
            Enrollment.semester == 5,
            Enrollment.student_id != data["student_id"],
        ).first()
        assert other_enrollment is not None
        session.add(AssessmentAttempt(
            assessment_id=correct_assessment_id,
            student_id=other_enrollment.student_id,
            enrollment_id=other_enrollment.enrollment_id,
            started_at=datetime.utcnow() - timedelta(minutes=2),
            submitted_at=datetime.utcnow(),
            status="Submitted",
            obtained_marks=10,
            total_marks=10,
        ))
        session.commit()
    validation = data["client"].get(
        "/teacher/gradebook/validate", headers=auth(data["teacher"]), params={"enrollment_id": data["enrollment_id"]}
    )
    assert validation.status_code == 200
    quiz = next(item for item in validation.json()["checks"] if item["type"] == "quiz_completion")
    assert quiz["status"] == "missing"
    assert quiz["evidence_ids"] == []

    assert data["client"].get(
        "/teacher/gradebook/validate", headers=auth(data["other"]), params={"enrollment_id": data["enrollment_id"]}
    ).status_code == 404
    assert data["client"].get(
        "/teacher/gradebook/validate", headers=auth(data["student"]), params={"enrollment_id": data["enrollment_id"]}
    ).status_code == 403


def test_course_without_lab_component_has_no_false_lab_failure(online_gradebook):
    data = online_gradebook
    components = [
        {"category": "Sessional", "name": "Quiz", "item_count": 1, "total_marks": 25},
        {"category": "Midterm", "name": "Midterm", "item_count": 1, "total_marks": 25},
        {"category": "Final", "name": "Final", "item_count": 1, "total_marks": 50},
    ]
    saved = data["client"].put("/teacher/gradebook/settings", headers=auth(data["teacher"]), json={
        "course_id": 25, "academic_year": "2024-2025", "semester": 5, "components": components,
    })
    assert saved.status_code == 200
    assessment_id, question_id = create_assessment(data["Session"], data)
    submit_correct_attempt(data, assessment_id, question_id)
    validation = data["client"].get(
        "/teacher/gradebook/validate", headers=auth(data["teacher"]), params={"enrollment_id": data["enrollment_id"]}
    ).json()
    assert validation["status"] == "VERIFIED"
    assert not any(item["type"] == "lab_completion" for item in validation["checks"])


@pytest.mark.parametrize("assessment_type, expected_value", [("Midterm", 25.0), ("Final", 50.0)])
def test_online_midterm_and_final_use_attempt_as_authoritative_source(online_gradebook, assessment_type, expected_value):
    data = online_gradebook
    assessment_id, question_id = create_assessment(
        data["Session"], data, assessment_type=assessment_type, title=f"Online {assessment_type}"
    )
    attempt_id = submit_correct_attempt(data, assessment_id, question_id)
    validation = data["client"].get(
        "/teacher/gradebook/validate", headers=auth(data["teacher"]), params={"enrollment_id": data["enrollment_id"]}
    ).json()
    component = next(item for item in validation["components"] if item["name"] == assessment_type)
    assert component["source"] == "online_assessment"
    assert component["synchronized_value"] == expected_value
    assert component["online_evidence"][0]["attempt_id"] == attempt_id

    with data["Session"]() as session:
        projection = session.query(Grade).filter(
            Grade.enrollment_id == data["enrollment_id"],
            Grade.title == f"OnlineAssessment:{assessment_id}:Online {assessment_type}",
        ).all()
        assert len(projection) == 1
        result = session.query(CourseResult).filter_by(enrollment_id=data["enrollment_id"]).one()
        assert getattr(result, f"{assessment_type.casefold()}_marks") == expected_value

    repeated = data["client"].post(
        f"/student/attempts/{attempt_id}/submit", headers=auth(data["student"]), json={}
    )
    assert repeated.status_code == 200
    with data["Session"]() as session:
        assert session.query(Grade).filter(
            Grade.enrollment_id == data["enrollment_id"],
            Grade.title == f"OnlineAssessment:{assessment_id}:Online {assessment_type}",
        ).count() == 1
