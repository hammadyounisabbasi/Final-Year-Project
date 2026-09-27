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


class SemesterGPA(Base):
    __tablename__ = "Semester_GPA"

    semester_gpa_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = Column(
        Integer,
        ForeignKey("Students.student_id"),
        nullable=False
    )

    semester = Column(
        Integer,
        nullable=False
    )

    academic_year = Column(
        String,
        nullable=False
    )

    total_credit_hours = Column(
        Integer,
        nullable=False,
        default=0
    )

    earned_credit_hours = Column(
        Integer,
        nullable=False,
        default=0
    )

    total_grade_points = Column(
        Float,
        nullable=False,
        default=0.0
    )

    semester_gpa = Column(
        Float,
        nullable=False,
        default=0.0
    )

    academic_status = Column(
        String,
        nullable=False,
        default="Good Standing"
    )

    remarks = Column(
        String,
        nullable=True
    )

    calculated_at = Column(
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
        backref="semester_gpas"
    )
