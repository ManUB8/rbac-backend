from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Date,
    Time,
    Text,
    TIMESTAMP,
    Numeric,
    UniqueConstraint,
    CheckConstraint,
    text,
    DateTime,
)


# =========================
# Faculty
# =========================
class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)
    faculty_name = Column(String(255), nullable=False, unique=True)

    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    majors = relationship("Major", back_populates="faculty", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="faculty")


# =========================
# Major
# =========================
class Major(Base):
    __tablename__ = "majors"

    __table_args__ = (
        UniqueConstraint("major_name", "faculty_id", name="uq_major_name_faculty"),
    )

    id = Column(Integer, primary_key=True, index=True)
    major_name = Column(String(255), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="CASCADE"), nullable=False)

    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    faculty = relationship("Faculty", back_populates="majors")
    students = relationship("Student", back_populates="major")


# =========================
# User
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    name = Column(String(150), nullable=True)
    is_active = Column(Boolean, default=True)

    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'student')", name="check_user_role"),
    )

    student = relationship(
        "Student",
        back_populates="user",
        uselist=False,
        foreign_keys="Student.user_id",
    )


# =========================
# Student
# =========================
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), nullable=False, unique=True, index=True)
    prefix = Column(String(20), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    citizen_id = Column(String(20), nullable=True, unique=True)
    gender = Column(String(20), nullable=True)

    faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="RESTRICT"), nullable=False)
    major_id = Column(Integer, ForeignKey("majors.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    img_stu = Column(Text, nullable=True)

    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    deleted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deleted_by_name = Column(String(150), nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    faculty = relationship("Faculty", back_populates="students")
    major = relationship("Major", back_populates="students")

    user = relationship(
        "User",
        back_populates="student",
        foreign_keys=[user_id],
    )

    @property
    def faculty_name(self):
        return self.faculty.faculty_name if self.faculty else None

    @property
    def major_name(self):
        return self.major.major_name if self.major else None


# =========================
# Activity
# =========================

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    activity_name = Column(String(255), nullable=False)
    activity_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    hours = Column(Numeric(4, 2), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    activity_img = Column(Text, nullable=True)

    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())