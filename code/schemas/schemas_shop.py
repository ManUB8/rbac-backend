from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class ProductCategoryCreateRequest(BaseModel):
    category_name: str
    created_by_name: str


class ProductCategoryUpdateRequest(BaseModel):
    category_name: Optional[str] = None
    is_active: Optional[bool] = None
    updated_by_name: str


class ProductCategoryItemResponse(BaseModel):
    category_id: UUID
    category_name: str
    is_active: bool
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    class Config:
        from_attributes = True


class ProductCategoryMessageResponse(BaseModel):
    detail: str
    data: Optional[ProductCategoryItemResponse] = None


class ProductCategoryListResponse(BaseModel):
    detail: str
    data: List[ProductCategoryItemResponse]
    
from decimal import Decimal
from typing import Any


class ProductCreateRequest(BaseModel):
    product_name: str
    description: Optional[str] = None
    category_id: Optional[UUID] = None

    base_price: Optional[Decimal] = None
    base_stock: int = 0

    owner_type: str = "club"  # club | faculty | major | external
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    external_name: Optional[str] = None

    main_image: Optional[str] = None
    product_images: Optional[List[str]] = None

    has_variant: bool = False
    is_active: bool = True
    is_limited: bool = False
    limit_per_student: Optional[int] = None

    weight_gram: Optional[int] = None
    created_by_name: str


class ProductUpdateRequest(BaseModel):
    product_name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None

    base_price: Optional[Decimal] = None
    base_stock: Optional[int] = None

    owner_type: Optional[str] = None
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    external_name: Optional[str] = None

    main_image: Optional[str] = None
    product_images: Optional[List[str]] = None

    has_variant: Optional[bool] = None
    is_active: Optional[bool] = None
    is_limited: Optional[bool] = None
    limit_per_student: Optional[int] = None

    weight_gram: Optional[int] = None
    updated_by_name: str


class ProductItemResponse(BaseModel):
    product_id: UUID
    product_name: str
    description: Optional[str] = None
    category_id: Optional[UUID] = None

    base_price: Optional[Decimal] = None
    base_stock: int

    owner_type: str
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    external_name: Optional[str] = None

    main_image: Optional[str] = None
    product_images: Optional[List[str]] = None

    has_variant: bool
    is_active: bool
    is_limited: bool
    limit_per_student: Optional[int] = None

    weight_gram: Optional[int] = None
    sold_count: int

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    class Config:
        from_attributes = True


class ProductMessageResponse(BaseModel):
    detail: str
    data: Optional[ProductItemResponse] = None


class ProductListResponse(BaseModel):
    detail: str
    total_all: int
    page: int
    limit: int
    data: List[ProductItemResponse]
    
class ProductVariantCreateRequest(BaseModel):
    variant_name: str = "Default"
    color_name: Optional[str] = None
    variant_image: Optional[str] = None
    sku_code: Optional[str] = None
    price: Decimal
    stock: int = 0
    is_active: bool = True
    created_by_name: str


class ProductVariantUpdateRequest(BaseModel):
    variant_name: Optional[str] = None
    color_name: Optional[str] = None
    variant_image: Optional[str] = None
    sku_code: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None
    updated_by_name: str


class ProductVariantStockRequest(BaseModel):
    movement_type: str  # increase | decrease | adjust
    quantity: int
    note: Optional[str] = None
    updated_by_name: str


class ProductVariantItemResponse(BaseModel):
    variant_id: UUID
    product_id: UUID
    variant_name: str
    color_name: Optional[str] = None
    variant_image: Optional[str] = None
    sku_code: Optional[str] = None
    price: Decimal
    stock: int
    is_active: bool
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    class Config:
        from_attributes = True


class ProductVariantMessageResponse(BaseModel):
    detail: str
    data: Optional[ProductVariantItemResponse] = None


class ProductVariantListResponse(BaseModel):
    detail: str
    data: List[ProductVariantItemResponse]
    
class ProductVariantInProductResponse(BaseModel):
    variant_id: UUID
    variant_name: str
    color_name: Optional[str] = None
    variant_image: Optional[str] = None
    sku_code: Optional[str] = None
    price: Decimal
    stock: int
    is_active: bool

    class Config:
        from_attributes = True


class ProductWithVariantsResponse(BaseModel):
    product_id: UUID
    product_name: str
    description: Optional[str] = None
    category_id: Optional[UUID] = None

    base_price: Optional[Decimal] = None
    base_stock: int

    owner_type: str
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    external_name: Optional[str] = None

    main_image: Optional[str] = None
    product_images: Optional[List[str]] = None

    has_variant: bool
    is_active: bool
    is_limited: bool
    limit_per_student: Optional[int] = None

    weight_gram: Optional[int] = None
    sold_count: int

    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    total_stock: int = 0

    variants: List[ProductVariantInProductResponse] = []

    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    class Config:
        from_attributes = True


class ProductWithVariantsListResponse(BaseModel):
    detail: str
    total_all: int
    page: int
    limit: int
    data: List[ProductWithVariantsResponse]


class ProductWithVariantsMessageResponse(BaseModel):
    detail: str
    data: Optional[ProductWithVariantsResponse] = None
    
class CartAddRequest(BaseModel):
    student_code: str
    product_id: UUID
    variant_id: Optional[UUID] = None
    quantity: int = 1


class CartUpdateItemRequest(BaseModel):
    student_code: str
    quantity: int


class CartItemResponse(BaseModel):
    cart_item_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None

    product_name: str
    main_image: Optional[str] = None

    variant_name: Optional[str] = None
    color_name: Optional[str] = None
    variant_image: Optional[str] = None

    price: Decimal
    quantity: int
    total_price: Decimal
    stock: int

    class Config:
        from_attributes = True


class CartResponseData(BaseModel):
    cart_id: UUID
    student_id: int
    student_code: str
    total_amount: Decimal
    total_items: int
    items: List[CartItemResponse]


class CartMessageResponse(BaseModel):
    detail: str
    data: Optional[CartResponseData] = None

# Order
class OrderCreateRequest(BaseModel):
    student_code: str
    delivery_type: str = "pickup"  # pickup | shipping
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    shipping_address: Optional[str] = None


class OrderCancelRequest(BaseModel):
    student_code: str
    reason: Optional[str] = None


class OrderItemResponse(BaseModel):
    order_item_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    product_name_snapshot: str
    variant_name_snapshot: Optional[str] = None
    color_name_snapshot: Optional[str] = None
    price_snapshot: Decimal
    quantity: int
    total_price: Decimal

    class Config:
        from_attributes = True


class PaymentItemResponse(BaseModel):
    payment_id: UUID
    order_id: UUID
    amount: Decimal
    promptpay_payload: Optional[str] = None
    qr_code: Optional[str] = None
    payment_status: str
    paid_at: Optional[int] = None

    class Config:
        from_attributes = True


class OrderDetailResponseData(BaseModel):
    order_id: UUID
    order_no: str
    student_id: int
    total_amount: Decimal
    order_status: str
    payment_status: str
    delivery_type: str
    pickup_code: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    shipping_address: Optional[str] = None
    carrier: Optional[str] = None
    tracking_no: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    items: List[OrderItemResponse]
    payment: Optional[PaymentItemResponse] = None

    class Config:
        from_attributes = True


class OrderMessageResponse(BaseModel):
    detail: str
    data: Optional[OrderDetailResponseData] = None


class OrderListResponse(BaseModel):
    detail: str
    data: List[OrderDetailResponseData]


# Admin
class AdminOrderSearchRequest(BaseModel):
    search: str = ""
    student_code: str = ""
    order_status: str = ""
    payment_status: str = ""
    delivery_type: str = ""
    page: int = 1
    limit: int = 20


class AdminConfirmPaymentRequest(BaseModel):
    updated_by_name: str


class AdminUpdateOrderStatusRequest(BaseModel):
    order_status: str
    updated_by_name: str


class AdminUpdateShippingRequest(BaseModel):
    carrier: Optional[str] = None
    tracking_no: Optional[str] = None
    updated_by_name: str


# Dashboard
class ShopDashboardSummaryResponse(BaseModel):
    detail: str
    data: dict


# Stock Movement
class StockMovementSearchRequest(BaseModel):
    product_id: str = ""
    variant_id: str = ""
    movement_type: str = ""
    search: str = ""
    page: int = 1
    limit: int = 20


class StockMovementItemResponse(BaseModel):
    stock_movement_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None

    product_name: Optional[str] = None
    variant_name: Optional[str] = None
    color_name: Optional[str] = None

    movement_type: str
    quantity: int
    before_stock: int
    after_stock: int

    ref_order_id: Optional[UUID] = None
    note: Optional[str] = None

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: Optional[int] = None

    class Config:
        from_attributes = True


class StockMovementListResponse(BaseModel):
    detail: str
    total_all: int
    page: int
    limit: int
    data: List[StockMovementItemResponse]
