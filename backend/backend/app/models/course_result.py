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


class CourseResult(Base):
    __tablename__ = "Course_Results"

    result_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    enrollment_id = Column(
        Integer,
        ForeignKey("Enrollments.enrollment_id"),
        nullable=False
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

    teacher_id = Column(
        Integer,
        ForeignKey("Teachers.teacher_id"),
        nullable=True
    )

    semester = Column(
        Integer,
        nullable=False
    )

    academic_year = Column(
        String,
        nullable=False
    )

    credit_hours = Column(
        Integer,
        nullable=False
    )

    quality_points = Column(
        Float,
        nullable=False,
        default=0.0
    )

    sessional_marks = Column(
        Float,
        nullable=True,
        default=0.0
    )

    midterm_marks = Column(
        Float,
        nullable=True,
        default=0.0
    )

    final_marks = Column(
        Float,
        nullable=True,
        default=0.0
    )

    total_marks = Column(
        Float,
        nullable=True,
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

    result_status = Column(
        String,
        nullable=False,
        default="Pass"
    )

    verified = Column(
        Integer,
        default=0
    )

    published = Column(
        Integer,
        default=1
    )

    locked = Column(
        Integer,
        default=0
    )

    verification_hash = Column(
        String,
        nullable=True
    )

    remarks = Column(
        String,
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

    student = relationship(
        "Student",
        backref="course_results"
    )

    course = relationship(
        "Course",
        backref="course_results"
    )

    enrollment = relationship(
        "Enrollment",
        backref="course_result"
    )

    teacher = relationship(
        "Teacher",
        backref="course_results"
    )
