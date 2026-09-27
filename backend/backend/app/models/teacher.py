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


class Teacher(Base):
    __tablename__ = "Teachers"

    # Primary Key
    teacher_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Relationships
    user_id = Column(
        Integer,
        ForeignKey("Users.user_id"),
        nullable=False,
        unique=True
    )

    department_id = Column(
        Integer,
        ForeignKey("Departments.department_id"),
        nullable=False
    )

    # Faculty Identification
    employee_id = Column(
        String,
        nullable=False,
        unique=True
    )

    # Personal Information
    first_name = Column(
        String,
        nullable=False
    )

    last_name = Column(
        String,
        nullable=False
    )

    gender = Column(
        String,
        nullable=True
    )

    date_of_birth = Column(
        Date,
        nullable=True
    )

    phone = Column(
        String,
        nullable=True
    )

    office_email = Column(
        String,
        nullable=False,
        unique=True
    )

    # Professional Information
    designation = Column(
        String,
        nullable=False
    )

    qualification = Column(
        String,
        nullable=True
    )

    specialization = Column(
        String,
        nullable=True
    )

    joining_date = Column(
        Date,
        nullable=True
    )

    office_room = Column(
        String,
        nullable=True
    )

    profile_photo = Column(
        String,
        nullable=True
    )

    employment_type = Column(
        String,
        nullable=False,
        default="Permanent"
    )

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
        back_populates="teacher"
    )

    department = relationship(
        "Department",
        back_populates="teachers"
    )

    courses = relationship(
        "Course",
        back_populates="teacher"
    )

    # ------------------------------------------------------
    # Constraints
    # ------------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            "gender IN ('Male', 'Female', 'Other') "
            "OR gender IS NULL",
            name="check_teacher_gender"
        ),

        CheckConstraint(
            "employment_type IN "
            "('Permanent', 'Contract', 'Visiting')",
            name="check_teacher_employment_type"
        ),

        CheckConstraint(
            "status IN "
            "('Active', 'On Leave', 'Retired', 'Resigned')",
            name="check_teacher_status"
        ),
    )