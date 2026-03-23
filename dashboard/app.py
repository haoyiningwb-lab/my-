from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import latest_snapshot, load_metrics

st.set_page_config(page_title="业务数据看板", page_icon="📊", layout="wide")

st.markdown(
    """
<style>
.block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1400px;}
.main-title {font-size: 2.1rem; font-weight: 700; margin-bottom: 0.2rem;}
.sub-title {color: #64748b; margin-bottom: 1.2rem;}
.card {background: linear-gradient(135deg,#0f172a 0%,#1e293b 100%); padding: 1rem 1.1rem; border-radius: 18px; color: white; box-shadow: 0 8px 24px rgba(15,23,42,.18);}
.card small {opacity: .8;}
[data-testid='stMetric'] {background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.8rem 1rem; border-radius: 16px;}
[data-testid='stMetricValue'] {font-size: 1.55rem;}
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


df = get_df()
st.markdown('<div class="main-title">📊 业务监控可视化看板</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">基于本地落地文件自动更新，适合日常监控、趋势观察和异常排查。</div>', unsafe_allow_html=True)

if df.empty:
    st.error("未读取到数据，请检查本地落地目录是否存在可用 xlsx 文件。")
    st.stop()

snapshot = latest_snapshot(df)
global_latest = df['date'].max().date()

with st.sidebar:
    st.header("筛选条件")
    groups = sorted(df['biz_group'].dropna().unique().tolist())
    selected_groups = st.multiselect("业务分组", groups, default=groups)
    base = df[df['biz_group'].isin(selected_groups)] if selected_groups else df.copy()
    biz_names = sorted(base['biz_name'].dropna().unique().tolist())
    selected_biz = st.multiselect("业务", biz_names, default=biz_names)
    days = st.selectbox("观察窗口", [7, 15, 30, 60], index=2)
    st.caption(f"全局最新数据日期：{global_latest}")

filtered = df[df['biz_group'].isin(selected_groups) & df['biz_name'].isin(selected_biz)].copy()
filtered = filtered[filtered['date'] >= (pd.Timestamp(global_latest) - pd.Timedelta(days=days - 1))]
snap_filtered = snapshot[snapshot['biz_group'].isin(selected_groups) & snapshot['biz_name'].isin(selected_biz)].copy()

hero1, hero2 = st.columns([1.6, 1])
with hero1:
    st.markdown(
        f'''<div class="card"><div style="font-size:1.05rem;font-weight:700">今日总览</div>
        <div style="margin-top:.6rem;font-size:2rem;font-weight:800">{global_latest}</div>
        <small>已覆盖 {snap_filtered['biz_name'].nunique()} 个业务，异常 {int(snap_filtered['status'].isin(['🔴', '⚠️', '⚡']).sum())} 个。</small></div>''',
        unsafe_allow_html=True,
    )
with hero2:
    stale_cnt = int((snap_filtered['freshness_days'] > 0).sum())
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
        trend_df = filtered.groupby('date', as_index=False).agg(total_count=('total_count', 'sum'))
        fig = px.line(trend_df, x='date', y='total_count', markers=True, title='总进审量趋势', template='plotly_white')
        fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10), yaxis_title='进审量')
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        status_df = snap_filtered.groupby('status', as_index=False).size().sort_values('status')
        fig = px.bar(status_df, x='status', y='size', color='status', text='size', title='最新状态分布', template='plotly_white')
        fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10), showlegend=False, xaxis_title='状态', yaxis_title='业务数')
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        push_df = filtered.groupby('date', as_index=False).agg(push_rate=('push_rate', 'mean'))
        fig = px.area(push_df, x='date', y='push_rate', title='平均推审率趋势', template='plotly_white')
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10), yaxis_tickformat='.1%')
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        vio_df = filtered.groupby('date', as_index=False).agg(violation_rate=('violation_rate', 'mean'))
        fig = px.area(vio_df, x='date', y='violation_rate', title='平均违规率趋势', template='plotly_white')
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10), yaxis_tickformat='.2%')
        st.plotly_chart(fig, use_container_width=True)

with biz_tab:
    focus_biz = st.selectbox('选择业务', sorted(snap_filtered['biz_name'].unique().tolist()))
    focus_df = filtered[filtered['biz_name'] == focus_biz].copy().sort_values('date')
    top1, top2, top3, top4 = st.columns(4)
    if not focus_df.empty:
        latest_row = focus_df.iloc[-1]
        top1.metric('最新进审量', num_text(latest_row['total_count']))
        top2.metric('最新推审率', pct_text(latest_row['push_rate']))
        top3.metric('最新违规率', pct_text(latest_row['violation_rate']))
        top4.metric('数据日期', str(latest_row['date'].date()))

        fig = px.line(focus_df, x='date', y=['total_count', 'total_7d_avg'], markers=True, title=f'{focus_biz} · 进审量 vs 7日均量', template='plotly_white')
        fig.update_layout(height=350, margin=dict(l=10, r=10, t=50, b=10), legend_title='指标')
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.line(focus_df, x='date', y=['push_rate', 'violation_rate'], markers=True, title=f'{focus_biz} · 推审率 / 违规率趋势', template='plotly_white')
        fig2.update_layout(height=350, margin=dict(l=10, r=10, t=50, b=10), yaxis_tickformat='.2%')
        st.plotly_chart(fig2, use_container_width=True)

        show_cols = focus_df[['date', 'total_count', 'total_7d_avg', 'push_rate', 'violation_rate', 'review_count', 'reject_count', 'error_value', 'source_file']].copy()
        show_cols['date'] = show_cols['date'].dt.date
        show_cols['total_count'] = show_cols['total_count'].map(num_text)
        show_cols['total_7d_avg'] = show_cols['total_7d_avg'].map(num_text)
        show_cols['push_rate'] = show_cols['push_rate'].map(pct_text)
        show_cols['violation_rate'] = show_cols['violation_rate'].map(pct_text)
        show_cols['review_count'] = show_cols['review_count'].map(num_text)
        show_cols['reject_count'] = show_cols['reject_count'].map(num_text)
        show_cols['error_value'] = show_cols['error_value'].map(num_text)
        st.dataframe(show_cols.rename(columns={'date': '日期', 'total_count': '进审量', 'total_7d_avg': '7日均量', 'push_rate': '推审率', 'violation_rate': '违规率', 'review_count': '人审量', 'reject_count': '驳回量', 'error_value': '误差值', 'source_file': '来源文件'}), use_container_width=True, hide_index=True)

with alert_tab:
    alerts = snap_filtered.copy()
    alerts['进审量'] = alerts['total_count'].map(num_text)
    alerts['推审率'] = alerts['push_rate'].map(pct_text)
    alerts['违规率'] = alerts['violation_rate'].map(pct_text)
    alerts['量级偏差'] = alerts['total_vs_7d_pct'].map(signed_pct)
    alerts['数据新鲜度'] = alerts['freshness_label']

    st.subheader('优先排查列表')
    abnormal = alerts[(alerts['status'].isin(['🔴', '⚠️', '⚡'])) | (alerts['freshness_days'] > 0)].copy()
    st.dataframe(abnormal[['biz_name', 'biz_group', 'status', '数据新鲜度', '进审量', '推审率', '违规率', '量级偏差', 'source_file']].rename(columns={'biz_name': '业务', 'biz_group': '分组', 'status': '状态', 'source_file': '来源文件'}), use_container_width=True, hide_index=True)

    st.subheader('最新业务明细')
    st.dataframe(alerts[['biz_name', 'biz_group', 'status', '数据新鲜度', '进审量', '推审率', '违规率', '量级偏差']].rename(columns={'biz_name': '业务', 'biz_group': '分组', 'status': '状态'}), use_container_width=True, hide_index=True)
