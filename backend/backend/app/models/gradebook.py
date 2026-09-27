from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class GradebookSetting(Base):
    __tablename__ = "Gradebook_Settings"

    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("Courses.course_id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("Teachers.teacher_id"), nullable=False)
    academic_year = Column(String, nullable=False)
    semester = Column(Integer, nullable=False)
    total_marks = Column(Float, nullable=False, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    components = relationship(
        "GradebookComponent",
        back_populates="setting",
        cascade="all, delete-orphan",
        order_by="GradebookComponent.sort_order",
    )

    __table_args__ = (UniqueConstraint("course_id", "academic_year", "semester", name="uq_gradebook_setting_term"),)


class GradebookComponent(Base):
    __tablename__ = "Gradebook_Components"

    component_id = Column(Integer, primary_key=True, autoincrement=True)
    setting_id = Column(Integer, ForeignKey("Gradebook_Settings.setting_id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)
    name = Column(String, nullable=False)
    item_count = Column(Integer, nullable=False, default=1)
    total_marks = Column(Float, nullable=False)
    item_total_marks = Column(Float, nullable=False)
    aggregation = Column(String, nullable=False, default="average")
    sort_order = Column(Integer, nullable=False, default=0)

    setting = relationship("GradebookSetting", back_populates="components")
