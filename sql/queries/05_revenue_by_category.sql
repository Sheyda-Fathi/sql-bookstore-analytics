-- Question: How much revenue does each category bring in?
-- Notes:    revenue = quantity * unit_price, cancelled orders are excluded.
--           A book with several categories is counted once in EACH of its categories,
--           so the category totals add up to more than the real total revenue.

SELECT c.name AS category,
       SUM(oi.quantity * oi.unit_price) AS revenue
FROM categories c
JOIN book_categories bc ON bc.category_id = c.category_id
JOIN order_items oi     ON oi.book_id = bc.book_id
JOIN orders o           ON o.order_id = oi.order_id
WHERE o.status <> 'cancelled'
GROUP BY c.category_id, c.name
ORDER BY revenue DESC, c.name;
