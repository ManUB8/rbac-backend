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
    Numeric,
    BigInteger,
    UniqueConstraint,
    CheckConstraint,
)


# =========================
# User
# =========================
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    created_by_id = Column(Integer, nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)

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
# Faculty
# =========================
class Faculty(Base):
    __tablename__ = "faculties"

    faculty_id = Column(Integer, primary_key=True, index=True)
    faculty_name = Column(String(255), nullable=False, unique=True)

    created_by_id = Column(Integer, nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)

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

    major_id = Column(Integer, primary_key=True, index=True)
    major_name = Column(String(255), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculties.faculty_id", ondelete="CASCADE"), nullable=False)

    created_by_id = Column(Integer, nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)

    faculty = relationship("Faculty", back_populates="majors")
    students = relationship("Student", back_populates="major")


# =========================
# Student
# =========================
class Student(Base):
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String(20), nullable=False, unique=True, index=True)

    prefix = Column(String(20), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    gender = Column(String(20), nullable=True)

    faculty_id = Column(Integer, ForeignKey("faculties.faculty_id", ondelete="RESTRICT"), nullable=False)
    major_id = Column(Integer, ForeignKey("majors.major_id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)

    img_stu = Column(Text, nullable=True)

    created_by_id = Column(Integer, nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)

    faculty = relationship("Faculty", back_populates="students")
    major = relationship("Major", back_populates="students")

    user = relationship(
        "User",
        back_populates="student",
        foreign_keys=[user_id],
    )

    student_activities = relationship(
        "StudentActivity",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    @property
    def faculty_name(self):
        return self.faculty.faculty_name if self.faculty else None

    @property
    def major_name(self):
        return self.major.major_name if self.major else None

    @property
    def full_name(self):
        parts = [self.prefix, self.first_name, self.last_name]
        return " ".join([p for p in parts if p])


# =========================
# Activity
# =========================
class Activity(Base):
    __tablename__ = "activities"

    activity_id = Column(Integer, primary_key=True, index=True)
    activity_name = Column(String(255), nullable=False)
    activity_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    hours = Column(Numeric(4, 2), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    activity_img = Column(Text, nullable=True)
    activity_status = Column(Boolean, nullable=False, default=True)

    created_by_id = Column(Integer, nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)

    student_activities = relationship(
        "StudentActivity",
        back_populates="activity",
        cascade="all, delete-orphan"
    )


# =========================
# Student Activity
# =========================
class StudentActivity(Base):
    __tablename__ = "student_activities"

    student_activity_id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.activity_id", ondelete="CASCADE"), nullable=False)

    attendance_status = Column(String(20), nullable=False, default="ไม่เข้าร่วม")
    checkin_at = Column(BigInteger, nullable=True)

    created_by_id = Column(Integer, nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)

    student = relationship("Student", back_populates="student_activities", foreign_keys=[student_id])
    activity = relationship("Activity", back_populates="student_activities", foreign_keys=[activity_id])

    __table_args__ = (
        UniqueConstraint("student_id", "activity_id", name="uq_student_activity"),
        CheckConstraint(
            "attendance_status IN ('เข้าร่วม', 'ไม่เข้าร่วม')",
            name="chk_attendance_status"
        ),
    )