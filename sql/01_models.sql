-- DECIMAL retains the four-decimal precision present in the source price field.
CREATE OR REPLACE TABLE lines AS
SELECT *, TRY_CAST(quantity AS BIGINT) AS units,
       TRY_CAST(unit_price AS DECIMAL(18,4)) AS price,
       TRY_CAST(quantity * TRY_CAST(unit_price AS DECIMAL(18,4)) AS DECIMAL(22,4)) AS amount,
       CASE WHEN NOT is_valid THEN 'invalid'
            WHEN unit_price = 0 THEN 'zero_price'
            WHEN quantity < 0 AND is_cancelled THEN 'cancellation'
            WHEN quantity < 0 THEN 'negative_adjustment'
            WHEN is_cancelled THEN 'positive_cancelled_anomaly'
            ELSE 'sale' END AS line_type
FROM input_lines;
CREATE OR REPLACE VIEW financial_lines AS
SELECT * FROM lines WHERE is_valid AND price > 0 AND units <> 0;
CREATE OR REPLACE VIEW sale_lines AS
SELECT * FROM lines WHERE line_type = 'sale';
CREATE OR REPLACE TABLE orders AS
SELECT customer_id, invoice_no, MIN(invoice_date) AS order_date,
       MIN(country) AS country, SUM(amount) AS gross_sales
FROM sale_lines WHERE customer_id IS NOT NULL
GROUP BY customer_id, invoice_no;
-- Country is assigned at the first observed order. Later international activity stays in its cohort.
CREATE OR REPLACE TABLE customer_history AS
WITH ranked AS (
 SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date, invoice_no) AS rn,
 LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, invoice_no) AS next_order_date
 FROM orders
)
SELECT customer_id, order_date AS first_order_date, next_order_date AS second_order_date,
       country AS first_country, DATE_TRUNC('month', order_date)::DATE AS cohort_month
FROM ranked WHERE rn = 1;
CREATE OR REPLACE TABLE negative_candidates AS
-- This is evidence of a plausible prior line, NOT a one-to-one allocation or return confirmation.
SELECT n.line_id, n.customer_id, n.country, n.line_type, n.amount,
       COUNT(p.line_id) AS candidate_count
FROM financial_lines n
LEFT JOIN sale_lines p ON n.customer_id = p.customer_id AND n.stock_code = p.stock_code
 AND n.price = p.price AND p.invoice_date < n.invoice_date AND p.units >= ABS(n.units)
WHERE n.units < 0
GROUP BY n.line_id, n.customer_id, n.country, n.line_type, n.amount;
