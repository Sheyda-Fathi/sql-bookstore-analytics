
from src.bookstore.db import fetch_all


def test_seeded_publishers_exist():
    result = fetch_all(
        """
        SELECT name
        FROM publishers
        WHERE name IN (
            'Ketab-e Pars',
            'Doran Publishing',
            'Mehr Books'
        )
        """
    )
    assert len(result) == 3


def test_seeded_books_exist():
    result = fetch_all(
        """
        SELECT title
        FROM books
        WHERE isbn13 IN (
            '9786000000001',
            '9786000000002',
            '9786000000003'
        )
        """
    )
    assert len(result) == 3


def test_seeded_customers_exist():
    result = fetch_all(
        """
        SELECT email
        FROM customers
        WHERE email IN (
            'sara.seed@example.com',
            'amir.seed@example.com',
            'neda.seed@example.com',
            'reza.seed@example.com',
            'mina.seed@example.com'
        )
        """
    )
    assert len(result) == 5


def test_all_books_have_author_and_category():
    result = fetch_all(
        """
        SELECT b.book_id
        FROM books b
        WHERE NOT EXISTS (
            SELECT 1
            FROM author_books ab
            WHERE ab.book_id = b.book_id
        )
        OR NOT EXISTS (
            SELECT 1
            FROM book_categories bc
            WHERE bc.book_id = b.book_id
        )
        """
    )
    assert result == []


def test_seeded_orders_have_order_items():
    result = fetch_all(
        """
        SELECT o.order_id
        FROM orders o
        JOIN customers c
            ON c.customer_id = o.customer_id
        LEFT JOIN order_items oi
            ON oi.order_id = o.order_id
        WHERE c.email IN (
            'sara.seed@example.com',
            'amir.seed@example.com',
            'neda.seed@example.com',
            'reza.seed@example.com',
            'mina.seed@example.com'
        )
        GROUP BY o.order_id
        HAVING COUNT(oi.order_item_id) = 0
        """
    )
    assert result == []
