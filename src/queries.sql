-- ============================================
-- Forecast & Purchase Planning - SQL Queries
-- Used by the n8n MySQL nodes (main workflow +
-- "Forecast Calculation Engine" sub-workflow)
-- ============================================

-- 1. Get weekly sales (aggregated by product, last weeks)
SELECT
    product_id,
    DATE(DATE_SUB(sale_date, INTERVAL WEEKDAY(sale_date) DAY)) AS week_start,
    SUM(quantity) AS qty_sold
FROM sales
WHERE sale_date >= DATE_SUB(CURDATE(), INTERVAL 8 WEEK)
GROUP BY product_id, week_start
ORDER BY product_id, week_start;

-- 2. Get latest inventory snapshot per product (joined with product/supplier data)
SELECT
    p.product_id,
    p.sku,
    p.name,
    p.supplier_id,
    p.lead_time_days,
    p.unit_cost,
    i.quantity AS on_hand,
    i.snapshot_date
FROM inventory_snapshots i
JOIN products p ON p.product_id = i.product_id
WHERE i.snapshot_date = (
    SELECT MAX(snapshot_date)
    FROM inventory_snapshots
    WHERE product_id = i.product_id
);

-- 3. Upsert forecast results
-- (written by the sub-workflow's output, one row per product per week)
INSERT INTO forecasts (product_id, forecast_date, forecast_qty, method)
VALUES (?, CURDATE(), ?, 'moving_average_1w')
ON DUPLICATE KEY UPDATE
    forecast_qty = VALUES(forecast_qty),
    method = VALUES(method);

-- 4. Upsert purchase plan
INSERT INTO purchase_plan (
    product_id, supplier_id, plan_date,
    quantity, unit_cost, lead_time_days
)
VALUES (?, ?, CURDATE(), ?, ?, ?)
ON DUPLICATE KEY UPDATE
    quantity = VALUES(quantity),
    unit_cost = VALUES(unit_cost);

-- 5. Get current planning snapshot for the dashboard / notifications
-- (consumed by the Streamlit dashboard and by the AI Agent context)
SELECT
    p.product_id,
    p.name,
    p.sku,
    i.quantity        AS current_stock,
    f.forecast_qty,
    f.forecast_date,
    pp.quantity       AS purchase_qty,
    pp.unit_cost,
    pp.lead_time_days
FROM forecasts f
JOIN products p
    ON f.product_id = p.product_id
LEFT JOIN purchase_plan pp
    ON f.product_id = pp.product_id
    AND f.forecast_date = pp.plan_date
LEFT JOIN inventory_snapshots i
    ON f.product_id = i.product_id
    AND i.snapshot_date = (
        SELECT MAX(snapshot_date) FROM inventory_snapshots
        WHERE product_id = i.product_id
    )
WHERE f.forecast_date = (SELECT MAX(forecast_date) FROM forecasts)
ORDER BY pp.quantity DESC;
