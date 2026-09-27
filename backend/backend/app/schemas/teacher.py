from typing import Literal
from datetime import date, datetime

from pydantic import BaseModel, Field


class TeacherScheduleCreate(BaseModel):
    course_id: int
    academic_year: str = Field(..., min_length=1, max_length=20)
    semester: int = Field(..., ge=1, le=20)
    section: str = Field(..., min_length=1, max_length=30)
    day_of_week: Literal[
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]
    start_time: str = Field(..., min_length=5, max_length=5)
    end_time: str = Field(..., min_length=5, max_length=5)
    room_location: str = Field(..., min_length=1, max_length=100)
    class_type: Literal["Lecture", "Lab", "Tutorial", "Seminar"] = "Lecture"


class TeacherAssignmentCreate(BaseModel):
    course_id: int
    academic_year: str = Field(..., min_length=1, max_length=20)
    section: str = Field(..., min_length=1, max_length=30)
    title: str = Field(..., min_length=1, max_length=250)
    description: str | None = None
    assignment_type: Literal["Assignment", "Quiz", "Project", "Lab", "Presentation"] = "Assignment"
    total_marks: float = Field(..., gt=0)
    due_date: datetime


class TeacherSubmissionReview(BaseModel):
    teacher_marks: float | None = Field(default=None, ge=0)
    teacher_feedback: str | None = None


class AttendanceEntry(BaseModel):
    student_id: int
    status: Literal["Present", "Absent", "Late", "Leave"]
    remarks: str | None = Field(default=None, max_length=500)


class TeacherAttendanceSave(BaseModel):
    schedule_id: int
    attendance_date: date
    records: list[AttendanceEntry] = Field(..., min_length=1)


class GradebookComponentInput(BaseModel):
    category: Literal["Sessional", "Midterm", "Final"]
    name: str = Field(..., min_length=1, max_length=100)
    item_count: int = Field(..., ge=1, le=100)
    total_marks: float = Field(..., gt=0, le=100)


class GradebookSettingsSave(BaseModel):
    course_id: int
    academic_year: str = Field(..., min_length=1, max_length=20)
    semester: int = Field(..., ge=1, le=20)
    components: list[GradebookComponentInput] = Field(..., min_length=1)


class GradebookComponentScores(BaseModel):
    component_id: int
    scores: list[float] = Field(..., min_length=1)


class GradebookMarksSave(BaseModel):
    enrollment_id: int
    components: list[GradebookComponentScores] = Field(..., min_length=1)
