import os
from contextlib import contextmanager
import psycopg2
from dotenv import load_dotenv

load_dotenv()
CONNECT_TIMEOUT_SECONDS = 5

class DatabaseConfigError(Exception):
    """Database configuration is missing or invalid"""

class DatabaseConnectionError(Exception):
    """The database could not be reached or the login was rejected"""


def _get_database_settings():
    required_settings = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    settings = {}

    for setting in required_settings:
        value = os.getenv(setting)

        if not value:
            raise DatabaseConfigError(f"Missing database setting: {setting}")
        settings[setting] = value

    try:
        settings["DB_PORT"] = int(settings["DB_PORT"])
    except ValueError as exc:
        raise DatabaseConfigError("DB_PORT must be a number") from exc

    return {
        "host": settings["DB_HOST"],
        "port": settings["DB_PORT"],
        "dbname": settings["DB_NAME"],
        "user": settings["DB_USER"],
        "password": settings["DB_PASSWORD"],
    }


@contextmanager
def get_connection():
    """Open a connection; commit on success, roll back on error, always close"""
    settings = _get_database_settings()

    try:
        connection = psycopg2.connect(connect_timeout=CONNECT_TIMEOUT_SECONDS, **settings)
    except psycopg2.OperationalError as exc:
        raise DatabaseConnectionError(f"Could not connect to the database: {exc}") from exc

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def fetch_all(query, params=None):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()