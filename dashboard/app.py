from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import latest_snapshot, load_metrics

st.set_page_config(page_title="业务数据看板", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
<style>
.block-container {padding-top: 2.4rem; padding-bottom: 2rem; max-width: 1420px;}
h1, h2, h3 {scroll-margin-top: 90px;}
.main-title {font-size: 2.15rem; font-weight: 800; margin-bottom: 0.15rem; display:flex; align-items:center; gap:10px;}
.sub-title {color: #64748b; margin-bottom: 1.15rem;}
.card {background: linear-gradient(135deg,#0f172a 0%,#1e293b 100%); padding: 1rem 1.1rem; border-radius: 18px; color: white; box-shadow: 0 8px 24px rgba(15,23,42,.18);}
.card small {opacity: .86;}
[data-testid='stMetric'] {background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.8rem 1rem; border-radius: 16px;}
[data-testid='stMetricValue'] {font-size: 1.55rem;}
[data-testid='stSidebar'] {background: linear-gradient(180deg,#eef2ff 0%,#f8fafc 45%,#fefefe 100%); border-right:1px solid #dbe4ff;}
[data-testid='stSidebar'] .block-container {padding-top: 0.8rem; padding-left: 0.9rem; padding-right: 0.9rem;}
.sidebar-panel {background: linear-gradient(180deg,rgba(255,255,255,.95) 0%,rgba(248,250,252,.98) 100%); border:1px solid #dbe4ff; border-radius:20px; padding:15px 14px 10px 14px; box-shadow: 0 10px 28px rgba(59,130,246,.08); margin-bottom: 12px;}
.side-kpi {background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%); border:1px solid #dbe4ff; border-radius:14px; padding:10px 12px; margin-top:10px; box-shadow: inset 0 1px 0 rgba(255,255,255,.9);}
.small-muted {font-size:12px; color:#64748b;}
</style>
""",
    unsafe_allow_html=True,
)

@st.cache_data(ttl=300)
def get_df():
    return load_metrics()


def pct_text(v):
    return "-" if pd.isna(v) else f"{v * 100:.2f}%"


def num_text(v):
    return "-" if pd.isna(v) else f"{int(v):,}"


def signed_pct(v):
    return "-" if pd.isna(v) else f"{v * 100:+.1f}%"


def zh_date(v):
    dt = pd.to_datetime(v)
    return f"{dt.year}年{dt.month}月{dt.day}日"


def short_zh_date(v):
    dt = pd.to_datetime(v)
    return f"{dt.month}月{dt.day}日"


def format_axis_date(series: pd.Series) -> list[str]:
    return [short_zh_date(x) for x in series]


def add_line_labels(fig, text_col: str):
    fig.update_traces(text=text_col, textposition="top center", cliponaxis=False, textfont=dict(size=10), mode="lines+markers+text")
    return fig


def style_single_series_line(fig, date_vals, yaxis_title=None, percent_axis=False):
    fig.update_traces(line=dict(width=2.2, color="#5B6CFF"), marker=dict(size=6, color="#5B6CFF"), textposition="top center", cliponaxis=False, textfont=dict(size=10), mode="lines+markers+text")
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=72, b=36),
        xaxis_title=None,
        yaxis_title=yaxis_title,
        title=dict(y=0.95),
        xaxis=dict(tickmode="array", tickvals=date_vals, automargin=True, tickangle=0),
        showlegend=False,
    )
    if percent_axis:
        fig.update_layout(yaxis_tickformat='.2%')
    return fig


def compact_num_label(v):
    if pd.isna(v):
        return "-"
    if v >= 100000000:
        return f"{v/100000000:.2f}亿"
    if v >= 10000:
        return f"{v/10000:.1f}万"
    return f"{int(v)}"


df = get_df()
st.markdown('<div class="main-title">📊 业务监控可视化看板</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">基于本地落地文件自动更新，适合日常监控、趋势观察和异常排查。</div>', unsafe_allow_html=True)

if df.empty:
    st.error("未读取到数据，请检查本地落地目录是否存在可用 xlsx 文件。")
    st.stop()

snapshot = latest_snapshot(df)
global_latest = df["date"].max().date()
all_groups = sorted(df["biz_group"].dropna().unique().tolist())
all_biz = sorted(df["biz_name"].dropna().unique().tolist())

with st.sidebar:
    st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
    st.markdown("### 筛选中心")
    st.caption("支持按分组、业务、状态和时间快速切换，后续我还能继续加快捷筛选。")

    default_all_groups = st.checkbox("全部业务分组", value=True)
    selected_groups = st.multiselect("选择业务分组", all_groups, default=all_groups if default_all_groups else all_groups[:2], placeholder="选择业务分组")
    if not selected_groups:
        selected_groups = all_groups

    base = df[df["biz_group"].isin(selected_groups)]
    biz_names = sorted(base["biz_name"].dropna().unique().tolist())
    default_all_biz = st.checkbox("全部业务", value=True)
    selected_biz = st.multiselect("选择业务", biz_names, default=biz_names if default_all_biz else biz_names[: min(5, len(biz_names))], placeholder="选择业务")
    if not selected_biz:
        selected_biz = biz_names

    days = st.select_slider("观察窗口", options=[7, 15, 30, 60], value=30)
    status_filter = st.segmented_control("状态筛选", options=["全部", "异常", "正常"], default="全部", selection_mode="single")
    only_abnormal = st.toggle("仅保留异常业务", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

filtered = df[df["biz_group"].isin(selected_groups) & df["biz_name"].isin(selected_biz)].copy()
filtered = filtered[filtered["date"] >= (pd.Timestamp(global_latest) - pd.Timedelta(days=days - 1))]
snap_filtered = snapshot[snapshot["biz_group"].isin(selected_groups) & snapshot["biz_name"].isin(selected_biz)].copy()
if status_filter == "异常":
    snap_filtered = snap_filtered[snap_filtered["status"].isin(["🔴", "⚠️", "⚡"])]
elif status_filter == "正常":
    snap_filtered = snap_filtered[snap_filtered["status"] == "✓"]
if only_abnormal:
    snap_filtered = snap_filtered[snap_filtered["status"].isin(["🔴", "⚠️", "⚡"])]
    filtered = filtered[filtered["biz_name"].isin(snap_filtered["biz_name"])]

with st.sidebar:
    abnormal_cnt = int(snap_filtered["status"].isin(["🔴", "⚠️", "⚡"]).sum()) if not snap_filtered.empty else 0
    stale_cnt = int((snap_filtered["freshness_days"] > 0).sum()) if not snap_filtered.empty else 0
    st.markdown(f'<div class="side-kpi"><strong>全局最新日期</strong><br><span class="small-muted">{zh_date(global_latest)}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-kpi"><strong>当前业务数</strong><br><span class="small-muted">{snap_filtered["biz_name"].nunique()} 个</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-kpi"><strong>异常业务</strong><br><span class="small-muted">{abnormal_cnt} 个</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-kpi"><strong>数据滞后</strong><br><span class="small-muted">{stale_cnt} 个</span></div>', unsafe_allow_html=True)

hero1, hero2 = st.columns([1.6, 1])
with hero1:
    st.markdown(
        f'''<div class="card"><div style="font-size:1.05rem;font-weight:700">今日总览</div>
        <div style="margin-top:.6rem;font-size:2rem;font-weight:800">{zh_date(global_latest)}</div>
        <small>已覆盖 {snap_filtered['biz_name'].nunique()} 个业务，异常 {int(snap_filtered['status'].isin(['🔴', '⚠️', '⚡']).sum())} 个。</small></div>''',
        unsafe_allow_html=True,
    )
with hero2:
    stale_cnt = int((snap_filtered["freshness_days"] > 0).sum()) if not snap_filtered.empty else 0
    st.markdown(
        f'''<div class="card"><div style="font-size:1.05rem;font-weight:700">数据新鲜度</div>
        <div style="margin-top:.6rem;font-size:2rem;font-weight:800">{stale_cnt} 个滞后</div>
        <small>若某业务未更新到全局最新日期，会直接在看板中标红提示。</small></div>''',
        unsafe_allow_html=True,
    )

k1, k2, k3, k4 = st.columns(4)
k1.metric("总进审量", f"{int(snap_filtered['total_count'].fillna(0).sum()):,}")
k2.metric("平均推审率", pct_text(snap_filtered['push_rate'].mean()))
k3.metric("平均违规率", pct_text(snap_filtered['violation_rate'].mean()))
k4.metric("红色业务", str(int((snap_filtered['status'] == '🔴').sum())))

trend_tab, biz_tab, alert_tab = st.tabs(["总览趋势", "业务钻取", "异常排查"])

with trend_tab:
    c1, c2 = st.columns([1.7, 1.1])
    with c1:
        trend_df = filtered.groupby("date", as_index=False).agg(total_count=("total_count", "sum"))
        trend_df["date_label"] = format_axis_date(trend_df["date"])
        trend_df["label"] = trend_df["total_count"].map(compact_num_label)
        fig = px.line(trend_df, x="date_label", y="total_count", markers=True, text="label", title="总进审量趋势", template="plotly_white")
        fig = style_single_series_line(fig, trend_df['date_label'], yaxis_title="进审量", percent_axis=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        status_df = snap_filtered.groupby("status", as_index=False).size().sort_values("status")
        fig = px.bar(status_df, x="status", y="size", color="status", text="size", title="最新状态分布", template="plotly_white")
        fig.update_layout(height=360, margin=dict(l=20, r=20, t=70, b=20), showlegend=False, xaxis_title="状态", yaxis_title="业务数", title=dict(y=0.96))
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        push_df = filtered.groupby("date", as_index=False).agg(push_rate=("push_rate", "mean"))
        push_df["date_label"] = format_axis_date(push_df["date"])
        push_df["label"] = push_df["push_rate"].map(lambda x: "-" if pd.isna(x) else f"{x*100:.2f}%")
        fig = px.line(push_df, x="date_label", y="push_rate", markers=True, text="label", title="平均推审率趋势", template="plotly_white")
        fig = style_single_series_line(fig, push_df['date_label'], yaxis_title="推审率", percent_axis=True)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        vio_df = filtered.groupby("date", as_index=False).agg(violation_rate=("violation_rate", "mean"))
        vio_df["date_label"] = format_axis_date(vio_df["date"])
        vio_df["label"] = vio_df["violation_rate"].map(lambda x: "-" if pd.isna(x) else f"{x*100:.2f}%")
        fig = px.line(vio_df, x="date_label", y="violation_rate", markers=True, text="label", title="平均违规率趋势", template="plotly_white")
        fig = style_single_series_line(fig, vio_df['date_label'], yaxis_title="违规率", percent_axis=True)
        st.plotly_chart(fig, use_container_width=True)

with biz_tab:
    focus_candidates = sorted(snap_filtered["biz_name"].unique().tolist()) if not snap_filtered.empty else sorted(filtered["biz_name"].unique().tolist())
    if not focus_candidates:
        st.warning("当前筛选条件下暂无业务数据。")
    else:
        focus_biz = st.selectbox("选择业务", focus_candidates)
        focus_df = filtered[filtered["biz_name"] == focus_biz].copy().sort_values("date")
        top1, top2, top3, top4 = st.columns(4)
        if not focus_df.empty:
            latest_row = focus_df.iloc[-1]
            top1.metric("最新进审量", num_text(latest_row["total_count"]))
            top2.metric("最新推审率", pct_text(latest_row["push_rate"]))
            top3.metric("最新违规率", pct_text(latest_row["violation_rate"]))
            top4.metric("数据日期", zh_date(latest_row["date"]))

            focus_df["date_label"] = format_axis_date(focus_df["date"])
            focus_df["count_label"] = focus_df["total_count"].map(compact_num_label)
            focus_df["avg_label"] = focus_df["total_7d_avg"].map(compact_num_label)
            fig = px.line(focus_df, x="date_label", y=["total_count", "total_7d_avg"], markers=True, title=f"{focus_biz} · 进审量 vs 7日均量", template="plotly_white")
            fig.update_layout(height=370, margin=dict(l=20, r=20, t=72, b=36), legend_title="指标", xaxis_title=None, yaxis_title="进审量", title=dict(y=0.95), xaxis=dict(tickmode='array', tickvals=focus_df['date_label'], automargin=True))
            fig.data[0].name = "进审量"
            fig.data[1].name = "7日均量"
            fig.data[0].text = focus_df["count_label"]
            fig.data[1].text = focus_df["avg_label"]
            fig.data[0].update(line=dict(width=2.2, color="#5B6CFF"), marker=dict(size=6, color="#5B6CFF"), cliponaxis=False, textposition="top center", textfont=dict(size=10), mode="lines+markers+text")
            fig.data[1].update(line=dict(width=2.2, color="#F59E0B", dash="dot"), marker=dict(size=6, color="#F59E0B"), cliponaxis=False, textposition="top center", textfont=dict(size=10), mode="lines+markers+text")
            st.plotly_chart(fig, use_container_width=True)

            focus_df["push_label"] = focus_df["push_rate"].map(pct_text)
            focus_df["vio_label"] = focus_df["violation_rate"].map(pct_text)
            fig2 = px.line(focus_df, x="date_label", y=["push_rate", "violation_rate"], markers=True, title=f"{focus_biz} · 推审率 / 违规率趋势", template="plotly_white")
            fig2.update_layout(height=370, margin=dict(l=20, r=20, t=72, b=36), yaxis_tickformat='.2%', xaxis_title=None, yaxis_title="比率", title=dict(y=0.95), xaxis=dict(tickmode='array', tickvals=focus_df['date_label'], automargin=True))
            fig2.data[0].name = "推审率"
            fig2.data[1].name = "违规率"
            fig2.data[0].text = focus_df["push_label"]
            fig2.data[1].text = focus_df["vio_label"]
            fig2.data[0].update(line=dict(width=2.2, color="#5B6CFF"), marker=dict(size=6, color="#5B6CFF"), cliponaxis=False, textposition="top center", textfont=dict(size=10), mode="lines+markers+text")
            fig2.data[1].update(line=dict(width=2.2, color="#EF4444"), marker=dict(size=6, color="#EF4444"), cliponaxis=False, textposition="top center", textfont=dict(size=10), mode="lines+markers+text")
            st.plotly_chart(fig2, use_container_width=True)

            show_cols = focus_df[["date", "total_count", "total_7d_avg", "push_rate", "violation_rate", "review_count", "reject_count", "error_value", "source_file"]].copy()
            show_cols["date"] = show_cols["date"].map(zh_date)
            show_cols["total_count"] = show_cols["total_count"].map(num_text)
            show_cols["total_7d_avg"] = show_cols["total_7d_avg"].map(num_text)
            show_cols["push_rate"] = show_cols["push_rate"].map(pct_text)
            show_cols["violation_rate"] = show_cols["violation_rate"].map(pct_text)
            show_cols["review_count"] = show_cols["review_count"].map(num_text)
            show_cols["reject_count"] = show_cols["reject_count"].map(num_text)
            show_cols["error_value"] = show_cols["error_value"].map(num_text)
            st.dataframe(show_cols.rename(columns={"date": "日期", "total_count": "进审量", "total_7d_avg": "7日均量", "push_rate": "推审率", "violation_rate": "违规率", "review_count": "人审量", "reject_count": "驳回量", "error_value": "误差值", "source_file": "来源文件"}), use_container_width=True, hide_index=True)

with alert_tab:
    alerts = snap_filtered.copy()
    alerts["进审量"] = alerts["total_count"].map(num_text)
    alerts["推审率"] = alerts["push_rate"].map(pct_text)
    alerts["违规率"] = alerts["violation_rate"].map(pct_text)
    alerts["量级偏差"] = alerts["total_vs_7d_pct"].map(signed_pct)
    alerts["数据新鲜度"] = alerts["freshness_label"]

    st.subheader("优先排查列表")
    abnormal = alerts[(alerts["status"].isin(["🔴", "⚠️", "⚡"])) | (alerts["freshness_days"] > 0)].copy()
    st.dataframe(abnormal[["biz_name", "biz_group", "status", "数据新鲜度", "进审量", "推审率", "违规率", "量级偏差", "source_file"]].rename(columns={"biz_name": "业务", "biz_group": "分组", "status": "状态", "source_file": "来源文件"}), use_container_width=True, hide_index=True)

    st.subheader("最新业务明细")
    st.dataframe(alerts[["biz_name", "biz_group", "status", "数据新鲜度", "进审量", "推审率", "违规率", "量级偏差"]].rename(columns={"biz_name": "业务", "biz_group": "分组", "status": "状态"}), use_container_width=True, hide_index=True)
