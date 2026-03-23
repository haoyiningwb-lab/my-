from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_loader import load_metrics, latest_snapshot

OUT_DIR = Path(__file__).resolve().parent / "exports"


def signed_pct(v):
    if pd.isna(v):
        return None
    return round(v * 100, 2)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_metrics()
    if df.empty:
        raise SystemExit("No data loaded from source xlsx files.")

    latest = latest_snapshot(df)

    fact_daily_metrics = df.copy()
    fact_daily_metrics["date"] = fact_daily_metrics["date"].dt.date.astype(str)
    fact_daily_metrics.to_csv(OUT_DIR / "fact_daily_metrics.csv", index=False)

    dim_business = (
        df[["biz_name", "biz_group", "base_status", "source_file"]]
        .sort_values(["biz_group", "biz_name"])
        .drop_duplicates(subset=["biz_name"])
        .rename(columns={"biz_name": "business_name", "biz_group": "business_group", "base_status": "default_status", "source_file": "latest_source_file"})
    )
    dim_business.to_csv(OUT_DIR / "dim_business.csv", index=False)

    latest_summary = latest[[
        "biz_name",
        "biz_group",
        "date",
        "status",
        "freshness_days",
        "freshness_label",
        "total_count",
        "push_rate",
        "violation_rate",
        "review_count",
        "reject_count",
        "error_value",
        "total_7d_avg",
        "push_rate_7d_avg",
        "violation_rate_7d_avg",
        "total_vs_7d_pct",
        "push_vs_7d_pct",
        "vio_vs_7d_pct",
        "source_file",
    ]].copy()
    latest_summary["date"] = latest_summary["date"].dt.date.astype(str)
    latest_summary["total_vs_7d_pct_point"] = latest_summary["total_vs_7d_pct"].map(signed_pct)
    latest_summary["push_vs_7d_pct_point"] = latest_summary["push_vs_7d_pct"].map(signed_pct)
    latest_summary["vio_vs_7d_pct_point"] = latest_summary["vio_vs_7d_pct"].map(signed_pct)
    latest_summary.to_csv(OUT_DIR / "biz_summary_latest.csv", index=False)

    alerts = latest[(latest["status"].isin(["🔴", "⚠️", "⚡"])) | (latest["freshness_days"] > 0)].copy()
    alerts["date"] = alerts["date"].dt.date.astype(str)
    alerts["alert_level"] = alerts["status"].map({"🔴": "high", "⚠️": "medium", "⚡": "medium", "✓": "normal"})
    alerts["alert_reason"] = alerts.apply(
        lambda r: "数据滞后" if r["freshness_days"] > 0 else ("状态异常" if r["status"] in ["🔴", "⚠️", "⚡"] else "正常"), axis=1
    )
    alerts.to_csv(OUT_DIR / "fact_alerts.csv", index=False)

    trend_30d = df.sort_values(["biz_name", "date"]).copy()
    latest_day = pd.to_datetime(df["date"].max())
    trend_30d = trend_30d[trend_30d["date"] >= latest_day - pd.Timedelta(days=29)]
    trend_30d["date"] = trend_30d["date"].dt.date.astype(str)
    trend_30d.to_csv(OUT_DIR / "biz_trend_30d.csv", index=False)

    with open(OUT_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(
            "# BI 导出数据\n\n"
            "- fact_daily_metrics.csv：按日按业务明细事实表\n"
            "- dim_business.csv：业务维表\n"
            "- biz_summary_latest.csv：最新快照汇总表\n"
            "- fact_alerts.csv：异常/预警表\n"
            "- biz_trend_30d.csv：近30天趋势表\n"
        )

    print(f"Exported BI files to: {OUT_DIR}")


if __name__ == "__main__":
    main()
