from copy import deepcopy
import pytest
from src.bookstore.seed import (
    ANCHOR_BOOKS,
    ANCHOR_CUSTOMERS,
    ANCHOR_PUBLISHERS,
    SEED,
    build_dataset,
    validate_dataset,
)

@pytest.fixture(scope="module")
def data():
    return build_dataset(SEED)

def test_table_sizes(data):
    assert len(data.publishers) == 50
    assert len(data.authors) == 500
    assert len(data.categories) == 30
    assert len(data.customers) == 1000
    assert len(data.books) == 2000
    assert len(data.orders) == 5000
    assert 2500 <= len(data.author_books) <= 3500
    assert 4500 <= len(data.book_categories) <= 5500
    assert 9000 <= len(data.order_items) <= 11000


def test_dataset_passes_validation(data):
    validate_dataset(data)  

def test_same_seed_gives_same_dataset(data):
    assert build_dataset(SEED) == data

def test_different_seed_gives_different_dataset(data):
    other = build_dataset(SEED + 1)
    assert other.books != data.books

def test_anchor_rows_are_present(data):
    isbns = {row[7] for row in data.books}
    assert {book["isbn13"] for book in ANCHOR_BOOKS} <= isbns
    emails = {row[2] for row in data.customers}
    assert {email for _, email, _ in ANCHOR_CUSTOMERS} <= emails
    names = {row[1] for row in data.publishers}
    assert set(ANCHOR_PUBLISHERS) <= names

def test_every_book_has_author_and_category(data):
    book_ids = {row[0] for row in data.books}
    assert {book_id for _, book_id in data.author_books} == book_ids
    assert {book_id for book_id, _ in data.book_categories} == book_ids

def test_no_book_is_ordered_before_it_was_published(data):
    published = {row[0]: row[4] for row in data.books}
    order_day = {row[0]: row[2].date() for row in data.orders}
    for _, order_id, book_id, _, _ in data.order_items:
        assert order_day[order_id] >= published[book_id]

def test_validation_rejects_a_bad_rating(data):
    broken = deepcopy(data)
    book = list(broken.books[10])
    book[5] = 11
    broken.books[10] = tuple(book)
    with pytest.raises(ValueError, match="rating"):
        validate_dataset(broken)

def test_validation_rejects_a_book_without_author(data):
    broken = deepcopy(data)
    broken.author_books = [pair for pair in broken.author_books if pair[1] != 5]
    with pytest.raises(ValueError, match="author"):
        validate_dataset(broken)
