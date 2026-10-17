-- Question: How many orders are there in each status?
SELECT status,COUNT(*) AS orders_count FROM orders
GROUP BY status
ORDER BY orders_count DESC, status;
