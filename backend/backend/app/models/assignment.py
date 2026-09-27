from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Assignment(Base):
    __tablename__ = "Assignments"

    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("Courses.course_id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("Teachers.teacher_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    assignment_type = Column(String, nullable=False, default="Assignment")
    total_marks = Column(Float, nullable=False)
    semester = Column(Integer, nullable=False)
    academic_year = Column(String, nullable=False)
    section = Column(String, nullable=True)
    release_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    allow_late_submission = Column(Boolean, nullable=False, default=False)
    late_penalty_percentage = Column(Float, nullable=False, default=0)
    attachment_path = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Published")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("Course", backref="assignments")
    teacher = relationship("Teacher", backref="assignments")

    __table_args__ = (
        CheckConstraint("assignment_type IN ('Assignment', 'Quiz', 'Project', 'Lab', 'Presentation')"),
        CheckConstraint("status IN ('Draft', 'Published', 'Closed', 'Archived')"),
        CheckConstraint("total_marks > 0"),
    )
