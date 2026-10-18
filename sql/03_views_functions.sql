-- 03_views_functions.sql 
DROP VIEW IF EXISTS v_order_totals;
DROP VIEW IF EXISTS v_book_full_info;
CREATE VIEW v_book_full_info AS
SELECT b.book_id,
       b.title,
       p.name AS publisher,
       b.mrp,
       b.rating,
       b.date_published,
       COALESCE(a.authors, '') AS authors,
       COALESCE(c.categories, '') AS categories
FROM books b
JOIN publishers p ON p.publisher_id = b.publisher_id
LEFT JOIN (
    SELECT ab.book_id,
           STRING_AGG(au.name, ', ' ORDER BY au.name) AS authors
    FROM author_books ab
    JOIN authors au ON au.author_id = ab.author_id
    GROUP BY ab.book_id
) a ON a.book_id = b.book_id
LEFT JOIN (
    SELECT bc.book_id,
           STRING_AGG(ca.name, ', ' ORDER BY ca.name) AS categories
    FROM book_categories bc
    JOIN categories ca ON ca.category_id = bc.category_id
    GROUP BY bc.book_id
) c ON c.book_id = b.book_id;

CREATE VIEW v_order_totals AS
SELECT o.order_id,
       o.order_date,
       o.status,
       c.customer_id,
       c.name AS customer,
       COUNT(oi.order_item_id) AS items_count,
       COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_amount
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.order_date, o.status, c.customer_id, c.name;

CREATE OR REPLACE FUNCTION place_order(
    p_customer_id INT,
    p_book_ids    INT[],
    p_quantities  INT[]
)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_id INT;
    v_lines    INT;
BEGIN
    IF p_book_ids IS NULL OR p_quantities IS NULL
       OR cardinality(p_book_ids) = 0
       OR cardinality(p_book_ids) <> cardinality(p_quantities) THEN
        RAISE EXCEPTION 'place_order: book ids and quantities must be non-empty arrays of the same length';
    END IF;
    INSERT INTO orders (customer_id)
    VALUES (p_customer_id)
    RETURNING order_id INTO v_order_id;
    INSERT INTO order_items (order_id, book_id, quantity, unit_price)
    SELECT v_order_id, t.book_id, t.quantity, b.mrp
    FROM unnest(p_book_ids, p_quantities) AS t(book_id, quantity)
    JOIN books b ON b.book_id = t.book_id;
    GET DIAGNOSTICS v_lines = ROW_COUNT;
    IF v_lines <> cardinality(p_book_ids) THEN
        RAISE EXCEPTION 'place_order: at least one book id does not exist (%)', p_book_ids;
    END IF;
    RETURN v_order_id;
END;
$$;
