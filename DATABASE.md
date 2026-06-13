# Database Schema

เอกสารนี้สรุป database schema ของ RBAC Activity Backend โดยอ้างอิงจาก `code/models.py` เป็น schema ปัจจุบัน และเก็บ SQL เดิมที่เคยใช้สร้างตารางไว้ด้านล่างเพื่อใช้อ้างอิงเวลาแก้ไขต่อ

## ภาพรวม

Database ใช้ PostgreSQL และ SQLAlchemy models อยู่ใน `code/models.py`

ตารางหลัก:

- `users`
- `faculties`
- `majors`
- `students`
- `activities`
- `student_activities`
- `positions`
- `student_positions`
- `activity_hour_types`
- `product_categories`
- `products`
- `product_variants`
- `carts`
- `cart_items`
- `orders`
- `order_items`
- `payments`
- `stock_movements`

Migration ที่มีในโปรเจกต์:

- `migrations/20260606_add_activity_target_group.sql`
- `migrations/20260613_add_shop_tables.sql`
- `migrations/20260613_harden_shop_constraints_indexes.sql`

## Relationships

```text
users 1 ── 0..1 students
faculties 1 ── * majors
faculties 1 ── * students
majors 1 ── * students
students 1 ── * student_activities
activities 1 ── * student_activities
students 1 ── * student_positions
positions 1 ── * student_positions
activity_hour_types 1 ── * activities
product_categories 1 ── * products
faculties 1 ── * products
majors 1 ── * products
products 1 ── * product_variants
students 1 ── 0..1 carts
carts 1 ── * cart_items
products 1 ── * cart_items
product_variants 1 ── * cart_items
students 1 ── * orders
orders 1 ── * order_items
orders 1 ── * payments
products 1 ── * order_items
product_variants 1 ── * order_items
products 1 ── * stock_movements
product_variants 1 ── * stock_movements
orders 1 ── * stock_movements
```

## Current Schema From `code/models.py`

### `users`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `user_id` | Integer | No | Primary key, index |
| `username` | String(100) | No | Unique |
| `password` | String(255) | No | Plain text ตาม logic ปัจจุบัน |
| `role` | String(20) | No | Check: `admin`, `student`, `temporary_admin` |
| `name` | String(255) | No |  |
| `is_active` | Boolean | Yes | Default true |
| `created_by_id` | Integer | Yes |  |
| `created_by_name` | String(150) | Yes |  |
| `updated_by_id` | Integer | Yes |  |
| `updated_by_name` | String(150) | Yes |  |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

### `faculties`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `faculty_id` | Integer | No | Primary key, index |
| `faculty_name` | String(255) | No | Unique |
| `created_by_id` | Integer | Yes |  |
| `created_by_name` | String(150) | Yes |  |
| `updated_by_id` | Integer | Yes |  |
| `updated_by_name` | String(150) | Yes |  |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

### `majors`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `major_id` | Integer | No | Primary key, index |
| `major_name` | String(255) | No | Unique with `faculty_id` |
| `faculty_id` | Integer | No | FK to `faculties.faculty_id`, on delete cascade |
| `created_by_id` | Integer | Yes |  |
| `created_by_name` | String(150) | Yes |  |
| `updated_by_id` | Integer | Yes |  |
| `updated_by_name` | String(150) | Yes |  |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

Constraints:

- `uq_major_name_faculty`: unique `major_name`, `faculty_id`

### `students`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `student_id` | Integer | No | Primary key, index |
| `student_code` | String(20) | No | Unique, index |
| `prefix` | String(20) | Yes |  |
| `first_name` | String(100) | No |  |
| `last_name` | String(100) | No |  |
| `gender` | String(20) | Yes |  |
| `faculty_id` | Integer | No | FK to `faculties.faculty_id`, on delete restrict |
| `major_id` | Integer | No | FK to `majors.major_id`, on delete restrict |
| `user_id` | Integer | No | FK to `users.user_id`, unique, on delete cascade |
| `year_status` | String(20) | Yes | ใช้ค่า `ปี 1`, `ปี 2`, `ปี 3`, `ปี 4`, `บัณฑิต` ใน schema |
| `img_stu` | Text | Yes | URL รูปนิสิต |
| `created_by_id` | Integer | Yes |  |
| `created_by_name` | String(150) | Yes |  |
| `updated_by_id` | Integer | Yes |  |
| `updated_by_name` | String(150) | Yes |  |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

### `activities`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `activity_id` | Integer | No | Primary key, index |
| `activity_name` | String(255) | No |  |
| `activity_date` | Date | No |  |
| `target_group` | String(30) | No | Default `all`, check `all`, `freshman`, `senior` |
| `start_time` | Time | No |  |
| `end_time` | Time | No |  |
| `hours` | Numeric(4,2) | No |  |
| `volunteer_hours` | Numeric(4,2) | No | Default 0 |
| `location` | String(255) | Yes |  |
| `description` | Text | Yes |  |
| `activity_img` | Text | Yes | URL รูปกิจกรรม |
| `activity_status` | Boolean | No | Default true |
| `checkin_open_time` | Time | Yes | เวลาเปิด check-in |
| `checkin_close_time` | Time | Yes | เวลาปิด check-in |
| `checkout_open_time` | Time | Yes | เวลาเปิด check-out |
| `checkout_close_time` | Time | Yes | เวลาปิด check-out |
| `hour_type_id` | UUID | Yes | FK to `activity_hour_types.hour_type_id` |
| `created_by_id` | Integer | Yes |  |
| `created_by_name` | String(150) | Yes |  |
| `updated_by_id` | Integer | Yes |  |
| `updated_by_name` | String(150) | Yes |  |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |
| `check_type` | String(30) | No | Default `checkin_only` |
| `require_registration` | Boolean | No | Default false |
| `max_participants` | Integer | Yes |  |
| `activity_lat` | Numeric(10,7) | Yes |  |
| `activity_lng` | Numeric(10,7) | Yes |  |
| `activity_radius_meter` | Integer | No | Default 100 |

ค่า `check_type` ที่ code schema รองรับ:

- `checkin_only`
- `checkout_only`
- `checkin_checkout`

ค่า `target_group` ที่รองรับ:

- `all`: เปิดให้ทุกชั้นปี
- `freshman`: สำหรับนิสิต `ปี 1`
- `senior`: สำหรับนิสิต `ปี 2`, `ปี 3`, `ปี 4`

Constraints:

- `chk_activity_target_group`: `target_group IN ('all', 'freshman', 'senior')`

หมายเหตุ: SQL เดิมด้านล่างมี check constraint แค่ `checkin_only` และ `checkin_checkout` ถ้า database จริงยังมี constraint เดิมนี้อยู่ แต่ code ส่ง `checkout_only` จะ insert/update ไม่ผ่าน

### `student_activities`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `student_activity_id` | Integer | No | Primary key, index |
| `student_id` | Integer | No | FK to `students.student_id`, on delete cascade |
| `activity_id` | Integer | No | FK to `activities.activity_id`, on delete cascade |
| `attendance_status` | String(20) | No | Default `ไม่เข้าร่วม`, check `เข้าร่วม` หรือ `ไม่เข้าร่วม` |
| `checkin_at` | BigInteger | Yes | Unix timestamp |
| `checkin_status` | String(20) | Yes | `valid` หรือ `manual` ตาม logic scan |
| `checkout_status` | String(20) | Yes | `valid` หรือ `manual` ตาม logic scan |
| `earned_hours` | Numeric(4,2) | No | Default 0 |
| `created_by_id` | Integer | Yes |  |
| `created_by_name` | String(150) | Yes |  |
| `updated_by_id` | Integer | Yes |  |
| `updated_by_name` | String(150) | Yes |  |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |
| `registered_at` | BigInteger | Yes | Unix timestamp |
| `checkout_at` | BigInteger | Yes | Unix timestamp |
| `checkin_lat` | Numeric(10,7) | Yes |  |
| `checkin_lng` | Numeric(10,7) | Yes |  |
| `checkout_lat` | Numeric(10,7) | Yes |  |
| `checkout_lng` | Numeric(10,7) | Yes |  |

Constraints:

- `uq_student_activity`: unique `student_id`, `activity_id`
- `chk_attendance_status`: `attendance_status IN ('เข้าร่วม', 'ไม่เข้าร่วม')`

### `positions`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `position_id` | Integer | No | Primary key, index |
| `position_name` | String(100) | No | Unique |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

### `student_positions`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `student_position_id` | Integer | No | Primary key, index |
| `student_id` | Integer | No | FK to `students.student_id`, on delete cascade |
| `position_id` | Integer | No | FK to `positions.position_id`, on delete cascade |
| `is_current` | Boolean | No | Default true |
| `start_date` | Date | No |  |
| `end_date` | Date | Yes |  |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

### `activity_hour_types`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `hour_type_id` | UUID | No | Primary key, default `uuid.uuid4` ใน SQLAlchemy |
| `hour_type_name` | String(100) | No |  |

ค่าเริ่มต้นที่เคย insert:

- `กยศ.`
- `ทั่วไป`

## Shop Schema

### `product_categories`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `category_id` | UUID | No | Primary key, default `uuid.uuid4` |
| `category_name` | String(150) | No | Unique |
| `is_active` | Boolean | No | Default true |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

### `products`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `product_id` | UUID | No | Primary key, default `uuid.uuid4` |
| `product_name` | String(255) | No |  |
| `description` | Text | Yes |  |
| `category_id` | UUID | Yes | FK to `product_categories.category_id` |
| `base_price` | Numeric(10,2) | Yes | ใช้เมื่อไม่มี variant |
| `base_stock` | Integer | No | Default 0 |
| `owner_type` | String(30) | No | Default `club` |
| `faculty_id` | Integer | Yes | FK to `faculties.faculty_id` |
| `major_id` | Integer | Yes | FK to `majors.major_id` |
| `external_name` | String(255) | Yes | ชื่อเจ้าของภายนอก |
| `main_image` | Text | Yes |  |
| `product_images` | JSONB | Yes | รายการ URL รูป |
| `has_variant` | Boolean | No | Default false |
| `is_active` | Boolean | No | Default true |
| `is_limited` | Boolean | No | Default false |
| `limit_per_student` | Integer | Yes | จำนวนสูงสุดต่อคน |
| `weight_gram` | Integer | Yes |  |
| `sold_count` | Integer | No | Default 0 |
| `created_by_id` | Integer | Yes |  |
| `created_by_name` | String(150) | Yes |  |
| `updated_by_id` | Integer | Yes |  |
| `updated_by_name` | String(150) | Yes |  |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

ค่า `owner_type` ที่ application รองรับ: `club`, `faculty`, `major`, `external`

### `product_variants`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `variant_id` | UUID | No | Primary key, default `uuid.uuid4` |
| `product_id` | UUID | No | FK to `products.product_id`, on delete cascade |
| `variant_name` | String(100) | No | Default `Default` |
| `color_name` | String(100) | Yes |  |
| `variant_image` | Text | Yes |  |
| `sku_code` | String(100) | Yes | Unique เมื่อมีค่า |
| `price` | Numeric(10,2) | No |  |
| `stock` | Integer | No | Default 0 |
| `is_active` | Boolean | No | Default true |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

### `carts`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `cart_id` | UUID | No | Primary key, default `uuid.uuid4` |
| `student_id` | Integer | No | FK to `students.student_id`, unique, on delete cascade |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

### `cart_items`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `cart_item_id` | UUID | No | Primary key, default `uuid.uuid4` |
| `cart_id` | UUID | No | FK to `carts.cart_id`, on delete cascade |
| `product_id` | UUID | No | FK to `products.product_id` |
| `variant_id` | UUID | Yes | FK to `product_variants.variant_id` |
| `quantity` | Integer | No | Default 1 |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

### `orders`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `order_id` | UUID | No | Primary key, default `uuid.uuid4` |
| `order_no` | String(50) | No | Unique |
| `student_id` | Integer | No | FK to `students.student_id` |
| `total_amount` | Numeric(10,2) | No | Default 0 |
| `order_status` | String(30) | No | Default `pending_payment` |
| `payment_status` | String(30) | No | Default `waiting_payment` |
| `delivery_type` | String(30) | No | Default `pickup` |
| `pickup_code` | String(50) | Yes |  |
| `receiver_name` | String(255) | Yes |  |
| `receiver_phone` | String(50) | Yes |  |
| `shipping_address` | Text | Yes |  |
| `carrier` | String(100) | Yes |  |
| `tracking_no` | String(100) | Yes |  |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

สถานะที่ application รองรับ:

- `order_status`: `pending_payment`, `paid`, `preparing`, `ready_for_pickup`, `shipping`, `completed`, `cancelled`
- `payment_status`: `waiting_payment`, `paid`, `rejected`, `expired`, `cancelled`
- `delivery_type`: `pickup`, `shipping`

### `order_items`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `order_item_id` | UUID | No | Primary key, default `uuid.uuid4` |
| `order_id` | UUID | No | FK to `orders.order_id`, unique, on delete cascade |
| `product_id` | UUID | No | FK to `products.product_id` |
| `variant_id` | UUID | Yes | FK to `product_variants.variant_id` |
| `product_name_snapshot` | String(255) | No | ชื่อสินค้าตอนสั่ง |
| `variant_name_snapshot` | String(100) | Yes |  |
| `color_name_snapshot` | String(100) | Yes |  |
| `price_snapshot` | Numeric(10,2) | No | ราคาตอนสั่ง |
| `quantity` | Integer | No |  |
| `total_price` | Numeric(10,2) | No |  |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

### `payments`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `payment_id` | UUID | No | Primary key, default `uuid.uuid4` |
| `order_id` | UUID | No | FK to `orders.order_id`, on delete cascade |
| `amount` | Numeric(10,2) | No |  |
| `promptpay_payload` | Text | Yes | Thai QR payload |
| `qr_code` | Text | Yes | PNG แบบ base64 data URI |
| `payment_status` | String(30) | No | Default `waiting_payment` |
| `paid_at` | BigInteger | Yes | Unix timestamp |
| `created_at` | BigInteger | Yes | Unix timestamp |
| `updated_at` | BigInteger | Yes | Unix timestamp |

### `stock_movements`

| Column | Type | Null | Constraint / Default |
| --- | --- | --- | --- |
| `stock_movement_id` | UUID | No | Primary key, default `uuid.uuid4` |
| `product_id` | UUID | No | FK to `products.product_id` |
| `variant_id` | UUID | Yes | FK to `product_variants.variant_id` |
| `movement_type` | String(30) | No |  |
| `quantity` | Integer | No |  |
| `before_stock` | Integer | No |  |
| `after_stock` | Integer | No |  |
| `ref_order_id` | UUID | Yes | FK to `orders.order_id` |
| `note` | Text | Yes |  |
| `created_by_id` | Integer | Yes |  |
| `created_by_name` | String(150) | Yes |  |
| `created_at` | BigInteger | Yes | Unix timestamp |

ค่า `movement_type` ที่ application รองรับ: `increase`, `decrease`, `sale`, `cancel_return`, `adjust`

## Shop Schema Hardening

`migrations/20260613_harden_shop_constraints_indexes.sql` เพิ่ม:

- unique index สำหรับ `payments.order_id`
- unique index สำหรับ `product_variants.sku_code` เมื่อมีค่า
- indexes สำหรับ product filter, order owner/status/time, order item และ stock movement
- check constraints ให้ quantity และ stock ก่อน/หลัง movement ไม่ติดลบ

ก่อนรัน migration ต้องตรวจ duplicate payment ต่อ order และ SKU ซ้ำ เพราะ unique index จะสร้างไม่ผ่านหากมีข้อมูลซ้ำ

สิ่งที่ยังควรพิจารณา:

- FK ของ `orders.student_id`, product/category และหลายตารางยังไม่ได้กำหนด `ondelete`; ควรกำหนด delete policy ให้ชัด
- unique `(product_id, variant_name, color_name)` ของ PostgreSQL ยอมให้ `color_name = NULL` ซ้ำได้ ควรใช้ `NULLS NOT DISTINCT` หากต้องการห้ามซ้ำกรณีไม่มีสี

## Audit Fields Pattern

ตารางหลักส่วนใหญ่มี field สำหรับตรวจว่าใครสร้าง/แก้ไข:

- `created_by_id`
- `created_by_name`
- `updated_by_id`
- `updated_by_name`
- `created_at`
- `updated_at`

ใน code ปัจจุบันเวลาส่วนใหญ่ใช้ `int(time.time())` เป็น Unix timestamp หน่วยวินาที

## SQL เดิมที่เคยใช้สร้างฐานข้อมูล

SQL ชุดนี้มาจากข้อมูลที่ส่งมา ใช้เป็น reference ของ schema เดิม ก่อน field/table บางส่วนใน `models.py` ปัจจุบัน

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'student')),
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,

    created_by_id INT NULL,
    created_by_name VARCHAR(150) NULL,
    updated_by_id INT NULL,
    updated_by_name VARCHAR(150) NULL,

    created_at BIGINT NULL,
    updated_at BIGINT NULL
);


CREATE TABLE faculties (
    faculty_id SERIAL PRIMARY KEY,
    faculty_name VARCHAR(255) NOT NULL UNIQUE,

    created_by_id INT NULL,
    created_by_name VARCHAR(150) NULL,
    updated_by_id INT NULL,
    updated_by_name VARCHAR(150) NULL,

    created_at BIGINT NULL,
    updated_at BIGINT NULL
);


CREATE TABLE majors (
    major_id SERIAL PRIMARY KEY,
    major_name VARCHAR(255) NOT NULL,
    faculty_id INT NOT NULL,

    created_by_id INT NULL,
    created_by_name VARCHAR(150) NULL,
    updated_by_id INT NULL,
    updated_by_name VARCHAR(150) NULL,

    created_at BIGINT NULL,
    updated_at BIGINT NULL,

    CONSTRAINT fk_major_faculty
        FOREIGN KEY (faculty_id)
        REFERENCES faculties(faculty_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_major_name_faculty
        UNIQUE (major_name, faculty_id)
);


CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    student_code VARCHAR(20) NOT NULL UNIQUE,
    prefix VARCHAR(20),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    gender VARCHAR(20),
    faculty_id INT NOT NULL,
    major_id INT NOT NULL,
    user_id INT NOT NULL UNIQUE,
    img_stu TEXT,

    created_by_id INT NULL,
    created_by_name VARCHAR(150) NULL,
    updated_by_id INT NULL,
    updated_by_name VARCHAR(150) NULL,

    created_at BIGINT NULL,
    updated_at BIGINT NULL,

    CONSTRAINT fk_student_faculty
        FOREIGN KEY (faculty_id)
        REFERENCES faculties(faculty_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_student_major
        FOREIGN KEY (major_id)
        REFERENCES majors(major_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_student_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);


CREATE TABLE activities (
    activity_id SERIAL PRIMARY KEY,
    activity_name VARCHAR(255) NOT NULL,
    activity_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    hours NUMERIC(4,2) NOT NULL,
    location VARCHAR(255),
    description TEXT,
    activity_img TEXT,
    activity_status BOOLEAN NOT NULL DEFAULT TRUE,

    created_by_id INT NULL,
    created_by_name VARCHAR(150) NULL,
    updated_by_id INT NULL,
    updated_by_name VARCHAR(150) NULL,

    created_at BIGINT NULL,
    updated_at BIGINT NULL
);


CREATE TABLE student_activities (
    student_activity_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL,
    activity_id INT NOT NULL,
    attendance_status VARCHAR(20) NOT NULL DEFAULT 'ไม่เข้าร่วม',
    checkin_at BIGINT NULL,

    created_by_id INT NULL,
    created_by_name VARCHAR(150) NULL,
    updated_by_id INT NULL,
    updated_by_name VARCHAR(150) NULL,

    created_at BIGINT NULL,
    updated_at BIGINT NULL,

    CONSTRAINT fk_sa_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_sa_activity
        FOREIGN KEY (activity_id)
        REFERENCES activities(activity_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_student_activity
        UNIQUE (student_id, activity_id),

    CONSTRAINT chk_attendance_status
        CHECK (attendance_status IN ('เข้าร่วม', 'ไม่เข้าร่วม'))
);


ALTER TABLE activities
ADD COLUMN check_type VARCHAR(30) NOT NULL DEFAULT 'checkin_only',
ADD COLUMN require_registration BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN max_participants INT NULL,
ADD COLUMN activity_lat NUMERIC(10, 7) NULL,
ADD COLUMN activity_lng NUMERIC(10, 7) NULL,
ADD COLUMN activity_radius_meter INT NOT NULL DEFAULT 100;

ALTER TABLE activities
ADD CONSTRAINT chk_activity_check_type
CHECK (check_type IN ('checkin_only', 'checkin_checkout'));



ALTER TABLE student_activities
ADD COLUMN registered_at BIGINT NULL,
ADD COLUMN checkout_at BIGINT NULL,
ADD COLUMN checkin_lat NUMERIC(10, 7) NULL,
ADD COLUMN checkin_lng NUMERIC(10, 7) NULL,
ADD COLUMN checkout_lat NUMERIC(10, 7) NULL,
ADD COLUMN checkout_lng NUMERIC(10, 7) NULL;



CREATE TABLE activity_hour_types (
    hour_type_id UUID PRIMARY KEY,
    hour_type_name VARCHAR(100) NOT NULL
);

INSERT INTO activity_hour_types (hour_type_id, hour_type_name)
VALUES
(gen_random_uuid(), 'กยศ.'),
(gen_random_uuid(), 'ทั่วไป');

ALTER TABLE activities
ADD COLUMN hour_type_id UUID;

ALTER TABLE activities
ADD CONSTRAINT fk_activities_hour_type
FOREIGN KEY (hour_type_id)
REFERENCES activity_hour_types(hour_type_id);
```

## สิ่งที่ model ปัจจุบันมีเพิ่มจาก SQL เดิมที่ส่งมา

ถ้าใช้ SQL เดิมกับ code ปัจจุบัน ให้เช็คว่ามี field/table เหล่านี้แล้ว:

```sql
ALTER TABLE students
ADD COLUMN year_status VARCHAR(20) NULL;

ALTER TABLE users
DROP CONSTRAINT IF EXISTS check_user_role;

ALTER TABLE users
ADD CONSTRAINT check_user_role
CHECK (role IN ('admin', 'student', 'temporary_admin'));

ALTER TABLE activities
DROP CONSTRAINT IF EXISTS chk_activity_check_type;

ALTER TABLE activities
ADD CONSTRAINT chk_activity_check_type
CHECK (check_type IN ('checkin_only', 'checkout_only', 'checkin_checkout'));

ALTER TABLE activities
ADD COLUMN IF NOT EXISTS volunteer_hours NUMERIC(4,2) NOT NULL DEFAULT 0,
ADD COLUMN IF NOT EXISTS checkin_open_time TIME NULL,
ADD COLUMN IF NOT EXISTS checkin_close_time TIME NULL,
ADD COLUMN IF NOT EXISTS checkout_open_time TIME NULL,
ADD COLUMN IF NOT EXISTS checkout_close_time TIME NULL;

ALTER TABLE activities
ADD COLUMN IF NOT EXISTS target_group VARCHAR(30) NOT NULL DEFAULT 'all';

ALTER TABLE activities
DROP CONSTRAINT IF EXISTS chk_activity_target_group;

ALTER TABLE activities
ADD CONSTRAINT chk_activity_target_group
CHECK (target_group IN ('all', 'freshman', 'senior'));

ALTER TABLE student_activities
ADD COLUMN IF NOT EXISTS checkin_status VARCHAR(20) NULL,
ADD COLUMN IF NOT EXISTS checkout_status VARCHAR(20) NULL,
ADD COLUMN IF NOT EXISTS earned_hours NUMERIC(4,2) NOT NULL DEFAULT 0;

CREATE TABLE positions (
    position_id SERIAL PRIMARY KEY,
    position_name VARCHAR(100) NOT NULL UNIQUE,
    created_at BIGINT NULL,
    updated_at BIGINT NULL
);

CREATE TABLE student_positions (
    student_position_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL,
    position_id INT NOT NULL,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    created_at BIGINT NULL,
    updated_at BIGINT NULL,

    CONSTRAINT fk_student_position_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_student_position_position
        FOREIGN KEY (position_id)
        REFERENCES positions(position_id)
        ON DELETE CASCADE
);
```

## Migration ปัจจุบัน

### เพิ่มกลุ่มเป้าหมายของกิจกรรม

ไฟล์: `migrations/20260606_add_activity_target_group.sql`

Migration นี้ทำงานดังนี้:

1. เพิ่ม `activities.target_group` เป็น `VARCHAR(30) NOT NULL DEFAULT 'all'`
2. ลบ constraint `chk_activity_target_group` เดิม ถ้ามี
3. สร้าง constraint ใหม่ให้รับเฉพาะ `all`, `freshman`, `senior`

คำสั่งตัวอย่าง:

```bash
psql "$DATABASE_URL" -f migrations/20260606_add_activity_target_group.sql
```

ต้องรัน migration นี้กับ database ที่สร้างไว้ก่อนเพิ่ม `target_group` เพราะ `Base.metadata.create_all(bind=engine)` จะไม่เพิ่ม column ให้ตาราง `activities` ที่มีอยู่แล้ว

### Shop

รันตามลำดับ:

```bash
psql "$DATABASE_URL" -f migrations/20260613_add_shop_tables.sql
psql "$DATABASE_URL" -f migrations/20260613_harden_shop_constraints_indexes.sql
```

ไฟล์ hardening จะสร้าง unique indexes, query indexes และ stock check constraints เพิ่มเติม หากมี payment ต่อ order ซ้ำหรือ SKU ซ้ำต้องแก้ข้อมูลก่อนรัน

ถ้า database จริงยังมี constraint เดิมของ `activities.check_type` และต้องการใช้ `checkout_only` ด้วย ให้ปรับ constraint:

```sql
ALTER TABLE activities
DROP CONSTRAINT IF EXISTS chk_activity_check_type;

ALTER TABLE activities
ADD CONSTRAINT chk_activity_check_type
CHECK (check_type IN ('checkin_only', 'checkout_only', 'checkin_checkout'));
```

## ข้อควรจำเวลาแก้ schema

- `Base.metadata.create_all(bind=engine)` สร้าง table ที่ยังไม่มี แต่ไม่แก้ column/constraint เดิมที่มีอยู่แล้ว
- ถ้าเพิ่ม/แก้ column ใน `models.py` ควรมี SQL migration หรือ manual ALTER TABLE ตามด้วย
- ถ้าเพิ่ม constraint ใน database ต้องเช็คว่า logic ใน schema/router ส่งค่าได้ตรงกับ constraint
- การลบ `students` หรือ `activities` จะกระทบ `student_activities` ตาม FK `ON DELETE CASCADE`
- การลบ activity แบบ soft delete เป็นการเปลี่ยน `activity_status`; การ hard delete จะลบ activity และข้อมูลการเข้าร่วมที่สัมพันธ์กัน
- endpoint hard delete ของ activity ลบ `student_activities` ก่อนลบ `activities`; ควรจำกัดสิทธิ์ admin และใช้ด้วยความระมัดระวัง
- ห้ามเปลี่ยนชื่อ column เดิมถ้า frontend หรือ API response ยังใช้อยู่
- ถ้าต้องแก้ relation ต้องเช็ค cascade/delete behavior ก่อนเสมอ
