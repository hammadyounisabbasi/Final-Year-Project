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


class Department(Base):
    __tablename__ = "Departments"

    department_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    department_code = Column(
        String,
        nullable=False,
        unique=True
    )

    department_name = Column(
        String,
        nullable=False,
        unique=True
    )

    department_short_name = Column(
        String,
        nullable=True
    )

    office_location = Column(
        String,
        nullable=True
    )

    office_phone = Column(
        String,
        nullable=True
    )

    office_email = Column(
        String,
        nullable=True,
        unique=True
    )

    hod_user_id = Column(
        Integer,
        ForeignKey("Users.user_id"),
        nullable=True
    )

    status = Column(
        String,
        nullable=False,
        default="Active"
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    students = relationship(
        "Student",
        back_populates="department"
    )

    teachers = relationship(
        "Teacher",
        back_populates="department"
    )

    courses = relationship(
        "Course",
        back_populates="department"
    )

    # ------------------------------------------------------
    # Constraints
    # ------------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            "status IN ('Active', 'Inactive')",
            name="check_department_status"
        ),
    )