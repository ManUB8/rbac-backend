from decimal import Decimal
from uuid import UUID
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Student, Product, ProductVariant, Cart, CartItem, Order, OrderItem
from schemas.schemas_shop import (
    CartAddRequest,
    CartUpdateItemRequest,
    CartMessageResponse,
)

router = APIRouter(prefix="/shop/v1", tags=["Shop Cart"])


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


def get_or_create_cart(db: Session, student: Student) -> Cart:
    cart = (
        db.query(Cart)
        .filter(Cart.student_id == student.student_id)
        .first()
    )

    if cart:
        return cart

    now = get_unix_time()

    cart = Cart(
        student_id=student.student_id,
        created_at=now,
        updated_at=now,
    )

    db.add(cart)
    db.flush()

    return cart


def check_limited_product(
    db: Session,
    student: Student,
    product: Product,
    add_quantity: int,
):
    if not product.is_limited:
        return

    limit = product.limit_per_student or 1

    purchased_qty = (
        db.query(OrderItem)
        .join(Order, Order.order_id == OrderItem.order_id)
        .filter(
            Order.student_id == student.student_id,
            OrderItem.product_id == product.product_id,
            Order.order_status != "cancelled",
        )
        .with_entities(OrderItem.quantity)
        .all()
    )

    total_purchased = sum(row[0] for row in purchased_qty)

    if total_purchased + add_quantity > limit:
        raise HTTPException(
            status_code=400,
            detail=f"สินค้า Limited นี้ซื้อได้ไม่เกิน {limit} ชิ้นต่อคน"
        )


def build_cart_response(db: Session, cart: Cart, student: Student):
    cart_items = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.cart_id)
        .all()
    )

    items = []
    total_amount = Decimal("0")
    total_items = 0

    for item in cart_items:
        product = (
            db.query(Product)
            .filter(Product.product_id == item.product_id)
            .first()
        )

        if not product:
            continue

        variant = None

        if item.variant_id is not None:
            variant = (
                db.query(ProductVariant)
                .filter(ProductVariant.variant_id == item.variant_id)
                .first()
            )

        if product.has_variant:
            if not variant:
                continue

            price = variant.price
            stock = variant.stock
            variant_name = variant.variant_name
            color_name = variant.color_name
            variant_image = variant.variant_image
        else:
            price = product.base_price
            stock = product.base_stock
            variant_name = None
            color_name = None
            variant_image = None

        total_price = Decimal(price) * item.quantity
        total_amount += total_price
        total_items += item.quantity

        items.append({
            "cart_item_id": item.cart_item_id,
            "product_id": product.product_id,
            "variant_id": variant.variant_id if variant else None,

            "product_name": product.product_name,
            "main_image": product.main_image,

            "variant_name": variant_name,
            "color_name": color_name,
            "variant_image": variant_image,

            "price": price,
            "quantity": item.quantity,
            "total_price": total_price,
            "stock": stock,
        })

    return {
        "cart_id": cart.cart_id,
        "student_id": student.student_id,
        "student_code": student.student_code,
        "total_amount": total_amount,
        "total_items": total_items,
        "items": items,
    }


@router.get("/cart/{student_code}", response_model=CartMessageResponse)
def get_my_cart(
    student_code: str,
    db: Session = Depends(get_db),
):
    student = get_student_by_code(db, student_code)
    cart = get_or_create_cart(db, student)

    db.commit()
    db.refresh(cart)

    return {
        "detail": "ดึงข้อมูลตะกร้าสำเร็จ",
        "data": build_cart_response(db, cart, student),
    }


@router.post("/cart/add", response_model=CartMessageResponse)
def add_cart_item(
    body: CartAddRequest,
    db: Session = Depends(get_db),
):
    if body.quantity <= 0:
        raise HTTPException(status_code=400, detail="จำนวนสินค้าต้องมากกว่า 0")

    student = get_student_by_code(db, body.student_code)

    product = (
        db.query(Product)
        .filter(Product.product_id == body.product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")

    if not product.is_active:
        raise HTTPException(status_code=400, detail="สินค้านี้ปิดการขายแล้ว")

    variant = None

    if product.has_variant:
        if body.variant_id is None:
            raise HTTPException(status_code=400, detail="กรุณาเลือกตัวเลือกสินค้า")

        variant = (
            db.query(ProductVariant)
            .filter(
                ProductVariant.variant_id == body.variant_id,
                ProductVariant.product_id == product.product_id,
            )
            .first()
        )

        if not variant:
            raise HTTPException(status_code=404, detail="ไม่พบตัวเลือกสินค้า")

        if not variant.is_active:
            raise HTTPException(status_code=400, detail="ตัวเลือกสินค้านี้ปิดการขายแล้ว")

        stock = variant.stock

    else:
        if body.variant_id is not None:
            raise HTTPException(status_code=400, detail="สินค้านี้ไม่มีตัวเลือกสินค้า")

        if product.base_price is None:
            raise HTTPException(status_code=400, detail="สินค้านี้ยังไม่ได้ตั้งราคา")

        stock = product.base_stock

    cart = get_or_create_cart(db, student)

    existing_item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.cart_id,
            CartItem.product_id == product.product_id,
            CartItem.variant_id == body.variant_id,
        )
        .first()
    )

    current_qty = existing_item.quantity if existing_item else 0
    next_qty = current_qty + body.quantity

    if next_qty > stock:
        raise HTTPException(status_code=400, detail="จำนวนสินค้าใน stock ไม่เพียงพอ")

    check_limited_product(
        db=db,
        student=student,
        product=product,
        add_quantity=next_qty,
    )

    now = get_unix_time()

    if existing_item:
        existing_item.quantity = next_qty
        existing_item.updated_at = now
    else:
        item = CartItem(
            cart_id=cart.cart_id,
            product_id=product.product_id,
            variant_id=body.variant_id,
            quantity=body.quantity,
            created_at=now,
            updated_at=now,
        )
        db.add(item)

    cart.updated_at = now

    db.commit()
    db.refresh(cart)

    return {
        "detail": "เพิ่มสินค้าลงตะกร้าสำเร็จ",
        "data": build_cart_response(db, cart, student),
    }


@router.patch("/cart/item/{cart_item_id}", response_model=CartMessageResponse)
def update_cart_item(
    cart_item_id: UUID,
    body: CartUpdateItemRequest,
    db: Session = Depends(get_db),
):
    if body.quantity <= 0:
        raise HTTPException(status_code=400, detail="จำนวนสินค้าต้องมากกว่า 0")

    item = (
        db.query(CartItem)
        .filter(CartItem.cart_item_id == cart_item_id)
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้าในตะกร้า")

    cart = db.query(Cart).filter(Cart.cart_id == item.cart_id).first()
    student = db.query(Student).filter(Student.student_id == cart.student_id).first()

    product = db.query(Product).filter(Product.product_id == item.product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")

    if product.has_variant:
        variant = db.query(ProductVariant).filter(ProductVariant.variant_id == item.variant_id).first()
        stock = variant.stock if variant else 0
    else:
        stock = product.base_stock

    if body.quantity > stock:
        raise HTTPException(status_code=400, detail="จำนวนสินค้าใน stock ไม่เพียงพอ")

    check_limited_product(
        db=db,
        student=student,
        product=product,
        add_quantity=body.quantity,
    )

    now = get_unix_time()

    item.quantity = body.quantity
    item.updated_at = now
    cart.updated_at = now

    db.commit()
    db.refresh(cart)

    return {
        "detail": "แก้ไขจำนวนสินค้าในตะกร้าสำเร็จ",
        "data": build_cart_response(db, cart, student),
    }


@router.delete("/cart/item/{cart_item_id}", response_model=CartMessageResponse)
def delete_cart_item(
    cart_item_id: UUID,
    db: Session = Depends(get_db),
):
    item = (
        db.query(CartItem)
        .filter(CartItem.cart_item_id == cart_item_id)
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้าในตะกร้า")

    cart = db.query(Cart).filter(Cart.cart_id == item.cart_id).first()
    student = db.query(Student).filter(Student.student_id == cart.student_id).first()

    db.delete(item)
    cart.updated_at = get_unix_time()

    db.commit()
    db.refresh(cart)

    return {
        "detail": "ลบสินค้าออกจากตะกร้าสำเร็จ",
        "data": build_cart_response(db, cart, student),
    }


@router.delete("/cart/clear/{student_code}", response_model=CartMessageResponse)
def clear_cart(
    student_code: str,
    db: Session = Depends(get_db),
):
    student = get_student_by_code(db, student_code)
    cart = get_or_create_cart(db, student)

    db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).delete()

    cart.updated_at = get_unix_time()

    db.commit()
    db.refresh(cart)

    return {
        "detail": "ล้างตะกร้าสำเร็จ",
        "data": build_cart_response(db, cart, student),
    }