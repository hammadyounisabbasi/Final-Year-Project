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


class Grade(Base):
    __tablename__ = "Grades"

    grade_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    enrollment_id = Column(
        Integer,
        ForeignKey("Enrollments.enrollment_id"),
        nullable=False
    )

    assessment_type = Column(
        String,
        nullable=False
    )

    title = Column(
        String,
        nullable=False
    )

    obtained_marks = Column(
        Float,
        nullable=False,
        default=0.0
    )

    total_marks = Column(
        Float,
        nullable=False,
        default=0.0
    )

    percentage = Column(
        Float,
        nullable=True,
        default=0.0
    )

    letter_grade = Column(
        String,
        nullable=True
    )

    grade_points = Column(
        Float,
        nullable=True,
        default=0.0
    )

    remarks = Column(
        String,
        nullable=True
    )

    graded_by = Column(
        Integer,
        ForeignKey("Teachers.teacher_id"),
        nullable=True
    )

    graded_at = Column(
        DateTime,
        nullable=True
    )

    verified = Column(
        Integer,
        default=0
    )

    verification_hash = Column(
        String,
        nullable=True
    )

    published = Column(
        Integer,
        default=1
    )

    is_locked = Column(
        Integer,
        default=0
    )

    academic_year = Column(
        String,
        nullable=True
    )

    semester = Column(
        Integer,
        nullable=True
    )

    created_at = Column(
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

    enrollment = relationship(
        "Enrollment",
        backref="grades"
    )

    teacher = relationship(
        "Teacher",
        backref="given_grades"
    )
