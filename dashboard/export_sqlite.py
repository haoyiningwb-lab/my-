from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from export_duckdb import build_tables

OUT_DIR = Path(__file__).resolve().parent / "exports"
DB_PATH = OUT_DIR / "dashboard.sqlite"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tables = build_tables()
    con = sqlite3.connect(DB_PATH)
    try:
        for name, df in tables.items():
            if isinstance(df, pd.DataFrame):
                df.to_sql(name, con, if_exists="replace", index=False)
        cur = con.cursor()
        for name in tables:
            count = cur.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            print(f"{name}: {count}")
        con.commit()
        print(f"SQLite exported to: {DB_PATH}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
