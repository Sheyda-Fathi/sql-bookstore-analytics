import pytest
from psycopg2 import errors
from src.bookstore.db import fetch_all, get_connection

def test_book_view_has_exactly_one_row_per_book():
    (books,), = fetch_all("SELECT COUNT(*) FROM books")
    (rows, distinct_books), = fetch_all("SELECT COUNT(*), COUNT(DISTINCT book_id) FROM v_book_full_info")
    assert rows == distinct_books == books

def test_every_book_in_the_view_has_authors_and_categories():
    result = fetch_all("SELECT book_id FROM v_book_full_info WHERE authors = '' OR categories = ''")
    assert result == []

def test_book_view_shows_a_known_book():
    rows = fetch_all("SELECT title, publisher, authors FROM v_book_full_info WHERE book_id = 1")
    assert rows == [("The Blind Owl", "Ketab-e Pars", "Sadegh Hedayat")]

def test_order_totals_view_matches_the_order_items():
    (from_view,), = fetch_all("SELECT SUM(total_amount) FROM v_order_totals WHERE status <> 'cancelled'")
    (direct,), = fetch_all(
        """
        SELECT SUM(oi.quantity * oi.unit_price)
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.status <> 'cancelled'
        """
    )
    assert from_view == direct

def test_place_order_creates_the_order_and_its_items():
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT place_order(%s, %s, %s)", (1, [1, 2], [2, 1]))
        order_id = cursor.fetchone()[0]
        cursor.execute(
            """
            SELECT oi.book_id, oi.quantity, oi.unit_price = b.mrp
            FROM order_items oi JOIN books b ON b.book_id = oi.book_id
            WHERE oi.order_id = %s ORDER BY oi.book_id
            """,
            (order_id,),
        )
        assert cursor.fetchall() == [(1, 2, True), (2, 1, True)]
        cursor.execute("SELECT status, items_count FROM v_order_totals WHERE order_id = %s", (order_id,))
        assert cursor.fetchone() == ("pending", 2)
        connection.rollback()

def test_place_order_with_an_unknown_book_leaves_nothing_behind():
    with get_connection() as connection:
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        orders_before = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM order_items")
        items_before = cursor.fetchone()[0]
        with pytest.raises(errors.RaiseException):
            cursor.execute("SELECT place_order(%s, %s, %s)", (1, [1, 999999], [1, 1]))
        cursor.execute("SELECT COUNT(*) FROM orders")
        assert cursor.fetchone()[0] == orders_before
        cursor.execute("SELECT COUNT(*) FROM order_items")
        assert cursor.fetchone()[0] == items_before

def test_place_order_with_a_bad_quantity_is_rejected_by_the_check_constraint():
    with get_connection() as connection:
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        orders_before = cursor.fetchone()[0]
        with pytest.raises(errors.CheckViolation):
            cursor.execute("SELECT place_order(%s, %s, %s)", (1, [1], [0]))
        cursor.execute("SELECT COUNT(*) FROM orders")
        assert cursor.fetchone()[0] == orders_before

def test_place_order_rejects_arrays_of_different_length():
    with get_connection() as connection:
        connection.autocommit = True
        cursor = connection.cursor()
        with pytest.raises(errors.RaiseException):
            cursor.execute("SELECT place_order(%s, %s, %s)", (1, [1, 2], [1]))
