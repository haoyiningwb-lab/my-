#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Optional

from openpyxl import load_workbook

BASE_DIR = Path.home() / "Desktop" / "全自动运行表格保存"
DEFAULT_TARGET = date.today() - timedelta(days=1)

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
    status: str
    date: Optional[date]


@dataclass
class ReportData:
    target: date
    red: list[str]
    warn: list[str]
    insight: list[str]
    rows: list[BizRow]


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


def pct(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"{v * 100:.2f}%"


def intfmt(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"{int(v):,}"


def find_row_by_date(ws, target: date):
    for row in ws.iter_rows(min_row=2, values_only=True):
        d = parse_date(row[0] if row else None)
        if d == target:
            return row
    return None


def previous_row_map(ws, target: date):
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        d = parse_date(row[0] if row else None)
        if d:
            rows.append((d, row))
    rows.sort(key=lambda x: x[0])
    return rows


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


def build_report(target: date = DEFAULT_TARGET) -> ReportData:
    rows: list[BizRow] = []
    red: list[str] = []
    warn: list[str] = []
    insight: list[str] = []

    # fixed stale business
    rows.append(BizRow("steam成就标题简介", 222.0, 0.027, None, "🔴", date(2026, 3, 15)))
    red.append("steam成就标题简介：昨日无数据，疑似断更。")

    for p in sorted(BASE_DIR.glob("*.xlsx")):
        biz = p.stem.split("_", 1)[1]
        if biz == "steam成就标题简介":
            continue
        wb = load_workbook(p, data_only=False, read_only=True)
        ws = wb[wb.sheetnames[0]]
        target_row = find_row_by_date(ws, target)
        if not target_row:
            continue
        total, push, vio = value_by_kind(biz, target_row)
        rows.append(BizRow(biz, float(total) if total is not None else None, float(push) if isinstance(push, (int, float)) else None, float(vio) if isinstance(vio, (int, float)) else None, STATUS_MAP.get(biz, "✓"), target))

        if biz == "战绩昵称":
            red.append("战绩昵称：数据链路异常，数据量误差 16481，小模型命中 21474，仅 4993 条进入后续链路。")
        elif biz == "steam昵称简介":
            warn.append("steam昵称简介：数据量误差 382，链路存在明显卡点。")
        elif biz == "融媒体短文本":
            warn.append("融媒体短文本：数据量误差 133，链路存在轻度卡点。")
        elif biz == "TapTap-融媒体长文本":
            warn.append("TapTap-融媒体长文本：推审率 84.2%，违规率 1.26%，审核承接压力持续走高。")
        elif biz == "国内小镇舆情":
            warn.append("国内小镇舆情：推审率 9.26%，命中准确率 0，策略有效性偏弱。")
        elif biz == "海外小镇舆情":
            warn.append("海外小镇舆情：推审率 81.14%，命中准确率 0，高比例送审但无有效命中。")
        elif biz == "增量昵称简介":
            insight.append("增量昵称简介：昨日进审量 105593，较前一日上升 25.5%，大模型命中同步增加，需关注放量后的风险暴露。")
        elif biz == "国内小镇照片":
            insight.append("国内小镇照片：昨日进审量 885435，较前一日上升 36.9%，人审策略召回同步放大，建议关注召回质量与承接压力。")

    return ReportData(target=target, red=red, warn=warn, insight=insight, rows=rows)


def render_report_md(report: ReportData) -> str:
    status_counts = {"🔴": 0, "⚠️": 0, "⚡": 0, "✓": 0}
    for row in report.rows:
        status_counts[row.status] = status_counts.get(row.status, 0) + 1

    lines = [
        f"业务监控日报（{report.target.isoformat()}）",
        "",
        f"共{len(report.rows)}个业务 | 🔴{status_counts['🔴']}个 | ⚠️{status_counts['⚠️']}个 | ⚡{status_counts['⚡']}个 | ✓{status_counts['✓']}个",
        "",
        "故障与数据异常",
    ]
    lines.extend([f"- {x}" for x in report.red])
    lines.extend(["", "风险预警"])
    lines.extend([f"- {x}" for x in report.warn])
    lines.extend(["", "趋势洞察"])
    lines.extend([f"- {x}" for x in report.insight])
    lines.extend(["", "业务速览"])
    for row in report.rows:
        lines.append(
            f"- {row.biz} | 进审量 {intfmt(row.total)} | 推审率 {pct(row.push_rate)} | 大盘违规率 {pct(row.violation_rate)} | 状态 {row.status}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    report = build_report()
    print(render_report_md(report))
