-- ============================================
-- Forecast & Purchase Planning - SQL Queries
-- Used by n8n MySQL nodes
-- ============================================

-- 1. Get weekly sales (aggregated by product)
SELECT
    product_id,
    product_name,
    YEARWEEK(sale_date) AS sale_week,
    SUM(quantity) AS weekly_quantity,
    SUM(total_amount) AS weekly_revenue
FROM sales
GROUP BY product_id, product_name, YEARWEEK(sale_date)
ORDER BY product_id, sale_week;

-- 2. Get latest inventory snapshot per product
SELECT
    i.product_id,
    p.product_name,
    i.quantity AS current_stock,
    i.snapshot_date
FROM inventory_snapshots i
JOIN products p ON i.product_id = p.product_id
WHERE i.snapshot_date = (
    SELECT MAX(snapshot_date)
    FROM inventory_snapshots
    WHERE product_id = i.product_id
);

-- 3. Upsert forecast results
INSERT INTO forecasts (product_id, forecast_date, forecast_qty, method)
VALUES (?, CURDATE(), ?, 'moving_average')
ON DUPLICATE KEY UPDATE
    forecast_qty = VALUES(forecast_qty),
    method = VALUES(method);

-- 4. Upsert purchase plan
INSERT INTO purchase_plan (
    product_id, supplier_id, plan_date,
    quantity, unit_cost, lead_time_weeks
)
VALUES (?, ?, CURDATE(), ?, ?, ?)
ON DUPLICATE KEY UPDATE
    quantity = VALUES(quantity),
    unit_cost = VALUES(unit_cost);

-- 5. Get consolidated report for Telegram notification
SELECT
    f.product_id,
    p.product_name,
    f.forecast_qty,
    pp.quantity AS purchase_qty,
    pp.unit_cost,
    pp.lead_time_weeks,
    i.quantity AS current_stock
FROM forecasts f
JOIN products p ON f.product_id = p.product_id
JOIN purchase_plan pp ON f.product_id = pp.product_id
    AND f.forecast_date = pp.plan_date
JOIN inventory_snapshots i ON f.product_id = i.product_id
WHERE f.forecast_date = CURDATE()
  AND pp.quantity > 0;
