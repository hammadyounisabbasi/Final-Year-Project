import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "backend"))

from app.core.database import get_db
from app.main import app
from app.models.course_result import CourseResult
from app.models.enrollment import Enrollment
from app.models.user import User


@pytest.fixture()
def gradebook_api(tmp_path):
    database_copy = tmp_path / "gradebook.db"
    shutil.copy2(PROJECT_ROOT / "database" / "university.db", database_copy)
    engine = create_engine(
        f"sqlite:///{database_copy}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    try:
        login = client.post(
            "/auth/login",
            json={"identifier": "usman.ali", "password": "UOH@2025"},
        )
        assert login.status_code == 200
        teacher_token = login.json()["access_token"]

        other_login = client.post(
            "/auth/login",
            json={"identifier": "ahmad.malik", "password": "UOH@2025"},
        )
        assert other_login.status_code == 200
        other_teacher_token = other_login.json()["access_token"]

        with TestSession() as session:
            student_user = session.query(User).filter(User.role == "student").first()
            assert student_user is not None
            from app.core.security import create_access_token

            student_token = create_access_token(
                {"sub": str(student_user.user_id), "role": "student"}
            )

        yield client, teacher_token, other_teacher_token, student_token, TestSession
    finally:
        app.dependency_overrides.clear()
        client.close()
        engine.dispose()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_teacher_roster_uses_real_course_identity_and_authentication(gradebook_api):
    client, teacher_token, _, student_token, _ = gradebook_api

    me = client.get("/auth/me", headers=auth(teacher_token))
    assert me.status_code == 200
    assert me.json()["role"] == "teacher"

    response = client.get("/teacher/students", headers=auth(teacher_token))
    assert response.status_code == 200
    payload = response.json()
    available = {
        item["course_code"]: (item["course_id"], item["course_title"])
        for item in payload["available_courses"]
    }
    assert available["CSE-502"] == (25, "Theory of Automata")
    assert available["CSE-602"] == (31, "Compiler Construction")

    enrollments = [
        enrollment
        for student in payload["students"]
        for enrollment in student["enrollments"]
    ]
    assert enrollments
    assert all(enrollment["course_title"] for enrollment in enrollments)
    assert not any(
        enrollment["course_title"] == student["name"]
        for student in payload["students"]
        for enrollment in student["enrollments"]
    )

    forbidden = client.get("/teacher/students", headers=auth(student_token))
    assert forbidden.status_code == 403


def test_settings_round_trip_validation_and_course_ownership(gradebook_api):
    client, teacher_token, other_teacher_token, student_token, _ = gradebook_api
    headers = {**auth(teacher_token), "Content-Type": "application/json"}
    settings_url = "/teacher/gradebook/settings?course_id=25&academic_year=2024-2025&semester=5"

    initial = client.get(settings_url, headers=auth(teacher_token))
    assert initial.status_code == 200
    assert initial.json()["course_title"] == "Theory of Automata"

    components = [
        {"category": "Sessional", "name": "Assignments", "item_count": 2, "total_marks": 25},
        {"category": "Midterm", "name": "Midterm Exam", "item_count": 1, "total_marks": 25},
        {"category": "Final", "name": "Final Exam", "item_count": 1, "total_marks": 50},
    ]
    saved = client.put(
        "/teacher/gradebook/settings",
        headers=headers,
        json={"course_id": 25, "academic_year": "2024-2025", "semester": 5, "components": components},
    )
    assert saved.status_code == 200
    first_ids = [item["component_id"] for item in saved.json()["components"]]

    reloaded = client.get(settings_url, headers=auth(teacher_token))
    assert reloaded.status_code == 200
    assert [item["name"] for item in reloaded.json()["components"]] == [
        "Assignments", "Midterm Exam", "Final Exam"
    ]

    replacement = [
        {"category": "Sessional", "name": "Labs", "item_count": 1, "total_marks": 20},
        {"category": "Midterm", "name": "Midterm Exam", "item_count": 1, "total_marks": 30},
        {"category": "Final", "name": "Final Exam", "item_count": 1, "total_marks": 50},
    ]
    replaced = client.put(
        "/teacher/gradebook/settings",
        headers=headers,
        json={"course_id": 25, "academic_year": "2024-2025", "semester": 5, "components": replacement},
    )
    assert replaced.status_code == 200
    assert not set(first_ids) & {item["component_id"] for item in replaced.json()["components"]}

    invalid_total = client.put(
        "/teacher/gradebook/settings",
        headers=headers,
        json={
            "course_id": 25,
            "academic_year": "2024-2025",
            "semester": 5,
            "components": [{"category": "Final", "name": "Final", "item_count": 1, "total_marks": 90}],
        },
    )
    assert invalid_total.status_code == 422

    invalid_term = client.put(
        "/teacher/gradebook/settings",
        headers=headers,
        json={"course_id": 25, "academic_year": "2099-2100", "semester": 5, "components": replacement},
    )
    assert invalid_term.status_code == 422
    assert "do not match an enrollment" in invalid_term.json()["detail"]

    assert client.get(settings_url, headers=auth(other_teacher_token)).status_code == 404
    assert client.get(settings_url, headers=auth(student_token)).status_code == 403


def test_marks_bind_to_enrollment_validate_scores_and_block_other_teacher(gradebook_api):
    client, teacher_token, other_teacher_token, student_token, TestSession = gradebook_api
    headers = {**auth(teacher_token), "Content-Type": "application/json"}
    components = [
        {"category": "Sessional", "name": "Assignments", "item_count": 2, "total_marks": 20},
        {"category": "Midterm", "name": "Midterm", "item_count": 1, "total_marks": 30},
        {"category": "Final", "name": "Final", "item_count": 1, "total_marks": 50},
    ]
    saved = client.put(
        "/teacher/gradebook/settings",
        headers=headers,
        json={"course_id": 25, "academic_year": "2024-2025", "semester": 5, "components": components},
    )
    assert saved.status_code == 200
    component_ids = [item["component_id"] for item in saved.json()["components"]]

    with TestSession() as session:
        enrollment = (
            session.query(Enrollment)
            .filter_by(course_id=25, academic_year="2024-2025", semester=5)
            .first()
        )
        assert enrollment is not None
        enrollment_id = enrollment.enrollment_id
        expected_student_id = enrollment.student_id

    valid_payload = {
        "enrollment_id": enrollment_id,
        "components": [
            {"component_id": component_ids[0], "scores": [8, 10]},
            {"component_id": component_ids[1], "scores": [24]},
            {"component_id": component_ids[2], "scores": [45]},
        ],
    }
    valid = client.post("/teacher/gradebook/marks", headers=headers, json=valid_payload)
    assert valid.status_code == 200
    assert valid.json()["total"] == 87

    with TestSession() as session:
        result = session.query(CourseResult).filter_by(enrollment_id=enrollment_id).one()
        assert (result.student_id, result.course_id, result.academic_year, result.semester) == (
            expected_student_id, 25, "2024-2025", 5
        )

    invalid_score = {**valid_payload, "components": [dict(item) for item in valid_payload["components"]]}
    invalid_score["components"][0] = {"component_id": component_ids[0], "scores": [11, 10]}
    assert client.post("/teacher/gradebook/marks", headers=headers, json=invalid_score).status_code == 422

    duplicate_component = {
        "enrollment_id": enrollment_id,
        "components": valid_payload["components"] + [valid_payload["components"][0]],
    }
    duplicate = client.post("/teacher/gradebook/marks", headers=headers, json=duplicate_component)
    assert duplicate.status_code == 422
    assert "only once" in duplicate.json()["detail"]

    assert client.post(
        "/teacher/gradebook/marks", headers={**auth(other_teacher_token), "Content-Type": "application/json"}, json=valid_payload
    ).status_code == 404
    assert client.post(
        "/teacher/gradebook/marks", headers={**auth(student_token), "Content-Type": "application/json"}, json=valid_payload
    ).status_code == 403


def test_cse_104_physical_paper_manual_marks_round_trip(gradebook_api):
    client, _, _, _, TestSession = gradebook_api
    login = client.post(
        "/auth/login",
        json={"identifier": "hassan.raza", "password": "UOH@2025"},
    )
    assert login.status_code == 200
    teacher_token = login.json()["access_token"]
    headers = {**auth(teacher_token), "Content-Type": "application/json"}
    settings_url = "/teacher/gradebook/settings?course_id=4&academic_year=2026-2027&semester=1"

    initial = client.get(settings_url, headers=auth(teacher_token))
    assert initial.status_code == 200
    assert initial.json()["course_code"] == "CSE-104"
    assert initial.json()["course_title"] == "Civics and Community Engagement"
    assert initial.json()["components"] == []

    components = [
        {"category": "Sessional", "name": "Sessional Work", "item_count": 1, "total_marks": 25},
        {"category": "Midterm", "name": "Physical Midterm", "item_count": 1, "total_marks": 25},
        {"category": "Final", "name": "Physical Final", "item_count": 1, "total_marks": 50},
    ]
    saved = client.put(
        "/teacher/gradebook/settings",
        headers=headers,
        json={"course_id": 4, "academic_year": "2026-2027", "semester": 1, "components": components},
    )
    assert saved.status_code == 200
    component_ids = [item["component_id"] for item in saved.json()["components"]]

    validation = client.get(
        "/teacher/gradebook/validate",
        headers=auth(teacher_token),
        params={"enrollment_id": 28},
    )
    assert validation.status_code == 200
    assert all(item["source"] == "manual_gradebook" for item in validation.json()["components"])

    marks = client.post(
        "/teacher/gradebook/marks",
        headers=headers,
        json={
            "enrollment_id": 28,
            "components": [
                {"component_id": component_ids[0], "scores": [20]},
                {"component_id": component_ids[1], "scores": [22]},
                {"component_id": component_ids[2], "scores": [45]},
            ],
        },
    )
    assert marks.status_code == 200
    assert marks.json()["total"] == 87

    reloaded = client.get("/teacher/gradebook/marks", headers=auth(teacher_token))
    row = next(item for item in reloaded.json()["marks"] if item["enrollment_id"] == 28)
    assert (row["sessional"], row["midterm"], row["final"], row["total"]) == (20, 22, 45, 87)

    with TestSession() as session:
        result = session.query(CourseResult).filter_by(enrollment_id=28).one()
        assert (result.academic_year, result.semester, result.course_id, result.student_id) == (
            "2026-2027", 1, 4, 5
        )
