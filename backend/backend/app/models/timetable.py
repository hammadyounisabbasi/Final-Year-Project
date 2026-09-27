"""Data-driven timetable aggregate used by the replacement scheduling flow.

The existing ``ClassSchedule`` model remains untouched during migration.  A
published TimetableSession can later be projected to that legacy table until
all portal readers have moved to the new canonical sessions.
"""
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


class Room(Base):
    __tablename__ = "Rooms"

    room_id = Column(Integer, primary_key=True, autoincrement=True)
    room_code = Column(String, nullable=False, unique=True)
    room_name = Column(String, nullable=True)
    room_type = Column(String, nullable=False, default="Classroom")
    capacity = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="Active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("capacity > 0", name="check_room_positive_capacity"),
        CheckConstraint("room_type IN ('Classroom', 'Computer Lab', 'Laboratory', 'Seminar Room')", name="check_room_type"),
        CheckConstraint("status IN ('Active', 'Inactive')", name="check_room_status"),
    )


class TimetableConfiguration(Base):
    __tablename__ = "Timetable_Configurations"

    configuration_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    working_days = Column(String, nullable=False, default="Monday,Tuesday,Wednesday,Thursday,Friday")
    day_start_time = Column(String, nullable=False, default="08:30")
    day_end_time = Column(String, nullable=False, default="15:30")
    slot_minutes = Column(Integer, nullable=False, default=60)
    status = Column(String, nullable=False, default="Active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("slot_minutes > 0", name="check_timetable_slot_minutes"),
        CheckConstraint("status IN ('Active', 'Inactive')", name="check_timetable_configuration_status"),
    )

    @property
    def working_day_list(self):
        return [day.strip() for day in self.working_days.split(",") if day.strip()]


class TeacherAvailability(Base):
    __tablename__ = "Teacher_Availability"

    availability_id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("Teachers.teacher_id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    is_available = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher = relationship("Teacher", backref="availability_windows")

    __table_args__ = (
        UniqueConstraint("teacher_id", "day_of_week", "start_time", "end_time", name="uq_teacher_availability_window"),
        CheckConstraint("is_available IN (0, 1)", name="check_teacher_availability_flag"),
        CheckConstraint("start_time < end_time", name="check_teacher_availability_time_order"),
    )


class RoomAvailability(Base):
    __tablename__ = "Room_Availability"

    availability_id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("Rooms.room_id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    is_available = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    room = relationship("Room", backref="availability_windows")

    __table_args__ = (
        UniqueConstraint("room_id", "day_of_week", "start_time", "end_time", name="uq_room_availability_window"),
        CheckConstraint("is_available IN (0, 1)", name="check_room_availability_flag"),
        CheckConstraint("start_time < end_time", name="check_room_availability_time_order"),
    )


class Timetable(Base):
    __tablename__ = "Timetables"

    timetable_id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("Departments.department_id"), nullable=False)
    term_id = Column(Integer, ForeignKey("Academic_Terms.term_id"), nullable=False)
    configuration_id = Column(Integer, ForeignKey("Timetable_Configurations.configuration_id"), nullable=False)
    semester = Column(Integer, nullable=False)
    section = Column(String, nullable=False, default="A")
    status = Column(String, nullable=False, default="Draft")
    created_by = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("Users.user_id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department")
    term = relationship("AcademicTerm")
    configuration = relationship("TimetableConfiguration")
    courses = relationship("TimetableCourse", back_populates="timetable", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("department_id", "term_id", "semester", "section", name="uq_timetable_scope"),
        CheckConstraint("semester > 0", name="check_timetable_semester"),
        CheckConstraint("status IN ('Draft', 'Approved', 'Published', 'Archived')", name="check_timetable_status"),
    )


class TimetableCourse(Base):
    __tablename__ = "Timetable_Courses"

    timetable_course_id = Column(Integer, primary_key=True, autoincrement=True)
    timetable_id = Column(Integer, ForeignKey("Timetables.timetable_id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("Courses.course_id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("Teachers.teacher_id"), nullable=False)
    weekly_sessions = Column(Integer, nullable=False)
    session_duration_minutes = Column(Integer, nullable=False, default=60)
    class_type = Column(String, nullable=False, default="Lecture")
    required_room_type = Column(String, nullable=False, default="Classroom")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    timetable = relationship("Timetable", back_populates="courses")
    course = relationship("Course")
    teacher = relationship("Teacher")
    sessions = relationship("TimetableSession", back_populates="timetable_course", cascade="all, delete-orphan")
    eligible_rooms = relationship("TimetableCourseRoom", back_populates="timetable_course", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("timetable_id", "course_id", name="uq_timetable_course"),
        CheckConstraint("weekly_sessions > 0", name="check_weekly_sessions"),
        CheckConstraint("session_duration_minutes > 0", name="check_session_duration"),
        CheckConstraint("class_type IN ('Lecture', 'Lab', 'Tutorial', 'Seminar')", name="check_timetable_course_type"),
    )


class TimetableCourseRoom(Base):
    __tablename__ = "Timetable_Course_Rooms"

    timetable_course_id = Column(Integer, ForeignKey("Timetable_Courses.timetable_course_id", ondelete="CASCADE"), primary_key=True)
    room_id = Column(Integer, ForeignKey("Rooms.room_id"), primary_key=True)

    timetable_course = relationship("TimetableCourse", back_populates="eligible_rooms")
    room = relationship("Room")


class TimetableSession(Base):
    __tablename__ = "Timetable_Sessions"

    timetable_session_id = Column(Integer, primary_key=True, autoincrement=True)
    timetable_course_id = Column(Integer, ForeignKey("Timetable_Courses.timetable_course_id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("Rooms.room_id"), nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    legacy_schedule_id = Column(Integer, ForeignKey("Class_Schedules.schedule_id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    timetable_course = relationship("TimetableCourse", back_populates="sessions")
    room = relationship("Room")
    legacy_schedule = relationship("ClassSchedule")

    __table_args__ = (
        UniqueConstraint("timetable_course_id", "day_of_week", "start_time", name="uq_timetable_course_session_slot"),
        CheckConstraint("start_time < end_time", name="check_timetable_session_time_order"),
    )
