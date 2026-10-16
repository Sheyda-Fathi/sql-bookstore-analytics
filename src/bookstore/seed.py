
from datetime import datetime, timedelta
from decimal import Decimal
from src.bookstore.db import get_connection

def insert_if_missing(cursor, table, column, value):
    cursor.execute(f"SELECT 1 FROM {table} WHERE {column} = %s",(value,),)

    if cursor.fetchone() is None:
        cursor.execute(f"INSERT INTO {table} ({column}) VALUES (%s) RETURNING *",(value,),)
        return cursor.fetchone()

    return None


def seed_base_data():
    """Insert publishers, authors, and categories if missing"""

    publishers = [
        "Ketab-e Pars",
        "Doran Publishing",
        "Mehr Books",
    ]

    authors = [
        "Simin Behbahani",
        "Jalal Al-e Ahmad",
        "Forough Farrokhzad",
        "Sadegh Hedayat",
    ]

    categories = [
        "Fiction",
        "Science",
        "Technology",
        "Literature",
        "Business",
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for name in publishers:
                insert_if_missing(cursor, "publishers", "name", name)

            for name in authors:
                insert_if_missing(cursor, "authors", "name", name)

            for name in categories:
                insert_if_missing(cursor, "categories", "name", name)


def seed_books():
    """Insert sample books and their author/category links"""

    sample_books = [
        {
            "title": "The Blind Owl",
            "length": 250,
            "mrp": 320000,
            "date_published": "1937-01-01",
            "rating": 8.7,
            "publisher": "Ketab-e Pars",
            "isbn13": "9786000000001",
            "author": "Sadegh Hedayat",
            "category": "Fiction",
        },
        {
            "title": "The Little Black Fish",
            "length": 120,
            "mrp": 150000,
            "date_published": "1968-01-01",
            "rating": 9.1,
            "publisher": "Doran Publishing",
            "isbn13": "9786000000002",
            "author": "Simin Behbahani",
            "category": "Literature",
        },
        {
            "title": "Selected Poems",
            "length": 180,
            "mrp": 210000,
            "date_published": "1970-01-01",
            "rating": 8.9,
            "publisher": "Mehr Books",
            "isbn13": "9786000000003",
            "author": "Forough Farrokhzad",
            "category": "Literature",
        },
    ]

    original_books = [
        {
            "title": "Divan-e Hafez",
            "author": "Hafez",
            "category": "Poetry",
        },
        {
            "title": "Golestan",
            "author": "Hafez",
            "category": "Literature",
        },
        {
            "title": "Boostan",
            "author": "Hafez",
            "category": "Poetry",
        },
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for book in sample_books:
                cursor.execute("SELECT book_id FROM books WHERE isbn13 = %s",(book["isbn13"],),)
                result = cursor.fetchone()

                if result:
                    book_id = result[0]
                else:
                    cursor.execute(
                        """
                        INSERT INTO books (
                            title,
                            length,
                            mrp,
                            date_published,
                            rating,
                            publisher_id,
                            isbn13
                        )
                        VALUES (
                            %s, %s, %s, %s, %s,
                            (
                                SELECT publisher_id
                                FROM publishers
                                WHERE name = %s
                            ),
                            %s
                        )
                        RETURNING book_id
                        """,
                        (
                            book["title"],
                            book["length"],
                            book["mrp"],
                            book["date_published"],
                            book["rating"],
                            book["publisher"],
                            book["isbn13"],
                        ),
                    )
                    book_id = cursor.fetchone()[0]

                cursor.execute("SELECT author_id FROM authors WHERE name = %s",(book["author"],),)
                author_result = cursor.fetchone()

                cursor.execute("SELECT category_id FROM categories WHERE name = %s",(book["category"],),)
                category_result = cursor.fetchone()

                if author_result is None or category_result is None:
                    raise ValueError(f"Missing author or category for {book['title']}")

                cursor.execute(
                    """
                    INSERT INTO author_books (author_id, book_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (author_result[0], book_id),
                )

                cursor.execute(
                    """
                    INSERT INTO book_categories (book_id, category_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (book_id, category_result[0]),
                )

            for book in original_books:
                cursor.execute("SELECT book_id FROM books WHERE title = %s",(book["title"],),)
                result = cursor.fetchone()

                if result is None:
                    continue

                book_id = result[0]

                cursor.execute("SELECT author_id FROM authors WHERE name = %s",(book["author"],),)
                author_result = cursor.fetchone()

                cursor.execute("SELECT category_id FROM categories WHERE name = %s",(book["category"],),)
                category_result = cursor.fetchone()

                if author_result is None or category_result is None:
                    raise ValueError(f"Missing author or category for {book['title']}")

                cursor.execute(
                    """
                    INSERT INTO author_books (author_id, book_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (author_result[0], book_id),
                )

                cursor.execute(
                    """
                    INSERT INTO book_categories (book_id, category_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (book_id, category_result[0]),
                )


def seed_customers():
    """Insert sample customers without duplicating their email addresses"""

    customers = [
        ("Sara Mohammadi", "sara.seed@example.com", "Tehran"),
        ("Amir Hosseini", "amir.seed@example.com", "Shiraz"),
        ("Neda Karimi", "neda.seed@example.com", "Isfahan"),
        ("Reza Ahmadi", "reza.seed@example.com", "Tabriz"),
        ("Mina Jafari", "mina.seed@example.com", "Mashhad"),
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for name, email, city in customers:
                cursor.execute(
                    """
                    INSERT INTO customers (name, email, city)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (email) DO NOTHING
                    """,
                    (name, email, city),
                )


def seed_orders():
    """Create identifiable sample orders and their items"""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT customer_id
                FROM customers
                WHERE email IN (
                    'sara.seed@example.com',
                    'amir.seed@example.com',
                    'neda.seed@example.com',
                    'reza.seed@example.com',
                    'mina.seed@example.com'
                )
                ORDER BY email
                """
            )
            customer_ids = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT book_id, mrp
                FROM books
                WHERE isbn13 IN (
                    '9786000000001',
                    '9786000000002',
                    '9786000000003'
                )
                ORDER BY isbn13
                """
            )
            books = cursor.fetchall()

            if not customer_ids or not books:
                raise ValueError("Seed customers or books were not found.")

            statuses = ["paid", "shipped", "pending", "cancelled"]

            for index, customer_id in enumerate(customer_ids):
                order_date = datetime(2026, 1, 1) + timedelta(days=index)

                cursor.execute(
                    """
                    SELECT order_id
                    FROM orders
                    WHERE customer_id = %s AND order_date = %s
                    """,
                    (customer_id, order_date),)
                result = cursor.fetchone()

                if result:
                    order_id = result[0]
                else:
                    cursor.execute(
                        """
                        INSERT INTO orders (customer_id, order_date, status)
                        VALUES (%s, %s, %s)
                        RETURNING order_id
                        """,
                        (
                            customer_id,
                            order_date,
                            statuses[index % len(statuses)],
                        ),)
                    order_id = cursor.fetchone()[0]

                book_id, price = books[index % len(books)]
                quantity = index % 3 + 1

                cursor.execute(
                    """
                    SELECT 1
                    FROM order_items
                    WHERE order_id = %s AND book_id = %s
                    """,
                    (order_id, book_id),
                )

                if cursor.fetchone() is None:
                    cursor.execute(
                        """
                        INSERT INTO order_items (
                            order_id,
                            book_id,
                            quantity,
                            unit_price
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            order_id,
                            book_id,
                            quantity,
                            Decimal(price),
                        ),
                    )


def seed_data():
    """Run the bookstore seed process"""

    seed_base_data()
    seed_books()
    seed_customers()
    seed_orders()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for table in (
                "publishers",
                "authors",
                "categories",
                "books",
                "customers",
                "orders",
                "order_items",
                "author_books",
                "book_categories",
            ):
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                print(f"{table}: {cursor.fetchone()[0]}")


if __name__ == "__main__":
    seed_data()
