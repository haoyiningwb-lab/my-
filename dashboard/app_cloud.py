from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
EXPORT_DIR = APP_DIR / "exports"

st.set_page_config(page_title="业务数据看板（线上版）", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
<style>
.block-container {padding-top: 2.4rem; padding-bottom: 2rem; max-width: 1420px;}
.main-title {font-size: 2.15rem; font-weight: 800; margin-bottom: 0.15rem; display:flex; align-items:center; gap:10px;}
.sub-title {color: #64748b; margin-bottom: 1.15rem;}
.card {background: linear-gradient(135deg,#0f172a 0%,#1e293b 100%); padding: 1rem 1.1rem; border-radius: 18px; color: white; box-shadow: 0 8px 24px rgba(15,23,42,.18);}
.card small {opacity: .86;}
[data-testid='stMetric'] {background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.8rem 1rem; border-radius: 16px;}
[data-testid='stMetricValue'] {font-size: 1.55rem;}
[data-testid='stSidebar'] {background: linear-gradient(180deg,#eef2ff 0%,#f8fafc 45%,#fefefe 100%); border-right:1px solid #dbe4ff;}
[data-testid='stSidebar'] .block-container {padding-top: 0.6rem; padding-left: 0.8rem; padding-right: 0.8rem;}
.sidebar-panel {background: linear-gradient(180deg,rgba(255,255,255,.96) 0%,rgba(248,250,252,.98) 100%); border:1px solid #dbe4ff; border-radius:18px; padding:12px 12px 8px 12px; box-shadow: 0 8px 20px rgba(59,130,246,.07); margin-bottom: 10px;}
.side-kpi {background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%); border:1px solid #dbe4ff; border-radius:12px; padding:9px 11px; margin-top:8px;}
.small-muted {font-size:12px; color:#64748b;}
[data-baseweb="tag"] {background:#eaf2ff !important; border-radius:9px !important; border:1px solid #bfd3ff !important; min-height:26px !important; padding:0 4px !important;}
[data-baseweb="tag"] span {color:#3157b7 !important; font-weight:600 !important; font-size:12px !important;}
[data-baseweb="tag"] svg {color:#6b88d6 !important; width:14px !important; height:14px !important;}
[data-baseweb="select"] > div {min-height:38px !important;}
[data-baseweb="input"] > div {min-height:38px !important;}
.stMultiSelect [data-baseweb="tag"] {max-width: 84px !important; overflow: hidden !important;}
.stMultiSelect [data-baseweb="select"] > div {max-height: 40px !important; overflow: hidden !important;}
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


def signed_pct(v):
    return "-" if pd.isna(v) else f"{float(v):+.1f}%"


def zh_date(v):
    dt = pd.to_datetime(v)
    return f"{dt.year}年{dt.month}月{dt.day}日"


def short_zh_date(v):
    dt = pd.to_datetime(v)
    return f"{dt.month}月{dt.day}日"


def format_axis_date(series: pd.Series) -> list[str]:
    return [short_zh_date(x) for x in series]


def compact_num_label(v):
    if pd.isna(v):
        return "-"
    v = float(v)
    if v >= 100000000:
        return f"{v/100000000:.2f}亿"
    if v >= 10000:
        return f"{v/10000:.1f}万"
    return f"{int(v)}"


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


def build_warning_texts(df: pd.DataFrame) -> list[str]:
    warnings = []
    def row_of(name: str):
        x = df[df['biz_name'] == name]
        return x.iloc[0] if not x.empty else None

    for name in ["steam昵称简介", "融媒体短文本", "TapTap-融媒体长文本", "国内小镇舆情", "海外小镇舆情"]:
        row = row_of(name)
        if row is None:
            continue
        push = pct_text(row.get('push_rate'))
        vio = pct_text(row.get('violation_rate'))
        if name == "steam昵称简介":
            warnings.append(f"{name}：当前推审率 {push}，违规率 {vio}，建议优先核查链路承接情况。")
        elif name == "融媒体短文本":
            warnings.append(f"{name}：当前推审率 {push}，违规率 {vio}，建议继续观察并排查轻度卡点。")
        elif name == "TapTap-融媒体长文本":
            warnings.append(f"{name}：当前推审率 {push}，违规率 {vio}，审核承接压力偏高。")
        elif name == "国内小镇舆情":
            warnings.append(f"{name}：当前推审率 {push}，违规率 {vio}，策略有效性需继续观察。")
        elif name == "海外小镇舆情":
            warnings.append(f"{name}：当前推审率 {push}，违规率 {vio}，高比例送审表现需继续核查。")
    stale = df[df['freshness_days'] > 0]
    if not stale.empty:
        warnings.insert(0, f"共有 {len(stale)} 个业务数据未更新到最新日期，需优先检查同步链路。")
    return warnings


def render_group_trend(source_df: pd.DataFrame, biz_names: list[str], title: str, key: str):
    part = source_df[source_df['biz_name'].isin(biz_names)].copy()
    if part.empty:
        st.info(f"{title}暂无数据")
        return
    d = part.groupby('date', as_index=False).agg(total_count=('total_count', 'sum'))
    d['date_label'] = format_axis_date(d['date'])
    d['label'] = d['total_count'].map(compact_num_label)
    fig = px.line(d, x='date_label', y='total_count', markers=True, text='label', title=title, template='plotly_white')
    fig = style_single_series_line(fig, d['date_label'], yaxis_title='进审量', percent_axis=False)
    st.plotly_chart(fig, use_container_width=True, key=key)

    c1, c2 = st.columns(2)
    with c1:
        push = part.groupby('date', as_index=False).agg(push_rate=('push_rate', 'mean'))
        push['date_label'] = format_axis_date(push['date'])
        push['label'] = push['push_rate'].map(lambda x: '-' if pd.isna(x) else f"{x*100:.2f}%")
        fig2 = px.line(push, x='date_label', y='push_rate', markers=True, text='label', title=f'{title} · 推审率', template='plotly_white')
        fig2 = style_single_series_line(fig2, push['date_label'], yaxis_title='推审率', percent_axis=True)
        st.plotly_chart(fig2, use_container_width=True, key=f'{key}_push')
    with c2:
        vio = part.groupby('date', as_index=False).agg(violation_rate=('violation_rate', 'mean'))
        vio['date_label'] = format_axis_date(vio['date'])
        vio['label'] = vio['violation_rate'].map(lambda x: '-' if pd.isna(x) else f"{x*100:.2f}%")
        fig3 = px.line(vio, x='date_label', y='violation_rate', markers=True, text='label', title=f'{title} · 违规率', template='plotly_white')
        fig3 = style_single_series_line(fig3, vio['date_label'], yaxis_title='违规率', percent_axis=True)
        st.plotly_chart(fig3, use_container_width=True, key=f'{key}_vio')


latest = load_csv("biz_summary_latest.csv")
trend = load_csv("biz_trend_30d.csv")
alerts = load_csv("fact_alerts.csv")

st.markdown('<div class="main-title">📊 业务数据看板</div>', unsafe_allow_html=True)

if latest.empty:
    st.error("未读取到导出数据，请先同步 exports 目录到线上仓库。")
    st.stop()

latest["date"] = pd.to_datetime(latest["date"])
trend["date"] = pd.to_datetime(trend["date"])
if not alerts.empty:
    alerts["date"] = pd.to_datetime(alerts["date"])

global_latest = latest["date"].max().date()
all_groups = sorted(latest["biz_group"].dropna().unique().tolist())
all_biz = sorted(latest["biz_name"].dropna().unique().tolist())

with st.sidebar:
    st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
    st.markdown("### 筛选中心")
    st.caption("支持按分组、业务快速切换，线上展示默认读取仓库内最新导出数据。")
    default_all_groups = st.checkbox("全部业务分组", value=True)
    selected_groups = st.multiselect("选择业务分组", all_groups, default=all_groups if default_all_groups else all_groups[:2])
    if not selected_groups:
        selected_groups = all_groups
    base = latest[latest["biz_group"].isin(selected_groups)]
    biz_names = sorted(base["biz_name"].dropna().unique().tolist())
    default_all_biz = st.checkbox("全部业务", value=True)
    selected_biz = st.multiselect("选择业务", biz_names, default=biz_names if default_all_biz else biz_names[: min(5, len(biz_names))])
    if not selected_biz:
        selected_biz = biz_names
    days = st.select_slider("观察窗口", options=[7, 15, 30, 60], value=7)
    status_filter = st.segmented_control("状态筛选", options=["全部", "异常", "正常"], default="全部", selection_mode="single")
    st.markdown('</div>', unsafe_allow_html=True)

latest_f = latest[latest["biz_group"].isin(selected_groups) & latest["biz_name"].isin(selected_biz)].copy()
trend_f = trend[trend["biz_group"].isin(selected_groups) & trend["biz_name"].isin(selected_biz)].copy()
trend_f = trend_f[trend_f["date"] >= (pd.Timestamp(global_latest) - pd.Timedelta(days=days - 1))]
if status_filter == "异常":
    latest_f = latest_f[latest_f["status"].isin(["🔴", "⚠️", "⚡"])]
elif status_filter == "正常":
    latest_f = latest_f[latest_f["status"] == "✓"]
trend_f = trend_f[trend_f["biz_name"].isin(latest_f["biz_name"])]

with st.sidebar:
    abnormal_cnt = int(latest_f["status"].isin(["🔴", "⚠️", "⚡"]).sum()) if not latest_f.empty else 0
    stale_cnt = int((latest_f["freshness_days"] > 0).sum()) if not latest_f.empty else 0
    st.markdown(f'<div class="side-kpi"><strong>全局最新日期</strong><br><span class="small-muted">{zh_date(global_latest)}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-kpi"><strong>当前业务数</strong><br><span class="small-muted">{latest_f["biz_name"].nunique()} 个</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-kpi"><strong>异常业务</strong><br><span class="small-muted">{abnormal_cnt} 个</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-kpi"><strong>数据滞后</strong><br><span class="small-muted">{stale_cnt} 个</span></div>', unsafe_allow_html=True)

hero1, hero2 = st.columns([1.6, 1])
with hero1:
    st.markdown(
        f'''<div class="card"><div style="font-size:1.05rem;font-weight:700">今日总览</div>
        <div style="margin-top:.6rem;font-size:2rem;font-weight:800">{zh_date(global_latest)}</div>
        <small>已覆盖 {latest_f['biz_name'].nunique()} 个业务，异常 {int(latest_f['status'].isin(['🔴', '⚠️', '⚡']).sum())} 个。</small></div>''',
        unsafe_allow_html=True,
    )
with hero2:
    stale_cnt = int((latest_f["freshness_days"] > 0).sum()) if not latest_f.empty else 0
    st.markdown(
        f'''<div class="card"><div style="font-size:1.05rem;font-weight:700">数据新鲜度</div>
        <div style="margin-top:.6rem;font-size:2rem;font-weight:800">{stale_cnt} 个滞后</div>
        <small>若某业务未更新到全局最新日期，会直接在看板中标红提示。</small></div>''',
        unsafe_allow_html=True,
    )

k1, k2, k3, k4 = st.columns(4)
k1.metric("总进审量", f"{int(latest_f['total_count'].fillna(0).sum()):,}")
k2.metric("平均推审率", pct_text(latest_f['push_rate'].mean()))
k3.metric("平均违规率", pct_text(latest_f['violation_rate'].mean()))
k4.metric("红色业务", str(int((latest_f['status'] == '🔴').sum())))

page = st.radio("", ["总览趋势", "分组趋势", "业务钻取", "异常排查"], horizontal=True, label_visibility="collapsed")

group_options = {
    "社区业务": ["增量昵称简介", "TapTap-头像-用户资料图片", "融媒体短文本", "TapTap-融媒体长文本"],
    "小镇业务": ["国内小镇书籍", "国内小镇照片", "国内小镇舆情", "海外小镇书籍", "海外小镇照片", "海外小镇舆情"],
    "其他业务": ["steam成就标题简介", "steam昵称简介", "steam头像封面", "战绩昵称", "战绩头像"],
}

if page == "总览趋势":
    c1, c2 = st.columns([1.7, 1.1])
    with c1:
        trend_df = trend_f.groupby("date", as_index=False).agg(total_count=("total_count", "sum"))
        trend_df["date_label"] = format_axis_date(trend_df["date"])
        trend_df["label"] = trend_df["total_count"].map(compact_num_label)
        fig = px.line(trend_df, x="date_label", y="total_count", markers=True, text="label", title="总进审量趋势", template="plotly_white")
        fig = style_single_series_line(fig, trend_df["date_label"], yaxis_title="进审量", percent_axis=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        status_df = latest_f.groupby("status", as_index=False).size().sort_values("status")
        fig = px.bar(status_df, x="status", y="size", color="status", text="size", title="最新状态分布", template="plotly_white")
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=72, b=36), showlegend=False, xaxis_title="状态", yaxis_title="业务数", title=dict(y=0.95))
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        push_df = trend_f.groupby("date", as_index=False).agg(push_rate=("push_rate", "mean"))
        push_df["date_label"] = format_axis_date(push_df["date"])
        push_df["label"] = push_df["push_rate"].map(lambda x: "-" if pd.isna(x) else f"{x*100:.2f}%")
        fig = px.line(push_df, x="date_label", y="push_rate", markers=True, text="label", title="平均推审率趋势", template="plotly_white")
        fig = style_single_series_line(fig, push_df["date_label"], yaxis_title="推审率", percent_axis=True)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        vio_df = trend_f.groupby("date", as_index=False).agg(violation_rate=("violation_rate", "mean"))
        vio_df["date_label"] = format_axis_date(vio_df["date"])
        vio_df["label"] = vio_df["violation_rate"].map(lambda x: "-" if pd.isna(x) else f"{x*100:.2f}%")
        fig = px.line(vio_df, x="date_label", y="violation_rate", markers=True, text="label", title="平均违规率趋势", template="plotly_white")
        fig = style_single_series_line(fig, vio_df["date_label"], yaxis_title="违规率", percent_axis=True)
        st.plotly_chart(fig, use_container_width=True)

elif page == "分组趋势":
    selected_group_trend = st.selectbox("选择分组板块", list(group_options.keys()), index=0)
    render_group_trend(trend_f, group_options[selected_group_trend], f"{selected_group_trend}趋势", "selected_group_trend")

elif page == "业务钻取":
    focus_candidates = sorted(latest_f["biz_name"].unique().tolist()) if not latest_f.empty else []
    if not focus_candidates:
        st.warning("当前筛选条件下暂无业务数据。")
    else:
        focus_biz = st.selectbox("选择业务", focus_candidates)
        focus_df = trend_f[trend_f["biz_name"] == focus_biz].copy().sort_values("date")
        top1, top2, top3, top4 = st.columns(4)
        if not focus_df.empty:
            latest_row = latest_f[latest_f["biz_name"] == focus_biz].iloc[-1]
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

else:
    alerts_f = alerts[alerts["biz_group"].isin(selected_groups) & alerts["biz_name"].isin(selected_biz)].copy() if not alerts.empty else pd.DataFrame()
    st.markdown("#### 风险预警")
    warnings = build_warning_texts(latest_f)
    if warnings:
        for w in warnings:
            st.markdown(f"- {w}")
    else:
        st.caption("当前暂无额外风险预警文字。")

    if not alerts_f.empty:
        alerts_f["进审量"] = alerts_f["total_count"].map(num_text)
        alerts_f["推审率"] = alerts_f["push_rate"].map(pct_text)
        alerts_f["违规率"] = alerts_f["violation_rate"].map(pct_text)
        if "total_vs_7d_pct_point" in alerts_f.columns:
            alerts_f["量级偏差"] = alerts_f["total_vs_7d_pct_point"].map(signed_pct)
        elif "total_vs_7d_pct" in alerts_f.columns:
            alerts_f["量级偏差"] = alerts_f["total_vs_7d_pct"].map(lambda x: "-" if pd.isna(x) else f"{float(x) * 100:+.1f}%")
        else:
            alerts_f["量级偏差"] = "-"
        alerts_f["数据新鲜度"] = alerts_f["freshness_label"]
        st.markdown("#### 优先排查列表")
        st.dataframe(alerts_f[["biz_name", "biz_group", "status", "数据新鲜度", "进审量", "推审率", "违规率", "量级偏差", "source_file"]].rename(columns={"biz_name": "业务", "biz_group": "分组", "status": "状态", "source_file": "来源文件"}), use_container_width=True, hide_index=True)

    st.markdown("#### 最新业务明细")
    latest_show = latest_f.copy()
    latest_show["进审量"] = latest_show["total_count"].map(num_text)
    latest_show["推审率"] = latest_show["push_rate"].map(pct_text)
    latest_show["违规率"] = latest_show["violation_rate"].map(pct_text)
    if "total_vs_7d_pct_point" in latest_show.columns:
        latest_show["量级偏差"] = latest_show["total_vs_7d_pct_point"].map(signed_pct)
    elif "total_vs_7d_pct" in latest_show.columns:
        latest_show["量级偏差"] = latest_show["total_vs_7d_pct"].map(lambda x: "-" if pd.isna(x) else f"{float(x) * 100:+.1f}%")
    else:
        latest_show["量级偏差"] = "-"
    latest_show["数据新鲜度"] = latest_show["freshness_label"]
    st.dataframe(latest_show[["biz_name", "biz_group", "status", "数据新鲜度", "进审量", "推审率", "违规率", "量级偏差"]].rename(columns={"biz_name": "业务", "biz_group": "分组", "status": "状态"}), use_container_width=True, hide_index=True)
