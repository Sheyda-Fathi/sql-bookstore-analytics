-- Question: Which categories have an average book rating of at least 7.55?
SELECT c.name AS category,
       ROUND(AVG(b.rating), 2) AS avg_rating,
       COUNT(b.rating)         AS rated_books
FROM categories c
JOIN book_categories bc ON bc.category_id = c.category_id
JOIN books b            ON b.book_id = bc.book_id
GROUP BY c.category_id, c.name
HAVING AVG(b.rating) >= 7.55
ORDER BY avg_rating DESC, c.name;
