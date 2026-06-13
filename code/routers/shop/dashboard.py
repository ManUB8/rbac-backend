from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Order, OrderItem, Product, ProductVariant
from schemas.schemas_shop import ShopDashboardSummaryResponse

router = APIRouter(prefix="/shop/v1", tags=["Shop Admin Dashboard"])


def get_today_range_unix():
    tz = ZoneInfo("Asia/Bangkok")
    now = datetime.now(tz)

    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    return int(start.timestamp()), int(end.timestamp())


@router.get(
    "/admin/dashboard/summary",
    response_model=ShopDashboardSummaryResponse,
)
def get_shop_admin_dashboard_summary(
    db: Session = Depends(get_db),
):
    today_start, today_end = get_today_range_unix()

    total_sales = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.payment_status == "paid")
        .scalar()
        or 0
    )

    today_sales = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(
            Order.payment_status == "paid",
            Order.created_at >= today_start,
            Order.created_at <= today_end,
        )
        .scalar()
        or 0
    )

    total_orders = db.query(func.count(Order.order_id)).scalar() or 0

    waiting_payment_count = (
        db.query(func.count(Order.order_id))
        .filter(Order.payment_status == "waiting_payment")
        .scalar()
        or 0
    )

    paid_count = (
        db.query(func.count(Order.order_id))
        .filter(Order.order_status == "paid")
        .scalar()
        or 0
    )

    preparing_count = (
        db.query(func.count(Order.order_id))
        .filter(Order.order_status == "preparing")
        .scalar()
        or 0
    )

    ready_for_pickup_count = (
        db.query(func.count(Order.order_id))
        .filter(Order.order_status == "ready_for_pickup")
        .scalar()
        or 0
    )

    shipping_count = (
        db.query(func.count(Order.order_id))
        .filter(Order.order_status == "shipping")
        .scalar()
        or 0
    )

    completed_count = (
        db.query(func.count(Order.order_id))
        .filter(Order.order_status == "completed")
        .scalar()
        or 0
    )

    cancelled_count = (
        db.query(func.count(Order.order_id))
        .filter(Order.order_status == "cancelled")
        .scalar()
        or 0
    )

    low_stock_variants = (
        db.query(Product, ProductVariant)
        .join(ProductVariant, ProductVariant.product_id == Product.product_id)
        .filter(
            Product.has_variant == True,
            Product.is_active == True,
            ProductVariant.is_active == True,
            ProductVariant.stock <= 10,
        )
        .limit(10)
        .all()
    )

    low_stock_base_products = (
        db.query(Product)
        .filter(
            Product.has_variant == False,
            Product.is_active == True,
            Product.base_stock <= 10,
        )
        .limit(10)
        .all()
    )

    low_stock = []

    for product, variant in low_stock_variants:
        low_stock.append({
            "product_id": product.product_id,
            "product_name": product.product_name,
            "variant_id": variant.variant_id,
            "variant_name": variant.variant_name,
            "color_name": variant.color_name,
            "stock": variant.stock,
        })

    for product in low_stock_base_products:
        low_stock.append({
            "product_id": product.product_id,
            "product_name": product.product_name,
            "variant_id": None,
            "variant_name": None,
            "color_name": None,
            "stock": product.base_stock,
        })

    top_products = (
        db.query(
            Product.product_id,
            Product.product_name,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("sold_qty"),
            func.coalesce(func.sum(OrderItem.total_price), 0).label("sales_amount"),
        )
        .join(OrderItem, OrderItem.product_id == Product.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .filter(Order.payment_status == "paid")
        .group_by(Product.product_id, Product.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )

    top_product_list = [
        {
            "product_id": item.product_id,
            "product_name": item.product_name,
            "sold_qty": int(item.sold_qty or 0),
            "sales_amount": float(item.sales_amount or 0),
        }
        for item in top_products
    ]

    recent_orders = (
        db.query(Order)
        .order_by(Order.created_at.desc().nullslast())
        .limit(10)
        .all()
    )

    recent_order_list = [
        {
            "order_id": order.order_id,
            "order_no": order.order_no,
            "student_id": order.student_id,
            "total_amount": float(order.total_amount or 0),
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "delivery_type": order.delivery_type,
            "created_at": order.created_at,
        }
        for order in recent_orders
    ]

    return {
        "detail": "ดึงข้อมูล Dashboard ร้านค้าสำเร็จ",
        "data": {
            "sales": {
                "total_sales": float(total_sales),
                "today_sales": float(today_sales),
            },
            "orders": {
                "total_orders": total_orders,
                "waiting_payment_count": waiting_payment_count,
                "paid_count": paid_count,
                "preparing_count": preparing_count,
                "ready_for_pickup_count": ready_for_pickup_count,
                "shipping_count": shipping_count,
                "completed_count": completed_count,
                "cancelled_count": cancelled_count,
            },
            "low_stock": low_stock[:10],
            "top_products": top_product_list,
            "recent_orders": recent_order_list,
        },
    }