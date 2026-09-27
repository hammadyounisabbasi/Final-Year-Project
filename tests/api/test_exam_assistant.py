"""End-to-end service coverage for the temporary Admin Exam Assistant."""

from datetime import datetime, timedelta, timezone
from io import BytesIO

import pytest
from docx import Document
from pypdf import PdfReader

from app.core.database import SessionLocal
from app.services.exam_assistant import add_document, chat, store
from app.services.exam_documents import build_exam_docx, build_exam_pdf, validate_and_extract


@pytest.fixture()
def db():
    value = SessionLocal()
    try:
        yield value
    finally:
        value.close()


@pytest.fixture()
def session():
    created = store.create(1)
    value = store.get(created["session_id"], 1)
    yield value
    store.delete(created["session_id"], 1)


def build_proposals(db, session):
    first = chat(db, session, "Create a date sheet for CS Semester 6.")
    assert first["intent"] == "clarification"
    generated = chat(db, session, "Start exams from 10 November 2026, use morning slots and keep exams on alternate days.")
    assert generated["intent"] == "date_sheet"
    return generated


def test_inventory_question_is_answered_without_starting_generation(db, session):
    inventory = chat(db, session, "What departments, semesters, courses, and rooms are currently available for creating an exam schedule? Only tell me information that actually exists in the system.")
    assert inventory["intent"] == "inventory"
    assert not inventory["date_sheet"]
    assert "Department of Computer Science (CSE)" in inventory["reply"]
    assert "CSE-606 — Artificial Intelligence" in inventory["reply"]
    assert "capacity: 60" in inventory["reply"]
    assert "still need the semester" not in inventory["reply"]

    request = chat(db, session, "Create an exam date sheet for CS Semester 6. Use the existing courses and available rooms from the database. If any essential information is missing, ask me before generating the schedule.")
    assert request["intent"] == "clarification"
    assert "exam start date" in request["reply"]
    assert "semester" not in request["reply"].replace("exam start date", "")


def test_multiturn_date_sheet_and_seating_use_real_records(db, session):
    generated = build_proposals(db, session)
    rows = generated["date_sheet"]
    assert len(rows) == 6
    assert {row["course_code"] for row in rows} == {f"CSE-60{number}" for number in range(1, 7)}
    assert all(row["room_ids"] and row["room"] != "Unassigned" for row in rows)
    dates = [datetime.fromisoformat(row["date"]).date() for row in rows]
    assert all((right - left).days >= 2 for left, right in zip(dates, dates[1:]))

    seating = chat(db, session, "Generate only the seating plan.")
    assert seating["intent"] == "seating_plan"
    assert seating["seating_plan"]
    assert all(row["assigned_students"] <= row["capacity"] for row in seating["seating_plan"])
    for code in {row["course_code"] for row in seating["seating_plan"]}:
        assigned = [student_id for row in seating["seating_plan"] if row["course_code"] == code for student_id in row["student_ids"]]
        assert len(assigned) == len(set(assigned))


def test_followup_modifies_current_proposal(db, session):
    build_proposals(db, session)
    changed = chat(db, session, "Move the AI exam to Thursday.")
    ai_exam = next(row for row in changed["date_sheet"] if row["course_code"] == "CSE-606")
    assert ai_exam["day"] == "Thursday"
    changed = chat(db, session, "Change this exam to 2 PM.")
    ai_exam = next(row for row in changed["date_sheet"] if row["course_code"] == "CSE-606")
    assert ai_exam["start_time"] == "14:00"
    changed = chat(db, session, "Use Room 5 instead.")
    ai_exam = next(row for row in changed["date_sheet"] if row["course_code"] == "CSE-606")
    assert ai_exam["room"].endswith("Room 5")
    seating = chat(db, session, "Regenerate only the seating plan.")
    assert seating["intent"] == "seating_plan" and seating["seating_plan"]


def test_structured_upload_is_embedded_retrievable_and_deduplicated(db, session):
    content = b"Course,Code,Semester,Section,Room,Capacity\nArtificial Intelligence,CSE-606,6,A,CSE Faculty Room 1,60\n"
    text, metadata = validate_and_extract("exam-data.csv", content)
    assert "Course: Artificial Intelligence" in text
    assert metadata["columns"] == ["Course", "Code", "Semester", "Section", "Room", "Capacity"]
    indexed = add_document(session, "exam-data.csv", text, metadata)
    assert indexed["chunks"] >= 1
    assert session["knowledge"]["chunks"][0]["embedding"]
    grounded = chat(db, session, "Create a date sheet using this file starting 10 November 2026.")
    assert {row["course_code"] for row in grounded["date_sheet"]} == {"CSE-606"}
    with pytest.raises(FileExistsError):
        add_document(session, "copy.csv", text, metadata)


def test_exports_match_current_proposals(db, session):
    generated = build_proposals(db, session)
    rows = generated["date_sheet"]
    pdf = build_exam_pdf("Exam Date Sheet", rows, generated["scope"])
    assert PdfReader(pdf).pages
    pdf.seek(0)
    assert b"%PDF" == pdf.read(4)
    docx = build_exam_docx("Exam Date Sheet", rows, generated["scope"])
    document = Document(docx)
    assert len(document.tables[0].rows) == len(rows) + 1
    assert document.tables[0].rows[1].cells[2].text == rows[0]["course_code"]


def test_invalid_empty_and_oversized_files_are_rejected():
    with pytest.raises(ValueError, match="empty"):
        validate_and_extract("empty.csv", b"")
    with pytest.raises(ValueError, match="PDF"):
        validate_and_extract("fake.pdf", b"not a pdf")
    with pytest.raises(OverflowError):
        validate_and_extract("large.txt", b"x" * (8 * 1024 * 1024 + 1))


def test_session_isolation_and_expiration():
    first = store.create(1001)
    with pytest.raises(KeyError):
        store.get(first["session_id"], 1002)
    value = store.get(first["session_id"], 1001)
    value["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    store.cleanup()
    with pytest.raises(KeyError):
        store.get(first["session_id"], 1001)
