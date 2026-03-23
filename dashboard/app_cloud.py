from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
EXPORT_DIR = APP_DIR / "exports"

st.set_page_config(page_title="业务数据看板（线上版）", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
<style>
.block-container {padding-top: 2rem; padding-bottom: 2rem; max-width: 1420px;}
.main-title {font-size: 2.1rem; font-weight: 800; margin-bottom: 0.15rem;}
.sub-title {color: #64748b; margin-bottom: 1rem;}
[data-testid='stMetric'] {background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.8rem 1rem; border-radius: 16px;}
</style>
""",
    unsafe_allow_html=True,
)

@st.cache_data(ttl=600)
def load_csv(name: str) -> pd.DataFrame:
    path = EXPORT_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def pct_text(v):
    return "-" if pd.isna(v) else f"{float(v) * 100:.2f}%"


def num_text(v):
    return "-" if pd.isna(v) else f"{int(float(v)):,}"


def zh_date_short(v):
    dt = pd.to_datetime(v)
    return f"{dt.month}月{dt.day}日"


def signed_pct_point(v):
    return "-" if pd.isna(v) else f"{float(v):+.1f}%"

latest = load_csv("biz_summary_latest.csv")
trend = load_csv("biz_trend_30d.csv")
alerts = load_csv("fact_alerts.csv")

st.markdown('<div class="main-title">📊 业务监控数据看板（线上版）</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">读取仓库内导出的标准化数据文件，适合多人访问统一查看。</div>', unsafe_allow_html=True)

if latest.empty:
    st.error("未读取到导出数据，请先同步 exports 目录到线上仓库。")
    st.stop()

latest["date"] = pd.to_datetime(latest["date"])
trend["date"] = pd.to_datetime(trend["date"])
latest_day = latest["date"].max().date()

with st.sidebar:
    groups = sorted(latest["biz_group"].dropna().unique().tolist())
    selected_groups = st.multiselect("业务分组", groups, default=groups)
    base = latest[latest["biz_group"].isin(selected_groups)] if selected_groups else latest.copy()
    bizs = sorted(base["biz_name"].dropna().unique().tolist())
    selected_biz = st.multiselect("业务", bizs, default=bizs)

latest_f = latest[latest["biz_group"].isin(selected_groups) & latest["biz_name"].isin(selected_biz)].copy()
trend_f = trend[trend["biz_group"].isin(selected_groups) & trend["biz_name"].isin(selected_biz)].copy()

k1, k2, k3, k4 = st.columns(4)
k1.metric("最新日期", f"{latest_day.month}月{latest_day.day}日")
k2.metric("覆盖业务数", str(latest_f["biz_name"].nunique()))
k3.metric("异常业务数", str(int(latest_f["status"].isin(["🔴", "⚠️", "⚡"]).sum())))
k4.metric("总进审量", f"{int(latest_f['total_count'].fillna(0).sum()):,}")

st.subheader("最新快照")
show = latest_f.copy().sort_values(["status", "biz_group", "biz_name"])
show["日期"] = show["date"].map(zh_date_short)
show["进审量"] = show["total_count"].map(num_text)
show["推审率"] = show["push_rate"].map(pct_text)
show["违规率"] = show["violation_rate"].map(pct_text)
show["量级偏差"] = show["total_vs_7d_pct_point"].map(signed_pct_point)
st.dataframe(show[["日期", "biz_name", "biz_group", "status", "进审量", "推审率", "违规率", "量级偏差"]].rename(columns={"biz_name": "业务", "biz_group": "分组", "status": "状态"}), use_container_width=True, hide_index=True)

st.subheader("异常列表")
if not alerts.empty:
    alerts_show = alerts.copy()
    alerts_show["date"] = pd.to_datetime(alerts_show["date"]).map(zh_date_short)
    alerts_show["total_count"] = alerts_show["total_count"].map(num_text)
    alerts_show["push_rate"] = alerts_show["push_rate"].map(pct_text)
    alerts_show["violation_rate"] = alerts_show["violation_rate"].map(pct_text)
    st.dataframe(alerts_show[["date", "biz_name", "biz_group", "status", "alert_level", "alert_reason", "total_count", "push_rate", "violation_rate"]].rename(columns={"date": "日期", "biz_name": "业务", "biz_group": "分组", "status": "状态", "alert_level": "等级", "alert_reason": "原因", "total_count": "进审量", "push_rate": "推审率", "violation_rate": "违规率"}), use_container_width=True, hide_index=True)

st.subheader("说明")
st.info("这版线上页以稳定展示为主，默认读取仓库内 exports 目录的数据文件。只要每天同步 exports，所有访问同一链接的人都会看到同一份更新结果。")
