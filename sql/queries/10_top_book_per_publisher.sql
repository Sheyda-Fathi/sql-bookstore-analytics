-- Question: What is the best-selling book (by revenue) of each publisher?
-- Notes:    revenue = quantity * unit_price, cancelled orders are excluded.
--           RANK() ... PARTITION BY publisher_id numbers the books inside each publisher;

WITH book_revenue AS (
    SELECT b.publisher_id,
           b.book_id,
           b.title,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM books b
    JOIN order_items oi ON oi.book_id = b.book_id
    JOIN orders o       ON o.order_id = oi.order_id
    WHERE o.status <> 'cancelled'
    GROUP BY b.publisher_id, b.book_id, b.title
),
ranked AS (
    SELECT publisher_id, book_id, title, revenue,
           RANK() OVER (PARTITION BY publisher_id ORDER BY revenue DESC) AS rnk
    FROM book_revenue
)
SELECT p.publisher_id,
       p.name AS publisher,
       r.book_id,
       r.title,
       r.revenue
FROM ranked r
JOIN publishers p ON p.publisher_id = r.publisher_id
WHERE r.rnk = 1
ORDER BY p.publisher_id;
