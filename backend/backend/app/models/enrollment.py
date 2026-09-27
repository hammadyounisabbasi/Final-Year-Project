from datetime import date, datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Enrollment(Base):
    __tablename__ = "Enrollments"

    enrollment_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = Column(
        Integer,
        ForeignKey("Students.student_id"),
        nullable=False
    )

    course_id = Column(
        Integer,
        ForeignKey("Courses.course_id"),
        nullable=False
    )

    academic_year = Column(
        String,
        nullable=False
    )

    semester = Column(
        Integer,
        nullable=False
    )

    section = Column(
        String,
        nullable=True
    )

    enrollment_date = Column(
        Date,
        default=date.today
    )

    enrollment_status = Column(
        String,
        nullable=False,
        default="Enrolled"
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

    student = relationship(
        "Student",
        back_populates="enrollments"
    )

    course = relationship(
        "Course",
        back_populates="enrollments"
    )

    # ------------------------------------------------------
    # Constraints
    # ------------------------------------------------------

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_id",
            "academic_year",
            name="unique_student_course_year"
        ),
        CheckConstraint(
            "enrollment_status IN ('Enrolled', 'Dropped', 'Completed', 'Withdrawn')",
            name="check_enrollment_status"
        ),
    )
