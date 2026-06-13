from uuid import UUID
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import Order, Payment, Student, User
from routers.shop.order import build_order_response, cancel_order_and_restore_stock
from schemas.schemas_shop import (
    AdminOrderSearchRequest,
    AdminConfirmPaymentRequest,
    AdminUpdateOrderStatusRequest,
    AdminUpdateShippingRequest,
    OrderMessageResponse,
)

router = APIRouter(prefix="/shop/v1", tags=["Shop Admin Order"])


ORDER_STATUS_LIST = [
    "pending_payment",
    "paid",
    "preparing",
    "ready_for_pickup",
    "shipping",
    "completed",
    "cancelled",
]

PAYMENT_STATUS_LIST = [
    "waiting_payment",
    "paid",
    "rejected",
    "expired",
    "cancelled",
]


def get_unix_time() -> int:
    return int(time.time())


def get_admin_by_name(db: Session, admin_name: str) -> User:
    admin = (
        db.query(User)
        .filter(
            User.name == admin_name,
            User.role == "admin",
            User.is_active == True,
        )
        .first()
    )

    if not admin:
        raise HTTPException(status_code=403, detail="ไม่พบสิทธิ์แอดมิน")

    return admin

# Admin Get All Orders
@router.post("/admin/orders/get-all")
def admin_get_all_orders(
    body: AdminOrderSearchRequest,
    db: Session = Depends(get_db),
):
    page = max(body.page, 1)
    limit = max(body.limit, 1)
    offset = (page - 1) * limit

    query = (
        db.query(Order)
        .join(Student, Student.student_id == Order.student_id)
    )

    if body.search.strip() != "":
        search_text = f"%{body.search.strip()}%"
        query = query.filter(
            or_(
                Order.order_no.ilike(search_text),
                Student.student_code.ilike(search_text),
                Student.first_name.ilike(search_text),
                Student.last_name.ilike(search_text),
            )
        )

    if body.student_code.strip() != "":
        query = query.filter(
            Student.student_code.ilike(f"%{body.student_code.strip()}%")
        )

    if body.order_status.strip() != "":
        if body.order_status not in ORDER_STATUS_LIST:
            raise HTTPException(status_code=400, detail="สถานะคำสั่งซื้อไม่ถูกต้อง")

        query = query.filter(Order.order_status == body.order_status)

    if body.payment_status.strip() != "":
        if body.payment_status not in PAYMENT_STATUS_LIST:
            raise HTTPException(status_code=400, detail="สถานะการชำระเงินไม่ถูกต้อง")

        query = query.filter(Order.payment_status == body.payment_status)

    if body.delivery_type.strip() != "":
        if body.delivery_type not in ["pickup", "shipping"]:
            raise HTTPException(status_code=400, detail="ประเภทการรับสินค้าไม่ถูกต้อง")

        query = query.filter(Order.delivery_type == body.delivery_type)

    total_all = query.count()

    orders = (
        query
        .order_by(Order.created_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "detail": "ดึงรายการคำสั่งซื้อสำเร็จ",
        "total_all": total_all,
        "page": page,
        "limit": limit,
        "data": [build_order_response(db, order) for order in orders],
    }
    
    
# Admin Get Order Detail
@router.get("/admin/orders/{order_id}", response_model=OrderMessageResponse)
def admin_get_order_detail(
    order_id: UUID,
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(Order.order_id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="ไม่พบคำสั่งซื้อ")

    return {
        "detail": "ดึงรายละเอียดคำสั่งซื้อสำเร็จ",
        "data": build_order_response(db, order),
    }

# Admin Confirm Payment
@router.patch("/admin/orders/payment/{order_id}", response_model=OrderMessageResponse)
def admin_confirm_payment(
    order_id: UUID,
    body: AdminConfirmPaymentRequest,
    db: Session = Depends(get_db),
):
    admin = get_admin_by_name(db, body.updated_by_name)

    order = db.query(Order).filter(Order.order_id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="ไม่พบคำสั่งซื้อ")

    if order.order_status == "cancelled":
        raise HTTPException(status_code=400, detail="คำสั่งซื้อนี้ถูกยกเลิกแล้ว")

    payment = db.query(Payment).filter(Payment.order_id == order.order_id).first()

    if not payment:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลการชำระเงิน")

    now = get_unix_time()

    order.payment_status = "paid"
    order.order_status = "paid"
    order.updated_at = now

    payment.payment_status = "paid"
    payment.paid_at = now
    payment.updated_at = now

    db.commit()
    db.refresh(order)

    return {
        "detail": "ยืนยันการชำระเงินสำเร็จ",
        "data": build_order_response(db, order),
    }
    
# Admin Update Order Status
@router.patch("/admin/orders/status/{order_id}", response_model=OrderMessageResponse)
def admin_update_order_status(
    order_id: UUID,
    body: AdminUpdateOrderStatusRequest,
    db: Session = Depends(get_db),
):
    admin = get_admin_by_name(db, body.updated_by_name)

    if body.order_status not in ORDER_STATUS_LIST:
        raise HTTPException(status_code=400, detail="สถานะคำสั่งซื้อไม่ถูกต้อง")

    order = (
        db.query(Order)
        .filter(Order.order_id == order_id)
        .with_for_update()
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="ไม่พบคำสั่งซื้อ")

    if body.order_status == "cancelled":
        cancel_order_and_restore_stock(
            db=db,
            order=order,
            actor_id=admin.user_id,
            actor_name=admin.name,
            reason=f"แอดมิน {admin.name} ยกเลิกคำสั่งซื้อ",
        )
    elif order.payment_status != "paid":
        raise HTTPException(
            status_code=400,
            detail="ยังไม่สามารถเปลี่ยนสถานะได้ เพราะยังไม่ได้ยืนยันการชำระเงิน"
        )
    else:
        order.order_status = body.order_status
        order.updated_at = get_unix_time()

    db.commit()
    db.refresh(order)

    return {
        "detail": "แก้ไขสถานะคำสั่งซื้อสำเร็จ",
        "data": build_order_response(db, order),
    }
    
# Admin Update Shipping
@router.patch("/admin/orders/shipping/{order_id}", response_model=OrderMessageResponse)
def admin_update_shipping(
    order_id: UUID,
    body: AdminUpdateShippingRequest,
    db: Session = Depends(get_db),
):
    get_admin_by_name(db, body.updated_by_name)

    order = db.query(Order).filter(Order.order_id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="ไม่พบคำสั่งซื้อ")

    if order.delivery_type != "shipping":
        raise HTTPException(status_code=400, detail="คำสั่งซื้อนี้ไม่ใช่แบบจัดส่ง")

    if order.payment_status != "paid":
        raise HTTPException(status_code=400, detail="คำสั่งซื้อนี้ยังไม่ได้ชำระเงิน")

    if body.carrier is not None:
        order.carrier = body.carrier.strip()

    if body.tracking_no is not None:
        order.tracking_no = body.tracking_no.strip()

    order.order_status = "shipping"
    order.updated_at = get_unix_time()

    db.commit()
    db.refresh(order)

    return {
        "detail": "อัปเดตข้อมูลจัดส่งสำเร็จ",
        "data": build_order_response(db, order),
    }
    
