"""Seed the bookstore database with reproducible data.
Run:  python -m src.bookstore.seed
The seed is a "reset and reseed": it empties every table and fills it again, so
running it twice always gives the same database 

How it is organised:
  build_dataset()     pure Python, no database: generates every row (explicit ids)
  validate_dataset()  checks the rows against the rules of sql/01_schema.sql
  seed_data()         one transaction: reset, insert, sync sequences, count rows
"""
from __future__ import annotations

import random
from bisect import bisect_right
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from itertools import accumulate

from faker import Faker
from psycopg2 import sql
from psycopg2.extras import execute_values

from src.bookstore.db import get_connection

SEED = 42
TARGET_PUBLISHERS = 50
TARGET_AUTHORS = 500
TARGET_BOOKS = 2000
TARGET_CUSTOMERS = 1000
TARGET_ORDERS = 5000

ORDER_STATUSES = ("pending", "paid", "shipped", "cancelled")
ORDER_STATUS_WEIGHTS = (8, 55, 30, 7)

ANCHOR_PUBLISHERS = ["Ketab-e Pars", "Doran Publishing", "Mehr Books"]

ANCHOR_AUTHORS = [
    "Simin Behbahani",
    "Jalal Al-e Ahmad",
    "Forough Farrokhzad",
    "Sadegh Hedayat",
]

CATEGORY_NAMES = [
    "Fiction", "Science", "Technology", "Literature", "Business",
    "Poetry", "History", "Philosophy", "Biography", "Travel",
    "Cooking", "Art", "Music", "Religion", "Psychology",
    "Self-Help", "Health", "Education", "Children", "Comics",
    "Mystery", "Romance", "Fantasy", "Science Fiction", "Politics",
    "Economics", "Law", "Sports", "Nature", "Mathematics",
]

ANCHOR_BOOKS = [
    {
        "title": "The Blind Owl",
        "length": 250,
        "mrp": Decimal("320000"),
        "date_published": date(1937, 1, 1),
        "rating": Decimal("8.7"),
        "publisher": "Ketab-e Pars",
        "isbn13": "9786000000001",
        "author": "Sadegh Hedayat",
        "category": "Fiction",
    },
    {
        "title": "The Little Black Fish",
        "length": 120,
        "mrp": Decimal("150000"),
        "date_published": date(1968, 1, 1),
        "rating": Decimal("9.1"),
        "publisher": "Doran Publishing",
        "isbn13": "9786000000002",
        "author": "Simin Behbahani",
        "category": "Literature",
    },
    {
        "title": "Selected Poems",
        "length": 180,
        "mrp": Decimal("210000"),
        "date_published": date(1970, 1, 1),
        "rating": Decimal("8.9"),
        "publisher": "Mehr Books",
        "isbn13": "9786000000003",
        "author": "Forough Farrokhzad",
        "category": "Literature",
    },
]

ANCHOR_CUSTOMERS = [
    ("Sara Mohammadi", "sara.seed@example.com", "Tehran"),
    ("Amir Hosseini", "amir.seed@example.com", "Shiraz"),
    ("Neda Karimi", "neda.seed@example.com", "Isfahan"),
    ("Reza Ahmadi", "reza.seed@example.com", "Tabriz"),
    ("Mina Jafari", "mina.seed@example.com", "Mashhad"),
]

ANCHOR_ORDER_STATUSES = ("paid", "shipped", "pending", "cancelled")

CITIES = [
    "Tehran", "Shiraz", "Isfahan", "Tabriz", "Mashhad",
    "Karaj", "Ahvaz", "Qom", "Rasht", "Kerman",
    "Yazd", "Urmia", "Hamadan", "Sari", "Zahedan",
]

TABLES = (
    ("publishers", ("publisher_id", "name")),
    ("authors", ("author_id", "name")),
    ("categories", ("category_id", "name")),
    ("customers", ("customer_id", "name", "email", "city")),
    ("books", ("book_id", "title", "length", "mrp", "date_published",
               "rating", "publisher_id", "isbn13")),
    ("author_books", ("author_id", "book_id")),
    ("book_categories", ("book_id", "category_id")),
    ("orders", ("order_id", "customer_id", "order_date", "status")),
    ("order_items", ("order_item_id", "order_id", "book_id", "quantity", "unit_price")),
)

SERIAL_COLUMNS = (
    ("publishers", "publisher_id"),
    ("authors", "author_id"),
    ("categories", "category_id"),
    ("customers", "customer_id"),
    ("books", "book_id"),
    ("orders", "order_id"),
    ("order_items", "order_item_id"),
)

RESET_SQL = """
TRUNCATE order_items, orders, book_categories, author_books,
         books, customers, categories, authors, publishers
RESTART IDENTITY CASCADE
"""


@dataclass
class Dataset:
    publishers: list      # (publisher_id, name)
    authors: list         # (author_id, name)
    categories: list      # (category_id, name)
    customers: list       # (customer_id, name, email, city)
    books: list           # (book_id, title, length, mrp, date_published, rating, publisher_id, isbn13)
    author_books: list    # (author_id, book_id)
    book_categories: list  # (book_id, category_id)
    orders: list          # (order_id, customer_id, order_date, status)
    order_items: list     # (order_item_id, order_id, book_id, quantity, unit_price)


# build

def make_faker(seed: int) -> Faker:
    fake = Faker("en_US")
    fake.seed_instance(seed)
    return fake


def unique_values(make_value, count, taken):
    values = []
    while len(values) < count:
        value = make_value()
        if value not in taken:
            taken.add(value)
            values.append(value)
    return values


def random_rating(rng: random.Random):
    if rng.random() < 0.10:
        return None
    value = min(10.0, max(0.0, rng.gauss(7.5, 1.3)))
    return Decimal(str(round(value, 1)))


def random_publication_date(rng: random.Random) -> date:
    first, last = date(1990, 1, 1), date(2025, 12, 31)
    return first + timedelta(days=rng.randrange((last - first).days + 1))


def build_dataset(seed: int = SEED) -> Dataset:
    fake = make_faker(seed)
    rng = random.Random(seed)

    # publishers
    names = ANCHOR_PUBLISHERS + unique_values(
        fake.company, TARGET_PUBLISHERS - len(ANCHOR_PUBLISHERS), set(ANCHOR_PUBLISHERS)
    )
    publishers = list(enumerate(names, start=1))
    publisher_id = {name: pid for pid, name in publishers}
    publisher_ids = [pid for pid, _ in publishers]

    # authors
    def author_name():
        return f"{fake.first_name()} {fake.last_name()}"

    names = ANCHOR_AUTHORS + unique_values(
        author_name, TARGET_AUTHORS - len(ANCHOR_AUTHORS), set(ANCHOR_AUTHORS)
    )
    authors = list(enumerate(names, start=1))
    author_id = {name: aid for aid, name in authors}
    author_ids = [aid for aid, _ in authors]

    # categories
    categories = list(enumerate(CATEGORY_NAMES, start=1))
    category_id = {name: cid for cid, name in categories}
    category_ids = [cid for cid, _ in categories]

    # customers
    emails = unique_values(
        fake.email,
        TARGET_CUSTOMERS - len(ANCHOR_CUSTOMERS),
        {email for _, email, _ in ANCHOR_CUSTOMERS},
    )
    customers = [
        (index, name, email, city)
        for index, (name, email, city) in enumerate(ANCHOR_CUSTOMERS, start=1)
    ]
    for email in emails:
        customers.append((
            len(customers) + 1,
            f"{fake.first_name()} {fake.last_name()}",
            email,
            rng.choice(CITIES),
        ))

    # books
    books = []
    for book in ANCHOR_BOOKS:
        books.append((
            len(books) + 1, book["title"], book["length"], book["mrp"],
            book["date_published"], book["rating"],
            publisher_id[book["publisher"]], book["isbn13"],
        ))
    new_isbns = unique_values(
        lambda: fake.isbn13(separator=""),
        TARGET_BOOKS - len(ANCHOR_BOOKS),
        {book["isbn13"] for book in ANCHOR_BOOKS},
    )
    for isbn in new_isbns:
        books.append((
            len(books) + 1,
            fake.sentence(nb_words=4).rstrip("."),
            rng.randint(80, 900),
            Decimal(rng.randrange(50, 501) * 1000),
            random_publication_date(rng),
            random_rating(rng),
            rng.choice(publisher_ids),
            isbn,
        ))

    # author_books and book_categories
    author_books, book_categories = [], []
    for index, book in enumerate(ANCHOR_BOOKS, start=1):
        author_books.append((author_id[book["author"]], index))
        book_categories.append((index, category_id[book["category"]]))
    for book_id in range(len(ANCHOR_BOOKS) + 1, len(books) + 1):
        for aid in rng.sample(author_ids, rng.choice((1, 2))):
            author_books.append((aid, book_id))
        for cid in rng.sample(category_ids, rng.randint(1, 4)):
            book_categories.append((book_id, cid))

    orders, order_items = build_sales(rng, customers, books)

    return Dataset(publishers, authors, categories, customers, books,
                   author_books, book_categories, orders, order_items)


def build_sales(rng: random.Random, customers: list, books: list):
    customer_ids = [row[0] for row in customers]
    customer_by_email = {row[2]: row[0] for row in customers}
    book_by_isbn = {row[7]: row for row in books}
    anchor_books = [book_by_isbn[book["isbn13"]] for book in ANCHOR_BOOKS]

    pending = []
    anchor_emails = sorted(email for _, email, _ in ANCHOR_CUSTOMERS)
    for index, email in enumerate(anchor_emails):
        book = anchor_books[index % len(anchor_books)]
        pending.append((
            customer_by_email[email],
            datetime(2026, 1, 1) + timedelta(days=index),
            ANCHOR_ORDER_STATUSES[index % len(ANCHOR_ORDER_STATUSES)],
            [(book[0], index % 3 + 1, book[3])],
            ))

    start = datetime(2024, 1, 1)
    span_seconds = int((datetime(2026, 6, 30, 23, 59, 59) - start).total_seconds())
    for _ in range(TARGET_ORDERS - len(anchor_emails)):
        pending.append((
            rng.choice(customer_ids),
            start + timedelta(seconds=rng.randrange(span_seconds)),
            rng.choices(ORDER_STATUSES, weights=ORDER_STATUS_WEIGHTS)[0],
            None,
        ))
    pending.sort(key=lambda row: (row[1], row[0]))
    by_date = sorted(books, key=lambda row: (row[4], row[0]))
    published = [row[4] for row in by_date]
    cumulative = list(accumulate(rng.paretovariate(1.2) for _ in by_date))

    orders, order_items = [], []
    for order_id, (customer_id, order_date, status, items) in enumerate(pending, start=1):
        orders.append((order_id, customer_id, order_date, status))
        if items is None:
            items = random_items(rng, by_date, published, cumulative, order_date.date())
        for book_id, quantity, unit_price in items:
            order_items.append((len(order_items) + 1, order_id, book_id, quantity, unit_price))
    return orders, order_items


def random_items(rng, by_date, published, cumulative, order_day):
    eligible = bisect_right(published, order_day)
    count = rng.choices((1, 2, 3), weights=(25, 50, 25))[0]
    chosen = []
    while len(chosen) < count:
        position = rng.choices(range(eligible), cum_weights=cumulative[:eligible])[0]
        if position not in chosen:
            chosen.append(position)

    items = []
    for position in chosen:
        book = by_date[position]
        mrp = book[3]
        if rng.random() < 0.15:
            unit_price = (mrp * Decimal("0.90")).quantize(Decimal("0.01"))
        else:
            unit_price = mrp
        quantity = rng.choices((1, 2, 3), weights=(70, 22, 8))[0]
        items.append((book[0], quantity, unit_price))
    return items


# validate

def validate_dataset(data: Dataset) -> None:
    def check(condition, message):
        if not condition:
            raise ValueError(message)

    publisher_ids = {row[0] for row in data.publishers}
    author_ids = {row[0] for row in data.authors}
    category_ids = {row[0] for row in data.categories}
    customer_ids = {row[0] for row in data.customers}
    book_ids = {row[0] for row in data.books}
    order_ids = {row[0] for row in data.orders}
    for name, rows in (
        ("publishers", data.publishers), ("authors", data.authors),
        ("categories", data.categories), ("customers", data.customers),
        ("books", data.books), ("orders", data.orders),
        ("order_items", data.order_items),
    ):
        check(len({row[0] for row in rows}) == len(rows), f"duplicate ids in {name}")

    check(all(0 < len(name) <= 100 for _, name in data.publishers), "publisher name length")
    check(all(0 < len(name) <= 100 for _, name in data.authors), "author name length")
    check(len({name for _, name in data.categories}) == len(data.categories), "duplicate category")
    check(len({row[2] for row in data.customers}) == len(data.customers), "duplicate email")
    check(all(0 < len(row[1]) <= 100 and len(row[3]) <= 60 for row in data.customers),
          "customer name/city length")

    isbns = [row[7] for row in data.books]
    check(len(set(isbns)) == len(isbns), "duplicate isbn13")
    for book_id, title, length, mrp, published, rating, publisher_id, isbn in data.books:
        check(0 < len(title) <= 255, f"book {book_id}: title length")
        check(length is None or length > 0, f"book {book_id}: length")
        check(mrp > 0, f"book {book_id}: mrp")
        check(rating is None or 0 <= rating <= 10, f"book {book_id}: rating")
        check(len(isbn) == 13 and isbn.isdigit(), f"book {book_id}: isbn13")
        check(publisher_id in publisher_ids, f"book {book_id}: unknown publisher")
        check(isinstance(published, date), f"book {book_id}: date_published")

    check(len(set(data.author_books)) == len(data.author_books), "duplicate author_books pair")
    check(all(a in author_ids and b in book_ids for a, b in data.author_books), "author_books FK")
    check({b for _, b in data.author_books} == book_ids, "every book needs an author")
    check(len(set(data.book_categories)) == len(data.book_categories), "duplicate book_categories pair")
    check(all(b in book_ids and c in category_ids for b, c in data.book_categories),"book_categories FK")
    check({b for b, _ in data.book_categories} == book_ids, "every book needs a category")

    check(all(row[1] in customer_ids for row in data.orders), "orders FK")
    check(all(row[3] in ORDER_STATUSES for row in data.orders), "order status")
    check({row[1] for row in data.order_items} == order_ids, "every order needs an item")

    published_on = {row[0]: row[4] for row in data.books}
    order_date = {row[0]: row[2] for row in data.orders}
    seen_pairs = set()
    for item_id, order_id, book_id, quantity, unit_price in data.order_items:
        check(order_id in order_ids and book_id in book_ids, f"item {item_id}: FK")
        check(quantity > 0 and unit_price > 0, f"item {item_id}: quantity/price")
        check((order_id, book_id) not in seen_pairs, f"item {item_id}: book twice in one order")
        seen_pairs.add((order_id, book_id))
        check(order_date[order_id].date() >= published_on[book_id],
              f"item {item_id}: ordered before the book was published")


#database

def insert_dataset(cursor, data: Dataset) -> None:
    for table, columns in TABLES:
        query = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
            sql.Identifier(table),
            sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        )
        execute_values(cursor, query, getattr(data, table), page_size=1000)


def sync_sequences(cursor) -> None:
    for table, column in SERIAL_COLUMNS:
        cursor.execute(
            sql.SQL(
                "SELECT setval(pg_get_serial_sequence(%s, %s), COALESCE(MAX({}), 1)) FROM {}"
            ).format(sql.Identifier(column), sql.Identifier(table)),
            (table, column),
        )


def count_rows(cursor) -> dict:
    counts = {}
    for table, _ in TABLES:
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
        counts[table] = cursor.fetchone()[0]
    return counts


def seed_data(seed: int = SEED) -> dict:
    data = build_dataset(seed)
    validate_dataset(data)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(RESET_SQL)
            insert_dataset(cursor, data)
            sync_sequences(cursor)
            return count_rows(cursor)


def main() -> None:
    for table, count in seed_data().items():
        print(f"{table}: {count}")


if __name__ == "__main__":
    main()