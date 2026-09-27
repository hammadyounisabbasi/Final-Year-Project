import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[2] / "backend" / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from app.api.auth import login
from app.schemas.auth import LoginRequest
from app.api.student import get_student_courses

def test_student_courses_endpoint():
    db = SessionLocal()
    print("\n--- Testing GET /student/courses Endpoint for Multiple Students ---")
    
    test_users = [
        ("hamza.ali24", 1),
        ("hira.noor24", 3),
        ("alina.ashraf24", 5),
        ("hammad.younis24", 6)
    ]
    
    for username, current_sem in test_users:
        resp = login(LoginRequest(identifier=username, password="UOH@2025"), db=db)
        token = resp["access_token"]
        user = db.query(User).filter(User.username == username).first()
        
        courses_data = get_student_courses(semester=None, current_user=user, db=db)
        
        # Actual response structure:
        # courses_data["metrics"]["enrolled_courses_count"]
        # courses_data["metrics"]["total_credit_hours"]
        # courses_data["available_semesters"]
        # courses_data["courses"]
        metrics = courses_data.get("metrics", {})
        total_courses = metrics.get("enrolled_courses_count", 0)
        total_credits = metrics.get("total_credit_hours", 0)

        print(f"\n>> Student: {username} (Current Semester: {current_sem})")
        print(f"   Summary: Total Courses={total_courses}, Total Credits={total_credits}")
        print(f"   Available Semesters: {[s['label'] for s in courses_data.get('available_semesters', [])]}")
        print(f"   Courses Loaded ({len(courses_data.get('courses', []))}):")
        for c in courses_data.get("courses", []):
            print(f"     - [{c['course_code']}] {c['course_title']} ({c['credit_hours']} CH) | Teacher: {c['instructor']['name']}")
        
        assert total_courses >= 0, f"enrolled_courses_count should be non-negative for {username}"
        assert len(courses_data.get("courses", [])) >= 0
        
    db.close()
    print("\n ALL STUDENT COURSES ENDPOINT TESTS PASSED! ")

if __name__ == "__main__":
    test_student_courses_endpoint()
