from typing import Optional
from uuid import UUID
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func

from database import get_db
from models import (
    Product,
    ProductVariant,
    ProductCategory,
    Faculty,
    Major,
    User,
)
from schemas.schemas_shop import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductMessageResponse,
    ProductListResponse,
    ProductWithVariantsListResponse,
    ProductWithVariantsMessageResponse,
)


router = APIRouter(prefix="/shop/v1", tags=["Shop Product"])


OWNER_TYPE_LIST = ["club", "faculty", "major", "external"]


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


def validate_owner_data(
    db: Session,
    owner_type: str,
    faculty_id: Optional[int],
    major_id: Optional[int],
    external_name: Optional[str],
):
    if owner_type not in OWNER_TYPE_LIST:
        raise HTTPException(status_code=400, detail="ประเภทเจ้าของสินค้าไม่ถูกต้อง")

    if owner_type == "club":
        return

    if owner_type == "faculty":
        if faculty_id is None:
            raise HTTPException(status_code=400, detail="กรุณาระบุคณะของสินค้า")

        faculty = db.query(Faculty).filter(Faculty.faculty_id == faculty_id).first()

        if not faculty:
            raise HTTPException(status_code=404, detail="ไม่พบคณะ")

        return

    if owner_type == "major":
        if faculty_id is None:
            raise HTTPException(status_code=400, detail="กรุณาระบุคณะของสินค้า")

        if major_id is None:
            raise HTTPException(status_code=400, detail="กรุณาระบุสาขาของสินค้า")

        faculty = db.query(Faculty).filter(Faculty.faculty_id == faculty_id).first()

        if not faculty:
            raise HTTPException(status_code=404, detail="ไม่พบคณะ")

        major = db.query(Major).filter(Major.major_id == major_id).first()

        if not major:
            raise HTTPException(status_code=404, detail="ไม่พบสาขา")

        if major.faculty_id != faculty_id:
            raise HTTPException(status_code=400, detail="สาขาไม่ตรงกับคณะ")

        return

    if owner_type == "external":
        if external_name is None or external_name.strip() == "":
            raise HTTPException(status_code=400, detail="กรุณาระบุชื่อร้านค้าภายนอก")

        return


def validate_product_data(
    db: Session,
    product_name: str,
    category_id: Optional[UUID],
    has_variant: bool,
    base_price,
    base_stock: Optional[int],
    owner_type: str,
    faculty_id: Optional[int],
    major_id: Optional[int],
    external_name: Optional[str],
    is_limited: bool,
    limit_per_student: Optional[int],
    weight_gram: Optional[int],
):
    if product_name.strip() == "":
        raise HTTPException(status_code=400, detail="กรุณาระบุชื่อสินค้า")

    if category_id is not None:
        category = (
            db.query(ProductCategory)
            .filter(ProductCategory.category_id == category_id)
            .first()
        )

        if not category:
            raise HTTPException(status_code=404, detail="ไม่พบหมวดหมู่สินค้า")

    if not has_variant:
        if base_price is None:
            raise HTTPException(status_code=400, detail="สินค้าที่ไม่มีตัวเลือกต้องระบุราคาเริ่มต้น")

        if base_price < 0:
            raise HTTPException(status_code=400, detail="ราคาสินค้าต้องไม่ติดลบ")

        if base_stock is None or base_stock < 0:
            raise HTTPException(status_code=400, detail="จำนวนสินค้าในสต๊อกต้องไม่ติดลบ")

    if has_variant:
        # ถ้ามี variant จริง ราคา/stock จะไปอยู่ใน product_variants
        # base_price จะไม่บังคับ
        if base_stock is not None and base_stock < 0:
            raise HTTPException(status_code=400, detail="จำนวนสินค้าในสต๊อกต้องไม่ติดลบ")

    validate_owner_data(
        db=db,
        owner_type=owner_type,
        faculty_id=faculty_id,
        major_id=major_id,
        external_name=external_name,
    )

    if is_limited:
        if limit_per_student is None or limit_per_student <= 0:
            raise HTTPException(
                status_code=400,
                detail="สินค้า Limited ต้องระบุจำนวนจำกัดต่อคนมากกว่า 0"
            )

    if limit_per_student is not None and limit_per_student <= 0:
        raise HTTPException(status_code=400, detail="limit_per_student ต้องมากกว่า 0")

    if weight_gram is not None and weight_gram < 0:
        raise HTTPException(status_code=400, detail="น้ำหนักสินค้าต้องไม่ติดลบ")


@router.post(
    "/admin/products/create",
    response_model=ProductMessageResponse,
)
def create_product(
    body: ProductCreateRequest,
    db: Session = Depends(get_db),
):
    admin = get_admin_by_name(db, body.created_by_name)

    validate_product_data(
        db=db,
        product_name=body.product_name,
        category_id=body.category_id,
        has_variant=body.has_variant,
        base_price=body.base_price,
        base_stock=body.base_stock,
        owner_type=body.owner_type,
        faculty_id=body.faculty_id,
        major_id=body.major_id,
        external_name=body.external_name,
        is_limited=body.is_limited,
        limit_per_student=body.limit_per_student,
        weight_gram=body.weight_gram,
    )

    now = get_unix_time()

    product = Product(
        product_name=body.product_name.strip(),
        description=body.description,
        category_id=body.category_id,

        base_price=body.base_price,
        base_stock=body.base_stock,

        owner_type=body.owner_type,
        faculty_id=body.faculty_id,
        major_id=body.major_id,
        external_name=body.external_name.strip() if body.external_name else None,

        main_image=body.main_image,
        product_images=body.product_images,

        has_variant=body.has_variant,
        is_active=body.is_active,
        is_limited=body.is_limited,
        limit_per_student=body.limit_per_student,

        weight_gram=body.weight_gram,
        sold_count=0,

        created_by_id=admin.user_id,
        created_by_name=admin.name,
        updated_by_id=admin.user_id,
        updated_by_name=admin.name,
        created_at=now,
        updated_at=now,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return {
        "detail": "สร้างสินค้าสำเร็จ",
        "data": product,
    }


@router.patch(
    "/admin/products/update/{product_id}",
    response_model=ProductMessageResponse,
)
def update_product(
    product_id: UUID,
    body: ProductUpdateRequest,
    db: Session = Depends(get_db),
):
    admin = get_admin_by_name(db, body.updated_by_name)

    product = (
        db.query(Product)
        .filter(Product.product_id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")

    update_data = body.model_dump(exclude_unset=True)

    next_product_name = update_data.get("product_name", product.product_name)
    next_category_id = update_data.get("category_id", product.category_id)
    next_has_variant = update_data.get("has_variant", product.has_variant)
    next_base_price = update_data.get("base_price", product.base_price)
    next_base_stock = update_data.get("base_stock", product.base_stock)
    next_owner_type = update_data.get("owner_type", product.owner_type)
    next_faculty_id = update_data.get("faculty_id", product.faculty_id)
    next_major_id = update_data.get("major_id", product.major_id)
    next_external_name = update_data.get("external_name", product.external_name)
    next_is_limited = update_data.get("is_limited", product.is_limited)
    next_limit_per_student = update_data.get("limit_per_student", product.limit_per_student)
    next_weight_gram = update_data.get("weight_gram", product.weight_gram)

    validate_product_data(
        db=db,
        product_name=next_product_name,
        category_id=next_category_id,
        has_variant=next_has_variant,
        base_price=next_base_price,
        base_stock=next_base_stock,
        owner_type=next_owner_type,
        faculty_id=next_faculty_id,
        major_id=next_major_id,
        external_name=next_external_name,
        is_limited=next_is_limited,
        limit_per_student=next_limit_per_student,
        weight_gram=next_weight_gram,
    )

    ignore_fields = {"updated_by_name"}

    for key, value in update_data.items():
        if key in ignore_fields:
            continue

        if key == "product_name" and value is not None:
            value = value.strip()

        if key == "external_name" and value is not None:
            value = value.strip()

        setattr(product, key, value)

    product.updated_by_id = admin.user_id
    product.updated_by_name = admin.name
    product.updated_at = get_unix_time()

    db.commit()
    db.refresh(product)

    return {
        "detail": "แก้ไขสินค้าสำเร็จ",
        "data": product,
    }


@router.get(
    "/products",
    response_model=ProductListResponse,
)
def get_products(
    search: str = "",
    category_id: Optional[UUID] = Query(default=None),
    owner_type: str = "",
    faculty_id: Optional[int] = Query(default=None),
    major_id: Optional[int] = Query(default=None),
    is_limited: Optional[bool] = Query(default=None),
    active_only: bool = True,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    page = max(page, 1)
    limit = max(limit, 1)
    offset = (page - 1) * limit

    query = db.query(Product)

    if active_only:
        query = query.filter(Product.is_active == True)

    if search.strip() != "":
        search_text = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.product_name.ilike(search_text),
                Product.description.ilike(search_text),
                Product.external_name.ilike(search_text),
            )
        )

    if category_id is not None:
        query = query.filter(Product.category_id == category_id)

    if owner_type.strip() != "":
        if owner_type not in OWNER_TYPE_LIST:
            raise HTTPException(status_code=400, detail="ประเภทเจ้าของสินค้าไม่ถูกต้อง")

        query = query.filter(Product.owner_type == owner_type)

    if faculty_id is not None:
        query = query.filter(Product.faculty_id == faculty_id)

    if major_id is not None:
        query = query.filter(Product.major_id == major_id)

    if is_limited is not None:
        query = query.filter(Product.is_limited == is_limited)

    total_all = query.count()

    products = (
        query
        .order_by(Product.created_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "detail": "ดึงรายการสินค้าสำเร็จ",
        "total_all": total_all,
        "page": page,
        "limit": limit,
        "data": products,
    }


@router.get(
    "/products-first/{product_id}",
    response_model=ProductMessageResponse,
)
def get_product_detail(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(Product.product_id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")

    return {
        "detail": "ดึงข้อมูลสินค้าสำเร็จ",
        "data": product,
    }
    
@router.get(
    "/products/{product_id}",
    response_model=ProductWithVariantsMessageResponse,
)
def get_product_detail(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(Product.product_id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")

    variants = (
        db.query(ProductVariant)
        .filter(ProductVariant.product_id == product.product_id)
        .order_by(
            ProductVariant.color_name.asc().nullslast(),
            ProductVariant.variant_name.asc(),
        )
        .all()
    )

    return {
        "detail": "ดึงข้อมูลสินค้าสำเร็จ",
        "data": build_product_with_variants(product, variants),
    }
    
def build_product_with_variants(product: Product, variants: list[ProductVariant]):
    active_variants = [v for v in variants if v.is_active]

    if product.has_variant:
        prices = [v.price for v in active_variants]
        total_stock = sum(v.stock or 0 for v in active_variants)

        min_price = min(prices) if prices else None
        max_price = max(prices) if prices else None
    else:
        min_price = product.base_price
        max_price = product.base_price
        total_stock = product.base_stock or 0

    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "description": product.description,
        "category_id": product.category_id,

        "base_price": product.base_price,
        "base_stock": product.base_stock,

        "owner_type": product.owner_type,
        "faculty_id": product.faculty_id,
        "major_id": product.major_id,
        "external_name": product.external_name,

        "main_image": product.main_image,
        "product_images": product.product_images,

        "has_variant": product.has_variant,
        "is_active": product.is_active,
        "is_limited": product.is_limited,
        "limit_per_student": product.limit_per_student,

        "weight_gram": product.weight_gram,
        "sold_count": product.sold_count,

        "min_price": min_price,
        "max_price": max_price,
        "total_stock": total_stock,

        "variants": active_variants,

        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }