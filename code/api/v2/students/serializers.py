from models import Student


def get_current_position(student: Student):
    if not hasattr(student, "student_positions") or not student.student_positions:
        return None

    for item in student.student_positions:
        if item.is_current:
            return item

    return None


def build_student_response(student: Student):
    current_position = get_current_position(student)
    position_data = None

    if current_position:
        position_data = {
            "position_id": current_position.position_id,
            "position_name": current_position.position.position_name if current_position.position else None,
            "start_date": current_position.start_date,
            "end_date": current_position.end_date,
        }

    return {
        "student_id": student.student_id,
        "student_code": student.student_code,
        "prefix": student.prefix,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "gender": student.gender,
        "year_status": student.year_status,
        "faculty_id": student.faculty_id,
        "major_id": student.major_id,
        "user_id": student.user_id,
        "faculty_name": student.faculty.faculty_name if student.faculty else None,
        "major_name": student.major.major_name if student.major else None,
        "img_stu": student.img_stu,
        "position": position_data,
        "created_by_id": student.created_by_id,
        "created_by_name": student.created_by_name,
        "updated_by_id": student.updated_by_id,
        "updated_by_name": student.updated_by_name,
        "created_at": student.created_at,
        "updated_at": student.updated_at,
        "user": {
            "username": student.user.username if student.user else None,
            "password": student.user.password if student.user else None,
        } if student.user else None,
    }
