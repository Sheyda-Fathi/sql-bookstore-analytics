-- Question: For every book, who are its authors and who published it?
--           Joins 4 tables: books, author_books, authors, publishers

SELECT b.book_id,
       b.title,
       a.name AS author,
       p.name AS publisher
FROM books b
JOIN author_books ab ON ab.book_id = b.book_id
JOIN authors a       ON a.author_id = ab.author_id
JOIN publishers p    ON p.publisher_id = b.publisher_id
ORDER BY b.book_id, a.author_id;
