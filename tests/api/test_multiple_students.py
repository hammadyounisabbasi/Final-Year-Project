import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[2] / "backend" / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from app.api.auth import login
from app.schemas.auth import LoginRequest
from app.api.student import get_student_profile

def test_multiple_students():
    db = SessionLocal()
    test_users = ["hamza.ali24", "ahmed.raza24", "usman.khan24", "bilal.raja24", "zain.abidin24"]
    
    print("\n--- Testing Multi-Student Authentication & Dynamic Profile Fetch ---")
    for username in test_users:
        resp = login(LoginRequest(identifier=username, password="UOH@2025"), db=db)
        token = resp["access_token"]
        user = db.query(User).filter(User.username == username).first()
        profile = get_student_profile(current_user=user, db=db)
        
        print(f" Verified: {username}")
        print(f"    Name: {profile['first_name']} {profile['last_name']}")
        print(f"    Roll No: {profile['roll_number']}")
        print(f"    Department: {profile['department']['department_name']}")
        print(f"    Semester: {profile['semester']} (Section: {profile['section']})")
        print(f"    Email: {profile['email']}")
        print("    ------------------------------------------")
    db.close()
    print("\n MULTI-STUDENT PROFILE TESTS PASSED! ")

if __name__ == "__main__":
    test_multiple_students()
