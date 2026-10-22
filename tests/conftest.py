import pytest
from src.bookstore.db import get_connection

@pytest.fixture
def cur():
    with get_connection() as connection:
        cursor = connection.cursor()
        yield cursor
        connection.rollback()
