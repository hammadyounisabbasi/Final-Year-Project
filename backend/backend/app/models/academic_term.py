from datetime import datetime

from sqlalchemy import CheckConstraint, Column, Date, DateTime, Integer, String, UniqueConstraint

from app.core.database import Base


class AcademicTerm(Base):
    """The authoritative publication state for an academic year/semester."""

    __tablename__ = "Academic_Terms"

    term_id = Column(Integer, primary_key=True, autoincrement=True)
    academic_year = Column(String, nullable=False)
    semester = Column(Integer, nullable=False)
    term_name = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Upcoming")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("academic_year", "semester", name="uq_academic_term_year_semester"),
        CheckConstraint("status IN ('Upcoming', 'Active', 'Completed')", name="check_academic_term_status"),
    )
