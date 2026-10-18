-- 02_indexes.sql - indexes for the bookstore database
-- PostgreSQL creates an index automatically for PRIMARY KEY and UNIQUE columns,but NOT for FOREIGN KEY columns

CREATE INDEX IF NOT EXISTS idx_books_publisher_id          ON books (publisher_id);
CREATE INDEX IF NOT EXISTS idx_author_books_book_id        ON author_books (book_id);
CREATE INDEX IF NOT EXISTS idx_book_categories_category_id ON book_categories (category_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id          ON orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id        ON order_items (order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_book_id         ON order_items (book_id);

-- Refresh the planner statistics so it can choose the new indexes.
ANALYZE;
