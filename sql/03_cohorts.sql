WITH months AS (
 SELECT UNNEST(generate_series(
   (SELECT MIN(cohort_month) FROM customer_history),
   (SELECT DATE_TRUNC('month', MAX(invoice_date)) FROM lines WHERE is_valid),
   INTERVAL '1 month'))::DATE AS activity_month
), sizes AS (
 SELECT first_country AS country, cohort_month, COUNT(*) AS cohort_size
 FROM customer_history GROUP BY first_country, cohort_month
), activity AS (
 SELECT h.first_country AS country, h.cohort_month,
 DATE_TRUNC('month', o.order_date)::DATE AS activity_month,
 COUNT(DISTINCT o.customer_id) AS active_customers
 FROM orders o JOIN customer_history h USING (customer_id)
 GROUP BY h.first_country, h.cohort_month, activity_month
)
SELECT s.*, m.activity_month,
 DATE_DIFF('month', s.cohort_month, m.activity_month) AS month_index,
 m.activity_month + INTERVAL '1 month' <=
   (SELECT MAX(invoice_date) FROM lines WHERE is_valid) AS complete_month,
 COALESCE(a.active_customers, 0) AS active_customers,
 CASE WHEN m.activity_month + INTERVAL '1 month' <=
   (SELECT MAX(invoice_date) FROM lines WHERE is_valid)
 THEN COALESCE(a.active_customers, 0)::DOUBLE / s.cohort_size END AS retention_rate
FROM sizes s CROSS JOIN months m LEFT JOIN activity a
 ON s.country IS NOT DISTINCT FROM a.country AND s.cohort_month = a.cohort_month
 AND m.activity_month = a.activity_month
WHERE m.activity_month >= s.cohort_month ORDER BY s.country, s.cohort_month, month_index;
