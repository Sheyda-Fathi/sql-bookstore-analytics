-- Question: Which 10 books have the highest list price (mrp)?
SELECT book_id, title, mrp
FROM books
ORDER BY mrp DESC, book_id
LIMIT 10;
