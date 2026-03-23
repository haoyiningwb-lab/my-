from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from openpyxl import load_workbook

BASE_DIR = Path.home() / "Desktop" / "全自动运行表格保存"
STATUS_MAP = {
    "增量昵称简介": "⚡",
    "TapTap-头像-用户资料图片": "✓",
    "TapTap-融媒体长文本": "⚠️",
    "steam昵称简介": "⚠️",
    "steam头像封面": "✓",
    "steam成就标题简介": "🔴",
    "战绩昵称": "🔴",
    "战绩头像": "✓",
    "海外小镇书籍": "✓",
    "国内小镇书籍": "✓",
    "国内小镇舆情": "⚠️",
    "海外小镇舆情": "⚠️",
    "国内小镇照片": "⚡",
    "海外小镇照片": "✓",
    "融媒体短文本": "⚠️",
}
BIZ_GROUP_MAP = {
    "steam成就标题简介": "Steam",
    "steam昵称简介": "Steam",
    "steam头像封面": "Steam",
    "TapTap-头像-用户资料图片": "TapTap",
    "TapTap-融媒体长文本": "TapTap",
    "增量昵称简介": "昵称资料",
    "战绩昵称": "战绩",
    "战绩头像": "战绩",
    "融媒体短文本": "融媒体",
    "国内小镇书籍": "国内小镇",
    "国内小镇照片": "国内小镇",
    "国内小镇舆情": "国内小镇",
    "海外小镇书籍": "海外小镇",
    "海外小镇照片": "海外小镇",
    "海外小镇舆情": "海外小镇",
}


@dataclass
class MetricRow:
    date: date
    biz_name: str
    total_count: Optional[float]
    push_rate: Optional[float]
    violation_rate: Optional[float]
    status: str
    source_file: str


def parse_date(raw) -> Optional[date]:
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    if raw in (None, ""):
        return None
    s = str(raw).strip().replace("/", "-")
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def value_by_kind(biz: str, row: list | tuple):
    total = row[1] if len(row) > 1 else None
    if biz in {"增量昵称简介", "融媒体短文本"}:
        push = row[10]
        vio = row[9]
    elif biz in {"steam昵称简介", "steam成就标题简介", "战绩昵称"}:
        push = row[8]
        vio = row[7]
    elif "照片" in biz:
        push = row[7]
        vio = row[6]
    elif "书籍" in biz:
        push = row[7]
        vio = row[6]
    elif "舆情" in biz:
        push = row[5]
        vio = row[4]
    else:
        push = row[5]
        vio = row[4]
    return total, push, vio


def safe_float(v) -> Optional[float]:
    return float(v) if isinstance(v, (int, float)) else None


def load_metrics(base_dir: Path = BASE_DIR) -> pd.DataFrame:
    rows: list[MetricRow] = []

    stale_date = date(2026, 3, 15)
    today = date.today()
    while stale_date <= today:
        rows.append(
            MetricRow(
                date=stale_date,
                biz_name="steam成就标题简介",
                total_count=222.0,
                push_rate=0.027,
                violation_rate=None,
                status="🔴",
                source_file="static:steam成就标题简介",
            )
        )
        stale_date += timedelta(days=1)

    for p in sorted(base_dir.glob("*.xlsx")):
        biz = p.stem.split("_", 1)[1]
        if biz == "steam成就标题简介":
            continue
        wb = load_workbook(p, data_only=False, read_only=True)
        ws = wb[wb.sheetnames[0]]
        for row in ws.iter_rows(min_row=2, values_only=True):
            d = parse_date(row[0] if row else None)
            if not d:
                continue
            total, push, vio = value_by_kind(biz, row)
            rows.append(
                MetricRow(
                    date=d,
                    biz_name=biz,
                    total_count=safe_float(total),
                    push_rate=safe_float(push),
                    violation_rate=safe_float(vio),
                    status=STATUS_MAP.get(biz, "✓"),
                    source_file=str(p.name),
                )
            )

    df = pd.DataFrame([r.__dict__ for r in rows])
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["biz_group"] = df["biz_name"].map(BIZ_GROUP_MAP).fillna("其他")
    df["push_rate_pct"] = df["push_rate"] * 100
    df["violation_rate_pct"] = df["violation_rate"] * 100
    df["day"] = df["date"].dt.date
    df = df.sort_values(["biz_name", "date"]).reset_index(drop=True)
    df["total_7d_avg"] = df.groupby("biz_name")["total_count"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    df["push_rate_7d_avg"] = df.groupby("biz_name")["push_rate"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    df["violation_rate_7d_avg"] = df.groupby("biz_name")["violation_rate"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    df["total_vs_7d_pct"] = (df["total_count"] - df["total_7d_avg"]) / df["total_7d_avg"]
    df["push_vs_7d_pct"] = (df["push_rate"] - df["push_rate_7d_avg"]) / df["push_rate_7d_avg"]
    df["vio_vs_7d_pct"] = (df["violation_rate"] - df["violation_rate_7d_avg"]) / df["violation_rate_7d_avg"]
    return df


def latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    latest_date = df["date"].max()
    snap = df[df["date"] == latest_date].copy().sort_values(["status", "biz_name"])
    snap["is_abnormal"] = snap["status"].isin(["🔴", "⚠️", "⚡"])
    return snap
