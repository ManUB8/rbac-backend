from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import StockMovement, Product, ProductVariant, User
from schemas.schemas_shop import (
    StockMovementSearchRequest,
    StockMovementListResponse,
)

router = APIRouter(prefix="/shop/v1", tags=["Shop Stock Movement"])


MOVEMENT_TYPE_LIST = [
    "increase",
    "decrease",
    "sale",
    "cancel_return",
    "adjust",
]


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
    "/admin/stock-movements/get-all",
    response_model=StockMovementListResponse,
)
def get_stock_movements_admin(
    body: StockMovementSearchRequest,
    db: Session = Depends(get_db),
):
    page = max(body.page, 1)
    limit = max(body.limit, 1)
    offset = (page - 1) * limit

    query = (
        db.query(StockMovement, Product, ProductVariant)
        .join(Product, Product.product_id == StockMovement.product_id)
        .outerjoin(ProductVariant, ProductVariant.variant_id == StockMovement.variant_id)
    )

    if body.product_id.strip() != "":
        query = query.filter(
            StockMovement.product_id == UUID(body.product_id)
        )

    if body.variant_id.strip() != "":
        query = query.filter(
            StockMovement.variant_id == UUID(body.variant_id)
        )

    if body.movement_type.strip() != "":
        if body.movement_type not in MOVEMENT_TYPE_LIST:
            raise HTTPException(status_code=400, detail="ประเภทการเคลื่อนไหว stock ไม่ถูกต้อง")

        query = query.filter(StockMovement.movement_type == body.movement_type)

    if body.search.strip() != "":
        search_text = f"%{body.search.strip()}%"
        query = query.filter(
            or_(
                Product.product_name.ilike(search_text),
                ProductVariant.variant_name.ilike(search_text),
                ProductVariant.color_name.ilike(search_text),
                StockMovement.note.ilike(search_text),
                StockMovement.created_by_name.ilike(search_text),
            )
        )

    total_all = query.count()

    rows = (
        query
        .order_by(StockMovement.created_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )

    data = []

    for movement, product, variant in rows:
        data.append({
            "stock_movement_id": movement.stock_movement_id,
            "product_id": movement.product_id,
            "variant_id": movement.variant_id,

            "product_name": product.product_name if product else None,
            "variant_name": variant.variant_name if variant else None,
            "color_name": variant.color_name if variant else None,

            "movement_type": movement.movement_type,
            "quantity": movement.quantity,
            "before_stock": movement.before_stock,
            "after_stock": movement.after_stock,

            "ref_order_id": movement.ref_order_id,
            "note": movement.note,

            "created_by_id": movement.created_by_id,
            "created_by_name": movement.created_by_name,
            "created_at": movement.created_at,
        })

    return {
        "detail": "ดึงประวัติการเคลื่อนไหว stock สำเร็จ",
        "total_all": total_all,
        "page": page,
        "limit": limit,
        "data": data,
    }