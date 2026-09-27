import shutil
import sys
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
from app.models.student import Student
from app.models.user import User


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database_copy = tmp_path / "university-test.db"
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
    monkeypatch.setenv("STUDENT_MANAGEMENT_AI_DISABLE_LLM", "1")
    session = TestSession()
    admin = session.query(User).filter(User.role == "admin").first()
    student_user = session.query(User).filter(User.role == "student").first()
    first_student_id = session.query(Student.student_id).order_by(Student.student_id).first()[0]
    admin_token = create_access_token({"sub": str(admin.user_id), "role": "admin"})
    student_token = create_access_token({"sub": str(student_user.user_id), "role": "student"})
    session.close()
    try:
        yield TestClient(app), admin_token, student_token, first_student_id, TestSession
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_admin_authentication_and_rbac(client):
    browser, admin_token, student_token, _, _ = client
    assert browser.get("/admin/students/overview").status_code == 401
    assert browser.get("/admin/students/overview", headers=auth(student_token)).status_code == 403
    assert browser.get("/admin/students/overview", headers=auth(admin_token)).status_code == 200


def test_real_overview_directory_search_filters_and_pagination(client):
    browser, token, _, _, TestSession = client
    session = TestSession()
    expected_total = session.query(Student).count()
    expected_semester_six = session.query(Student).filter(Student.semester == 6).count()
    sample = session.query(Student).order_by(Student.student_id).first()
    sample_email = sample.user.email
    department_count = session.query(Student).filter(Student.department_id == sample.department_id).count()
    session.close()

    overview = browser.get("/admin/students/overview", headers=auth(token)).json()
    assert overview["stats"]["total_students"] == expected_total

    search = browser.get("/admin/students", headers=auth(token), params={"search": sample.roll_number, "page_size": 5}).json()
    assert search["pagination"]["total"] == 1
    assert search["items"][0]["roll_number"] == sample.roll_number

    for value in (sample.registration_number, sample_email, f"{sample.first_name} {sample.last_name}"):
        found = browser.get("/admin/students", headers=auth(token), params={"search": value, "page_size": 5}).json()
        assert found["pagination"]["total"] >= 1
        assert any(row["student_id"] == sample.student_id for row in found["items"])

    department = browser.get("/admin/students", headers=auth(token), params={"department_id": sample.department_id, "page_size": 5}).json()
    assert department["pagination"]["total"] == department_count
    assert all(row["department_id"] == sample.department_id for row in department["items"])

    filtered = browser.get("/admin/students", headers=auth(token), params={"semester": 6, "page_size": 5}).json()
    assert filtered["pagination"]["total"] == expected_semester_six
    assert len(filtered["items"]) <= 5
    assert all(row["semester"] == 6 for row in filtered["items"])


def test_detail_aggregates_existing_modules_and_missing_data(client):
    browser, token, _, student_id, _ = client
    response = browser.get(f"/admin/students/{student_id}", headers=auth(token))
    assert response.status_code == 200
    data = response.json()
    assert set(data) >= {"profile", "academics", "enrollments", "attendance", "fees", "assignments", "timetable", "notifications"}
    assert data["profile"]["student_id"] == student_id
    assert "has_records" in data["attendance"]
    assert "has_fee_records" in data["fees"]
    assert "has_cgpa_record" in data["academics"]


def test_safe_edit_uses_temporary_database(client):
    browser, token, _, student_id, TestSession = client
    response = browser.patch(f"/admin/students/{student_id}", headers=auth(token), json={"phone": "+92-TEST", "account_active": True})
    assert response.status_code == 200
    session = TestSession()
    student = session.get(Student, student_id)
    assert student.phone == "+92-TEST"
    session.close()


@pytest.mark.parametrize("question", [
    "How many students are currently in Semester 6?",
    "Can you give me the number of learners in sem 6?",
])
def test_grounded_ai_understands_count_variations(client, question):
    browser, token, _, _, TestSession = client
    session = TestSession()
    expected = session.query(Student).filter(Student.semester == 6).count()
    session.close()
    response = browser.post("/admin/students/ai/chat", headers=auth(token), json={"message": question})
    assert response.status_code == 200
    assert f"**{expected}**" in response.json()["response"]
    assert response.json()["provider"] == "Grounded local fallback"


def test_ai_selected_student_and_unknown_student_handling(client):
    browser, token, _, student_id, _ = client
    selected = browser.post("/admin/students/ai/chat", headers=auth(token), json={"message": "Summarize this student's academic standing.", "selected_student_id": student_id})
    assert selected.status_code == 200
    assert selected.json()["response"]
    unknown = browser.post("/admin/students/ai/chat", headers=auth(token), json={"message": "Find student nobody.unknown@example.invalid"})
    assert unknown.status_code == 200
    assert "could not uniquely identify" in unknown.json()["response"]


def test_ai_department_wording_is_grounded(client):
    browser, token, _, _, TestSession = client
    session = TestSession()
    expected = session.query(Student).join(Student.department).filter_by(department_name="Department of Computer Science").count()
    session.close()
    response = browser.post("/admin/students/ai/chat", headers=auth(token), json={"message": "Show students from the Computer Science department."})
    assert response.status_code == 200
    assert f"**{expected}**" in response.json()["response"]


def test_ai_greeting_does_not_leak_selected_student(client):
    browser, token, _, student_id, _ = client
    response = browser.post("/admin/students/ai/chat", headers=auth(token), json={
        "message": "hello how are you?",
        "selected_student_id": student_id,
    })
    assert response.status_code == 200
    answer = response.json()["response"]
    assert "doing well" in answer
    assert "CGPA" not in answer
    assert "Semester" not in answer


def test_ai_reports_real_database_coverage(client):
    browser, token, _, _, _ = client
    response = browser.post("/admin/students/ai/chat", headers=auth(token), json={
        "message": "Is the student database record complete?",
    })
    assert response.status_code == 200
    answer = response.json()["response"]
    assert "not complete" in answer
    assert "890" in answer
    assert "attendance" in answer
