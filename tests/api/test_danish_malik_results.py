import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[2] / "backend" / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from app.api.student import get_student_results

def test_danish_malik_results():
    print("\n--- Testing Danish Malik (Semester 4 Student) Results ---")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "danish.malik24").first()
        assert user is not None, "User danish.malik24 not found in database"

        res = get_student_results(semester=None, current_user=user, db=db)
        assert res["success"] is True
        
        student = res["student"]
        metrics = res["metrics"]
        course_results = res["course_results"]
        sem_summary = res["semester_summary"]
        avail_sems = res["available_semesters"]

        print(f"Logged in Student: {student['name']} | Roll No: {student['roll_number']} | Semester: {student['semester']}")
        print(f"CGPA: {metrics['cgpa']} | Total Credits: {metrics['total_credit_hours']} | Total Grade Points: {metrics['total_grade_points']}")
        print(f"Available Semesters ({len(avail_sems)}): {[s['label'] for s in avail_sems]}")
        print(f"Total Enrolled Courses in Record: {len(course_results)}")

        # Check each semester
        for sem_info in avail_sems:
            s_num = sem_info["semester"]
            sem_courses = [c for c in course_results if c["semester"] == s_num]
            sem_rec = next((s for s in sem_summary if s["semester"] == s_num), None)
            print(f"\n>> Checking Semester {s_num} for Danish Malik:")
            print(f"   Semester GPA: {sem_rec['gpa']} | Earned Credits: {sem_rec['credit_hours']} | Grade Points: {sem_rec['grade_points']}")
            print(f"   Courses ({len(sem_courses)}):")
            for c in sem_courses:
                print(f"     - [{c['code']}] {c['name']} | Marks: {c['marks']} | Grade: {c['grade']} | Points: {c['gradePoints']}")

        assert len(avail_sems) >= 3, "Danish Malik should have at least 3 finalized semesters available"
        print("\n DANISH MALIK MULTI-SEMESTER VERIFICATION SUCCEEDED! ")
    finally:
        db.close()

if __name__ == "__main__":
    test_danish_malik_results()
