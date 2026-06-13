from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ProductCategory, User
from schemas.schemas_shop import (
    ProductCategoryCreateRequest,
    ProductCategoryUpdateRequest,
    ProductCategoryMessageResponse,
    ProductCategoryListResponse,
)

import time

router = APIRouter(prefix="/shop/v1", tags=["Shop Category"])


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


@router.post(
    "/admin/categories/create",
    response_model=ProductCategoryMessageResponse,
)
def create_product_category(
    body: ProductCategoryCreateRequest,
    db: Session = Depends(get_db),
):
    admin = get_admin_by_name(db, body.created_by_name)

    category_name = body.category_name.strip()

    if category_name == "":
        raise HTTPException(status_code=400, detail="กรุณาระบุชื่อหมวดหมู่สินค้า")

    existing = (
        db.query(ProductCategory)
        .filter(ProductCategory.category_name == category_name)
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="ชื่อหมวดหมู่นี้มีอยู่แล้ว")

    now = get_unix_time()

    category = ProductCategory(
        category_name=category_name,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return {
        "detail": "สร้างหมวดหมู่สินค้าสำเร็จ",
        "data": category,
    }


@router.patch(
    "/admin/categories/update/{category_id}",
    response_model=ProductCategoryMessageResponse,
)
def update_product_category(
    category_id: str,
    body: ProductCategoryUpdateRequest,
    db: Session = Depends(get_db),
):
    get_admin_by_name(db, body.updated_by_name)

    category = (
        db.query(ProductCategory)
        .filter(ProductCategory.category_id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(status_code=404, detail="ไม่พบหมวดหมู่สินค้า")

    if body.category_name is not None:
        new_name = body.category_name.strip()

        if new_name == "":
            raise HTTPException(status_code=400, detail="กรุณาระบุชื่อหมวดหมู่สินค้า")

        duplicate = (
            db.query(ProductCategory)
            .filter(
                ProductCategory.category_name == new_name,
                ProductCategory.category_id != category.category_id,
            )
            .first()
        )

        if duplicate:
            raise HTTPException(status_code=400, detail="ชื่อหมวดหมู่นี้มีอยู่แล้ว")

        category.category_name = new_name

    if body.is_active is not None:
        category.is_active = body.is_active

    category.updated_at = get_unix_time()

    db.commit()
    db.refresh(category)

    return {
        "detail": "แก้ไขหมวดหมู่สินค้าสำเร็จ",
        "data": category,
    }


@router.get(
    "/get-all/categories",
    response_model=ProductCategoryListResponse,
)
def get_product_categories(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(ProductCategory)

    if active_only:
        query = query.filter(ProductCategory.is_active == True)

    categories = query.order_by(ProductCategory.category_name.asc()).all()

    return {
        "detail": "ดึงหมวดหมู่สินค้าสำเร็จ",
        "data": categories,
    }