from datetime import date, datetime

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Attendance(Base):
    __tablename__ = "Attendance"

    attendance_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("Students.student_id"), nullable=False)
    course_id = Column(Integer, ForeignKey("Courses.course_id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("Teachers.teacher_id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("Class_Schedules.schedule_id"), nullable=True)
    academic_year = Column(String, nullable=False)
    semester = Column(Integer, nullable=False)
    section = Column(String, nullable=False)
    attendance_date = Column(Date, nullable=False, default=date.today)
    session_key = Column(String, nullable=False)
    status = Column(String, nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", backref="attendance_records")
    course = relationship("Course", backref="attendance_records")
    teacher = relationship("Teacher", backref="attendance_records")
    schedule = relationship("ClassSchedule", backref="attendance_records")

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "academic_year", "semester", "section", "attendance_date", "session_key", name="unique_attendance_student_session"),
        CheckConstraint("status IN ('Present', 'Absent', 'Late', 'Leave')", name="check_attendance_status"),
    )
