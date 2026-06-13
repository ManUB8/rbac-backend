from uuid import UUID
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Product, ProductVariant, StockMovement, User
from schemas.schemas_shop import (
    ProductVariantCreateRequest,
    ProductVariantUpdateRequest,
    ProductVariantStockRequest,
    ProductVariantMessageResponse,
    ProductVariantListResponse,
)


router = APIRouter(prefix="/shop/v1", tags=["Shop Variant"])


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


def validate_variant_data(
    variant_name: str,
    price,
    stock: int,
):
    if variant_name is None or variant_name.strip() == "":
        raise HTTPException(status_code=400, detail="กรุณาระบุชื่อตัวเลือกสินค้า")

    if price is None or price < 0:
        raise HTTPException(status_code=400, detail="ราคาตัวเลือกสินค้าต้องไม่ติดลบ")

    if stock is None or stock < 0:
        raise HTTPException(status_code=400, detail="จำนวน stock ต้องไม่ติดลบ")


@router.post(
    "/admin/products/{product_id}/variants/create",
    response_model=ProductVariantMessageResponse,
)
def create_product_variant(
    product_id: UUID,
    body: ProductVariantCreateRequest,
    db: Session = Depends(get_db),
):
    get_admin_by_name(db, body.created_by_name)

    product = (
        db.query(Product)
        .filter(Product.product_id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")

    validate_variant_data(
        variant_name=body.variant_name,
        price=body.price,
        stock=body.stock,
    )

    variant_name = body.variant_name.strip()
    color_name = body.color_name.strip() if body.color_name else None

    duplicate = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.product_id == product.product_id,
            ProductVariant.variant_name == variant_name,
            ProductVariant.color_name == color_name,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=400,
            detail="ตัวเลือกสินค้านี้มีอยู่แล้ว"
        )

    now = get_unix_time()

    variant = ProductVariant(
        product_id=product.product_id,
        variant_name=variant_name,
        color_name=color_name,
        variant_image=body.variant_image,
        sku_code=body.sku_code,
        price=body.price,
        stock=body.stock,
        is_active=body.is_active,
        created_at=now,
        updated_at=now,
    )

    product.has_variant = True
    product.updated_at = now

    db.add(variant)
    db.commit()
    db.refresh(variant)

    return {
        "detail": "สร้างตัวเลือกสินค้าสำเร็จ",
        "data": variant,
    }


@router.get(
    "/products/{product_id}/variants",
    response_model=ProductVariantListResponse,
)
def get_product_variants(
    product_id: UUID,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(Product.product_id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")

    query = db.query(ProductVariant).filter(ProductVariant.product_id == product_id)

    if active_only:
        query = query.filter(ProductVariant.is_active == True)

    variants = (
        query
        .order_by(ProductVariant.color_name.asc().nullslast(), ProductVariant.variant_name.asc())
        .all()
    )

    return {
        "detail": "ดึงตัวเลือกสินค้าสำเร็จ",
        "data": variants,
    }


@router.patch(
    "/admin/variants/{variant_id}",
    response_model=ProductVariantMessageResponse,
)
def update_product_variant(
    variant_id: UUID,
    body: ProductVariantUpdateRequest,
    db: Session = Depends(get_db),
):
    get_admin_by_name(db, body.updated_by_name)

    variant = (
        db.query(ProductVariant)
        .filter(ProductVariant.variant_id == variant_id)
        .first()
    )

    if not variant:
        raise HTTPException(status_code=404, detail="ไม่พบตัวเลือกสินค้า")

    update_data = body.model_dump(exclude_unset=True)

    next_variant_name = update_data.get("variant_name", variant.variant_name)
    next_color_name = update_data.get("color_name", variant.color_name)
    next_price = update_data.get("price", variant.price)
    next_stock = update_data.get("stock", variant.stock)

    validate_variant_data(
        variant_name=next_variant_name,
        price=next_price,
        stock=next_stock,
    )

    clean_variant_name = next_variant_name.strip()
    clean_color_name = next_color_name.strip() if next_color_name else None

    duplicate = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.product_id == variant.product_id,
            ProductVariant.variant_name == clean_variant_name,
            ProductVariant.color_name == clean_color_name,
            ProductVariant.variant_id != variant.variant_id,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=400,
            detail="ตัวเลือกสินค้านี้มีอยู่แล้ว"
        )

    ignore_fields = {"updated_by_name"}

    for key, value in update_data.items():
        if key in ignore_fields:
            continue

        if key == "variant_name" and value is not None:
            value = value.strip()

        if key == "color_name" and value is not None:
            value = value.strip()

        setattr(variant, key, value)

    variant.updated_at = get_unix_time()

    db.commit()
    db.refresh(variant)

    return {
        "detail": "แก้ไขตัวเลือกสินค้าสำเร็จ",
        "data": variant,
    }


@router.patch(
    "/admin/variants/{variant_id}/stock",
    response_model=ProductVariantMessageResponse,
)
def update_variant_stock(
    variant_id: UUID,
    body: ProductVariantStockRequest,
    db: Session = Depends(get_db),
):
    admin = get_admin_by_name(db, body.updated_by_name)

    variant = (
        db.query(ProductVariant)
        .filter(ProductVariant.variant_id == variant_id)
        .first()
    )

    if not variant:
        raise HTTPException(status_code=404, detail="ไม่พบตัวเลือกสินค้า")

    if body.quantity <= 0:
        raise HTTPException(status_code=400, detail="จำนวนต้องมากกว่า 0")

    if body.movement_type not in ["increase", "decrease", "adjust"]:
        raise HTTPException(status_code=400, detail="ประเภทการปรับ stock ไม่ถูกต้อง")

    before_stock = variant.stock

    if body.movement_type == "increase":
        after_stock = before_stock + body.quantity

    elif body.movement_type == "decrease":
        after_stock = before_stock - body.quantity
        if after_stock < 0:
            raise HTTPException(status_code=400, detail="stock ไม่พอสำหรับการลดจำนวน")

    else:
        # adjust = ตั้ง stock เป็น quantity
        after_stock = body.quantity

    now = get_unix_time()

    variant.stock = after_stock
    variant.updated_at = now

    stock_movement = StockMovement(
        product_id=variant.product_id,
        variant_id=variant.variant_id,
        movement_type=body.movement_type,
        quantity=body.quantity,
        before_stock=before_stock,
        after_stock=after_stock,
        note=body.note,
        created_by_id=admin.user_id,
        created_by_name=admin.name,
        created_at=now,
    )

    db.add(stock_movement)
    db.commit()
    db.refresh(variant)

    return {
        "detail": "ปรับ stock สำเร็จ",
        "data": variant,
    }