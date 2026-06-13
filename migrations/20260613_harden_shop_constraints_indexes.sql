-- Run after 20260613_add_shop_tables.sql.
-- Resolve duplicate order payments or SKU values before running this migration.

CREATE UNIQUE INDEX IF NOT EXISTS uq_payments_order_id
ON payments (order_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_product_variants_sku_code
ON product_variants (sku_code)
WHERE sku_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_products_category_id
ON products (category_id);

CREATE INDEX IF NOT EXISTS ix_products_owner_type
ON products (owner_type);

CREATE INDEX IF NOT EXISTS ix_products_is_active
ON products (is_active);

CREATE INDEX IF NOT EXISTS ix_product_variants_product_id
ON product_variants (product_id);

CREATE INDEX IF NOT EXISTS ix_product_variants_is_active
ON product_variants (is_active);

CREATE INDEX IF NOT EXISTS ix_cart_items_cart_id
ON cart_items (cart_id);

CREATE INDEX IF NOT EXISTS ix_orders_student_id
ON orders (student_id);

CREATE INDEX IF NOT EXISTS ix_orders_order_status
ON orders (order_status);

CREATE INDEX IF NOT EXISTS ix_orders_payment_status
ON orders (payment_status);

CREATE INDEX IF NOT EXISTS ix_orders_created_at
ON orders (created_at DESC);

CREATE INDEX IF NOT EXISTS ix_order_items_order_id
ON order_items (order_id);

CREATE INDEX IF NOT EXISTS ix_order_items_product_id
ON order_items (product_id);

CREATE INDEX IF NOT EXISTS ix_payments_payment_status
ON payments (payment_status);

CREATE INDEX IF NOT EXISTS ix_stock_movements_product_id
ON stock_movements (product_id);

CREATE INDEX IF NOT EXISTS ix_stock_movements_variant_id
ON stock_movements (variant_id);

CREATE INDEX IF NOT EXISTS ix_stock_movements_ref_order_id
ON stock_movements (ref_order_id);

CREATE INDEX IF NOT EXISTS ix_stock_movements_created_at
ON stock_movements (created_at DESC);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_stock_movements_quantity'
    ) THEN
        ALTER TABLE stock_movements
        ADD CONSTRAINT chk_stock_movements_quantity
        CHECK (quantity > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_stock_movements_before_stock'
    ) THEN
        ALTER TABLE stock_movements
        ADD CONSTRAINT chk_stock_movements_before_stock
        CHECK (before_stock >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_stock_movements_after_stock'
    ) THEN
        ALTER TABLE stock_movements
        ADD CONSTRAINT chk_stock_movements_after_stock
        CHECK (after_stock >= 0);
    END IF;
END
$$;
