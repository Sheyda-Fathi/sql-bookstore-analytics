
import pytest
import psycopg2
from src.bookstore.db import (DatabaseConfigError,DatabaseConnectionError,fetch_all,get_connection,)


def test_connection_works():
    result = fetch_all("SELECT 1")
    assert result == [(1,)]


def test_parameterized_query():
    value = "hello"
    result = fetch_all("SELECT %s", (value,))
    assert result == [(value,)]


def test_missing_database_setting(monkeypatch):
    monkeypatch.delenv("DB_HOST", raising=False)
    with pytest.raises(DatabaseConfigError):
        with get_connection():
            pass


def test_connection_error(monkeypatch):
    import src.bookstore.db as db
    def fail_to_connect(**settings):
        raise psycopg2.OperationalError("connection failed")
    monkeypatch.setattr(db.psycopg2, "connect", fail_to_connect)
    with pytest.raises(DatabaseConnectionError):
        with get_connection():
            pass
