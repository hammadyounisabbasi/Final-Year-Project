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
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.user import User


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database_copy = tmp_path / "integrity-test.db"
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
    monkeypatch.setenv("ACADEMIC_INTEGRITY_AI_DISABLE_LLM", "1")
    session = TestSession()
    admin = session.query(User).filter(User.role == "admin").first()
    student = session.query(User).filter(User.role == "student").first()
    teacher = session.query(User).filter(User.role == "teacher").first()
    tokens = {
        "admin": create_access_token({"sub": str(admin.user_id), "role": "admin"}),
        "student": create_access_token({"sub": str(student.user_id), "role": "student"}),
        "teacher": create_access_token({"sub": str(teacher.user_id), "role": "teacher"}),
    }
    session.close()
    try:
        yield TestClient(app), tokens, TestSession
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_admin_only_rbac(client):
    browser, tokens, _ = client
    path = "/admin/academic-integrity/overview"
    assert browser.get(path).status_code == 401
    assert browser.get(path, headers=auth(tokens["student"])).status_code == 403
    assert browser.get(path, headers=auth(tokens["teacher"])).status_code == 403
    assert browser.get(path, headers=auth(tokens["admin"])).status_code == 200


def test_overview_uses_real_database_counts(client):
    browser, tokens, Session = client
    session = Session()
    expected_assignments = session.query(func.count(Assignment.assignment_id)).scalar() or 0
    expected_submissions = session.query(func.count(Submission.submission_id)).scalar() or 0
    expected_scored = session.query(func.count(Submission.submission_id)).filter(Submission.plagiarism_score.isnot(None)).scalar() or 0
    session.close()
    data = browser.get("/admin/academic-integrity/overview", headers=auth(tokens["admin"])).json()
    assert data["stats"]["total_assignments"] == expected_assignments
    assert data["stats"]["total_submissions"] == expected_submissions
    assert data["stats"]["similarity_scored"] == expected_scored
    assert "limitations" in data


def test_submission_queue_search_filter_pagination_and_detail(client):
    browser, tokens, Session = client
    response = browser.get("/admin/academic-integrity/submissions", headers=auth(tokens["admin"]), params={"page_size": 5})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 5
    assert set(data["pagination"]) == {"page", "page_size", "total", "total_pages"}
    if not data["items"]:
        pytest.skip("The current database has no submissions to inspect")
    sample = data["items"][0]
    found = browser.get("/admin/academic-integrity/submissions", headers=auth(tokens["admin"]), params={"search": sample["roll_number"], "page_size": 5}).json()
    assert any(row["submission_id"] == sample["submission_id"] for row in found["items"])
    detail = browser.get(f"/admin/academic-integrity/submissions/{sample['submission_id']}", headers=auth(tokens["admin"]))
    assert detail.status_code == 200
    body = detail.json()
    assert set(body) >= {"submission", "student", "assignment", "enrollment", "integrity"}
    assert "file_path" not in body["submission"]
    assert "similarity_scope" in body["integrity"]


def test_grading_warning_structure_and_report(client):
    browser, tokens, _ = client
    warnings = browser.get("/admin/academic-integrity/grading-warnings", headers=auth(tokens["admin"]), params={"page_size": 100})
    assert warnings.status_code == 200
    for row in warnings.json()["items"]:
        assert set(row) >= {"code", "severity", "message", "record_type", "record_id"}
        assert "misconduct" not in row["message"].casefold()
    report = browser.get("/admin/academic-integrity/report.csv", headers=auth(tokens["admin"]))
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("text/csv")
    assert "ACADEMIC INTEGRITY EVIDENCE REPORT" in report.text


@pytest.mark.parametrize("question", ["hello", "Assalamualaikum", "Hi, how are you?"])
def test_ai_greeting_is_safe_and_context_independent(client, question):
    browser, tokens, _ = client
    response = browser.post("/admin/academic-integrity/ai/chat", headers=auth(tokens["admin"]), json={"message": question, "selected_submission_id": 999999})
    assert response.status_code == 200
    data = response.json()
    assert "investigate" in data["response"]
    assert "#999999" not in data["response"]
    assert data["provider"] == "Grounded intent guard"


def test_ai_answers_capability_and_database_permission_questions_directly(client):
    browser, tokens, _ = client
    help_response = browser.post("/admin/academic-integrity/ai/chat", headers=auth(tokens["admin"]), json={
        "message": "Hi, how are you and what type of assistance do you provide?",
    })
    assert help_response.status_code == 200
    assert "read-only investigation support" in help_response.json()["response"]

    for question in ("Do you have access to the database?", "Are you able to make changes in database?"):
        response = browser.post("/admin/academic-integrity/ai/chat", headers=auth(tokens["admin"]), json={"message": question})
        assert response.status_code == 200
        answer = response.json()["response"]
        assert "authenticated, read-only access" in answer
        assert "cannot insert, update, or delete" in answer
        assert response.json()["provider"] == "Grounded intent guard"


@pytest.mark.parametrize("question, expected", [
    ("Which students have marks greater than total marks?", "Invalid mark ranges"),
    ("Show marks recorded without a submission.", "submission evidence"),
    ("Are recorded auto scores different from calculated scores?", "Auto-score mismatches"),
])
def test_ai_dynamic_integrity_intents_use_deterministic_evidence(client, question, expected):
    browser, tokens, _ = client
    response = browser.post("/admin/academic-integrity/ai/chat", headers=auth(tokens["admin"]), json={"message": question})
    assert response.status_code == 200
    assert expected.casefold() in response.json()["response"].casefold()
    assert response.json()["provider"] in {"Grounded intent guard", "Grounded local fallback"}


@pytest.mark.parametrize("question, expected", [
    ("Are there students who received quiz marks without attempting the quiz?", "attempt evidence"),
    ("Explain how student-to-student similarity is calculated in this system.", "SequenceMatcher"),
    ("I want to know if anyone got marks without actually submitting the assignment.", "submission evidence"),
    ("Find grading records where the evidence behind the marks is missing.", "incomplete supporting evidence"),
    ("Show me the previous three times this teacher changed this student's marks.", "does not store or expose"),
])
def test_ai_routes_real_admin_phrasings_to_relevant_answers(client, question, expected):
    browser, tokens, _ = client
    response = browser.post("/admin/academic-integrity/ai/chat", headers=auth(tokens["admin"]), json={"message": question})
    assert response.status_code == 200
    assert expected.casefold() in response.json()["response"].casefold()
    assert "Academic Integrity overview" not in response.json()["response"]


def test_ai_count_only_and_selected_student_follow_up(client):
    browser, tokens, Session = client
    count = browser.post("/admin/academic-integrity/ai/chat", headers=auth(tokens["admin"]), json={"message": "How many submissions are ungraded?"})
    assert count.status_code == 200
    assert "There are **" in count.json()["response"]
    assert "Submission #" not in count.json()["response"]

    session = Session()
    sample = session.query(Submission).first()
    session.close()
    if sample is None:
        pytest.skip("The current database has no submission-backed student context")
    first = browser.post("/admin/academic-integrity/ai/chat", headers=auth(tokens["admin"]), json={
        "message": "What submissions does this student have?", "selected_student_id": sample.student_id,
    })
    assert first.status_code == 200
    assert "Submissions for" in first.json()["response"]
    follow_up = browser.post("/admin/academic-integrity/ai/chat", headers=auth(tokens["admin"]), json={
        "message": "Does any of them need review?", "selected_student_id": sample.student_id,
        "history": [{"role": "user", "content": "What submissions does this student have?"},
                    {"role": "assistant", "content": first.json()["response"]}],
    })
    assert follow_up.status_code == 200
    assert "review" in follow_up.json()["response"].casefold()
    assert "Academic Integrity overview" not in follow_up.json()["response"]
