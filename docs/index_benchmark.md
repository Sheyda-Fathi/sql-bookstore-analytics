# Index benchmark

PostgreSQL 18.3. Each query ran 9 times; the table shows the median `Execution Time` reported by `EXPLAIN (ANALYZE)`.

| Query | Before (plan) | Before (ms) | After (plan) | After (ms) | Speed-up |
|---|---|---|---|---|---|
| Sales rows of one book | Seq Scan on order_items | 0.554 | Bitmap Heap Scan on order_items | 0.048 | 11.5x |
| Orders of one customer | Seq Scan on orders | 0.258 | Bitmap Heap Scan on orders | 0.018 | 14.3x |
| Books of one publisher | Seq Scan on books | 0.155 | Bitmap Heap Scan on books | 0.033 | 4.7x |
| Books of one category | Seq Scan on book_categories | 0.263 | Bitmap Heap Scan on book_categories | 0.041 | 6.4x |
| Authors of one book | Seq Scan on author_books | 0.153 | Index Scan on author_books | 0.009 | 17.0x |
| Order lines of one customer (3-table join) | Seq Scan on order_items, Seq Scan on orders, Index Scan on books | 1.367 | Bitmap Heap Scan on orders, Index Scan on order_items, Index Scan on books | 0.082 | 16.7x |

Times are small because the database is small (about 10,000 order lines). The plan columns show what changed: a sequential scan reads the whole table, an index (or bitmap) scan jumps straight to the matching rows.
