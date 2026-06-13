from decimal import Decimal
from typing import Optional
from uuid import UUID
import random
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Student,
    Product,
    ProductVariant,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Payment,
    StockMovement,
)
from schemas.schemas_shop import (
    OrderCreateRequest,
    OrderCancelRequest,
    OrderMessageResponse,
    OrderListResponse,
)

from routers.shop.payment_qr import generate_promptpay_payload, generate_qr_base64

router = APIRouter(prefix="/shop/v1", tags=["Shop Order"])


def get_unix_time() -> int:
    return int(time.time())


def get_student_by_code(db: Session, student_code: str) -> Student:
    student = (
        db.query(Student)
        .filter(Student.student_code == student_code)
        .first()
    )

    if not student:
        raise HTTPException(status_code=404, detail="ไม่พบนิสิต")

    return student


def generate_order_no() -> str:
    now = time.strftime("%Y%m%d")
    random_no = random.randint(100000, 999999)
    return f"ORD-{now}-{random_no}"


def generate_pickup_code() -> str:
    random_no = random.randint(100000, 999999)
    return f"RBAC-{random_no}"


def build_order_response(db: Session, order: Order):
    items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.order_id)
        .all()
    )

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.order_id)
        .first()
    )

    return {
        "order_id": order.order_id,
        "order_no": order.order_no,
        "student_id": order.student_id,
        "total_amount": order.total_amount,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "delivery_type": order.delivery_type,
        "pickup_code": order.pickup_code,
        "receiver_name": order.receiver_name,
        "receiver_phone": order.receiver_phone,
        "shipping_address": order.shipping_address,
        "carrier": order.carrier,
        "tracking_no": order.tracking_no,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": items,
        "payment": payment,
    }


def get_owned_order(
    db: Session,
    order_id: UUID,
    student_code: str,
    lock: bool = False,
):
    student = get_student_by_code(db, student_code)
    query = db.query(Order).filter(
        Order.order_id == order_id,
        Order.student_id == student.student_id,
    )

    if lock:
        query = query.with_for_update()

    order = query.first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบคำสั่งซื้อของนิสิตนี้",
        )

    return student, order


def cancel_order_and_restore_stock(
    db: Session,
    order: Order,
    actor_id: int,
    actor_name: str,
    reason: Optional[str] = None,
):
    if order.order_status == "cancelled":
        raise HTTPException(status_code=400, detail="คำสั่งซื้อนี้ถูกยกเลิกแล้ว")

    if order.payment_status == "paid":
        raise HTTPException(
            status_code=400,
            detail="คำสั่งซื้อที่ชำระเงินแล้วต้องดำเนินการคืนเงินก่อนยกเลิก",
        )

    if order.order_status == "completed":
        raise HTTPException(status_code=400, detail="ไม่สามารถยกเลิกคำสั่งซื้อที่สำเร็จแล้ว")

    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.order_id)
        .with_for_update()
        .all()
    )
    now = get_unix_time()

    for item in order_items:
        product = (
            db.query(Product)
            .filter(Product.product_id == item.product_id)
            .with_for_update()
            .first()
        )

        if not product:
            raise HTTPException(status_code=409, detail="ไม่พบสินค้าที่ต้องคืน stock")

        if item.variant_id is not None:
            variant = (
                db.query(ProductVariant)
                .filter(
                    ProductVariant.variant_id == item.variant_id,
                    ProductVariant.product_id == product.product_id,
                )
                .with_for_update()
                .first()
            )

            if not variant:
                raise HTTPException(status_code=409, detail="ไม่พบตัวเลือกสินค้าที่ต้องคืน stock")

            before_stock = variant.stock
            variant.stock = before_stock + item.quantity
            variant.updated_at = now
            after_stock = variant.stock
        else:
            before_stock = product.base_stock
            product.base_stock = before_stock + item.quantity
            product.updated_at = now
            after_stock = product.base_stock

        product.sold_count = max((product.sold_count or 0) - item.quantity, 0)
        product.updated_at = now

        db.add(StockMovement(
            product_id=product.product_id,
            variant_id=item.variant_id,
            movement_type="cancel_return",
            quantity=item.quantity,
            before_stock=before_stock,
            after_stock=after_stock,
            ref_order_id=order.order_id,
            note=reason or f"คืน stock จากการยกเลิก order {order.order_no}",
            created_by_id=actor_id,
            created_by_name=actor_name,
            created_at=now,
        ))

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.order_id)
        .with_for_update()
        .first()
    )

    order.order_status = "cancelled"
    order.payment_status = "cancelled"
    order.updated_at = now

    if payment:
        payment.payment_status = "cancelled"
        payment.updated_at = now


def check_limited_product_for_order(
    db: Session,
    student: Student,
    product: Product,
    order_quantity: int,
):
    if not product.is_limited:
        return

    limit = product.limit_per_student or 1

    rows = (
        db.query(OrderItem.quantity)
        .join(Order, Order.order_id == OrderItem.order_id)
        .filter(
            Order.student_id == student.student_id,
            OrderItem.product_id == product.product_id,
            Order.order_status != "cancelled",
        )
        .all()
    )

    purchased_qty = sum(row[0] for row in rows)

    if purchased_qty + order_quantity > limit:
        raise HTTPException(
            status_code=400,
            detail=f"สินค้า Limited นี้ซื้อได้ไม่เกิน {limit} ชิ้นต่อคน"
        )


@router.post("/orders/create", response_model=OrderMessageResponse)
def create_order_from_cart(
    body: OrderCreateRequest,
    db: Session = Depends(get_db),
):
    student = get_student_by_code(db, body.student_code)

    if body.delivery_type not in ["pickup", "shipping"]:
        raise HTTPException(status_code=400, detail="ประเภทการรับสินค้าไม่ถูกต้อง")

    if body.delivery_type == "shipping":
        if not body.receiver_name or not body.receiver_phone or not body.shipping_address:
            raise HTTPException(
                status_code=400,
                detail="กรุณาระบุชื่อผู้รับ เบอร์โทร และที่อยู่จัดส่ง"
            )

    cart = (
        db.query(Cart)
        .filter(Cart.student_id == student.student_id)
        .with_for_update()
        .first()
    )

    if not cart:
        raise HTTPException(status_code=400, detail="ตะกร้าสินค้าว่าง")

    cart_items = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.cart_id)
        .order_by(CartItem.product_id.asc(), CartItem.variant_id.asc().nullsfirst())
        .with_for_update()
        .all()
    )

    if len(cart_items) == 0:
        raise HTTPException(status_code=400, detail="ตะกร้าสินค้าว่าง")

    now = get_unix_time()
    total_amount = Decimal("0")

    prepared_items = []

    for cart_item in cart_items:
        product = (
            db.query(Product)
            .filter(Product.product_id == cart_item.product_id)
            .with_for_update()
            .first()
        )

        if not product:
            raise HTTPException(status_code=404, detail="พบสินค้าในตะกร้าที่ไม่มีอยู่แล้ว")

        if not product.is_active:
            raise HTTPException(status_code=400, detail=f"สินค้า {product.product_name} ปิดการขายแล้ว")

        variant = None

        if product.has_variant:
            if cart_item.variant_id is None:
                raise HTTPException(status_code=400, detail=f"สินค้า {product.product_name} ต้องเลือกตัวเลือกสินค้า")

            variant = (
                db.query(ProductVariant)
                .filter(
                    ProductVariant.variant_id == cart_item.variant_id,
                    ProductVariant.product_id == product.product_id,
                )
                .with_for_update()
                .first()
            )

            if not variant:
                raise HTTPException(status_code=404, detail=f"ไม่พบตัวเลือกของสินค้า {product.product_name}")

            if not variant.is_active:
                raise HTTPException(status_code=400, detail=f"ตัวเลือกของสินค้า {product.product_name} ปิดการขายแล้ว")

            price = Decimal(variant.price)
            stock = variant.stock
            variant_name = variant.variant_name
            color_name = variant.color_name

        else:
            if product.base_price is None:
                raise HTTPException(status_code=400, detail=f"สินค้า {product.product_name} ยังไม่ได้ตั้งราคา")

            price = Decimal(product.base_price)
            stock = product.base_stock
            variant_name = None
            color_name = None

        if cart_item.quantity > stock:
            raise HTTPException(
                status_code=400,
                detail=f"สินค้า {product.product_name} มี stock ไม่เพียงพอ"
            )

        check_limited_product_for_order(
            db=db,
            student=student,
            product=product,
            order_quantity=cart_item.quantity,
        )

        total_price = price * cart_item.quantity
        total_amount += total_price

        prepared_items.append({
            "cart_item": cart_item,
            "product": product,
            "variant": variant,
            "price": price,
            "stock": stock,
            "variant_name": variant_name,
            "color_name": color_name,
            "total_price": total_price,
        })

    order = Order(
        order_no=generate_order_no(),
        student_id=student.student_id,
        total_amount=total_amount,
        order_status="pending_payment",
        payment_status="waiting_payment",
        delivery_type=body.delivery_type,
        pickup_code=generate_pickup_code() if body.delivery_type == "pickup" else None,
        receiver_name=body.receiver_name,
        receiver_phone=body.receiver_phone,
        shipping_address=body.shipping_address,
        created_at=now,
        updated_at=now,
    )

    db.add(order)
    db.flush()

    for data in prepared_items:
        product = data["product"]
        variant = data["variant"]
        cart_item = data["cart_item"]

        order_item = OrderItem(
            order_id=order.order_id,
            product_id=product.product_id,
            variant_id=variant.variant_id if variant else None,
            product_name_snapshot=product.product_name,
            variant_name_snapshot=data["variant_name"],
            color_name_snapshot=data["color_name"],
            price_snapshot=data["price"],
            quantity=cart_item.quantity,
            total_price=data["total_price"],
            created_at=now,
            updated_at=now,
        )

        db.add(order_item)

        if product.has_variant:
            before_stock = variant.stock
            after_stock = before_stock - cart_item.quantity
            variant.stock = after_stock
            variant.updated_at = now
            stock_variant_id = variant.variant_id
        else:
            before_stock = product.base_stock
            after_stock = before_stock - cart_item.quantity
            product.base_stock = after_stock
            product.updated_at = now
            stock_variant_id = None

        product.sold_count = (product.sold_count or 0) + cart_item.quantity
        product.updated_at = now

        stock_movement = StockMovement(
            product_id=product.product_id,
            variant_id=stock_variant_id,
            movement_type="sale",
            quantity=cart_item.quantity,
            before_stock=before_stock,
            after_stock=after_stock,
            ref_order_id=order.order_id,
            note=f"ขายสินค้า order {order.order_no}",
            created_by_id=student.user_id,
            created_by_name=f"{student.first_name} {student.last_name}",
            created_at=now,
        )

        db.add(stock_movement)

    try:
        promptpay_payload = generate_promptpay_payload(total_amount)
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    qr_code = generate_qr_base64(promptpay_payload)

    payment = Payment(
        order_id=order.order_id,
        amount=total_amount,
        promptpay_payload=promptpay_payload,
        qr_code=qr_code,
        payment_status="waiting_payment",
        created_at=now,
        updated_at=now,
    )

    db.add(payment)

    db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).delete()
    cart.updated_at = now

    db.commit()
    db.refresh(order)

    return {
        "detail": "สร้างคำสั่งซื้อสำเร็จ",
        "data": build_order_response(db, order),
    }


@router.get("/orders/my/{student_code}", response_model=OrderListResponse)
def get_my_orders(
    student_code: str,
    db: Session = Depends(get_db),
):
    student = get_student_by_code(db, student_code)

    orders = (
        db.query(Order)
        .filter(Order.student_id == student.student_id)
        .order_by(Order.created_at.desc().nullslast())
        .all()
    )

    return {
        "detail": "ดึงประวัติคำสั่งซื้อสำเร็จ",
        "data": [build_order_response(db, order) for order in orders],
    }


@router.get("/orders/{order_id}", response_model=OrderMessageResponse)
def get_order_detail(
    order_id: UUID,
    student_code: str = Query(...),
    db: Session = Depends(get_db),
):
    _, order = get_owned_order(
        db=db,
        order_id=order_id,
        student_code=student_code,
    )

    return {
        "detail": "ดึงรายละเอียดคำสั่งซื้อสำเร็จ",
        "data": build_order_response(db, order),
    }


@router.patch("/orders/{order_id}/cancel", response_model=OrderMessageResponse)
def cancel_my_order(
    order_id: UUID,
    body: OrderCancelRequest,
    db: Session = Depends(get_db),
):
    student, order = get_owned_order(
        db=db,
        order_id=order_id,
        student_code=body.student_code,
        lock=True,
    )

    cancel_order_and_restore_stock(
        db=db,
        order=order,
        actor_id=student.user_id,
        actor_name=f"{student.first_name} {student.last_name}",
        reason=body.reason,
    )

    db.commit()
    db.refresh(order)

    return {
        "detail": "ยกเลิกคำสั่งซื้อและคืน stock สำเร็จ",
        "data": build_order_response(db, order),
    }
