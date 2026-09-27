from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Submission(Base):
    __tablename__ = "Submissions"

    submission_id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("Assignments.assignment_id"), nullable=False)
    student_id = Column(Integer, ForeignKey("Students.student_id"), nullable=False)
    submission_title = Column(String, nullable=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    response_text = Column(String, nullable=True)
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_late = Column(Boolean, nullable=False, default=False)
    submission_attempt = Column(Integer, nullable=False, default=1)
    plagiarism_score = Column(Float, nullable=True)
    ai_score = Column(Float, nullable=True)
    ai_feedback = Column(String, nullable=True)
    teacher_marks = Column(Float, nullable=True)
    teacher_feedback = Column(String, nullable=True)
    submission_status = Column(String, nullable=False, default="Submitted")
    verified = Column(Boolean, nullable=False, default=False)
    graded = Column(Boolean, nullable=False, default=False)
    graded_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignment = relationship("Assignment", backref="submissions")
    student = relationship("Student", backref="submissions")

    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", "submission_attempt"),
        CheckConstraint("submission_status IN ('Draft', 'Submitted', 'Under Review', 'Reviewed', 'Returned', 'Accepted', 'Rejected')"),
    )
