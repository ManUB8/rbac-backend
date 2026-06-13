CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS product_categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_name VARCHAR(150) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at BIGINT NULL,
    updated_at BIGINT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    product_name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    category_id UUID NULL,

    base_price NUMERIC(10,2) NULL,
    base_stock INT NOT NULL DEFAULT 0,

    owner_type VARCHAR(30) NOT NULL DEFAULT 'club',
    faculty_id INT NULL,
    major_id INT NULL,
    external_name VARCHAR(255) NULL,

    main_image TEXT NULL,
    product_images JSONB NULL,

    has_variant BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_limited BOOLEAN NOT NULL DEFAULT FALSE,
    limit_per_student INT NULL,

    weight_gram INT NULL,
    sold_count INT NOT NULL DEFAULT 0,

    created_by_id INT NULL,
    created_by_name VARCHAR(150) NULL,
    updated_by_id INT NULL,
    updated_by_name VARCHAR(150) NULL,
    created_at BIGINT NULL,
    updated_at BIGINT NULL,

    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id) REFERENCES product_categories(category_id),

    CONSTRAINT fk_products_faculty
        FOREIGN KEY (faculty_id) REFERENCES faculties(faculty_id),

    CONSTRAINT fk_products_major
        FOREIGN KEY (major_id) REFERENCES majors(major_id),

    CONSTRAINT chk_products_owner_type
        CHECK (owner_type IN ('club', 'faculty', 'major', 'external')),

    CONSTRAINT chk_products_base_price
        CHECK (base_price IS NULL OR base_price >= 0),

    CONSTRAINT chk_products_base_stock
        CHECK (base_stock >= 0),

    CONSTRAINT chk_products_limit_per_student
        CHECK (limit_per_student IS NULL OR limit_per_student > 0),

    CONSTRAINT chk_products_weight
        CHECK (weight_gram IS NULL OR weight_gram >= 0),

    CONSTRAINT chk_products_sold_count
        CHECK (sold_count >= 0),

    CONSTRAINT chk_products_variant_price_rule
        CHECK (
            (has_variant = TRUE)
            OR
            (has_variant = FALSE AND base_price IS NOT NULL)
        )
);

CREATE TABLE IF NOT EXISTS product_variants (
    variant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL,

    variant_name VARCHAR(100) NOT NULL DEFAULT 'Default',
    color_name VARCHAR(100) NULL,
    variant_image TEXT NULL,
    sku_code VARCHAR(100) NULL,

    price NUMERIC(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at BIGINT NULL,
    updated_at BIGINT NULL,

    CONSTRAINT fk_variants_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_product_variant_color
        UNIQUE (product_id, variant_name, color_name),

    CONSTRAINT chk_variants_price
        CHECK (price >= 0),

    CONSTRAINT chk_variants_stock
        CHECK (stock >= 0)
);

CREATE TABLE IF NOT EXISTS carts (
    cart_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id INT NOT NULL UNIQUE,

    created_at BIGINT NULL,
    updated_at BIGINT NULL,

    CONSTRAINT fk_carts_student
        FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cart_items (
    cart_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id UUID NOT NULL,
    product_id UUID NOT NULL,
    variant_id UUID NULL,
    quantity INT NOT NULL DEFAULT 1,

    created_at BIGINT NULL,
    updated_at BIGINT NULL,

    CONSTRAINT fk_cart_items_cart
        FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_cart_items_product
        FOREIGN KEY (product_id) REFERENCES products(product_id),

    CONSTRAINT fk_cart_items_variant
        FOREIGN KEY (variant_id) REFERENCES product_variants(variant_id),

    CONSTRAINT uq_cart_product_base
        UNIQUE (cart_id, product_id, variant_id),

    CONSTRAINT chk_cart_items_quantity
        CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_no VARCHAR(50) NOT NULL UNIQUE,

    student_id INT NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL DEFAULT 0,

    order_status VARCHAR(30) NOT NULL DEFAULT 'pending_payment',
    payment_status VARCHAR(30) NOT NULL DEFAULT 'waiting_payment',
    delivery_type VARCHAR(30) NOT NULL DEFAULT 'pickup',

    pickup_code VARCHAR(50) NULL,

    receiver_name VARCHAR(255) NULL,
    receiver_phone VARCHAR(50) NULL,
    shipping_address TEXT NULL,
    carrier VARCHAR(100) NULL,
    tracking_no VARCHAR(100) NULL,

    created_at BIGINT NULL,
    updated_at BIGINT NULL,

    CONSTRAINT fk_orders_student
        FOREIGN KEY (student_id) REFERENCES students(student_id),

    CONSTRAINT chk_orders_total_amount
        CHECK (total_amount >= 0),

    CONSTRAINT chk_orders_order_status
        CHECK (order_status IN (
            'pending_payment',
            'paid',
            'preparing',
            'ready_for_pickup',
            'shipping',
            'completed',
            'cancelled'
        )),

    CONSTRAINT chk_orders_payment_status
        CHECK (payment_status IN (
            'waiting_payment',
            'paid',
            'rejected',
            'expired',
            'cancelled'
        )),

    CONSTRAINT chk_orders_delivery_type
        CHECK (delivery_type IN ('pickup', 'shipping'))
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    order_id UUID NOT NULL,
    product_id UUID NOT NULL,
    variant_id UUID NULL,

    product_name_snapshot VARCHAR(255) NOT NULL,
    variant_name_snapshot VARCHAR(100) NULL,
    color_name_snapshot VARCHAR(100) NULL,

    price_snapshot NUMERIC(10,2) NOT NULL,
    quantity INT NOT NULL,
    total_price NUMERIC(10,2) NOT NULL,

    created_at BIGINT NULL,
    updated_at BIGINT NULL,

    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id) REFERENCES products(product_id),

    CONSTRAINT fk_order_items_variant
        FOREIGN KEY (variant_id) REFERENCES product_variants(variant_id),

    CONSTRAINT chk_order_items_price
        CHECK (price_snapshot >= 0),

    CONSTRAINT chk_order_items_quantity
        CHECK (quantity > 0),

    CONSTRAINT chk_order_items_total
        CHECK (total_price >= 0)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,

    amount NUMERIC(10,2) NOT NULL,
    promptpay_payload TEXT NULL,
    qr_code TEXT NULL,

    payment_status VARCHAR(30) NOT NULL DEFAULT 'waiting_payment',
    paid_at BIGINT NULL,

    created_at BIGINT NULL,
    updated_at BIGINT NULL,

    CONSTRAINT fk_payments_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_payments_amount
        CHECK (amount >= 0),

    CONSTRAINT chk_payments_status
        CHECK (payment_status IN (
            'waiting_payment',
            'paid',
            'rejected',
            'expired',
            'cancelled'
        ))
);

CREATE TABLE IF NOT EXISTS stock_movements (
    stock_movement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    product_id UUID NOT NULL,
    variant_id UUID NULL,

    movement_type VARCHAR(30) NOT NULL,
    quantity INT NOT NULL,

    before_stock INT NOT NULL,
    after_stock INT NOT NULL,

    ref_order_id UUID NULL,
    note TEXT NULL,

    created_by_id INT NULL,
    created_by_name VARCHAR(150) NULL,
    created_at BIGINT NULL,

    CONSTRAINT fk_stock_movements_product
        FOREIGN KEY (product_id) REFERENCES products(product_id),

    CONSTRAINT fk_stock_movements_variant
        FOREIGN KEY (variant_id) REFERENCES product_variants(variant_id),

    CONSTRAINT fk_stock_movements_order
        FOREIGN KEY (ref_order_id) REFERENCES orders(order_id),

    CONSTRAINT chk_stock_movements_type
        CHECK (movement_type IN (
            'increase',
            'decrease',
            'sale',
            'cancel_return',
            'adjust'
        ))
);