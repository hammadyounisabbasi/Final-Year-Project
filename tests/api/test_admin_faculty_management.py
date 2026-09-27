import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "backend"))

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.class_schedule import ClassSchedule
from app.models.course import Course
from app.models.teacher import Teacher
from app.models.user import User


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database_copy = tmp_path / "university-faculty-test.db"
    shutil.copy2(ROOT / "database" / "university.db", database_copy)
    engine = create_engine(f"sqlite:///{database_copy}", connect_args={"check_same_thread": False})
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setenv("FACULTY_MANAGEMENT_AI_DISABLE_LLM", "1")
    session = TestSession()
    admin = session.query(User).filter(User.role == "admin").first()
    student_user = session.query(User).filter(User.role == "student").first()
    teacher_id = session.query(Teacher.teacher_id).order_by(Teacher.teacher_id).first()[0]
    admin_token = create_access_token({"sub": str(admin.user_id), "role": "admin"})
    student_token = create_access_token({"sub": str(student_user.user_id), "role": "student"})
    session.close()
    try:
        yield TestClient(app), admin_token, student_token, teacher_id, TestSession
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_admin_authentication_and_rbac(client):
    browser, admin_token, student_token, _, _ = client
    assert browser.get("/admin/faculty/overview").status_code == 401
    assert browser.get("/admin/faculty/overview", headers=auth(student_token)).status_code == 403
    assert browser.get("/admin/faculty/overview", headers=auth(admin_token)).status_code == 200


def test_real_overview_directory_search_filters_sorting_and_pagination(client):
    browser, token, _, _, TestSession = client
    session = TestSession()
    expected_total = session.query(Teacher).count()
    sample = session.query(Teacher).order_by(Teacher.teacher_id).first()
    sample_email = sample.user.email
    department_count = session.query(Teacher).filter(Teacher.department_id == sample.department_id).count()
    status_count = session.query(Teacher).filter(Teacher.status == sample.status).count()
    session.close()

    overview = browser.get("/admin/faculty/overview", headers=auth(token)).json()
    assert overview["stats"]["total_faculty"] == expected_total
    assert overview["stats"]["assigned_courses"] >= 0
    assert overview["stats"]["scheduled_faculty"] >= 0

    for value in (sample.employee_id, sample.office_email, sample_email, f"{sample.first_name} {sample.last_name}"):
        found = browser.get("/admin/faculty", headers=auth(token), params={"search": value, "page_size": 5}).json()
        assert found["pagination"]["total"] >= 1
        assert any(row["teacher_id"] == sample.teacher_id for row in found["items"])

    department = browser.get("/admin/faculty", headers=auth(token), params={"department_id": sample.department_id, "page_size": 5}).json()
    assert department["pagination"]["total"] == department_count
    assert all(row["department_id"] == sample.department_id for row in department["items"])
    status = browser.get("/admin/faculty", headers=auth(token), params={"faculty_status": sample.status, "page_size": 5}).json()
    assert status["pagination"]["total"] == status_count
    page = browser.get("/admin/faculty", headers=auth(token), params={"page": 2, "page_size": 5, "sort_by": "name", "sort_order": "desc"}).json()
    assert page["pagination"]["page"] == 2
    assert len(page["items"]) == 5


def test_detail_aggregates_courses_timetable_workload_and_grading(client):
    browser, token, _, _, TestSession = client
    session = TestSession()
    teacher_id = session.query(Course.teacher_id).filter(Course.teacher_id.isnot(None)).first()[0]
    session.close()
    response = browser.get(f"/admin/faculty/{teacher_id}", headers=auth(token))
    assert response.status_code == 200
    data = response.json()
    assert set(data) >= {"profile", "courses", "timetable", "workload", "assignments", "results"}
    assert data["profile"]["teacher_id"] == teacher_id
    assert data["workload"]["assigned_courses"] == len(data["courses"])
    assert data["workload"]["total_credit_hours"] == sum(row["credit_hours"] for row in data["courses"])


def test_safe_edit_uses_temporary_database(client):
    browser, token, _, teacher_id, TestSession = client
    response = browser.patch(f"/admin/faculty/{teacher_id}", headers=auth(token), json={"phone": "+92-FACULTY-TEST", "account_active": True})
    assert response.status_code == 200
    session = TestSession()
    teacher = session.get(Teacher, teacher_id)
    assert teacher.phone == "+92-FACULTY-TEST"
    session.close()


@pytest.mark.parametrize("question", [
    "How many faculty members are in the Computer Science department?",
    "Can you count teachers from Department of Computer Science?",
])
def test_grounded_ai_understands_department_count_variations(client, question):
    browser, token, _, _, TestSession = client
    session = TestSession()
    expected = session.query(Teacher).join(Teacher.department).filter_by(department_name="Department of Computer Science").count()
    session.close()
    response = browser.post("/admin/faculty/ai/chat", headers=auth(token), json={"message": question})
    assert response.status_code == 200
    assert f"**{expected}**" in response.json()["response"]
    assert response.json()["provider"] == "Grounded local fallback"


def test_ai_selected_faculty_courses_timetable_and_workload(client):
    browser, token, _, _, TestSession = client
    session = TestSession()
    teacher_id = session.query(Course.teacher_id).filter(Course.teacher_id.isnot(None)).first()[0]
    has_schedule = session.query(ClassSchedule).filter(ClassSchedule.teacher_id == teacher_id, ClassSchedule.status == "Active").count()
    session.close()
    for message, expected_term in (
        ("Which courses is this teacher teaching?", "Assigned courses"),
        ("Give me this faculty member's workload summary.", "Numeric teaching workload"),
        ("What is this teacher's timetable?", "timetable" if has_schedule else "No active timetable"),
    ):
        response = browser.post("/admin/faculty/ai/chat", headers=auth(token), json={"message": message, "selected_teacher_id": teacher_id})
        assert response.status_code == 200
        assert expected_term.casefold() in response.json()["response"].casefold()


def test_ai_finds_employee_course_teacher_and_handles_unknown(client):
    browser, token, _, teacher_id, TestSession = client
    session = TestSession()
    teacher = session.get(Teacher, teacher_id)
    course = session.query(Course).filter(Course.teacher_id.isnot(None)).first()
    assigned_teacher = session.get(Teacher, course.teacher_id)
    session.close()
    profile = browser.post("/admin/faculty/ai/chat", headers=auth(token), json={"message": f"Give me the profile of employee {teacher.employee_id}."})
    assert profile.status_code == 200
    assert teacher.employee_id in profile.json()["response"]
    course_answer = browser.post("/admin/faculty/ai/chat", headers=auth(token), json={"message": f"Which teacher teaches {course.course_code}?"})
    assert course_answer.status_code == 200
    assert assigned_teacher.employee_id in course_answer.json()["response"]
    unknown = browser.post("/admin/faculty/ai/chat", headers=auth(token), json={"message": "Find faculty nobody.unknown@example.invalid"})
    assert unknown.status_code == 200
    assert "could not uniquely identify" in unknown.json()["response"]


def test_ai_understands_natural_show_name_and_students_taught(client):
    browser, token, _, _, TestSession = client
    session = TestSession()
    teacher = session.query(Teacher).filter(Teacher.first_name == "Ahmad", Teacher.last_name == "Malik").first()
    if teacher is None:
        teacher = session.query(Teacher).first()
    full_name = f"{teacher.first_name} {teacher.last_name}"
    session.close()
    shown = browser.post("/admin/faculty/ai/chat", headers=auth(token), json={"message": f"Show me {full_name}."})
    assert shown.status_code == 200
    assert teacher.employee_id in shown.json()["response"]
    students = browser.post("/admin/faculty/ai/chat", headers=auth(token), json={
        "message": "How many students are being taught by this teacher?",
        "selected_teacher_id": teacher.teacher_id,
    })
    assert students.status_code == 200
    assert "distinct enrolled students" in students.json()["response"]


def test_ai_greeting_and_database_coverage_are_safe(client):
    browser, token, _, teacher_id, TestSession = client
    greeting = browser.post("/admin/faculty/ai/chat", headers=auth(token), json={"message": "hello how are you?", "selected_teacher_id": teacher_id})
    assert greeting.status_code == 200
    assert "doing well" in greeting.json()["response"]
    assert "Employee" not in greeting.json()["response"]
    session = TestSession()
    total = session.query(func.count(Teacher.teacher_id)).scalar()
    session.close()
    coverage = browser.post("/admin/faculty/ai/chat", headers=auth(token), json={"message": "Is the faculty database record complete?"})
    assert coverage.status_code == 200
    assert "not complete" in coverage.json()["response"]
    assert str(total) in coverage.json()["response"]


@pytest.mark.parametrize("question", [
    "Do you have complete access of my database, how do you provide information, and can you make changes?",
    "Can this assistant modify faculty records or is it read only?",
    "What database information can you access?",
])
def test_ai_explains_database_access_and_write_permissions(client, question):
    browser, token, _, _, _ = client
    response = browser.post("/admin/faculty/ai/chat", headers=auth(token), json={"message": question})
    assert response.status_code == 200
    answer = response.json()["response"]
    assert "not" in answer.casefold() and "complete access" in answer.casefold()
    assert "read-only" in answer.casefold()
    assert "cannot create, edit, delete, or change" in answer.casefold()
