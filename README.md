# RBAC Activity Backend

Backend นี้เป็น FastAPI สำหรับระบบจัดการกิจกรรมแบบ RBAC โดยแยกผู้ใช้หลักเป็น `admin` และ `student` ใช้ PostgreSQL ผ่าน SQLAlchemy และรองรับการอัปโหลดรูปไป Cloudflare R2

เอกสารนี้สรุปจากโค้ดปัจจุบันของโปรเจกต์ เพื่อใช้เป็น context เวลามีการเพิ่มเงื่อนไขหรือให้ช่วยแก้ไขต่อ โดยควรเก็บ behavior เดิมไว้เสมอ ยกเว้นมีการระบุว่าต้องเปลี่ยน

## ภาพรวมระบบ

ระบบนี้ดูแลข้อมูลหลักดังนี้

- ผู้ใช้งาน: admin, temporary_admin และ student
- นิสิต: ข้อมูลส่วนตัว คณะ สาขา ชั้นปี รูปภาพ และบัญชี login
- คณะและสาขา: โครงสร้างคณะกับ major
- กิจกรรม: วันที่ เวลา ชั่วโมง ประเภทชั่วโมง สถานที่ รูปภาพ เงื่อนไขการลงทะเบียน และพิกัด
- การเข้าร่วมกิจกรรม: ลงทะเบียน เช็คอิน เช็คเอาต์ สถานะเข้าร่วม และพิกัดขณะเช็คอิน/เช็คเอาต์
- ตำแหน่งนิสิต: ตำแหน่งปัจจุบันและประวัติตำแหน่งของนิสิต
- Dashboard: สรุปข้อมูลสำหรับ admin และ student
- Upload: อัปโหลดรูปกิจกรรมและรูปนิสิตไป Cloudflare R2

## Tech Stack

- Python 3.13
- FastAPI
- Uvicorn
- SQLAlchemy
- PostgreSQL ผ่าน `psycopg2-binary`
- Pydantic
- python-dotenv
- boto3 สำหรับ Cloudflare R2
- Docker / Docker Compose

## โครงสร้างไฟล์

```text
.
├── Dockerfile
├── docker-compose.yaml
├── .env
├── .gitignore
└── code
    ├── main.py
    ├── database.py
    ├── models.py
    ├── r2_service.py
    ├── requirements.txt
    ├── routers
    │   ├── admin_auth_router.py
    │   ├── student_auth_router.py
    │   ├── user_router.py
    │   ├── faculty_major_router.py
    │   ├── student_register_router.py
    │   ├── activity_router.py
    │   ├── student_activity_router.py
    │   ├── admin_dashboard.py
    │   ├── position_router.py
    │   └── upload_router.py
    ├── schemas
    │   ├── schemas_user.py
    │   ├── schemas_student.py
    │   ├── schemas_faculty_major.py
    │   ├── schemas_activity.py
    │   ├── schemas_student_activity.py
    │   ├── schemas_admin_dashboard.py
    │   └── schemas_position.py
    └── service
        └── student_router_v2.py
```

หมายเหตุ: โฟลเดอร์ `__pycache__` เป็นไฟล์ runtime ของ Python ไม่ใช่ source หลักของระบบ

## หน้าที่ของไฟล์หลัก

| ไฟล์ | หน้าที่ |
| --- | --- |
| `code/main.py` | สร้าง FastAPI app, ตั้งค่า CORS, create table ด้วย SQLAlchemy, include router ทั้งหมด, มี root และ health check |
| `code/database.py` | โหลด `.env`, สร้าง `engine`, `SessionLocal`, `Base`, และ dependency `get_db()` |
| `code/models.py` | SQLAlchemy models ทั้งหมด เช่น User, Student, Faculty, Major, Activity, StudentActivity, Position, StudentPosition, ActivityHourType |
| `code/r2_service.py` | อัปโหลด/ลบไฟล์บน Cloudflare R2 ตรวจชนิดไฟล์และขนาดสูงสุด 5 MB |
| `code/requirements.txt` | dependency ของ backend |
| `Dockerfile` | build Python image และรัน Uvicorn ที่ port 8000 |
| `docker-compose.yaml` | service `rbac-backend`, map port `8000:8000`, โหลด env จาก `.env`, mount `./code:/app/code` |

## Environment Variables

โปรเจกต์โหลดค่าจาก `.env`

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DB_NAME

R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=...
R2_PUBLIC_BASE_URL=...
```

ข้อควรระวัง:

- `database.py` มีการ `print("DATABASE_URL =", DATABASE_URL)` ตอน import
- `r2_service.py` จะ raise error ทันทีถ้า R2 env ไม่ครบ
- ปัจจุบัน password ถูกเก็บ/เช็คแบบ plain text ตามโค้ดเดิม

## การรันโปรเจกต์

รันแบบ local:

```bash
cd code
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

รันด้วย Docker Compose:

```bash
docker compose up --build
```

URL สำคัญ:

- API root: `http://localhost:8000/`
- Health check: `http://localhost:8000/health`
- Swagger docs: `http://localhost:8000/docs`

## Database Models

### User

ตาราง `users`

- เก็บบัญชี login
- role มีได้เฉพาะ `admin`, `temporary_admin` หรือ `student`
- มี `is_active` สำหรับปิดการใช้งาน
- ผูกกับ `Student` แบบ one-to-one ผ่าน `students.user_id`

### Faculty / Major

ตาราง `faculties` และ `majors`

- Faculty มีหลาย Major
- Major อยู่ใต้ Faculty
- ชื่อ major ห้ามซ้ำในคณะเดียวกันด้วย unique constraint `major_name + faculty_id`

### Student

ตาราง `students`

- เก็บรหัสนิสิต ชื่อ เพศ คณะ สาขา ชั้นปี รูปภาพ
- ผูกกับ user ผ่าน `user_id`
- ผูกกับ faculty และ major
- มี relation ไป `StudentActivity` และ `StudentPosition`

### Activity

ตาราง `activities`

- เก็บชื่อกิจกรรม วันที่ เวลา ชั่วโมงกิจกรรม ชั่วโมงจิตอาสา สถานที่ คำอธิบาย รูป และสถานะเปิด/ปิด
- มี `hour_type_id` ไป `activity_hour_types`
- รองรับ `check_type`
  - `checkin_only`
  - `checkout_only`
  - `checkin_checkout`
- รองรับช่วงเวลา scan ได้แก่ `checkin_open_time`, `checkin_close_time`, `checkout_open_time`, `checkout_close_time`
- รองรับการลงทะเบียนล่วงหน้าด้วย `require_registration`
- จำกัดจำนวนผู้เข้าร่วมด้วย `max_participants`
- รองรับพิกัดกิจกรรมและ radius สำหรับเช็คอิน/เช็คเอาต์

### StudentActivity

ตาราง `student_activities`

- เก็บความสัมพันธ์นิสิตกับกิจกรรม
- มี unique constraint `student_id + activity_id`
- `attendance_status` มีค่า `เข้าร่วม` หรือ `ไม่เข้าร่วม`
- เก็บเวลา register, checkin, checkout เป็น Unix timestamp
- เก็บ `checkin_status`, `checkout_status` เป็น `valid` หรือ `manual`
- เก็บ `earned_hours` จากชั่วโมงจิตอาสาที่ได้จริง
- เก็บพิกัด checkin/checkout

### Position / StudentPosition

ตาราง `positions` และ `student_positions`

- Position คือ master data ของตำแหน่ง
- StudentPosition คือประวัติตำแหน่งของนิสิต
- เมื่อสร้างตำแหน่งใหม่ให้นิสิต ระบบจะปิดตำแหน่งปัจจุบันเดิมและตั้ง `end_date`

### ActivityHourType

ตาราง `activity_hour_types`

- เก็บประเภทชั่วโมงกิจกรรม
- primary key เป็น UUID

## Flow การทำงานหลัก

### 1. Admin Login

Endpoint: `POST /admin-auth/v1/login`

Flow:

1. ค้นหา user จาก `username`
2. เช็ค password
3. เช็คว่า role เป็น `admin`
4. เช็คว่า `is_active` เป็น true
5. คืน `user_id`, `username`, `name`

### 2. Student Login

Endpoint: `POST /student-auth/v1/login`

Flow:

1. ค้นหา user จาก `username`
2. เช็ค password
3. เช็คว่า role เป็น `student`
4. เช็คว่า `is_active` เป็น true
5. หา student ที่ผูกกับ user
6. คืนข้อมูล student พร้อม faculty, major และข้อมูล user

### 3. สร้างนิสิต

Endpoint หลัก:

- `POST /student/v1/register`
- `POST /student/v1/admin/create`
- `POST /student/v2/register`
- `POST /student/v2/admin/create`

Flow:

1. เช็คว่า `student_code` ยังไม่ซ้ำ
2. เช็คว่า `username` ยังไม่ซ้ำ
3. resolve คณะและสาขาจาก id หรือชื่อ
4. สร้าง `User` role `student`
5. สร้าง `Student` แล้วผูกกับ user
6. บันทึก `created_by`, `updated_by`, `created_at`, `updated_at`
7. ใน v2 รองรับข้อมูลเพิ่ม เช่น `position` และ `year_status`

### 4. จัดการคณะและสาขา

Endpoint prefix: `/faculty-majors/v1`

Flow:

1. Admin สร้าง/แก้ไขคณะหรือสาขาโดยใช้ `created_by_name` หรือ `updated_by_name`
2. ระบบเช็คว่า admin มีอยู่จริงและ active
3. ป้องกันชื่อคณะซ้ำ
4. ป้องกันชื่อสาขาซ้ำภายในคณะเดียวกัน
5. การลบต้องผ่านรายชื่อ admin ที่อยู่ใน `DELETE_ALLOWED_ADMIN_NAMES`

### 5. สร้างกิจกรรม

Endpoint: `POST /activity/v1/create`

Flow:

1. ตรวจ admin จาก `created_by_name`
2. validate เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด
3. validate `max_participants`, radius, latitude, longitude
4. ตรวจว่า `hour_type_id` มีจริง
5. สร้าง activity พร้อมข้อมูล check type, registration, location และ audit fields

### 6. แสดงกิจกรรมให้ student

Endpoint: `GET /activity/v1/get-all`

Flow:

1. ดึงเฉพาะกิจกรรมที่ `activity_status == true`
2. นับจำนวนผู้ลงทะเบียนจาก `student_activities`
3. ถ้ากิจกรรมนั้นต้องลงทะเบียน จะสร้าง `register_text` เช่น `3/20`
4. คำนวณ `is_full`
5. คืนรายการกิจกรรมพร้อมข้อมูลจำนวนผู้ลงทะเบียน

### 7. ลงทะเบียนกิจกรรม

Endpoint: `POST /student_activities/v1/register`

Flow:

1. หา student จาก `student_code`
2. หา activity จาก `activity_id`
3. ต้องเป็นกิจกรรมที่ `require_registration == true`
4. ห้ามลงทะเบียนซ้ำ
5. ถ้ามี `max_participants` ต้องยังไม่เต็ม
6. สร้าง `StudentActivity` โดย status เริ่มต้นเป็น `ไม่เข้าร่วม`
7. เก็บ `registered_at`

### 8. Check-in

Endpoint: `POST /student_activities/v1/checkin`

Flow:

1. ตรวจผู้ scan จาก `created_by_name` โดยรับ `admin` และ `temporary_admin`
2. หา student และ activity
3. ถ้า `check_type == checkout_only` จะไม่รองรับการเช็คอิน
4. validate ระยะจากพิกัดที่ส่งมากับพิกัดกิจกรรม
5. ใช้เวลาจาก server เทียบกับ `checkin_open_time` และ `checkin_close_time`
6. `temporary_admin` เช็คอินได้เฉพาะในช่วงเวลา scan
7. `admin` หลักเช็คอินนอกเวลาได้เพื่อบันทึกว่านิสิตมา แต่ `checkin_status` จะเป็น `manual`
8. ถ้ากิจกรรมต้องลงทะเบียน ต้องมี record เดิมก่อน
9. ห้ามเช็คอินซ้ำ
10. ถ้ายังไม่มี record และกิจกรรมไม่บังคับลงทะเบียน จะสร้าง `StudentActivity` ให้
11. ตั้ง `attendance_status = เข้าร่วม`, เก็บเวลา/พิกัด check-in และคำนวณ `earned_hours`

### 9. Check-out

Endpoint: `PATCH /student_activities/v1/checkout`

Flow:

1. ตรวจผู้ scan จาก `updated_by_name` โดยรับ `admin` และ `temporary_admin`
2. หา student และ activity
3. ใช้ได้กับกิจกรรมที่ `check_type == checkout_only` หรือ `checkin_checkout`
4. ถ้าเป็น `checkin_checkout` ต้องมี record เดิมและต้องเคย check-in แล้ว
5. ถ้าเป็น `checkout_only` และยังไม่มี record จะสร้าง `StudentActivity` ได้
6. validate ระยะจากพิกัดที่ส่งมากับพิกัดกิจกรรม
7. ใช้เวลาจาก server เทียบกับ `checkout_open_time` และ `checkout_close_time`
8. `temporary_admin` เช็คเอาท์ได้เฉพาะในช่วงเวลา scan
9. `admin` หลักเช็คเอาท์นอกเวลาได้ แต่ `checkout_status` จะเป็น `manual`
10. เก็บเวลา/พิกัด check-out และคำนวณ `earned_hours`

### 10. การคำนวณชั่วโมงจิตอาสา

ระบบใช้ `volunteer_hours` ของกิจกรรม และใช้ `checkin_status` / `checkout_status` เป็นหลัก ไม่ได้ดูจาก timestamp อย่างเดียว

- `checkin_only`: ได้ `volunteer_hours` เมื่อ `checkin_status == valid`
- `checkout_only`: ได้ `volunteer_hours` เมื่อ `checkout_status == valid`
- `checkin_checkout`: ถ้า valid ทั้ง check-in และ check-out ได้เต็ม, ถ้า valid อย่างเดียวได้ครึ่ง, ถ้าไม่ valid เลยได้ 0
- ถ้า admin หลัก scan นอกเวลา status จะเป็น `manual` เพื่อบันทึกว่านิสิตมา แต่ไม่นับเป็น valid สำหรับชั่วโมงเต็ม

### 11. Dashboard

Endpoint prefix: `/dashboard/v1`

- `GET /dashboard/v1/admin/{activity_id}` สำหรับภาพรวมกิจกรรมในฝั่ง admin
- `GET /dashboard/v1/student/{student_id}` สำหรับภาพรวมกิจกรรมของ student

### 12. Upload รูป

Endpoint prefix: `/upload/v1`

- `POST /upload/v1/image-activities`
- `POST /upload/v1/student-image`

Flow:

1. รับ `UploadFile`
2. ตรวจ content type เฉพาะ JPG, PNG, WEBP, GIF
3. ตรวจไฟล์ไม่ว่าง
4. จำกัดขนาดไม่เกิน 5 MB
5. สร้างชื่อไฟล์จาก UUID
6. อัปโหลดไป Cloudflare R2
7. คืน `file_name`, `object_key`, `file_url`, `content_type`, `size`

## Endpoint Summary

### Core

| Method | Path | หน้าที่ |
| --- | --- | --- |
| GET | `/` | ตรวจว่า API ทำงาน |
| GET | `/health` | health check |

### Auth

| Method | Path | หน้าที่ |
| --- | --- | --- |
| POST | `/admin-auth/v1/login` | admin login |
| POST | `/student-auth/v1/login` | student login |

### User

| Method | Path | หน้าที่ |
| --- | --- | --- |
| POST | `/user/v1/create` | สร้าง user โดย admin |
| GET | `/user/v1/all-users` | ดึง user ทั้งหมด |
| POST | `/user/v1/get-all` | ดึง user แบบค้นหา/pagination ด้วย `search`, `page`, `limit`, `rol` |
| GET | `/user/v1/get-one/{user_id}` | ดึง user รายคน |
| PATCH | `/user/v1/update/{user_id}` | แก้ไข user |
| DELETE | `/user/v1/delete/{user_id}` | ปิดใช้งาน user |

### Faculty & Major

| Method | Path | หน้าที่ |
| --- | --- | --- |
| POST | `/faculty-majors/v1/faculties` | สร้างคณะ |
| GET | `/faculty-majors/v1/faculties-all` | ดึงคณะพร้อมสาขา |
| GET | `/faculty-majors/v1/get-one/faculties/{faculty_id}` | ดึงคณะรายตัว |
| PATCH | `/faculty-majors/v1/update/faculties/{faculty_id}` | แก้ไขคณะ |
| DELETE | `/faculty-majors/v1/delete/faculties/{faculty_id}` | ลบคณะ |
| POST | `/faculty-majors/v1/majors` | สร้างสาขา |
| GET | `/faculty-majors/v1/majors-all` | ดึงสาขาทั้งหมด |
| GET | `/faculty-majors/v1/get-one/majors/{major_id}` | ดึงสาขารายตัว |
| PATCH | `/faculty-majors/v1/majors/{major_id}` | แก้ไขสาขา |
| DELETE | `/faculty-majors/v1/delete/majors/{major_id}` | ลบสาขา |
| POST | `/faculty-majors/v1/bulk` | สร้างคณะพร้อมสาขาหลายรายการ |

### Student v1

| Method | Path | หน้าที่ |
| --- | --- | --- |
| POST | `/student/v1/register` | นิสิตสมัครเอง |
| POST | `/student/v1/admin/create` | admin สร้างนิสิต |
| PATCH | `/student/v1/update/{student_id}` | แก้ไขข้อมูลนิสิต |
| PATCH | `/student/v1/admin/update-stu/{student_id}` | admin แก้ไขนิสิตพร้อม user |
| DELETE | `/student/v1/delete/{student_id}` | ลบนิสิต |
| GET | `/student/v1/get-all/faculties-student` | สรุปนิสิตตามคณะ |
| GET | `/student/v1/all-students` | ดึงนิสิตทั้งหมด |
| GET | `/student/v1/get-one/{student_id}` | ดึงนิสิตรายคน |
| GET | `/student/v1/get-all/major/{faculty_id}` | ดึงสาขาตามคณะพร้อมจำนวนนิสิต |
| GET | `/student/v1/get-all/student-major/{major_id}` | ดึงนิสิตตามสาขา |

### Student v2

| Method | Path | หน้าที่ |
| --- | --- | --- |
| POST | `/student/v2/register` | นิสิตสมัครเองแบบ v2 |
| POST | `/student/v2/admin/create` | admin สร้างนิสิตแบบ v2 |
| PATCH | `/student/v2/admin/update-stu/{student_id}` | admin แก้ไขนิสิตแบบ v2 |
| DELETE | `/student/v2/delete/{student_id}` | ลบนิสิตแบบ v2 |
| GET | `/student/v2/all-students` | ดึงนิสิตทั้งหมดแบบ v2 |
| GET | `/student/v2/get-one/{student_id}` | ดึงนิสิตรายคนแบบ v2 |
| GET | `/student/v2/get-all/faculties-student` | สรุปนิสิตตามคณะ |
| GET | `/student/v2/get-all/major/{faculty_id}` | ดึงสาขาตามคณะ |
| GET | `/student/v2/get-all/student-major/{major_id}` | ดึงนิสิตตามสาขา |
| POST | `/student/v2/get-all/filter` | filter นิสิตแบบ POST พร้อม `year_status_summary` จากนิสิตทั้งหมด |
| GET | `/student/v2/get-all/filter` | filter นิสิตแบบ GET พร้อม `year_status_summary` จากนิสิตทั้งหมด |
| DELETE | `/student/v2/admin/delete-all-students` | ลบนิสิตทั้งหมด |

### Activity

| Method | Path | หน้าที่ |
| --- | --- | --- |
| POST | `/activity/v1/create` | สร้างกิจกรรม |
| GET | `/activity/v1/get-all` | ดึงกิจกรรม active สำหรับ public/student |
| POST | `/activity/v1/admin/get-all` | ดึงกิจกรรมสำหรับ admin พร้อม filter |
| GET | `/activity/v1/get-one/{activity_id}` | ดึงกิจกรรมรายตัว |
| PATCH | `/activity/v1/update/{activity_id}` | แก้ไขกิจกรรม |
| DELETE | `/activity/v1/delete/{activity_id}` | ปิดหรือลบกิจกรรมตาม logic เดิม |
| GET | `/activity/v1/filter-info` | ข้อมูล filter สำหรับ admin |
| GET | `/activity/v1/filter-all` | filter options ทั้งหมด |

### Student Activity

| Method | Path | หน้าที่ |
| --- | --- | --- |
| POST | `/student_activities/v1/register` | ลงทะเบียนกิจกรรม |
| POST | `/student_activities/v1/checkin` | check-in กิจกรรม |
| PATCH | `/student_activities/v1/checkout` | check-out กิจกรรม |
| GET | `/student_activities/v1/get-all/` | ดึงรายการ student activity ทั้งหมด |
| GET | `/student_activities/v1/get-one/{student_activity_id}` | ดึง student activity รายตัว |
| PATCH | `/student_activities/v1/update/{student_activity_id}` | แก้ไข student activity |
| DELETE | `/student_activities/v1/delete/{student_activity_id}` | ลบ student activity |
| GET | `/student_activities/v1/student/available/{student_code}` | ดึงกิจกรรมที่นิสิตเห็น/ทำได้ |
| POST | `/student_activities/v1/admin/get-all` | admin filter รายการเข้าร่วม |
| POST | `/student_activities/v1/admin/get-allinone-last` | all-in-one activity/student view รุ่นก่อน |
| POST | `/student_activities/v1/admin/get-allinone` | all-in-one activity/student view |
| DELETE | `/student_activities/v1/admin/delete-all-student-activities` | ลบ student activity ทั้งหมด |
| DELETE | `/student_activities/v1/admin/delete-all-activities` | ลบกิจกรรมทั้งหมด |
| DELETE | `/student_activities/v1/admin/delete-all-student-activities/{activity_id}` | ลบ student activity ตาม activity |

### Position

| Method | Path | หน้าที่ |
| --- | --- | --- |
| POST | `/position/v1/create` | สร้างตำแหน่ง |
| GET | `/position/v1/get-all` | ดึงตำแหน่งทั้งหมด |
| GET | `/position/v1/get-one/{position_id}` | ดึงตำแหน่งรายตัว |
| PATCH | `/position/v1/update/{position_id}` | แก้ไขตำแหน่ง |
| DELETE | `/position/v1/delete/{position_id}` | ลบตำแหน่ง ถ้าไม่มีนิสิตใช้อยู่ |
| POST | `/position/v1/student-position/create` | เพิ่มตำแหน่งให้นิสิต |
| GET | `/position/v1/student-position/student/{student_id}` | ดึงประวัติตำแหน่งของนิสิต |
| PATCH | `/position/v1/student-position/update/{student_position_id}` | แก้ไขตำแหน่งของนิสิต |
| DELETE | `/position/v1/student-position/delete/{student_position_id}` | ลบตำแหน่งของนิสิต |

### Dashboard

| Method | Path | หน้าที่ |
| --- | --- | --- |
| GET | `/dashboard/v1/admin/{activity_id}` | dashboard สำหรับ admin ตามกิจกรรม |
| GET | `/dashboard/v1/student/{student_id}` | dashboard สำหรับ student |

### Upload

| Method | Path | หน้าที่ |
| --- | --- | --- |
| POST | `/upload/v1/image-activities` | อัปโหลดรูปกิจกรรม |
| POST | `/upload/v1/student-image` | อัปโหลดรูปนิสิต |

## กติกาและเงื่อนไขสำคัญที่ควรรักษาไว้

- Admin ที่สร้าง/แก้ไขข้อมูลหลายจุดถูกอ้างด้วย `created_by_name` หรือ `updated_by_name`
- การลบข้อมูลสำคัญบางส่วนต้องเป็น admin ที่อยู่ใน `DELETE_ALLOWED_ADMIN_NAMES`
- เวลาที่เก็บใน audit fields ใช้ Unix timestamp แบบวินาที
- เวลา activity รองรับ input แบบ `HH.MM` หรือ `HH:MM` ใน schema บางจุด และ response serialize เป็น `HH.MM`
- `year_status` ที่ถูกต้องคือ `ปี 1`, `ปี 2`, `ปี 3`, `ปี 4`, `บัณฑิต`
- `check_type` ที่ถูกต้องคือ `checkin_only`, `checkout_only`, `checkin_checkout`
- การเช็คอิน/เช็คเอาต์ต้องอยู่ในรัศมีกิจกรรม ถ้ากิจกรรมมีพิกัด
- ถ้า `require_registration` เป็น true ต้องลงทะเบียนก่อน check-in
- ถ้ามี `max_participants` ต้องไม่ให้ลงทะเบียนเกินจำนวน
- `student_id + activity_id` ห้ามซ้ำใน `student_activities`
- การสร้างตำแหน่งใหม่ให้นิสิตจะปิดตำแหน่งปัจจุบันเดิม
- `temporary_admin` login admin ได้ แต่ scan ได้เฉพาะในช่วงเวลา check-in/check-out ของกิจกรรม
- `admin` หลัก scan นอกเวลาได้เพื่อบันทึกว่า “มาสาย” หรือ “เช็คเอาท์นอกเวลา”

## Postman Collection

ไฟล์ `postman_rbac.json` เป็น Postman collection ที่ generate จาก FastAPI routes ปัจจุบัน มีตัวแปร `baseUrl` ค่าเริ่มต้นเป็น `http://localhost:8000` และมี request body ตัวอย่างสำหรับ endpoint ที่ต้องส่ง body

ข้อควรระวัง: ค่าใน body เป็น placeholder ต้องเปลี่ยนเป็นข้อมูลจริงก่อนยิงทดสอบ

## CORS

ตั้งค่า origin ไว้ใน `code/main.py` เช่น

- `https://rbac-activity.com`
- `https://www.rbac-activity.com`
- `https://rbac-front.pages.dev`
- `https://api.rbac-activity.com`
- `http://localhost:3000`
- `http://localhost:5173`
- `http://127.0.0.1:8000`
- Cloudflare Pages environment อื่นตามที่ระบุในโค้ด

## ข้อควรระวังตอนแก้ไขต่อ

- อย่าเปลี่ยน response shape เดิมถ้า frontend ใช้อยู่แล้ว
- ถ้าจะเปลี่ยน endpoint ควรเพิ่ม version ใหม่หรือรักษา endpoint เดิมไว้
- ถ้าแก้ model ต้องคิดเรื่อง migration เพราะตอนนี้ใช้ `Base.metadata.create_all(bind=engine)` ซึ่งสร้าง table แต่ไม่ migrate schema เก่า
- ถ้าแก้ auth/password ควรวางแผน migrate password เดิม เพราะตอนนี้เช็ค plain text
- ถ้าแก้ upload ต้องคงข้อจำกัดชนิดไฟล์และขนาดไว้ เว้นแต่มี requirement ใหม่
- ถ้าแก้ delete flow ให้เช็ค `DELETE_ALLOWED_ADMIN_NAMES` และ audit fields เดิม

## บันทึกเงื่อนไขเพิ่มเติม

ใช้ส่วนนี้เติม requirement ใหม่ก่อนให้ช่วยแก้โค้ด เพื่อให้เข้าใจ flow และไม่ทับ behavior เดิม

```text
วันที่:
เรื่องที่ต้องการเพิ่ม/แก้:
ไฟล์หรือ endpoint ที่เกี่ยวข้อง:
เงื่อนไขเดิมที่ต้องเก็บไว้:
เงื่อนไขใหม่:
ตัวอย่าง request:
ตัวอย่าง response:
ข้อควรระวังกับ frontend:
```
