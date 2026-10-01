SELECT country, DATE_TRUNC('month', invoice_date)::DATE AS month,
 SUM(CASE WHEN units > 0 THEN amount ELSE 0 END) AS gross_positive_sales,
 -SUM(CASE WHEN units < 0 THEN amount ELSE 0 END) AS negative_value,
 SUM(amount) AS net_sales,
 -SUM(CASE WHEN line_type = 'cancellation' THEN amount ELSE 0 END) AS cancellation_value,
 -SUM(CASE WHEN line_type = 'negative_adjustment' THEN amount ELSE 0 END) AS adjustment_value,
 COUNT(*) AS financial_rows,
 COUNT(*) FILTER (WHERE units < 0) AS negative_rows,
 COUNT(*) FILTER (WHERE customer_id IS NULL) AS anonymous_rows
FROM financial_lines GROUP BY country, month ORDER BY country, month;
