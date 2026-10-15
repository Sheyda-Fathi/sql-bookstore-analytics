-- 01_schema.sql — Bookstore database schema (v1)
-- Based on the ERD: 9 tables
-- Build order: parents before children
-- Re-runnable: drops children first, then parents

-- DROP (children first, then parents) 
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS book_categories CASCADE;
DROP TABLE IF EXISTS author_books CASCADE;
DROP TABLE IF EXISTS books CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS authors CASCADE;
DROP TABLE IF EXISTS publishers CASCADE;


-- publishers: book publishing companies. Parent of books.
CREATE TABLE publishers(
	publisher_id SERIAL PRIMARY KEY NOT NULL,
	name VARCHAR(100) not null
);


-- authors: book authors. Single name column to support mononyms.
CREATE TABLE authors(
	author_id SERIAL PRIMARY KEY NOT NULL,
	name VARCHAR(100) not null
);


-- categories: book categories. Parent of book_categories.
CREATE TABLE categories(
	category_id SERIAL PRIMARY KEY NOT NULL,
	name VARCHAR(100) not null UNIQUE
);


-- customers: store customers who place orders. Parent of orders.
CREATE TABLE customers(
	customer_id SERIAL PRIMARY KEY NOT NULL,
	name VARCHAR(100) not null,
	email text UNIQUE NOT NULL,
	city VARCHAR(60)
);



-- books: the catalog of books. Central table; references publishers.
-- Rules: publisher_id required, isbn13 unique and 13.
CREATE TABLE books(
	book_id SERIAL PRIMARY KEY NOT NULL,
	title VARCHAR(255) NOT NULL,
	length INT,
	mrp NUMERIC(10,2) NOT NULL,
	date_published DATE,
	rating NUMERIC(3,1),
	publisher_id INT NOT NULL,
	isbn13 VARCHAR(13) UNIQUE,

	CONSTRAINT fk_book_publisher
		FOREIGN KEY (publisher_id) 
		REFERENCES publishers(publisher_id) 
		ON DELETE RESTRICT,
		
	CONSTRAINT chk_books_mrp
		CHECK (mrp > 0),
		
	CONSTRAINT chk_books_rating
		CHECK ( rating IS NULL OR (rating >=0 AND rating <=10)),
		
	CONSTRAINT chk_books_length
		CHECK (length IS NULL OR length>0),
		
	CONSTRAINT chk_books_isbn13_length
  		CHECK (isbn13 IS NULL OR LENGTH(isbn13) = 13)
);



-- author_books: junction table for the N:M relation between books and authors.
-- Composite PK prevents duplicate author-book pairs.
CREATE TABLE author_books(
	author_id INT NOT NULL,
    book_id   INT NOT NULL,
	PRIMARY KEY(author_id,book_id),
	
	CONSTRAINT fk_author_books_author
		FOREIGN KEY (author_id)
		REFERENCES authors(author_id)
		ON DELETE CASCADE,

	CONSTRAINT fk_author_books_book
		FOREIGN KEY (book_id)
		REFERENCES books(book_id)
		ON DELETE CASCADE
);


-- book_categories: junction table for the N:M relation between books and categories.
-- Composite PK prevents duplicate book-category pairs.
CREATE TABLE book_categories(
	book_id INT NOT NULL,
    category_id   INT NOT NULL,
	PRIMARY KEY(book_id,category_id),

	CONSTRAINT fk_book_categories_book
		FOREIGN KEY (book_id)
		REFERENCES books(book_id)
		ON DELETE CASCADE,

	CONSTRAINT fk_book_categories_category
		FOREIGN KEY (category_id)
		REFERENCES categories(category_id)
		ON DELETE CASCADE
);


-- orders: customer orders. Parent of order_items.
CREATE TABLE orders(
	order_id SERIAL PRIMARY KEY NOT NULL,
	customer_id INT NOT NULL,
	order_date TIMESTAMP NOT NULL DEFAULT NOW(),
	status VARCHAR(100) not null DEFAULT 'pending',

	CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_orders_status
        CHECK (status IN ('pending', 'paid', 'shipped', 'cancelled'))
	
);


-- order_items: line items of an order (junction between orders and books).
-- unit_price is a snapshot of the price at purchase time, not the current mrp.
CREATE TABLE order_items(
	order_item_id SERIAL PRIMARY KEY NOT NULL,
 	order_id       INT NOT NULL,
    book_id        INT NOT NULL,
    quantity       INT NOT NULL,
    unit_price     NUMERIC(10,2) NOT NULL,

    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_order_items_book
        FOREIGN KEY (book_id)
        REFERENCES books(book_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_order_items_quantity
        CHECK (quantity > 0),

    CONSTRAINT chk_order_items_unit_price
        CHECK (unit_price > 0)
);