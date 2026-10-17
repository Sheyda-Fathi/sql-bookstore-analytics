-- Question: Which books have never been ordered?
-- Notes:    LEFT JOIN + IS NULL finds books with no matching order_items row.
--           A book ordered only in a cancelled order still counts as ordered.

SELECT b.book_id,
       b.title,
       b.mrp
FROM books b
LEFT JOIN order_items oi ON oi.book_id = b.book_id
WHERE oi.order_item_id IS NULL
ORDER BY b.book_id;
