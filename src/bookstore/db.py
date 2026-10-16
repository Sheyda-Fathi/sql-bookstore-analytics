
import os
from contextlib import contextmanager
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfigError(Exception):
    """database configuration is missing or invalid"""


class DatabaseConnectionError(Exception):
    """database connection fails"""


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
            raise DatabaseConfigError(f"Missing database setting: {setting}" )

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
    settings = _get_database_settings()
    connection = None

    try:
        connection = psycopg2.connect(**settings)
        yield connection
        connection.commit()

    except psycopg2.Error as exc:
        if connection is not None:
            connection.rollback()

        raise DatabaseConnectionError("Could not complete the database operation") from exc

    except Exception:
        if connection is not None:
            connection.rollback()
        raise

    finally:
        if connection is not None:
            connection.close()


def fetch_all(query, params=None):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()