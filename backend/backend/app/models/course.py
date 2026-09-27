from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Course(Base):
    __tablename__ = "Courses"

    course_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    department_id = Column(
        Integer,
        ForeignKey("Departments.department_id"),
        nullable=False
    )

    course_code = Column(
        String,
        nullable=False,
        unique=True
    )

    course_title = Column(
        String,
        nullable=False
    )

    course_description = Column(
        String,
        nullable=True
    )

    credit_hours = Column(
        Integer,
        nullable=False
    )

    semester = Column(
        Integer,
        nullable=False
    )

    course_type = Column(
        String,
        nullable=False,
        default="Core"
    )

    teacher_id = Column(
        Integer,
        ForeignKey("Teachers.teacher_id"),
        nullable=True
    )

    status = Column(
        String,
        nullable=False,
        default="Active"
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

    department = relationship(
        "Department",
        back_populates="courses"
    )

    teacher = relationship(
        "Teacher",
        back_populates="courses"
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="course"
    )

    # ------------------------------------------------------
    # Constraints
    # ------------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            "course_type IN ('Core', 'Elective', 'Lab')",
            name="check_course_type"
        ),
        CheckConstraint(
            "status IN ('Active', 'Inactive')",
            name="check_course_status"
        ),
    )
