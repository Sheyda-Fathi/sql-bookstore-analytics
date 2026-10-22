"""
The schema must reject bad data
This replaces the manual tests/constraint_checks.sql. Every test runs in a transaction
that is rolled back (see the `cur` fixture in conftest.py), so the tests never change
the database and do not depend on the seed data.
"""
import itertools
import pytest
from psycopg2 import errors, sql
_numbers = itertools.count(1)


def next_number():
    return next(_numbers)

def missing_id(cur, table, column):
    cur.execute(sql.SQL("SELECT COALESCE(MAX({}), 0) + 1000000 FROM {}").format(sql.Identifier(column), sql.Identifier(table)))
    return cur.fetchone()[0]

def count_rows(cur, table, column, value):
    cur.execute(sql.SQL("SELECT COUNT(*) FROM {} WHERE {} = %s").format(sql.Identifier(table), sql.Identifier(column)),(value,),)
    return cur.fetchone()[0]

def new_publisher(cur):
    cur.execute("INSERT INTO publishers (name) VALUES (%s) RETURNING publisher_id",(f"Test Publisher {next_number()}",),)
    return cur.fetchone()[0]

def new_author(cur):
    cur.execute("INSERT INTO authors (name) VALUES (%s) RETURNING author_id",(f"Test Author {next_number()}",),)
    return cur.fetchone()[0]

def new_category(cur, name=None):
    cur.execute("INSERT INTO categories (name) VALUES (%s) RETURNING category_id",(name or f"Test Category {next_number()}",),)
    return cur.fetchone()[0]

def new_customer(cur, email=None):
    number = next_number()
    cur.execute("INSERT INTO customers (name, email, city) VALUES (%s, %s, %s) RETURNING customer_id",(f"Test Customer {number}", email or f"test{number}@example.test", "Tehran"),)
    return cur.fetchone()[0]

def new_book(cur, publisher_id=None, **overrides):
    number = next_number()
    values = {
        "title": f"Test Book {number}",
        "length": 300,
        "mrp": 100000,
        "date_published": "2020-01-01",
        "rating": 8.0,
        "isbn13": f"999{number:010d}",
    }
    values.update(overrides)
    if publisher_id is None:
        publisher_id = new_publisher(cur)
    cur.execute(
        """
        INSERT INTO books (title, length, mrp, date_published, rating, publisher_id, isbn13)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING book_id
        """,
        (
            values["title"], values["length"], values["mrp"], values["date_published"],
            values["rating"], publisher_id, values["isbn13"],
        ),
    )
    return cur.fetchone()[0]

def new_order(cur, customer_id=None):
    if customer_id is None:
        customer_id = new_customer(cur)
    cur.execute("INSERT INTO orders (customer_id) VALUES (%s) RETURNING order_id", (customer_id,))
    return cur.fetchone()[0]

def new_order_item(cur, order_id, book_id, quantity=1, unit_price=100000):
    cur.execute(
        """
        INSERT INTO order_items (order_id, book_id, quantity, unit_price)
        VALUES (%s, %s, %s, %s)
        RETURNING order_item_id
        """,
        (order_id, book_id, quantity, unit_price),
    )
    return cur.fetchone()[0]

BAD_BOOKS = [
    pytest.param("chk_books_mrp", {"mrp": -50}, id="negative-price"),
    pytest.param("chk_books_mrp", {"mrp": 0}, id="zero-price"),
    pytest.param("chk_books_rating", {"rating": 11}, id="rating-above-10"),
    pytest.param("chk_books_rating", {"rating": -0.1}, id="rating-below-0"),
    pytest.param("chk_books_length", {"length": 0}, id="zero-pages"),
    pytest.param("chk_books_isbn13_length", {"isbn13": "12345"}, id="short-isbn"),
]

@pytest.mark.parametrize("constraint, overrides", BAD_BOOKS)
def test_book_rules_reject_bad_values(cur, constraint, overrides):
    with pytest.raises(errors.CheckViolation) as excinfo:
        new_book(cur, **overrides)
    assert excinfo.value.diag.constraint_name == constraint

def test_isbn13_longer_than_13_characters_is_rejected_by_the_column_type(cur):
    with pytest.raises(errors.StringDataRightTruncation):
        new_book(cur, isbn13="99900000000012")

def test_book_needs_a_publisher(cur):
    with pytest.raises(errors.NotNullViolation) as excinfo:
        cur.execute("INSERT INTO books (title, mrp, publisher_id) VALUES ('No Publisher', 100000, NULL)")
    assert excinfo.value.diag.column_name == "publisher_id"

def test_book_publisher_must_exist(cur):
    with pytest.raises(errors.ForeignKeyViolation) as excinfo:
        new_book(cur, publisher_id=missing_id(cur, "publishers", "publisher_id"))
    assert excinfo.value.diag.constraint_name == "fk_book_publisher"

def test_isbn13_must_be_unique(cur):
    new_book(cur, isbn13="9990000000001")
    with pytest.raises(errors.UniqueViolation) as excinfo:
        new_book(cur, isbn13="9990000000001")
    assert excinfo.value.diag.constraint_name == "books_isbn13_key"

def test_customer_email_must_be_unique(cur):
    new_customer(cur, email="same@example.test")
    with pytest.raises(errors.UniqueViolation) as excinfo:
        new_customer(cur, email="same@example.test")
    assert excinfo.value.diag.constraint_name == "customers_email_key"

def test_category_name_must_be_unique(cur):
    new_category(cur, name="Duplicate Category")
    with pytest.raises(errors.UniqueViolation) as excinfo:
        new_category(cur, name="Duplicate Category")
    assert excinfo.value.diag.constraint_name == "categories_name_key"

def test_order_status_must_be_a_known_value(cur):
    customer_id = new_customer(cur)
    with pytest.raises(errors.CheckViolation) as excinfo:
        cur.execute("INSERT INTO orders (customer_id, status) VALUES (%s, 'flying')", (customer_id,))
    assert excinfo.value.diag.constraint_name == "chk_orders_status"

def test_order_customer_must_exist(cur):
    with pytest.raises(errors.ForeignKeyViolation) as excinfo:
        cur.execute(
            "INSERT INTO orders (customer_id) VALUES (%s)",
            (missing_id(cur, "customers", "customer_id"),),
        )
    assert excinfo.value.diag.constraint_name == "fk_orders_customer"

def test_order_item_book_must_exist(cur):
    order_id = new_order(cur)
    with pytest.raises(errors.ForeignKeyViolation) as excinfo:
        new_order_item(cur, order_id, missing_id(cur, "books", "book_id"))
    assert excinfo.value.diag.constraint_name == "fk_order_items_book"

def test_order_item_order_must_exist(cur):
    book_id = new_book(cur)
    with pytest.raises(errors.ForeignKeyViolation) as excinfo:
        new_order_item(cur, missing_id(cur, "orders", "order_id"), book_id)
    assert excinfo.value.diag.constraint_name == "fk_order_items_order"

BAD_ITEMS = [
    pytest.param("chk_order_items_quantity", {"quantity": 0}, id="zero-quantity"),
    pytest.param("chk_order_items_quantity", {"quantity": -1}, id="negative-quantity"),
    pytest.param("chk_order_items_unit_price", {"unit_price": 0}, id="zero-price"),
    pytest.param("chk_order_items_unit_price", {"unit_price": -5}, id="negative-price"),
]

@pytest.mark.parametrize("constraint, overrides", BAD_ITEMS)
def test_order_item_rules_reject_bad_values(cur, constraint, overrides):
    order_id, book_id = new_order(cur), new_book(cur)
    with pytest.raises(errors.CheckViolation) as excinfo:
        new_order_item(cur, order_id, book_id, **overrides)
    assert excinfo.value.diag.constraint_name == constraint

def test_author_cannot_be_linked_to_the_same_book_twice(cur):
    author_id, book_id = new_author(cur), new_book(cur)
    link = "INSERT INTO author_books (author_id, book_id) VALUES (%s, %s)"
    cur.execute(link, (author_id, book_id))
    with pytest.raises(errors.UniqueViolation) as excinfo:
        cur.execute(link, (author_id, book_id))
    assert excinfo.value.diag.constraint_name == "author_books_pkey"


def test_book_cannot_be_in_the_same_category_twice(cur):
    book_id, category_id = new_book(cur), new_category(cur)
    link = "INSERT INTO book_categories (book_id, category_id) VALUES (%s, %s)"
    cur.execute(link, (book_id, category_id))
    with pytest.raises(errors.UniqueViolation) as excinfo:
        cur.execute(link, (book_id, category_id))
    assert excinfo.value.diag.constraint_name == "book_categories_pkey"


def test_a_valid_book_with_all_fields_is_accepted(cur):
    book_id = new_book(cur, title="Boostan", length=400, mrp=200000, rating=7.5)
    cur.execute("SELECT title, rating FROM books WHERE book_id = %s", (book_id,))
    title, rating = cur.fetchone()
    assert title == "Boostan"
    assert float(rating) == 7.5

def test_optional_columns_may_be_null(cur):
    book_id = new_book(cur, length=None, rating=None, date_published=None, isbn13=None)
    assert count_rows(cur, "books", "book_id", book_id) == 1

def test_many_books_may_have_no_isbn(cur):
    publisher_id = new_publisher(cur)
    new_book(cur, publisher_id=publisher_id, isbn13=None)
    new_book(cur, publisher_id=publisher_id, isbn13=None)

def test_a_new_order_starts_as_pending_with_a_date(cur):
    order_id = new_order(cur)
    cur.execute("SELECT status, order_date IS NOT NULL FROM orders WHERE order_id = %s", (order_id,))
    assert cur.fetchone() == ("pending", True)

def test_links_can_be_created_without_hard_coded_ids(cur):
    author_id, category_id = new_author(cur), new_category(cur)
    book_id = new_book(cur, isbn13="9990000000777")
    cur.execute(
        "INSERT INTO author_books (author_id, book_id) SELECT %s, book_id FROM books WHERE isbn13 = %s",
        (author_id, "9990000000777"),
    )
    cur.execute(
        "INSERT INTO book_categories (book_id, category_id) SELECT book_id, %s FROM books WHERE isbn13 = %s",
        (category_id, "9990000000777"),
    )
    assert count_rows(cur, "author_books", "book_id", book_id) == 1
    assert count_rows(cur, "book_categories", "book_id", book_id) == 1


def test_a_rolled_back_insert_still_uses_up_a_sequence_number(cur):
    cur.execute("SAVEPOINT before_insert")
    first_id = new_publisher(cur)
    cur.execute("ROLLBACK TO SAVEPOINT before_insert")
    second_id = new_publisher(cur)
    assert second_id > first_id

def test_a_publisher_with_books_cannot_be_deleted(cur):
    publisher_id = new_publisher(cur)
    new_book(cur, publisher_id=publisher_id)
    with pytest.raises(errors.RestrictViolation) as excinfo:
        cur.execute("DELETE FROM publishers WHERE publisher_id = %s",(publisher_id,),)
    assert excinfo.value.diag.constraint_name == "fk_book_publisher"

def test_a_customer_with_orders_cannot_be_deleted(cur):
    customer_id = new_customer(cur)
    new_order(cur, customer_id)
    with pytest.raises(errors.RestrictViolation) as excinfo:
        cur.execute("DELETE FROM customers WHERE customer_id = %s",(customer_id,),)
    assert excinfo.value.diag.constraint_name == "fk_orders_customer"

def test_a_book_that_was_ordered_cannot_be_deleted(cur):
    book_id = new_book(cur)
    new_order_item(cur, new_order(cur), book_id)
    with pytest.raises(errors.RestrictViolation) as excinfo:
        cur.execute("DELETE FROM books WHERE book_id = %s",(book_id,),)
    assert excinfo.value.diag.constraint_name == "fk_order_items_book"

def test_deleting_an_author_removes_only_the_links(cur):
    author_id, book_id = new_author(cur), new_book(cur)
    cur.execute("INSERT INTO author_books (author_id, book_id) VALUES (%s, %s)", (author_id, book_id))
    cur.execute("DELETE FROM authors WHERE author_id = %s", (author_id,))
    assert count_rows(cur, "author_books", "author_id", author_id) == 0
    assert count_rows(cur, "books", "book_id", book_id) == 1

def test_deleting_a_book_removes_its_links(cur):
    author_id, category_id, book_id = new_author(cur), new_category(cur), new_book(cur)
    cur.execute("INSERT INTO author_books (author_id, book_id) VALUES (%s, %s)", (author_id, book_id))
    cur.execute("INSERT INTO book_categories (book_id, category_id) VALUES (%s, %s)", (book_id, category_id))
    cur.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
    assert count_rows(cur, "author_books", "book_id", book_id) == 0
    assert count_rows(cur, "book_categories", "book_id", book_id) == 0

def test_deleting_a_category_removes_its_links(cur):
    book_id, category_id = new_book(cur), new_category(cur)
    cur.execute("INSERT INTO book_categories (book_id, category_id) VALUES (%s, %s)", (book_id, category_id))
    cur.execute("DELETE FROM categories WHERE category_id = %s", (category_id,))
    assert count_rows(cur, "book_categories", "category_id", category_id) == 0
    assert count_rows(cur, "books", "book_id", book_id) == 1

def test_deleting_an_order_removes_its_items(cur):
    order_id, book_id = new_order(cur), new_book(cur)
    new_order_item(cur, order_id, book_id)
    cur.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
    assert count_rows(cur, "order_items", "order_id", order_id) == 0
    assert count_rows(cur, "books", "book_id", book_id) == 1
