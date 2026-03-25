#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import math
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.data_loader import load_metrics

DEFAULT_TARGET = date.today() - timedelta(days=1)
TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "team" / "DAILY-REPORT-TEMPLATE.md"

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


@dataclass
class BizRow:
    biz: str
    total: Optional[float]
    push_rate: Optional[float]
    violation_rate: Optional[float]
    error_value: Optional[float]
    status: str
    date: Optional[date]


@dataclass
class ReportData:
    target: date
    red: list[str]
    warn: list[str]
    insight: list[str]
    rows: list[BizRow]


def is_blank(v: Optional[float]) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def pct(v: Optional[float]) -> str:
    return "-" if is_blank(v) else f"{v * 100:.2f}%"


def intfmt(v: Optional[float]) -> str:
    return "-" if is_blank(v) else f"{int(v):,}"


def make_gap_text(v: Optional[float]) -> str:
    return "-" if is_blank(v) else f"{int(v):,}"


def build_report(target: date = DEFAULT_TARGET) -> ReportData:
    df = load_metrics()
    if df.empty:
        return ReportData(target=target, red=[], warn=[], insight=[], rows=[])

    rows: list[BizRow] = []
    red: list[str] = []
    warn: list[str] = []
    insight: list[str] = []

    latest_date = df["date"].max().date()
    biz_names = sorted(df["biz_name"].dropna().unique().tolist())

    for biz in biz_names:
        biz_df = df[df["biz_name"] == biz].sort_values("date")
        today_row = biz_df[biz_df["date"].dt.date == target]
        prev_row = biz_df[biz_df["date"].dt.date == (target - timedelta(days=1))]

        if today_row.empty:
            if biz == "steam成就标题简介":
                last = biz_df.iloc[-1]
                rows.append(BizRow(biz, last.get("total_count"), last.get("push_rate"), last.get("violation_rate"), last.get("error_value"), "🔴", last["date"].date()))
                red.append("steam成就标题简介：昨日无数据，疑似断更。")
            continue

        cur = today_row.iloc[-1]
        prev = prev_row.iloc[-1] if not prev_row.empty else None
        total = float(cur["total_count"]) if cur.get("total_count") is not None else None
        push = float(cur["push_rate"]) if cur.get("push_rate") is not None else None
        vio = float(cur["violation_rate"]) if cur.get("violation_rate") is not None else None
        err = float(cur["error_value"]) if cur.get("error_value") is not None else None
        rows.append(BizRow(biz, total, push, vio, err, STATUS_MAP.get(biz, "✓"), target))

        if biz == "战绩昵称":
            red.append(f"战绩昵称：数据链路异常，数据差 {make_gap_text(err)}，按当前口径可视为 {make_gap_text(err)} 条未回传，需优先复核上下游流转与结果回传，避免异常继续放大。")
        elif biz == "steam昵称简介":
            warn.append(f"steam昵称简介：链路存在明显卡点，数据差 {make_gap_text(err)}，按当前口径可视为 {make_gap_text(err)} 条未回传，建议优先核查中间节点承接情况。")
        elif biz == "融媒体短文本":
            warn.append(f"融媒体短文本：链路存在轻度卡点，数据差 {make_gap_text(err)}，按当前口径可视为 {make_gap_text(err)} 条未回传，建议继续观察并排查堵点。")
        elif biz == "TapTap-融媒体长文本":
            warn.append(f"TapTap-融媒体长文本：推审率 {pct(push)}，大盘违规率 {pct(vio)}，审核承接压力偏高。")
        elif biz == "国内小镇舆情":
            warn.append(f"国内小镇舆情：推审率 {pct(push)}，大盘违规率 {pct(vio)}，策略有效性需继续观察。")
        elif biz == "海外小镇舆情":
            warn.append(f"海外小镇舆情：推审率 {pct(push)}，大盘违规率 {pct(vio)}，高比例送审表现需继续核查。")
        elif biz in {"增量昵称简介", "国内小镇照片"}:
            if prev is not None and prev.get("total_count") not in (None, 0):
                growth = (float(cur["total_count"]) - float(prev["total_count"])) / float(prev["total_count"])
                verb = "上升" if growth >= 0 else "下降"
                tail = "需关注量级变化后的风险暴露。" if biz == "增量昵称简介" else "建议关注召回质量与承接压力。"
                insight.append(f"{biz}：昨日进审量 {intfmt(total)}，较前一日{verb} {abs(growth) * 100:.1f}%，{tail}")
            else:
                tail = "需关注量级变化后的风险暴露。" if biz == "增量昵称简介" else "建议关注召回质量与承接压力。"
                insight.append(f"{biz}：昨日进审量 {intfmt(total)}，{tail}")

    rows.sort(key=lambda x: (x.status, x.biz))
    return ReportData(target=target, red=red, warn=warn, insight=insight, rows=rows)


def render_report_table_values(report: ReportData) -> list[list[str]]:
    return [["业务", "进审量", "推审率", "大盘违规率", "状态"]] + [
        [row.biz, intfmt(row.total), pct(row.push_rate), pct(row.violation_rate), row.status]
        for row in report.rows
    ]


def render_report_md(report: ReportData) -> str:
    status_counts = {"🔴": 0, "⚠️": 0, "⚡": 0, "✓": 0}
    for row in report.rows:
        status_counts[row.status] = status_counts.get(row.status, 0) + 1

    lines = [
        f"# 业务监控日报（{report.target.isoformat()}）",
        "",
        f"共{len(report.rows)}个业务 | 🔴{status_counts['🔴']}个 | ⚠️{status_counts['⚠️']}个 | ⚡{status_counts['⚡']}个 | ✓{status_counts['✓']}个",
        "",
        "## 故障与数据异常",
    ]
    lines.extend([f"- {x}" for x in report.red] or ["- 无"])
    lines.extend(["", "## 风险预警"])
    lines.extend([f"- {x}" for x in report.warn] or ["- 无"])
    lines.extend(["", "## 趋势洞察"])
    lines.extend([f"- {x}" for x in report.insight] or ["- 无"])
    lines.extend(["", "## 业务速览", "", "| 业务 | 进审量 | 推审率 | 大盘违规率 | 状态 |", "| --- | ---: | ---: | ---: | --- |"])
    for row in report.rows:
        lines.append(f"| {row.biz} | {intfmt(row.total)} | {pct(row.push_rate)} | {pct(row.violation_rate)} | {row.status} |")
    return "\n".join(lines)


if __name__ == "__main__":
    report = build_report()
    print(render_report_md(report))
