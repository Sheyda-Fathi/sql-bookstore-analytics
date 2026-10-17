-- Question: What is the revenue of each month, and the running total so far?
-- Notes:    cancelled orders are excluded. SUM(...) OVER (ORDER BY month) is a running total.
--           The last running_total equals the total revenue of all non-cancelled orders.

WITH monthly AS (
    SELECT date_trunc('month', o.order_date)::date AS month,
           SUM(oi.quantity * oi.unit_price)        AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status <> 'cancelled'
    GROUP BY 1
)
SELECT to_char(month, 'YYYY-MM')           AS month,
       revenue,
       SUM(revenue) OVER (ORDER BY month)  AS running_total
FROM monthly
ORDER BY month;
