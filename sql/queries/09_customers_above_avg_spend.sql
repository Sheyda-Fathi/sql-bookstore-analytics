-- Question: Which customers spent more than the average customer?
-- Notes:    only customers with at least one non-cancelled order are counted.
--           CTE customer_spend = total spend per customer; the subquery gives the average.

WITH customer_spend AS (
    SELECT c.customer_id,
           c.name,
           SUM(oi.quantity * oi.unit_price) AS total_spent
    FROM customers c
    JOIN orders o       ON o.customer_id = c.customer_id
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status <> 'cancelled'
    GROUP BY c.customer_id, c.name
)
SELECT customer_id, name, total_spent
FROM customer_spend
WHERE total_spent > (SELECT AVG(total_spent) FROM customer_spend)
ORDER BY total_spent DESC, customer_id;
