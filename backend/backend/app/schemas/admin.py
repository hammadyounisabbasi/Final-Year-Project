from typing import Literal, Optional, List

from pydantic import BaseModel, Field, model_validator


class AdminStudentUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, min_length=3, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    emergency_contact: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    program: Optional[str] = Field(None, min_length=1, max_length=150)
    semester: Optional[int] = Field(None, ge=1, le=20)
    section: Optional[str] = Field(None, max_length=20)
    batch_year: Optional[int] = Field(None, ge=1900, le=2200)
    department_id: Optional[int] = Field(None, gt=0)
    status: Optional[Literal["Active", "Graduated", "Suspended", "Dropped"]] = None
    account_active: Optional[bool] = None


class AdminStudentChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=2000)


class AdminStudentAIRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: List[AdminStudentChatMessage] = Field(default_factory=list, max_length=12)
    selected_student_id: Optional[int] = Field(None, gt=0)


class AdminFacultyUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    account_email: Optional[str] = Field(None, min_length=3, max_length=255)
    office_email: Optional[str] = Field(None, min_length=3, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    designation: Optional[str] = Field(None, min_length=1, max_length=150)
    qualification: Optional[str] = Field(None, max_length=255)
    specialization: Optional[str] = Field(None, max_length=255)
    office_room: Optional[str] = Field(None, max_length=100)
    employment_type: Optional[Literal["Permanent", "Contract", "Visiting"]] = None
    department_id: Optional[int] = Field(None, gt=0)
    status: Optional[Literal["Active", "On Leave", "Retired", "Resigned"]] = None
    account_active: Optional[bool] = None


class AdminFacultyAIRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: List[AdminStudentChatMessage] = Field(default_factory=list, max_length=12)
    selected_teacher_id: Optional[int] = Field(None, gt=0)


class AdminIntegrityAIRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: List[AdminStudentChatMessage] = Field(default_factory=list, max_length=12)
    selected_submission_id: Optional[int] = Field(None, gt=0)
    selected_student_id: Optional[int] = Field(None, gt=0)
    selected_teacher_id: Optional[int] = Field(None, gt=0)


class AcademicTermStatusUpdate(BaseModel):
    academic_year: str = Field(..., min_length=1, max_length=20)
    semester: int = Field(..., ge=1, le=20)
    status: Literal["Upcoming", "Active", "Completed"]


class TimetableScope(BaseModel):
    department_id: Optional[int] = Field(None, gt=0)
    semester: Optional[int] = Field(None, ge=1, le=20)
    section: Optional[str] = Field(None, min_length=1, max_length=20)
    teacher_id: Optional[int] = Field(None, gt=0)
    student_id: Optional[int] = Field(None, gt=0)
    academic_year: Optional[str] = Field(None, min_length=1, max_length=20)


class TimetableHistoryMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(..., min_length=1, max_length=2000)


class ReviewedTimetableReference(BaseModel):
    document_reviewed: bool = False

    @model_validator(mode='after')
    def require_reference_review(self):
        if getattr(self, 'document_text', None) and not self.document_reviewed:
            raise ValueError('Review and confirm the extracted reference before generation')
        return self


class TimetableProposalRequest(TimetableScope, ReviewedTimetableReference):
    mode: Literal["student", "teacher", "department", "semester", "section", "university"] = "department"
    prompt: Optional[str] = Field(None, max_length=1000)
    history: List[TimetableHistoryMessage] = Field(default_factory=list, max_length=20)
    document_name: Optional[str] = Field(None, max_length=255)
    document_text: Optional[str] = Field(None, max_length=20000)


class TimetableApprovalRequest(BaseModel):
    changes: List[dict] = Field(..., min_length=1, max_length=500)
    approved: Literal[True]
    proposal_token: str = Field(..., min_length=1, max_length=4000)


class TimetablePdfRequest(BaseModel):
    schedules: List[dict] = Field(default_factory=list, max_length=1000)


class TimetableChatRequest(TimetableScope, ReviewedTimetableReference):
    conversation_state: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def bound_conversation_state(self):
        import json
        if len(json.dumps(self.conversation_state)) > 500000:
            raise ValueError("Conversation state exceeds 500 KB")
        return self

    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(None, min_length=1, max_length=100)
    history: List[TimetableHistoryMessage] = Field(default_factory=list, max_length=20)
    document_name: Optional[str] = Field(None, max_length=255)
    document_text: Optional[str] = Field(None, max_length=20000)


class CreateRoomRequest(BaseModel):
    room_code: str = Field(..., min_length=1, max_length=50)
    room_name: Optional[str] = Field(None, max_length=100)
    room_type: Literal["Classroom", "Computer Lab", "Laboratory", "Seminar Room"] = "Classroom"
    capacity: int = Field(..., ge=1, le=500)


class TimetableMeetingSetup(BaseModel):
    meeting_index: int = Field(..., ge=1, le=12)
    day: Optional[Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]] = None
    start_time: Optional[str] = Field(None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_time: Optional[str] = Field(None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    teacher_id: Optional[int] = Field(None, gt=0)
    room_id: Optional[int] = Field(None, gt=0)

    @model_validator(mode="after")
    def valid_time_order(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValueError("Class meeting start time must be before end time")
        return self


class TimetableCourseSetup(BaseModel):
    course_id: int = Field(..., gt=0)
    teacher_id: int = Field(..., gt=0)
    credit_hours: int = Field(..., ge=1, le=12)
    weekly_sessions: int = Field(..., ge=1, le=12)
    session_duration_minutes: int = Field(60, ge=30, le=240)
    class_type: Literal["Lecture", "Lab", "Tutorial", "Seminar"] = "Lecture"
    required_room_type: Literal["Classroom", "Computer Lab", "Laboratory", "Seminar Room"] = "Classroom"
    room_ids: List[int] = Field(..., min_length=1, max_length=50)
    meetings: Optional[List[TimetableMeetingSetup]] = Field(default_factory=list)


class TimetableSemesterSetup(BaseModel):
    semester: int = Field(..., ge=1, le=20)
    section: str = Field("A", min_length=1, max_length=20)
    courses: List[TimetableCourseSetup] = Field(..., min_length=1, max_length=30)

    @model_validator(mode="after")
    def unique_courses(self):
        course_ids = [item.course_id for item in self.courses]
        if len(course_ids) != len(set(course_ids)):
            raise ValueError("A course can only be selected once per semester")
        return self


class TimetableDraftSetupRequest(BaseModel):
    department_id: int = Field(..., gt=0)
    academic_year: str = Field(..., min_length=1, max_length=20)
    working_days: List[Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]] = Field(..., min_length=1, max_length=7)
    day_start_time: str = Field(..., pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    day_end_time: str = Field(..., pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    slot_minutes: int = Field(60, ge=30, le=240)
    semesters: List[TimetableSemesterSetup] = Field(..., min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_setup(self):
        if self.day_start_time >= self.day_end_time:
            raise ValueError("Day start time must be before day end time")
        if len(self.working_days) != len(set(self.working_days)):
            raise ValueError("Working days must be unique")
        scopes = [(item.semester, item.section.strip().casefold()) for item in self.semesters]
        if len(scopes) != len(set(scopes)):
            raise ValueError("Semester and section combinations must be unique")
        return self


class TimetableSessionEditRequest(BaseModel):
    day_of_week: Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    start_time: str = Field(..., pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(..., pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    room_id: int = Field(..., gt=0)
    teacher_id: Optional[int] = Field(None, gt=0)

    @model_validator(mode="after")
    def valid_time_order(self):
        if self.start_time >= self.end_time:
            raise ValueError("Session start time must be before end time")
        return self
