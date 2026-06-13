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
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid


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
        CheckConstraint("role IN ('admin', 'student', 'temporary_admin')", name="check_user_role"),
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
    year_status = Column(String(20), nullable=True)

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
    
    student_positions = relationship(
        "StudentPosition",
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
    __table_args__ = (
        CheckConstraint(
            "target_group IN ('all', 'freshman', 'senior')",
            name="chk_activity_target_group"
        ),
    )

    target_group = Column(String(30), nullable=False, default="all")
    activity_id = Column(Integer, primary_key=True, index=True)
    activity_name = Column(String(255), nullable=False)
    activity_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    hours = Column(Numeric(4, 2), nullable=False)
    volunteer_hours = Column(Numeric(4, 2), nullable=False, default=0)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    activity_img = Column(Text, nullable=True)
    activity_status = Column(Boolean, nullable=False, default=True)
    checkin_open_time = Column(Time, nullable=True)
    checkin_close_time = Column(Time, nullable=True)
    checkout_open_time = Column(Time, nullable=True)
    checkout_close_time = Column(Time, nullable=True)
    
    hour_type_id = Column(UUID(as_uuid=True), ForeignKey("activity_hour_types.hour_type_id"), nullable=True)
    hour_type = relationship("ActivityHourType")

    created_by_id = Column(Integer, nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)
    check_type = Column(String(30), nullable=False, default="checkin_only")
    require_registration = Column(Boolean, nullable=False, default=False)
    max_participants = Column(Integer, nullable=True)

    activity_lat = Column(Numeric(10, 7), nullable=True)
    activity_lng = Column(Numeric(10, 7), nullable=True)
    activity_radius_meter = Column(Integer, nullable=False, default=100)

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
    checkin_status = Column(String(20), nullable=True)
    checkout_status = Column(String(20), nullable=True)
    earned_hours = Column(Numeric(4, 2), nullable=False, default=0)

    created_by_id = Column(Integer, nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    updated_by_name = Column(String(150), nullable=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)

    student = relationship("Student", back_populates="student_activities", foreign_keys=[student_id])
    activity = relationship("Activity", back_populates="student_activities", foreign_keys=[activity_id])
    registered_at = Column(BigInteger, nullable=True)
    checkout_at = Column(BigInteger, nullable=True)

    checkin_lat = Column(Numeric(10, 7), nullable=True)
    checkin_lng = Column(Numeric(10, 7), nullable=True)

    checkout_lat = Column(Numeric(10, 7), nullable=True)
    checkout_lng = Column(Numeric(10, 7), nullable=True)

    __table_args__ = (
        UniqueConstraint("student_id", "activity_id", name="uq_student_activity"),
        CheckConstraint(
            "attendance_status IN ('เข้าร่วม', 'ไม่เข้าร่วม')",
            name="chk_attendance_status"
        ),
    )
    

    
class Position(Base):
    __tablename__ = "positions"

    position_id = Column(Integer, primary_key=True, index=True)
    position_name = Column(String(100), nullable=False, unique=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)

    student_positions = relationship("StudentPosition", back_populates="position")


class StudentPosition(Base):
    __tablename__ = "student_positions"

    student_position_id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.student_id", ondelete="CASCADE"),
        nullable=False
    )

    position_id = Column(
        Integer,
        ForeignKey("positions.position_id", ondelete="CASCADE"),
        nullable=False
    )

    is_current = Column(Boolean, nullable=False, default=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)

    student = relationship("Student", back_populates="student_positions")
    position = relationship("Position", back_populates="student_positions")
    
class ActivityHourType(Base):
    __tablename__ = "activity_hour_types"

    hour_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hour_type_name = Column(String(100), nullable=False)


class ProductCategory(Base):
    __tablename__ = "product_categories"

    category_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_name = Column(String(150), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "owner_type IN ('club', 'faculty', 'major', 'external')",
            name="chk_products_owner_type",
        ),
        CheckConstraint("base_price IS NULL OR base_price >= 0", name="chk_products_base_price"),
        CheckConstraint("base_stock >= 0", name="chk_products_base_stock"),
        CheckConstraint(
            "limit_per_student IS NULL OR limit_per_student > 0",
            name="chk_products_limit_per_student",
        ),
        CheckConstraint("weight_gram IS NULL OR weight_gram >= 0", name="chk_products_weight"),
        CheckConstraint("sold_count >= 0", name="chk_products_sold_count"),
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_owner_type", "owner_type"),
        Index("ix_products_is_active", "is_active"),
    )

    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    product_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.category_id"), nullable=True)

    base_price = Column(Numeric(10, 2), nullable=True)
    base_stock = Column(Integer, nullable=False, default=0)

    owner_type = Column(String(30), nullable=False, default="club")
    faculty_id = Column(Integer, ForeignKey("faculties.faculty_id"), nullable=True)
    major_id = Column(Integer, ForeignKey("majors.major_id"), nullable=True)
    external_name = Column(String(255), nullable=True)

    main_image = Column(Text, nullable=True)
    product_images = Column(JSONB, nullable=True)

    has_variant = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_limited = Column(Boolean, nullable=False, default=False)
    limit_per_student = Column(Integer, nullable=True)

    weight_gram = Column(Integer, nullable=True)
    sold_count = Column(Integer, nullable=False, default=0)

    created_by_id = Column(Integer, nullable=True)
    created_by_name = Column(String(150), nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    updated_by_name = Column(String(150), nullable=True)
    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "variant_name",
            "color_name",
            name="uq_product_variant_color",
        ),
        UniqueConstraint("sku_code", name="uq_product_variants_sku_code"),
        CheckConstraint("price >= 0", name="chk_variants_price"),
        CheckConstraint("stock >= 0", name="chk_variants_stock"),
        Index("ix_product_variants_product_id", "product_id"),
        Index("ix_product_variants_is_active", "is_active"),
    )

    variant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)

    variant_name = Column(String(100), nullable=False, default="Default")
    color_name = Column(String(100), nullable=True)
    variant_image = Column(Text, nullable=True)
    sku_code = Column(String(100), nullable=True)

    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)


class Cart(Base):
    __tablename__ = "carts"

    cart_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, unique=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint(
            "cart_id",
            "product_id",
            "variant_id",
            name="uq_cart_product_variant",
        ),
        CheckConstraint("quantity > 0", name="chk_cart_items_quantity"),
        Index("ix_cart_items_cart_id", "cart_id"),
    )

    cart_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.cart_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.variant_id"), nullable=True)

    quantity = Column(Integer, nullable=False, default=1)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_orders_total_amount"),
        CheckConstraint(
            "order_status IN ('pending_payment', 'paid', 'preparing', "
            "'ready_for_pickup', 'shipping', 'completed', 'cancelled')",
            name="chk_orders_order_status",
        ),
        CheckConstraint(
            "payment_status IN ('waiting_payment', 'paid', 'rejected', "
            "'expired', 'cancelled')",
            name="chk_orders_payment_status",
        ),
        CheckConstraint(
            "delivery_type IN ('pickup', 'shipping')",
            name="chk_orders_delivery_type",
        ),
        Index("ix_orders_student_id", "student_id"),
        Index("ix_orders_order_status", "order_status"),
        Index("ix_orders_payment_status", "payment_status"),
        Index("ix_orders_created_at", "created_at"),
    )

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no = Column(String(50), nullable=False, unique=True)

    student_id = Column(Integer, ForeignKey("students.student_id"), nullable=False)

    total_amount = Column(Numeric(10, 2), nullable=False, default=0)

    order_status = Column(String(30), nullable=False, default="pending_payment")
    payment_status = Column(String(30), nullable=False, default="waiting_payment")
    delivery_type = Column(String(30), nullable=False, default="pickup")

    pickup_code = Column(String(50), nullable=True)

    receiver_name = Column(String(255), nullable=True)
    receiver_phone = Column(String(50), nullable=True)
    shipping_address = Column(Text, nullable=True)
    carrier = Column(String(100), nullable=True)
    tracking_no = Column(String(100), nullable=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("price_snapshot >= 0", name="chk_order_items_price"),
        CheckConstraint("quantity > 0", name="chk_order_items_quantity"),
        CheckConstraint("total_price >= 0", name="chk_order_items_total"),
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_product_id", "product_id"),
    )

    order_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.variant_id"), nullable=True)

    product_name_snapshot = Column(String(255), nullable=False)
    variant_name_snapshot = Column(String(100), nullable=True)
    color_name_snapshot = Column(String(100), nullable=True)

    price_snapshot = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_payments_order_id"),
        CheckConstraint("amount >= 0", name="chk_payments_amount"),
        CheckConstraint(
            "payment_status IN ('waiting_payment', 'paid', 'rejected', "
            "'expired', 'cancelled')",
            name="chk_payments_status",
        ),
        Index("ix_payments_payment_status", "payment_status"),
    )

    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    promptpay_payload = Column(Text, nullable=True)
    qr_code = Column(Text, nullable=True)

    payment_status = Column(String(30), nullable=False, default="waiting_payment")
    paid_at = Column(BigInteger, nullable=True)

    created_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=True)


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint(
            "movement_type IN ('increase', 'decrease', 'sale', "
            "'cancel_return', 'adjust')",
            name="chk_stock_movements_type",
        ),
        CheckConstraint("quantity > 0", name="chk_stock_movements_quantity"),
        CheckConstraint("before_stock >= 0", name="chk_stock_movements_before_stock"),
        CheckConstraint("after_stock >= 0", name="chk_stock_movements_after_stock"),
        Index("ix_stock_movements_product_id", "product_id"),
        Index("ix_stock_movements_variant_id", "variant_id"),
        Index("ix_stock_movements_ref_order_id", "ref_order_id"),
        Index("ix_stock_movements_created_at", "created_at"),
    )

    stock_movement_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.variant_id"), nullable=True)

    movement_type = Column(String(30), nullable=False)
    quantity = Column(Integer, nullable=False)

    before_stock = Column(Integer, nullable=False)
    after_stock = Column(Integer, nullable=False)

    ref_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=True)
    note = Column(Text, nullable=True)

    created_by_id = Column(Integer, nullable=True)
    created_by_name = Column(String(150), nullable=True)
    created_at = Column(BigInteger, nullable=True)
