-- PART 1 - Seed base rows

INSERT INTO publishers (name) VALUES
    ('Nashr-e Markazi'),
    ('Nashr-e Cheshmeh');

INSERT INTO authors (name) VALUES
    ('Hafez'),
    ('Saadi');

INSERT INTO categories (name) VALUES
    ('Poetry'),
    ('History');

INSERT INTO customers (name, email, city) VALUES
    ('Ali Rezaei', 'ali@example.com', 'Tehran'),
    ('Maryam Ahmadi', 'maryam@example.com', 'Shiraz');

INSERT INTO books (title, length, mrp, date_published, rating, publisher_id, isbn13) VALUES
    ('Divan-e Hafez', 500, 250000.00, '2020-01-01', 9.5, 1, '9780000000001'),
    ('Golestan', 300, 180000.00, '2019-05-10', 8.5, 1, '9780000000002');

-- Link the books to authors
INSERT INTO author_books (author_id, book_id) VALUES
    (1, 1),   -- Hafez -> Divan-e Hafez
    (2, 2);   -- Saadi -> Golestan



-- PART 2 - INSERTs that MUST FAIL

-- fk_book_publisher
INSERT INTO books (title, mrp, publisher_id)
VALUES ('Book With Bad Publisher', 100000.00, 999);

-- chk_books_mrp
INSERT INTO books (title, mrp, publisher_id)
VALUES ('Book With Negative Price', -50.00, 1);

-- chk_books_rating
INSERT INTO books (title, mrp, publisher_id, rating)
VALUES ('Book With Bad Rating', 100000.00, 1, 11.0);

-- chk_books_isbn13_length
INSERT INTO books (title, mrp, publisher_id, isbn13)
VALUES ('Book With Short ISBN', 100000.00, 1, '12345');

-- customers_email_key (UNIQUE)
INSERT INTO customers (name, email, city)
VALUES ('Another Ali', 'ali@example.com', 'Mashhad');

-- chk_orders_status
INSERT INTO orders (customer_id, status)
VALUES (1, 'flying');



-- PART 3 - INSERTs that MUST SUCCEED

-- A valid book with all fields
INSERT INTO books (title, length, mrp, date_published, rating, publisher_id, isbn13)
VALUES ('Boostan', 400, 200000.00, '2018-03-15', 7.5, 1, '9780000000003');

-- A valid customer with a new email
INSERT INTO customers (name, email, city)
VALUES ('Reza Karimi', 'reza@example.com', 'Isfahan');

-- A valid order with default status
INSERT INTO orders (customer_id)
VALUES (2);

-- Link the new book to an author and a category (junction tables).
-- Do NOT hard-code book_id: the failed INSERTs in PART 2 already consumed
-- SERIAL values (sequences are not rolled back), so Boostan is not book 3.
INSERT INTO author_books (author_id, book_id)
SELECT 2, book_id FROM books WHERE isbn13 = '9780000000003';   -- Saadi -> Boostan

INSERT INTO book_categories (book_id, category_id)
SELECT book_id, 1 FROM books WHERE isbn13 = '9780000000003';   -- Boostan -> Poetry



-- PART 4 - ON DELETE tests

-- publisher 1 still has books (RESTRICT)
-- Expected error mentions: fk_book_publisher
DELETE FROM publishers WHERE publisher_id = 1;

-- First, check how many rows the author had BEFORE:
SELECT 'BEFORE - author_books for Saadi:' AS step, COUNT(*) AS rows
FROM author_books WHERE author_id = 2;

-- Deleting an author cascades to author_books.
DELETE FROM authors WHERE author_id = 2;

-- Then, verify the cascade worked:
SELECT 'AFTER - author_books for Saadi:' AS step, COUNT(*) AS rows
FROM author_books WHERE author_id = 2;