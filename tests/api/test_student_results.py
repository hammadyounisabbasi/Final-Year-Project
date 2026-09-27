import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[2] / "backend" / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from app.api.student import get_student_results

def test_student_results_endpoint():
    print("\n--- 1. Testing GET /student/results for Danish Malik (CSE-24-027) ---")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "danish.malik24").first()
        assert user is not None, "Test user not found"

        res = get_student_results(semester=None, current_user=user, db=db)
        assert res["success"] is True
        
        student = res["student"]
        metrics = res["metrics"]
        course_results = res["course_results"]
        sem_summary = res["semester_summary"]
        current_bar = res["current_semester_summary"]
        chart = res["chart"]

        print(f" Student: {student['name']} ({student['roll_number']}) - {student['program']}")
        print(f" Metrics: CGPA={metrics['cgpa']}, Credits={metrics['total_credit_hours']}, Points={metrics['total_grade_points']}, Standing={metrics['academic_standing']}")
        print(f" Available Semesters: {res['available_semesters']}")
        print(f" Summary Bar: GPA={current_bar['gpa']}, Credits={current_bar['credit_hours']}, Marks={current_bar['obtained_marks']}, Pct={current_bar['percentage']}")
        print(f" Chart Labels: {chart['labels']}, Data: {chart['data']}")

        print("\n--- 2. Checking Course Results Detail ---")
        for cr in course_results:
            print(f"   [{cr['code']}] {cr['name']} | Marks: {cr['marks']} | Grade: {cr['grade']} | Points: {cr['gradePoints']} | Remarks: {cr['remarks']}")

        print("\n--- 3. Checking Semester-Wise Summary ---")
        for ss in sem_summary:
            print(f"   {ss['semester_name']}: Credits={ss['credit_hours']}, GPA={ss['gpa']}, CGPA={ss['cgpa']}, Points={ss['grade_points']}, Pct={ss['percentage']}")

        assert len(course_results) > 0, "Expected non-empty course results"
        assert metrics["cgpa"] > 0, "Expected valid CGPA"
        print("\n ALL RESULTS & CGPA TESTS PASSED SUCCESSFULLY! ")
    finally:
        db.close()

if __name__ == "__main__":
    test_student_results_endpoint()
