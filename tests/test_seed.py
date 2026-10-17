import hashlib
import pytest
from psycopg2 import sql
from src.bookstore.db import fetch_all, get_connection
from src.bookstore.seed import SEED, build_dataset

SEED_EMAILS = (
    "sara.seed@example.com",
    "amir.seed@example.com",
    "neda.seed@example.com",
    "reza.seed@example.com",
    "mina.seed@example.com",
)


def test_seeded_publishers_exist():
    result = fetch_all(
        "SELECT name FROM publishers WHERE name IN (%s, %s, %s)",
        ("Ketab-e Pars", "Doran Publishing", "Mehr Books"),
    )
    assert len(result) == 3


def test_seeded_books_exist():
    result = fetch_all(
        "SELECT title FROM books WHERE isbn13 IN (%s, %s, %s)",
        ("9786000000001", "9786000000002", "9786000000003"),
    )
    assert len(result) == 3


def test_seeded_customers_exist():
    result = fetch_all("SELECT email FROM customers WHERE email = ANY(%s)", (list(SEED_EMAILS),))
    assert len(result) == 5


@pytest.mark.parametrize(
    "table, expected",
    [
        ("publishers", 50),
        ("authors", 500),
        ("categories", 30),
        ("customers", 1000),
        ("books", 2000),
        ("orders", 5000),
    ],
)
def test_table_has_expected_row_count(table, expected):
    rows = fetch_all(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
    assert rows == [(expected,)]


def test_relationship_tables_have_realistic_sizes():
    (author_books,), = fetch_all("SELECT COUNT(*) FROM author_books")
    (book_categories,), = fetch_all("SELECT COUNT(*) FROM book_categories")
    (order_items,), = fetch_all("SELECT COUNT(*) FROM order_items")
    assert 2500 <= author_books <= 3500
    assert 4500 <= book_categories <= 5500
    assert 9000 <= order_items <= 11000


def test_all_books_have_author_and_category():
    result = fetch_all(
        """
        SELECT b.book_id
        FROM books b
        WHERE NOT EXISTS (SELECT 1 FROM author_books ab WHERE ab.book_id = b.book_id)
           OR NOT EXISTS (SELECT 1 FROM book_categories bc WHERE bc.book_id = b.book_id)
        """
    )
    assert result == []


def test_every_order_has_at_least_one_item():
    result = fetch_all(
        """
        SELECT o.order_id
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        WHERE oi.order_item_id IS NULL
        """
    )
    assert result == []


def test_no_book_is_ordered_before_it_was_published():
    result = fetch_all(
        """
        SELECT oi.order_item_id
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN books b  ON b.book_id  = oi.book_id
        WHERE o.order_date::date < b.date_published
        """
    )
    assert result == []


def test_unit_price_is_mrp_or_a_ten_percent_discount():
    result = fetch_all(
        """
        SELECT oi.order_item_id
        FROM order_items oi
        JOIN books b ON b.book_id = oi.book_id
        WHERE oi.unit_price NOT IN (b.mrp, ROUND(b.mrp * 0.90, 2))
        """
    )
    assert result == []

def test_sequences_were_synced_after_seeding():
    (max_id,), = fetch_all("SELECT MAX(publisher_id) FROM publishers")
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO publishers (name) VALUES ('sequence probe') RETURNING publisher_id")
        new_id = cursor.fetchone()[0]
        connection.rollback()
    assert new_id > max_id


def test_database_content_matches_the_generated_dataset():
    isbns = ",".join(row[7] for row in build_dataset(SEED).books)
    expected = hashlib.md5(isbns.encode()).hexdigest()
    rows = fetch_all("SELECT md5(string_agg(isbn13, ',' ORDER BY book_id)) FROM books")
    assert rows == [(expected,)]