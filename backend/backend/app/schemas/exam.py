from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class ExamQuestionCreate(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    option_a: str = Field(min_length=1, max_length=2000)
    option_b: str = Field(min_length=1, max_length=2000)
    option_c: str = Field(min_length=1, max_length=2000)
    option_d: str = Field(min_length=1, max_length=2000)
    correct_option: Literal["A", "B", "C", "D"]
    marks: float = Field(gt=0)

class ExamCreate(BaseModel):
    course_id: int
    academic_year: str = Field(min_length=1, max_length=20)
    section: str = Field(min_length=1, max_length=30)
    title: str = Field(min_length=1, max_length=250)
    assessment_type: Literal["Quiz", "Midterm", "Final"]
    start_at: datetime
    end_at: datetime
    duration_minutes: int = Field(gt=0, le=600)
    total_marks: float = Field(gt=0)
    questions: list[ExamQuestionCreate] = Field(default_factory=list)
    student_ids: list[int] = Field(default_factory=list)
    publish: bool = True

    @model_validator(mode="after")
    def dates_and_marks(self):
        if self.end_at <= self.start_at:
            raise ValueError("End time must be after start time")
        if self.questions and abs(sum(q.marks for q in self.questions) - self.total_marks) > .01:
            raise ValueError("Question marks must equal total marks")
        if self.publish and not self.questions:
            raise ValueError("A published paper must contain at least one MCQ")
        return self

class AnswerSave(BaseModel):
    question_id: int
    selected_option: Literal["A", "B", "C", "D"] | None = None

class SubmitExam(BaseModel):
    auto_submit_reason: Literal["timer", "fullscreen_violation"] | None = None
    fullscreen_violations: int = Field(default=0, ge=0, le=3)

class ExamViolation(BaseModel):
    reason: str = Field(min_length=1, max_length=200)
