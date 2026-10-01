SELECT country, line_type,
 CASE WHEN customer_id IS NULL THEN 'missing_customer'
      WHEN candidate_count = 0 THEN 'no_candidate'
      WHEN candidate_count = 1 THEN 'one_candidate'
      ELSE 'multiple_candidates' END AS candidate_status,
 COUNT(*) AS negative_rows, -SUM(amount) AS negative_value
FROM negative_candidates GROUP BY country, line_type, candidate_status
ORDER BY country, line_type, candidate_status;
