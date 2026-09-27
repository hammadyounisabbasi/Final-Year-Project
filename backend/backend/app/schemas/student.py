from typing import Optional
from pydantic import BaseModel


class StudentProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    address: Optional[str] = None


class StudentAssignmentSubmissionCreate(BaseModel):
    submission_title: Optional[str] = None
    response_text: str
