from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Admin(Base):
    __tablename__ = "Admins"

    admin_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = Column(
        Integer,
        ForeignKey("Users.user_id"),
        nullable=False,
        unique=True
    )

    first_name = Column(
        String,
        nullable=False
    )

    last_name = Column(
        String,
        nullable=False
    )

    designation = Column(
        String,
        nullable=True
    )

    phone = Column(
        String,
        nullable=True
    )

    office_email = Column(
        String,
        nullable=True,
        unique=True
    )

    profile_photo = Column(
        String,
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

    user = relationship(
        "User",
        back_populates="admin"
    )
    