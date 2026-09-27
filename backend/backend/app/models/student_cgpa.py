from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class StudentCGPA(Base):
    __tablename__ = "Student_CGPA"

    cgpa_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = Column(
        Integer,
        ForeignKey("Students.student_id"),
        nullable=False,
        unique=True
    )

    total_completed_credit_hours = Column(
        Integer,
        nullable=False,
        default=0
    )

    total_grade_points = Column(
        Float,
        nullable=False,
        default=0.0
    )

    overall_cgpa = Column(
        Float,
        nullable=False,
        default=0.0
    )

    total_passed_courses = Column(
        Integer,
        nullable=False,
        default=0
    )

    total_failed_courses = Column(
        Integer,
        nullable=False,
        default=0
    )

    academic_status = Column(
        String,
        nullable=False,
        default="Good Standing"
    )

    graduation_eligible = Column(
        Integer,
        default=0
    )

    honors_status = Column(
        String,
        nullable=True,
        default="None"
    )

    remarks = Column(
        String,
        nullable=True
    )

    last_calculated = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    student = relationship(
        "Student",
        backref="cgpa_record"
    )
