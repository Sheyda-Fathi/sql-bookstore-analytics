-- Question: Which publishers have more than 45 books?
SELECT p.publisher_id,
       p.name AS publisher,
       COUNT(*) AS book_count
FROM publishers p
JOIN books b ON b.publisher_id = p.publisher_id
GROUP BY p.publisher_id, p.name
HAVING COUNT(*) > 45
ORDER BY book_count DESC, p.publisher_id;
