import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[2] / "backend" / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from app.api.student import get_student_results

def test_multi_semester_results():
    print("\n--- Testing Multi-Semester Results Across Different Students ---")
    db = SessionLocal()
    try:
        # Students with finalized completed semesters
        test_cases = [
            ("hira.noor24", 3, 2),        # Semester 3 student has completed Sem 1 & 2
            ("alina.ashraf24", 5, 4),    # Semester 5 student has completed Sem 1..4
            ("hammad.younis24", 6, 5)    # Semester 6 student has completed Sem 1..5
        ]

        for username, current_sem, expected_completed_sems in test_cases:
            user = db.query(User).filter(User.username == username).first()
            assert user is not None, f"User {username} not found"

            res = get_student_results(semester=None, current_user=user, db=db)
            assert res["success"] is True
            
            student = res["student"]
            metrics = res["metrics"]
            course_results = res["course_results"]
            sem_summary = res["semester_summary"]
            avail_sems = res["available_semesters"]

            print(f"\n========================================================")
            print(f"Student: {student['name']} ({student['roll_number']}) | Current Semester: {student['semester']}")
            print(f"CGPA: {metrics['cgpa']} | Total Credits: {metrics['total_credit_hours']} | Total Grade Points: {metrics['total_grade_points']}")
            print(f"Available Semesters ({len(avail_sems)}): {[s['label'] for s in avail_sems]}")
            print(f"Total Course Results Count: {len(course_results)}")
            print(f"Semester Wise Summary Rows: {len(sem_summary)}")

            assert len(avail_sems) == expected_completed_sems, f"Expected {expected_completed_sems} semesters, got {len(avail_sems)}"
            assert len(sem_summary) == expected_completed_sems, f"Expected {expected_completed_sems} semester summary rows, got {len(sem_summary)}"
            assert len(course_results) >= expected_completed_sems * 5, f"Expected at least {expected_completed_sems * 5} courses, got {len(course_results)}"

            # Test individual semester filtering
            for sem_num in range(1, expected_completed_sems + 1):
                sem_res = get_student_results(semester=sem_num, current_user=user, db=db)
                sem_courses = sem_res["course_results"]
                assert len(sem_courses) >= 5, f"Expected at least 5 courses in Semester {sem_num}"
                print(f"   Verified Semester {sem_num}: {len(sem_courses)} courses loaded. First course: [{sem_courses[0]['code']}] {sem_courses[0]['name']} (Grade: {sem_courses[0]['grade']})")

        print("\n ALL MULTI-SEMESTER DYNAMIC RESULTS TESTS PASSED SUCCESSFULLY! ")
    finally:
        db.close()

if __name__ == "__main__":
    test_multi_semester_results()
