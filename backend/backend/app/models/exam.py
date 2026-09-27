from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class Assessment(Base):
    __tablename__ = "Assessments"
    assessment_id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("Courses.course_id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("Teachers.teacher_id"), nullable=False)
    academic_year = Column(String, nullable=False)
    semester = Column(Integer, nullable=False)
    section = Column(String, nullable=False)
    title = Column(String, nullable=False)
    assessment_type = Column(String, nullable=False)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    total_marks = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="Draft")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    course = relationship("Course")
    teacher = relationship("Teacher")


class AssessmentQuestion(Base):
    __tablename__ = "Assessment_Questions"
    question_id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("Assessments.assessment_id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_option = Column(String, nullable=False)
    marks = Column(Float, nullable=False)
    position = Column(Integer, nullable=False)
    assessment = relationship("Assessment", backref="questions")


class AssessmentAttempt(Base):
    __tablename__ = "Assessment_Attempts"
    attempt_id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("Assessments.assessment_id"), nullable=False)
    student_id = Column(Integer, ForeignKey("Students.student_id"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("Enrollments.enrollment_id"), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    status = Column(String, nullable=False, default="In Progress")
    fullscreen_violations = Column(Integer, nullable=False, default=0)
    obtained_marks = Column(Float, nullable=False, default=0)
    total_marks = Column(Float, nullable=False, default=0)
    auto_submit_reason = Column(String)
    assessment = relationship("Assessment", backref="attempts")
    student = relationship("Student")
    __table_args__ = (UniqueConstraint("assessment_id", "student_id", name="uq_assessment_attempt_student"),)


class AssessmentResponse(Base):
    __tablename__ = "Assessment_Responses"
    response_id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("Assessment_Attempts.attempt_id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("Assessment_Questions.question_id"), nullable=False)
    selected_option = Column(String)
    is_correct = Column(Integer)
    awarded_marks = Column(Float, nullable=False, default=0)
    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_assessment_response_question"),)


class AssessmentTargetStudent(Base):
    __tablename__ = "Assessment_Target_Students"
    assessment_id = Column(Integer, ForeignKey("Assessments.assessment_id", ondelete="CASCADE"), primary_key=True)
    student_id = Column(Integer, ForeignKey("Students.student_id"), primary_key=True)
