from sqlalchemy.orm import Session, joinedload

from models import Faculty, Major, Position, Student, StudentPosition, User


def get_active_admin_by_name(db: Session, admin_name: str):
    return (
        db.query(User)
        .filter(
            User.name == admin_name,
            User.role == "admin",
            User.is_active == True,
        )
        .first()
    )


def get_faculty_by_id(db: Session, faculty_id: int):
    return db.query(Faculty).filter(Faculty.faculty_id == faculty_id).first()


def get_faculty_by_name(db: Session, faculty_name: str):
    return db.query(Faculty).filter(Faculty.faculty_name == faculty_name).first()


def get_major_by_id(db: Session, major_id: int):
    return db.query(Major).filter(Major.major_id == major_id).first()


def get_major_by_name(db: Session, major_name: str):
    return db.query(Major).filter(Major.major_name == major_name).first()


def get_position_by_id(db: Session, position_id: int):
    return db.query(Position).filter(Position.position_id == position_id).first()


def get_student_by_id(db: Session, student_id: int):
    return db.query(Student).filter(Student.student_id == student_id).first()


def get_student_by_code(db: Session, student_code: str):
    return db.query(Student).filter(Student.student_code == student_code).first()


def get_student_with_user(db: Session, student_id: int):
    return (
        db.query(Student)
        .options(joinedload(Student.user))
        .filter(Student.student_id == student_id)
        .first()
    )


def get_student_with_relations(db: Session, student_id: int):
    return (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            joinedload(Student.user),
            joinedload(Student.student_positions).joinedload(StudentPosition.position),
        )
        .filter(Student.student_id == student_id)
        .first()
    )


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.user_id == user_id).first()


def get_current_student_position(db: Session, student_id: int):
    return (
        db.query(StudentPosition)
        .filter(
            StudentPosition.student_id == student_id,
            StudentPosition.is_current == True,
        )
        .first()
    )

