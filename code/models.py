from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Time, Text, TIMESTAMP, Numeric, UniqueConstraint, CheckConstraint

# ตารางคณะ
class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)
    faculty_name = Column(String(255), nullable=False, unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 1 คณะ มีได้หลายสาขา
    majors = relationship("Major", back_populates="faculty", cascade="all, delete-orphan")
    # 1 faculty มีหลาย student
    students = relationship("Student", back_populates="faculty")

# ตารางสาขา
class Major(Base):
    __tablename__ = "majors"

    # ป้องกันชื่อสาขาซ้ำในคณะเดียวกัน
    __table_args__ = (
        UniqueConstraint("major_name", "faculty_id", name="uq_major_name_faculty"),
    )

    id = Column(Integer, primary_key=True, index=True)
    major_name = Column(String(255), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # ความสัมพันธ์ย้อนกลับไปยังคณะ
    faculty = relationship("Faculty", back_populates="majors")

    # 1 major มีหลาย student
    students = relationship("Student", back_populates="major")

    
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'student')", name="chk_user_role"),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

# 1 user student ผูกกับ student profile เดียว
    student = relationship("Student", back_populates="user", uselist=False)



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

    # รูปนักศึกษา เก็บเป็น URL หรือ path ก็ได้
    img_stu = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Student -> Faculty
    faculty = relationship("Faculty", back_populates="students")

    # Student -> Major
    major = relationship("Major", back_populates="students")

    # Student -> User
    user = relationship("User", back_populates="student")



class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)

    # ชื่อกิจกรรม
    activity_name = Column(String(255), nullable=False)

    # วันที่จัดกิจกรรม
    activity_date = Column(Date, nullable=False)

    # เวลาเริ่ม / เวลาจบ
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    # จำนวนชั่วโมงกิจกรรม
    hours = Column(Numeric(4, 2), nullable=False)

    # สถานที่
    location = Column(String(255), nullable=True)

    # รายละเอียดกิจกรรม
    description = Column(Text, nullable=True)

    # วันเวลาที่สร้าง / แก้ไข
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())