# Students V2 Module

โครงนี้คือ pattern สำหรับทำ API v2 แบบแยกหน้าที่ชัดเจน จุดสำคัญคือไม่ให้ไฟล์ router กลายเป็นที่รวมทุกอย่างเหมือน v1

## ภาพรวม

```text
HTTP request
  -> router.py
      -> service.py
          -> repository.py
          -> serializers.py
      -> interfaces.py
```

ความหมายคือ request เข้ามาที่ `router.py` ก่อน จากนั้น router เรียก `service.py` เพื่อทำงานจริง ถ้าต้อง query database ให้ service เรียก `repository.py` และถ้าต้องแปลงข้อมูลก่อนส่ง response ให้ใช้ `serializers.py`

## แต่ละไฟล์คืออะไร

### `router.py`

ไฟล์นี้คือชั้น HTTP หรือ controller

หน้าที่:

- กำหนด path เช่น `/register`, `/admin/create`
- กำหนด method เช่น `GET`, `POST`, `PATCH`, `DELETE`
- กำหนด `response_model`
- รับ request body, query param, path param
- เรียก `service.py`

สิ่งที่ไม่ควรอยู่ในไฟล์นี้:

- query database ยาวๆ
- business rule เช่น validate admin, เช็ค faculty/major
- loop แปลง response ซับซ้อน
- commit/rollback database

ตัวอย่าง:

```python
@router.post("/register", response_model=StudentMessageResponse)
def register_student(data: StudentRegisterRequest, db: Session = Depends(get_db)):
    return service.register_student(data=data, db=db)
```

อ่านแบบง่ายๆ คือ endpoint นี้รับ `StudentRegisterRequest` แล้วส่งต่อให้ `service.register_student`

### `interfaces.py`

ไฟล์นี้คือชั้น interface ของ API

ในโปรเจกต์นี้หมายถึง request/response schema ที่ API ใช้ เช่น Pydantic model

หน้าที่:

- รวม schema ที่ router ใช้
- ทำให้เปิด router แล้วรู้ทันทีว่า endpoint นี้รับ/ส่ง model อะไร
- แยก schema ของ v2 ออกจาก v1 ได้ในอนาคต

ตอนนี้ schema ของ students v2 อยู่ในไฟล์นี้โดยตรงแล้ว ไม่ต้องไปเปิด `schemas.schemas_student` เวลาทำ endpoint ใน module นี้ ถ้า v2 ต้องเปลี่ยน request/response ให้แก้ที่ `interfaces.py` ของ v2 ได้เลย โดยไม่กระทบ v1

ตัวอย่างชื่อ:

```text
StudentRegisterRequest       = body ตอนสมัครนิสิต
StudentMessageResponse       = response หลัง create สำเร็จ
StudentFilterRequest         = body ตอน filter
StudentFilterResponse        = response ของหน้า list/filter
```

### `service.py`

ไฟล์นี้คือชั้น business logic

หน้าที่:

- validate rule ของระบบ
- จัดลำดับการทำงาน
- สร้าง/แก้ไข/delete model
- commit/rollback transaction
- เรียก repository เพื่ออ่านข้อมูล
- เรียก serializer เพื่อเตรียม response

ตัวอย่าง logic ที่ควรอยู่ใน service:

- `get_admin_by_name`
- `resolve_faculty_and_major`
- `assign_student_position`
- `register_student`
- `admin_update_student_with_user`
- `delete_student`

ตัวอย่าง flow ใน `register_student`:

```text
เช็ค student_code ซ้ำ
เช็ค username ซ้ำ
resolve faculty/major
สร้าง User
สร้าง Student
assign position
commit
load student พร้อม relations
build response
```

ถ้า logic เป็น "กฎของระบบ" ให้วางที่ service

### `repository.py`

ไฟล์นี้คือชั้น database query

หน้าที่:

- รวม query ที่ใช้ซ้ำ
- ซ่อนรายละเอียด SQLAlchemy query ไม่ให้กระจายเต็ม service
- ทำให้ service อ่านง่ายขึ้น

ตัวอย่าง:

```python
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
```

service จะเรียกแบบนี้:

```python
admin = repository.get_active_admin_by_name(db, admin_name)
```

ถ้า function เป็น "หา record จาก database" ให้วางที่ repository

### `serializers.py`

ไฟล์นี้คือชั้นแปลงข้อมูลก่อนส่งออก

หน้าที่:

- แปลง SQLAlchemy model เป็น dict ที่ response schema ต้องการ
- รวม logic การอ่าน relation เช่น faculty, major, user, position
- ลดการ copy code เวลา endpoint หลายตัวส่ง response รูปแบบเดียวกัน

ตัวอย่าง:

```python
build_student_response(student)
```

ใช้เมื่อ service มี `Student` model แล้วต้องส่งออกเป็น response ที่ frontend ใช้

ถ้า function เป็น "จัดรูปข้อมูลเพื่อส่ง response" ให้วางที่ serializer

### `dependencies.py`

ไฟล์นี้คือชั้น FastAPI dependency

หน้าที่:

- รวม function ที่ใช้กับ `Depends(...)`
- เช่น `get_db`
- ในอนาคตอาจมี `get_current_admin`, `get_current_student`

ตัวอย่าง:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

router ใช้แบบนี้:

```python
db: Session = Depends(get_db)
```

### `constants.py`

ไฟล์นี้เก็บค่าคงที่ของ module

ตัวอย่าง:

```python
DELETE_ALLOWED_ADMIN_NAMES = ["mangpo", "first", "soda", "Tatum", "Tum"]
```

ถ้าค่าไหนใช้หลาย function และไม่ได้มาจาก database ให้วางที่นี่ก่อน

## Request เดินทางยังไง

ตัวอย่าง endpoint สมัครนิสิต:

```text
POST /student/v2/register
```

ลำดับการทำงาน:

```text
1. router.py รับ request body เป็น StudentRegisterRequest
2. router.py เปิด database session ผ่าน Depends(get_db)
3. router.py เรียก service.register_student(data, db)
4. service.py เช็คข้อมูลซ้ำและ validate business rule
5. service.py เรียก repository.py เมื่อต้องหา admin/faculty/major/student
6. service.py สร้าง User และ Student
7. service.py commit database
8. service.py โหลดข้อมูลพร้อม relations
9. service.py เรียก serializers.build_student_response
10. router.py ส่ง response กลับตาม StudentMessageResponse
```

## เวลาเพิ่ม endpoint ใหม่ต้องทำอะไร

ตัวอย่างอยากเพิ่ม:

```text
GET /student/v2/by-code/{student_code}
```

ลำดับที่ควรทำ:

```text
1. เพิ่ม response schema ใน interfaces.py หรือ import schema ที่มีอยู่แล้ว
2. เพิ่ม query ใน repository.py เช่น get_student_by_code
3. เพิ่ม business function ใน service.py เช่น get_student_by_code
4. เพิ่ม route ใน router.py
5. ทดสอบ import/router หรือยิง API
```

ตัวอย่าง route:

```python
@router.get("/by-code/{student_code}", response_model=StudentDetailWithUserResponse)
def get_student_by_code(student_code: str, db: Session = Depends(get_db)):
    return service.get_student_by_code(student_code=student_code, db=db)
```

## จะรู้ได้ไงว่าโค้ดควรวางไฟล์ไหน

ใช้คำถามนี้ตัดสิน:

```text
เกี่ยวกับ path/method/request/response_model ไหม
  -> router.py

เกี่ยวกับ request/response schema ไหม
  -> interfaces.py

เกี่ยวกับกฎของระบบหรือลำดับการทำงานไหม
  -> service.py

เกี่ยวกับ query database ไหม
  -> repository.py

เกี่ยวกับแปลง model เป็น response dict ไหม
  -> serializers.py

เกี่ยวกับ Depends(...) ไหม
  -> dependencies.py

เป็นค่าคงที่ไหม
  -> constants.py
```

## ทำไมไม่ใช้ `helpers.py`

คำว่า helper กว้างเกินไป พอโปรเจกต์โต ไฟล์ `helpers.py` มักกลายเป็นที่รวมทุกอย่างจนอ่านยาก

ใน v2 นี้เลยตั้งชื่อ helper ตามหน้าที่จริง:

```text
repository.py   = database helper
serializers.py  = response mapping helper
dependencies.py = FastAPI dependency helper
constants.py    = constant helper
service.py      = business helper
```

ถ้ามี helper ที่ใช้ได้หลาย module และไม่เกี่ยวกับ students โดยตรง ค่อยย้ายไปไว้ shared เช่น:

```text
code/shared/pagination.py
code/shared/time.py
code/shared/string.py
```

## Pattern สำหรับ module ถัดไป

ถ้าจะทำ `activities` หรือ `users` ให้ทำโครงคล้ายกัน:

```text
code/api/v2/activities/
  router.py
  interfaces.py
  service.py
  repository.py
  serializers.py
  dependencies.py
  constants.py
```

แล้วค่อย include router ใน `main.py`
