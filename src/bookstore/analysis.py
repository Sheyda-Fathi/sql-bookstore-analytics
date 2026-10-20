from decimal import Decimal
from pathlib import Path
import pandas as pd
from src.bookstore.db import get_connection

QUERIES_DIR = Path(__file__).resolve().parents[2] / "sql" / "queries"


def query_df(query, params=None):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            frame = pd.DataFrame(cursor.fetchall(), columns=columns)
    for column in frame.columns:
        if frame[column].map(lambda value: isinstance(value, Decimal)).any():
            frame[column] = pd.to_numeric(frame[column])
    return frame

def read_query(name):
    return (QUERIES_DIR / f"{name}.sql").read_text(encoding="utf-8")
