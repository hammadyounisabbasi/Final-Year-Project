"""Admin setup API integration tests against a migrated copy of university.db."""
import sqlite3
import sys
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend/backend"))

from app.api.admin import router
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import Course, Enrollment, Room, Student, Teacher, TeacherAvailability, Timetable, User
from app.api.student import get_student_timetable
from app.api.teacher import get_teacher_schedule


def migrated_database_copy():
    from uuid import uuid4
    uri = f"file:timetable-builder-{uuid4().hex}?mode=memory&cache=shared"
    keeper = sqlite3.connect(uri, uri=True, check_same_thread=False)
    source = sqlite3.connect(f"file:{(ROOT / 'database/university.db').as_posix()}?mode=ro", uri=True)
    source.backup(keeper)
    source.close()
    keeper.executescript((ROOT / "database/migrations/v21_data_driven_timetables.sql").read_text(encoding="utf-8"))

    def connect():
        connection = sqlite3.connect(uri, uri=True, check_same_thread=False)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    engine = create_engine("sqlite://", creator=connect, poolclass=QueuePool)
    event.listen(engine, "engine_disposed", lambda ignored: keeper.close())
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


class TimetableBuilderIntegration(unittest.TestCase):
    def setUp(self):
        self.engine, factory = migrated_database_copy()
        self.db = factory()
        self.user = self.db.query(User).filter_by(role="admin").first()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_options_and_multi_semester_draft_setup(self):
        options_response = self.client.get("/admin/timetable-builder/options")
        self.assertEqual(options_response.status_code, 200, options_response.text)
        options = options_response.json()
        self.assertTrue(options["departments"])
        self.assertTrue(options["rooms"])
        courses_by_scope = {}
        for course in options["courses"]:
            courses_by_scope.setdefault((course["department_id"], course["semester"]), []).append(course)
        department_id, semester = next(iter(courses_by_scope))
        course = courses_by_scope[(department_id, semester)][0]
        teacher = next((row for row in options["teachers"] if row["id"] == course["assigned_teacher_id"]), options["teachers"][0])
        room = next(row for row in options["rooms"] if row["room_type"] == "Classroom")
        payload = {
            "department_id": department_id,
            "academic_year": options["academic_years"][0],
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "day_start_time": "08:30",
            "day_end_time": "15:30",
            "slot_minutes": 60,
            "semesters": [{
                "semester": semester,
                "section": "API-TEST",
                "courses": [{
                    "course_id": course["id"],
                    "teacher_id": teacher["id"],
                    "credit_hours": course["credit_hours"],
                    "weekly_sessions": course["credit_hours"],
                    "session_duration_minutes": 60,
                    "class_type": "Lecture",
                    "required_room_type": "Classroom",
                    "room_ids": [room["id"]],
                }],
            }],
        }
        response = self.client.post("/admin/timetable-builder/drafts", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        draft = response.json()["drafts"][0]
        self.assertEqual(draft["status"], "Draft")
        self.assertEqual(draft["courses"][0]["weekly_sessions"], course["credit_hours"])
        self.assertEqual(self.db.query(Timetable).filter_by(section="API-TEST").count(), 1)

    def test_rejects_stale_credit_hours(self):
        options = self.client.get("/admin/timetable-builder/options").json()
        course = options["courses"][0]
        teacher = options["teachers"][0]
        room = next(row for row in options["rooms"] if row["room_type"] == "Classroom")
        payload = {"department_id": course["department_id"], "academic_year": options["academic_years"][0], "working_days":["Monday"], "day_start_time":"08:30", "day_end_time":"15:30", "slot_minutes":60, "semesters":[{"semester":course["semester"], "section":"STALE", "courses":[{"course_id":course["id"], "teacher_id":teacher["id"], "credit_hours":course["credit_hours"]+1, "weekly_sessions":1, "session_duration_minutes":60, "class_type":"Lecture", "required_room_type":"Classroom", "room_ids":[room["id"]]}]}]}
        response = self.client.post("/admin/timetable-builder/drafts", json=payload)
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn("credit hours changed", response.text)

    def test_generate_edit_validate_approve_publish_and_portal_reads(self):
        options = self.client.get("/admin/timetable-builder/options").json()
        rooms_by_type = {kind: [room for room in options["rooms"] if room["room_type"] == kind] for kind in ("Classroom", "Laboratory")}
        enrollment = next(row for row in self.db.query(Enrollment).filter_by(enrollment_status="Enrolled").all() if row.course.status == "Active" and row.course.teacher_id and self.db.get(Teacher, row.course.teacher_id).status == "Active" and rooms_by_type["Laboratory" if row.course.course_type == "Lab" else "Classroom"])
        course, teacher = enrollment.course, self.db.get(Teacher, enrollment.course.teacher_id)
        room_type = "Laboratory" if course.course_type == "Lab" else "Classroom"
        rooms = rooms_by_type[room_type]
        payload = {"department_id": course.department_id, "academic_year": enrollment.academic_year, "working_days":["Monday","Tuesday","Wednesday","Thursday","Friday"], "day_start_time":"08:00", "day_end_time":"17:00", "slot_minutes":60, "semesters":[{"semester":enrollment.semester,"section":enrollment.section or "A","courses":[{"course_id":course.course_id,"teacher_id":teacher.teacher_id,"credit_hours":course.credit_hours,"weekly_sessions":course.credit_hours,"session_duration_minutes":60,"class_type":"Lab" if course.course_type == "Lab" else "Lecture","required_room_type":room_type,"room_ids":[room["id"] for room in rooms]}]}]}
        created = self.client.post("/admin/timetable-builder/drafts", json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        timetable_id = created.json()["drafts"][0]["timetable_id"]
        generated = self.client.post(f"/admin/timetable-builder/drafts/{timetable_id}/generate")
        self.assertEqual(generated.status_code, 200, generated.text)
        self.assertTrue(generated.json()["success"], generated.text)
        draft = generated.json()["draft"]
        session = draft["courses"][0]["sessions"][0]
        edited = self.client.patch(f"/admin/timetable-builder/sessions/{session['session_id']}", json={"day_of_week":session["day"],"start_time":session["start_time"],"end_time":session["end_time"],"room_id":session["room_id"],"teacher_id":teacher.teacher_id})
        self.assertEqual(edited.status_code, 200, edited.text)
        validated = self.client.post(f"/admin/timetable-builder/drafts/{timetable_id}/validate")
        self.assertTrue(validated.json()["success"], validated.text)
        approved = self.client.post(f"/admin/timetable-builder/drafts/{timetable_id}/approve")
        self.assertEqual(approved.json()["draft"]["status"], "Approved")
        published = self.client.post(f"/admin/timetable-builder/drafts/{timetable_id}/publish")
        self.assertEqual(published.status_code, 200, published.text)
        self.assertEqual(published.json()["draft"]["status"], "Published")
        student = self.db.get(Student, enrollment.student_id)
        student_view = get_student_timetable(semester=enrollment.semester, current_user=student.user, db=self.db)
        self.assertTrue(any(item["code"] == course.course_code for value in student_view["timetable_grid"].values() for item in (value if isinstance(value, list) else [value])))
        teacher_view = get_teacher_schedule(course_id=None, academic_year=enrollment.academic_year, semester=enrollment.semester, schedule_status="Active", current_user=teacher.user, db=self.db)
        self.assertTrue(any(item["course_id"] == course.course_id for item in teacher_view["schedules"]))

    def test_impossible_teacher_availability_returns_actionable_report(self):
        options = self.client.get("/admin/timetable-builder/options").json()
        enrollment = next(row for row in self.db.query(Enrollment).filter_by(enrollment_status="Enrolled").all() if row.course.teacher_id and row.course.course_type != "Lab")
        teacher = self.db.get(Teacher, enrollment.course.teacher_id)
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            self.db.add(TeacherAvailability(teacher_id=teacher.teacher_id, day_of_week=day, start_time="08:00", end_time="17:00", is_available=0))
        self.db.commit()
        rooms = [room for room in options["rooms"] if room["room_type"] == "Classroom"]
        course = enrollment.course
        payload = {"department_id":course.department_id,"academic_year":enrollment.academic_year,"working_days":["Monday","Tuesday","Wednesday","Thursday","Friday"],"day_start_time":"08:00","day_end_time":"17:00","slot_minutes":60,"semesters":[{"semester":enrollment.semester,"section":enrollment.section or "A","courses":[{"course_id":course.course_id,"teacher_id":teacher.teacher_id,"credit_hours":course.credit_hours,"weekly_sessions":1,"session_duration_minutes":60,"class_type":"Lecture","required_room_type":"Classroom","room_ids":[room["id"] for room in rooms]}]}]}
        created = self.client.post("/admin/timetable-builder/drafts", json=payload).json()
        result = self.client.post(f"/admin/timetable-builder/drafts/{created['drafts'][0]['timetable_id']}/generate").json()
        self.assertFalse(result["success"])
        self.assertIn("no conflict-free eligible slot", result["conflicts"][0]["reason"])
    def test_create_room_and_prevent_duplicates(self):
        # 1. Create a new room
        res = self.client.post("/admin/timetable-builder/rooms", json={
            "room_code": "TEST-LAB-99",
            "room_name": "Test Lab 99",
            "room_type": "Laboratory",
            "capacity": 40
        })
        self.assertEqual(res.status_code, 201, res.text)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["room"]["code"], "TEST-LAB-99")
        self.assertEqual(data["room"]["capacity"], 40)
        
        # 2. Prevent duplicate creation (case-insensitive)
        dup = self.client.post("/admin/timetable-builder/rooms", json={
            "room_code": "test-lab-99",
            "room_name": "Duplicate Test Lab",
            "room_type": "Laboratory",
            "capacity": 30
        })
        self.assertEqual(dup.status_code, 409, dup.text)
        self.assertIn("already exists", dup.text)

    def test_flexible_independent_class_meetings(self):
        options = self.client.get("/admin/timetable-builder/options").json()
        course = options["courses"][0]
        teacher = options["teachers"][0]
        room_x = options["rooms"][0]
        room_y = options["rooms"][1] if len(options["rooms"]) > 1 else options["rooms"][0]

        payload = {
            "department_id": course["department_id"],
            "academic_year": options["academic_years"][0],
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "day_start_time": "08:00",
            "day_end_time": "17:00",
            "slot_minutes": 60,
            "semesters": [{
                "semester": course["semester"],
                "section": "FLEX-TEST",
                "courses": [{
                    "course_id": course["id"],
                    "teacher_id": teacher["id"],
                    "credit_hours": course["credit_hours"],
                    "weekly_sessions": 3,
                    "session_duration_minutes": 60,
                    "class_type": "Lecture",
                    "required_room_type": "Classroom",
                    "room_ids": [room_x["id"], room_y["id"]],
                    "meetings": [
                        {"meeting_index": 1, "day": "Monday", "start_time": "08:00", "end_time": "09:30", "room_id": room_x["id"], "teacher_id": teacher["id"]},
                        {"meeting_index": 2, "day": "Monday", "start_time": "14:00", "end_time": "15:00", "room_id": room_y["id"], "teacher_id": teacher["id"]},
                        {"meeting_index": 3, "day": "Thursday", "start_time": "10:00", "end_time": "11:30", "room_id": room_x["id"], "teacher_id": teacher["id"]}
                    ]
                }]
            }]
        }

        created = self.client.post("/admin/timetable-builder/drafts", json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        draft = created.json()["drafts"][0]
        
        # Verify 3 sessions were persisted with the specific days and times
        sessions = draft["courses"][0]["sessions"]
        self.assertEqual(len(sessions), 3)
        self.assertEqual(sessions[0]["day"], "Monday")
        self.assertEqual(sessions[0]["start_time"], "08:00")
        self.assertEqual(sessions[0]["end_time"], "09:30")
        self.assertEqual(sessions[0]["room_id"], room_x["id"])

        self.assertEqual(sessions[1]["day"], "Monday")
        self.assertEqual(sessions[1]["start_time"], "14:00")
        self.assertEqual(sessions[1]["end_time"], "15:00")

        self.assertEqual(sessions[2]["day"], "Thursday")
        self.assertEqual(sessions[2]["start_time"], "10:00")
        self.assertEqual(sessions[2]["end_time"], "11:30")


if __name__ == "__main__":
    unittest.main()
