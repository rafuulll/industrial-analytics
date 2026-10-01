"""Carrega os CSVs processados no SQLite e roda sql/queries.sql. Uso: py sql/load_sqlite.py"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "industrial.db"
TABLES = ["fact_production", "dim_machine", "kpi_daily", "alerts", "control_limits"]


def load(conn):
    for table in TABLES:
        df = pd.read_csv(PROCESSED / f"{table}.csv")
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"[sqlite] {table}: {len(df):,} linhas")


def run_queries(conn):
    sql_text = (Path(__file__).parent / "queries.sql").read_text(encoding="utf-8")
    for block in [b.strip() for b in sql_text.split(";") if b.strip()]:
        lines = block.splitlines()
        title = next((l.strip("- ").strip() for l in lines if l.startswith("-- Q")), "")
        query = "\n".join(l for l in lines if not l.strip().startswith("--"))
        if not query.strip():
            continue
        print(f"\n=== {title} ===")
        print(pd.read_sql_query(query, conn).to_string(index=False))


if __name__ == "__main__":
    with sqlite3.connect(DB_PATH) as conn:
        load(conn)
        run_queries(conn)
