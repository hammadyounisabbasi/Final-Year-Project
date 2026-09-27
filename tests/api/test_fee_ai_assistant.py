import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "backend"))
os.environ["FEE_AI_DISABLE_LLM"] = "1"

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.main import app  # noqa: E402
from app.models.student import Student  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.fee_ai_assistant import process_fee_chat  # noqa: E402
from app.services.fee_knowledge import load_fee_store, retrieve_fee_knowledge  # noqa: E402
from app.services.student_ai_context import get_fee_status_context  # noqa: E402


def _student_users(db, count=2):
    return (
        db.query(User, Student)
        .join(Student, Student.user_id == User.user_id)
        .filter(User.role == "student")
        .limit(count)
        .all()
    )


def test_persisted_store_and_langchain_retrieval():
    store = load_fee_store()
    assert store["embedding_model"] == "local-hash-v1"
    assert len(store["documents"]) >= 5
    hits = retrieve_fee_knowledge("I paid my challan but it is still pending")
    assert hits
    assert any("bank or payment agent" in document.page_content for document in hits)
    assert all(document.metadata["source_url"].startswith("https://") for document in hits)


def test_fee_context_uses_real_schema_and_does_not_fabricate_missing_record():
    db = SessionLocal()
    try:
        _, student = _student_users(db, 1)[0]
        context = get_fee_status_context(student, db)
        assert context["has_fee_records"] is True
        assert context["payment_status"] in {"Pending", "Partial", "Paid", "Overdue", "Cancelled"}

        missing = Student(
            student_id=999999999,
            user_id=999999999,
            roll_number="NO-FEE-TEST",
            registration_number="NO-FEE-TEST",
            first_name="No",
            last_name="Record",
            program="Test",
            semester=1,
        )
        empty = get_fee_status_context(missing, db)
        assert empty["has_fee_records"] is False
        assert empty["total_fee"] is None
        assert empty["payment_status"] is None
    finally:
        db.close()


def test_two_authenticated_students_receive_only_their_own_fee_record():
    db = SessionLocal()
    try:
        pairs = _student_users(db, 2)
        assert len(pairs) == 2
        (_, first), (_, second) = pairs
        first_context = get_fee_status_context(first, db)
        second_context = get_fee_status_context(second, db)
        assert first.student_id != second.student_id
        assert first_context["transaction_id"] != second_context["transaction_id"]

        first_reply, _, _ = process_fee_chat(first, db, "What is my current fee status?")
        second_reply, _, _ = process_fee_chat(second, db, "I already paid; what is my status?")
        assert first_context["transaction_id"] in first_reply
        assert second_context["transaction_id"] not in first_reply
        assert second_context["transaction_id"] in second_reply
        assert first_context["transaction_id"] not in second_reply
    finally:
        db.close()


def test_fee_ai_http_flow_requires_auth_and_keeps_identity_server_side():
    client = TestClient(app)
    unauthenticated = client.post("/student/fee-ai/chat", json={"message": "What is my fee?"})
    assert unauthenticated.status_code in {401, 403}

    db = SessionLocal()
    try:
        user, student = _student_users(db, 1)[0]
        context = get_fee_status_context(student, db)
        token = create_access_token({"sub": str(user.user_id), "role": "student"})
    finally:
        db.close()

    response = client.post(
        "/student/fee-ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "My payment is still pending. What should I do?",
            "history": [{"role": "user", "content": "I paid yesterday."}],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert context["transaction_id"] in payload["response"]
    assert payload["student_name"] == student.first_name
    assert payload["sources"]


def test_llm_receives_history_live_student_context_and_rag(monkeypatch):
    captured = {}

    def fake_generate(system_prompt, messages):
        captured["prompt"] = system_prompt
        captured["messages"] = messages
        return "### Fee answer\n\nYour grounded answer.", "Test LLM"

    monkeypatch.delenv("FEE_AI_DISABLE_LLM", raising=False)
    monkeypatch.setattr(
        "app.services.fee_ai_assistant.provider_manager.generate_chat",
        fake_generate,
    )
    db = SessionLocal()
    try:
        _, student = _student_users(db, 1)[0]
        context = get_fee_status_context(student, db)
        reply, provider, sources = process_fee_chat(
            student,
            db,
            "Why is my payment still pending?",
            history=[type("Message", (), {"role": "user", "content": "I paid yesterday"})()],
        )
    finally:
        db.close()

    assert provider == "Test LLM"
    assert reply.startswith("### Fee answer")
    assert str(student.student_id) in captured["prompt"]
    assert context["transaction_id"] in captured["prompt"]
    assert "OFFICIAL WEB KNOWLEDGE" in captured["prompt"]
    assert captured["messages"][0]["content"] == "I paid yesterday"
    assert sources


def test_extended_fee_knowledge_answers_improvement_transport_and_other_fees(monkeypatch):
    monkeypatch.setenv("FEE_AI_DISABLE_LLM", "1")
    db = SessionLocal()
    try:
        _, student = _student_users(db, 1)[0]
        improvement, _, _ = process_fee_chat(
            student, db, "What is the improvement fee for one repeated course?"
        )
        transport, _, _ = process_fee_chat(
            student, db, "What is the transport fee from Havelian?"
        )
        rechecking, _, _ = process_fee_chat(student, db, "What is the rechecking fee?")
        hostel, _, _ = process_fee_chat(
            student, db, "Tell me about the hostel fee and contact"
        )
        other, _, _ = process_fee_chat(student, db, "What other fees can I ask about?")
    finally:
        db.close()

    assert "PKR 3,000 per course" in improvement
    assert "Havelian PKR 16,110" in transport
    assert "rechecking PKR 1,500 per course" in rechecking
    assert "0995-920644" in hostel
    assert "saqib.awan@uoh.edu.pk" in hostel
    assert "migration and credit transfer" in other
