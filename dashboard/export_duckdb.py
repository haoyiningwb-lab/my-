from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from data_loader import load_metrics, latest_snapshot

OUT_DIR = Path(__file__).resolve().parent / "exports"
DB_PATH = OUT_DIR / "dashboard.duckdb"


def signed_pct(v):
    if pd.isna(v):
        return None
    return round(v * 100, 2)


def build_tables() -> dict[str, pd.DataFrame]:
    df = load_metrics()
    if df.empty:
        raise SystemExit("No data loaded from source xlsx files.")

    latest = latest_snapshot(df)

    fact_daily_metrics = df.copy()
    fact_daily_metrics["date"] = fact_daily_metrics["date"].dt.date.astype(str)

    dim_business = (
        df[["biz_name", "biz_group", "base_status", "source_file"]]
        .sort_values(["biz_group", "biz_name"])
        .drop_duplicates(subset=["biz_name"])
        .rename(columns={
            "biz_name": "business_name",
            "biz_group": "business_group",
            "base_status": "default_status",
            "source_file": "latest_source_file",
        })
    )

    biz_summary_latest = latest[[
        "biz_name", "biz_group", "date", "status", "freshness_days", "freshness_label",
        "total_count", "push_rate", "violation_rate", "review_count", "reject_count", "error_value",
        "total_7d_avg", "push_rate_7d_avg", "violation_rate_7d_avg",
        "total_vs_7d_pct", "push_vs_7d_pct", "vio_vs_7d_pct", "source_file"
    ]].copy()
    biz_summary_latest["date"] = biz_summary_latest["date"].dt.date.astype(str)
    biz_summary_latest["total_vs_7d_pct_point"] = biz_summary_latest["total_vs_7d_pct"].map(signed_pct)
    biz_summary_latest["push_vs_7d_pct_point"] = biz_summary_latest["push_vs_7d_pct"].map(signed_pct)
    biz_summary_latest["vio_vs_7d_pct_point"] = biz_summary_latest["vio_vs_7d_pct"].map(signed_pct)

    fact_alerts = latest[(latest["status"].isin(["🔴", "⚠️", "⚡"])) | (latest["freshness_days"] > 0)].copy()
    fact_alerts["date"] = fact_alerts["date"].dt.date.astype(str)
    fact_alerts["alert_level"] = fact_alerts["status"].map({"🔴": "high", "⚠️": "medium", "⚡": "medium", "✓": "normal"})
    fact_alerts["alert_reason"] = fact_alerts.apply(
        lambda r: "数据滞后" if r["freshness_days"] > 0 else ("状态异常" if r["status"] in ["🔴", "⚠️", "⚡"] else "正常"), axis=1
    )

    biz_trend_30d = df.sort_values(["biz_name", "date"]).copy()
    latest_day = pd.to_datetime(df["date"].max())
    biz_trend_30d = biz_trend_30d[biz_trend_30d["date"] >= latest_day - pd.Timedelta(days=29)]
    biz_trend_30d["date"] = biz_trend_30d["date"].dt.date.astype(str)

    return {
        "fact_daily_metrics": fact_daily_metrics,
        "dim_business": dim_business,
        "biz_summary_latest": biz_summary_latest,
        "fact_alerts": fact_alerts,
        "biz_trend_30d": biz_trend_30d,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tables = build_tables()
    con = duckdb.connect(str(DB_PATH))
    try:
        for name, df in tables.items():
            con.register("tmp_df", df)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM tmp_df")
            con.unregister("tmp_df")
        print(f"DuckDB exported to: {DB_PATH}")
        for name in tables:
            count = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            print(f"{name}: {count}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
