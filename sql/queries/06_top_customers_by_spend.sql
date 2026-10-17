-- Question: Who are the 5 customers who spent the most?
-- Notes:    spend = quantity * unit_price, cancelled orders are excluded.
--           COUNT(DISTINCT order_id) because the join with order_items repeats each order.

SELECT c.customer_id,
       c.name,
       COUNT(DISTINCT o.order_id)       AS orders_count,
       SUM(oi.quantity * oi.unit_price) AS total_spent
FROM customers c
JOIN orders o       ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status <> 'cancelled'
GROUP BY c.customer_id, c.name
ORDER BY total_spent DESC, c.customer_id
LIMIT 5;
