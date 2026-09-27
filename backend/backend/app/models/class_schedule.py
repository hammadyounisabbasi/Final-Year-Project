from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClassSchedule(Base):
    __tablename__ = "Class_Schedules"

    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("Courses.course_id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("Teachers.teacher_id"), nullable=False)
    academic_year = Column(String, nullable=False)
    semester = Column(Integer, nullable=False)
    section = Column(String, nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    room_location = Column(String, nullable=False)
    class_type = Column(String, nullable=False, default="Lecture")
    status = Column(String, nullable=False, default="Active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    course = relationship("Course", backref="class_schedules")
    teacher = relationship("Teacher", backref="class_schedules")

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "academic_year",
            "semester",
            "section",
            "day_of_week",
            "start_time",
            name="unique_course_schedule_slot",
        ),
        CheckConstraint(
            "day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')",
            name="check_schedule_day_of_week",
        ),
        CheckConstraint(
            "class_type IN ('Lecture', 'Lab', 'Tutorial', 'Seminar')",
            name="check_schedule_class_type",
        ),
        CheckConstraint(
            "status IN ('Active', 'Cancelled', 'Completed')",
            name="check_schedule_status",
        ),
    )
