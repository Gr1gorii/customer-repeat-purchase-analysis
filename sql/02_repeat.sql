WITH cutoff AS (SELECT MAX(invoice_date) AS observed_until FROM lines WHERE is_valid),
windows AS (SELECT UNNEST([30, 60, 90]) AS days),
flags AS (
 SELECT h.*, w.days,
 first_order_date + w.days * INTERVAL '1 day' <= observed_until AS eligible,
 second_order_date <= first_order_date + w.days * INTERVAL '1 day' AS repeated
 FROM customer_history h CROSS JOIN windows w CROSS JOIN cutoff
)
SELECT first_country AS country, cohort_month, days,
       COUNT(*) AS customers,
       COUNT(*) FILTER (WHERE eligible) AS eligible_customers,
       COUNT(*) FILTER (WHERE eligible AND repeated) AS repeat_customers,
       COUNT(*) FILTER (WHERE eligible AND repeated)::DOUBLE /
           NULLIF(COUNT(*) FILTER (WHERE eligible), 0) AS repeat_rate
FROM flags GROUP BY first_country, cohort_month, days ORDER BY country, cohort_month, days;
