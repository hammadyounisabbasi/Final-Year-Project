from datetime import date, datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Student(Base):
    __tablename__ = "Students"

    # Primary Key
    student_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # User Relationship
    user_id = Column(
        Integer,
        ForeignKey("Users.user_id"),
        nullable=False,
        unique=True
    )

    # Department Relationship
    department_id = Column(
        Integer,
        ForeignKey("Departments.department_id"),
        nullable=False
    )

    # Student Identifiers
    roll_number = Column(
        String,
        nullable=False,
        unique=True
    )

    registration_number = Column(
        String,
        nullable=False,
        unique=True
    )

    # Personal Information
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    gender = Column(String, nullable=True)

    date_of_birth = Column(
        Date,
        nullable=True
    )

    phone = Column(String, nullable=True)

    emergency_contact = Column(
        String,
        nullable=True
    )

    address = Column(
        String,
        nullable=True
    )

    # Academic Information
    program = Column(
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

    batch_year = Column(
        Integer,
        nullable=True
    )

    admission_date = Column(
        Date,
        nullable=True
    )

    expected_graduation = Column(
        Date,
        nullable=True
    )

    credits_completed = Column(
        Integer,
        default=0
    )

    profile_photo = Column(
        String,
        nullable=True
    )

    # Status
    status = Column(
        String,
        nullable=False,
        default="Active"
    )

    # Timestamps
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

    user = relationship(
        "User",
        back_populates="student"
    )

    department = relationship(
        "Department",
        back_populates="students"
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="student"
    )

    # ------------------------------------------------------
    # Constraints
    # ------------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            "gender IN ('Male', 'Female', 'Other') "
            "OR gender IS NULL",
            name="check_student_gender"
        ),

        CheckConstraint(
            "status IN "
            "('Active', 'Graduated', 'Suspended', 'Dropped')",
            name="check_student_status"
        ),
    )
    