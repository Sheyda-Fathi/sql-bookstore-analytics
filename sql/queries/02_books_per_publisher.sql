-- Question: How many books does each publisher have?
SELECT p.publisher_id,
       p.name AS publisher,
       COUNT(b.book_id) AS book_count
FROM publishers p
LEFT JOIN books b ON b.publisher_id = p.publisher_id
GROUP BY p.publisher_id, p.name
ORDER BY book_count DESC, p.publisher_id;
