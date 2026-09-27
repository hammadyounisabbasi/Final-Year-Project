from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class StudentTimetable(Base):
    """Links a student's active enrollment to its canonical class schedule."""

    __tablename__ = "Student_Timetable"

    student_timetable_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("Students.student_id", ondelete="CASCADE"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("Enrollments.enrollment_id", ondelete="CASCADE"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("Class_Schedules.schedule_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    student = relationship("Student", backref="timetable_entries")
    enrollment = relationship("Enrollment", backref="timetable_entries")
    schedule = relationship("ClassSchedule", backref="student_timetable_entries")

    __table_args__ = (
        UniqueConstraint("enrollment_id", "schedule_id", name="unique_student_enrollment_schedule"),
    )
