from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "Users"

    # Primary Key
    user_id = Column(Integer, primary_key=True, autoincrement=True)

    # Login Information
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)

    # Role
    role = Column(String, nullable=False)

    # Account Status
    is_active = Column(Integer, nullable=False, default=1)
    is_verified = Column(Integer, nullable=False, default=0)

    # Security / Login Tracking
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    last_login = Column(DateTime, nullable=True)

    # Password Tracking
    password_changed_at = Column(DateTime, nullable=True)

    # Timestamps
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

    student = relationship(
        "Student",
        back_populates="user",
        uselist=False
    )

    teacher = relationship(
        "Teacher",
        back_populates="user",
        uselist=False
    )
    
    admin = relationship(
        "Admin",
        back_populates="user",
        uselist=False
    )
    # ------------------------------------------------------
    # Constraints
    # ------------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            "role IN ('student', 'teacher', 'admin')",
            name="check_user_role"
        ),
        CheckConstraint(
            "is_active IN (0, 1)",
            name="check_user_active"
        ),
        CheckConstraint(
            "is_verified IN (0, 1)",
            name="check_user_verified"
        ),
    )