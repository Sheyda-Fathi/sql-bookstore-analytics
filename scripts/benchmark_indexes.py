"""Measure query times before and after the indexes in sql/02_indexes.sql.
"""
import statistics
from pathlib import Path
from psycopg2 import sql
from src.bookstore.db import get_connection
INDEX_FILE = Path("sql/02_indexes.sql")
OUTPUT_FILE = Path("docs/index_benchmark.md")
RUNS = 9

INDEX_NAMES = [
    "idx_books_publisher_id",
    "idx_author_books_book_id",
    "idx_book_categories_category_id",
    "idx_orders_customer_id",
    "idx_order_items_order_id",
    "idx_order_items_book_id",
]

QUERIES = [
    ("Sales rows of one book",
     "SELECT * FROM order_items WHERE book_id = %s", (1000,)),
    ("Orders of one customer",
     "SELECT * FROM orders WHERE customer_id = %s", (386,)),
    ("Books of one publisher",
     "SELECT * FROM books WHERE publisher_id = %s", (40,)),
    ("Books of one category",
     "SELECT * FROM book_categories WHERE category_id = %s", (3,)),
    ("Authors of one book",
     "SELECT * FROM author_books WHERE book_id = %s", (1000,)),
    ("Order lines of one customer (3-table join)",
     """
     SELECT o.order_id, b.title, oi.quantity, oi.unit_price
     FROM orders o
     JOIN order_items oi ON oi.order_id = o.order_id
     JOIN books b        ON b.book_id = oi.book_id
     WHERE o.customer_id = %s
     """, (386,)),
]


def scan_nodes(node, found=None):
    if found is None:
        found = []
    node_type = node["Node Type"]
    if "Scan" in node_type and "Relation Name" in node:
        found.append(f"{node_type} on {node['Relation Name']}")
    for child in node.get("Plans", []):
        scan_nodes(child, found)
    return found


def measure(cursor, query, params):
    times = []
    scans = []
    for run in range(RUNS + 1):
        cursor.execute("EXPLAIN (ANALYZE, FORMAT JSON) " + query, params)
        plan = cursor.fetchone()[0][0]
        if run > 0:
            times.append(plan["Execution Time"])
        scans = scan_nodes(plan["Plan"])
    return statistics.median(times), ", ".join(scans)


def measure_all(cursor):
    return [measure(cursor, query, params) for _, query, params in QUERIES]


def build_table(before, after):
    lines = [
        "| Query | Before (plan) | Before (ms) | After (plan) | After (ms) | Speed-up |",
        "|---|---|---|---|---|---|",
    ]
    for (label, _, _), (t_before, plan_before), (t_after, plan_after) in zip(QUERIES, before, after):
        speedup = t_before / t_after if t_after else float("inf")
        lines.append(
            f"| {label} | {plan_before} | {t_before:.3f} | {plan_after} | {t_after:.3f} | {speedup:.1f}x |"
        )
    return "\n".join(lines)


def main():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version")
            version = cursor.fetchone()[0]

            for name in INDEX_NAMES:
                cursor.execute(sql.SQL("DROP INDEX IF EXISTS {}").format(sql.Identifier(name)))
            cursor.execute("ANALYZE")
            before = measure_all(cursor)

            cursor.execute(INDEX_FILE.read_text(encoding="utf-8"))
            after = measure_all(cursor)

    table = build_table(before, after)
    report = (
        "# Index benchmark\n\n"
        f"PostgreSQL {version}. Each query ran {RUNS} times; the table shows the median "
        "`Execution Time` reported by `EXPLAIN (ANALYZE)`.\n\n"
        f"{table}\n\n"
        "Times are small because the database is small (about 10,000 order lines). "
        "The plan columns show what changed: a sequential scan reads the whole table, "
        "an index (or bitmap) scan jumps straight to the matching rows.\n"
    )
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(report, encoding="utf-8")
    print(table)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
