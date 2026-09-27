import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[2] / "backend" / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from app.api.student import get_student_profile

def test_direct_student_profile():
    print("\n--- Testing Direct Service/API Function `get_student_profile` ---")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "hamza.ali24").first()
        assert user is not None, "Test user hamza.ali24 not found"

        profile_data = get_student_profile(current_user=user, db=db)
        print(" Direct Profile Data fetched successfully:")
        print("   Name:", profile_data["first_name"], profile_data["last_name"])
        print("   Roll Number:", profile_data["roll_number"])
        print("   Registration Number:", profile_data["registration_number"])
        print("   Department:", profile_data["department"]["department_name"])
        print("   Credits Completed:", profile_data["credits_completed"])
        
        assert profile_data["first_name"] == "Hamza"
        assert profile_data["roll_number"] == "CSE-24-001"
        assert profile_data["department"]["department_code"] == "CSE"
        print(" All Direct Profile Assertions Passed!")
    finally:
        db.close()

if __name__ == "__main__":
    test_direct_student_profile()
