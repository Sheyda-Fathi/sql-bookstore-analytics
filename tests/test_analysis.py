import pandas as pd
from src.bookstore.analysis import query_df, read_query

def test_query_df_returns_a_dataframe_with_column_names():
    frame = query_df("SELECT 1 AS one, 'a' AS letter")
    assert isinstance(frame, pd.DataFrame)
    assert list(frame.columns) == ["one", "letter"]

def test_numeric_columns_become_floats():
    frame = query_df("SELECT 1.5::numeric AS amount")
    assert frame["amount"].dtype == "float64"

def test_query_df_accepts_parameters():
    frame = query_df("SELECT %s::int AS value", (42,))
    assert frame["value"].iloc[0] == 42

def test_read_query_returns_the_sql_text():
    assert "running_total" in read_query("11_monthly_revenue_running")

def test_saved_query_runs_and_matches_the_seed():
    frame = query_df(read_query("03_orders_by_status"))
    assert frame["orders_count"].sum() == 5000
