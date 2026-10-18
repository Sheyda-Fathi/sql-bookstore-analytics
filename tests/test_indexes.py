"""Check that every foreign-key column is covered by an index."""
from src.bookstore.db import fetch_all

def test_every_foreign_key_column_has_an_index():
    unindexed = fetch_all(
        """
        SELECT c.conrelid::regclass::text AS table_name, a.attname AS column_name
        FROM pg_constraint c
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
        WHERE c.contype = 'f'
          AND NOT EXISTS (
              SELECT 1 FROM pg_index i
              WHERE i.indrelid = c.conrelid AND i.indkey[0] = c.conkey[1]
          )
        ORDER BY 1, 2
        """
    )
    assert unindexed == []
