from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import latest_snapshot, load_metrics

st.set_page_config(page_title="业务数据看板", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
[data-testid='stMetricValue'] {font-size: 1.6rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def get_df():
    return load_metrics()


def pct_text(v):
    return "-" if pd.isna(v) else f"{v * 100:.1f}%"


def num_text(v):
    return "-" if pd.isna(v) else f"{int(v):,}"


df = get_df()

st.title("📊 业务监控数据看板")
st.caption("基于本地落地文件自动刷新，适合总览、趋势观察与异常排查。")

if df.empty:
    st.error("未读取到数据，请检查本地落地目录是否存在可用 xlsx 文件。")
    st.stop()

latest_date = df['date'].max().date()
snapshot = latest_snapshot(df)

with st.sidebar:
    st.header("筛选")
    biz_groups = sorted(df['biz_group'].dropna().unique().tolist())
    selected_groups = st.multiselect("业务分组", biz_groups, default=biz_groups)
    candidate = df[df['biz_group'].isin(selected_groups)] if selected_groups else df.copy()
    biz_names = sorted(candidate['biz_name'].dropna().unique().tolist())
    selected_biz = st.multiselect("业务", biz_names, default=biz_names)
    days = st.selectbox("时间范围", [7, 15, 30, 60], index=2)

filtered = df[df['biz_group'].isin(selected_groups) & df['biz_name'].isin(selected_biz)].copy()
filtered = filtered[filtered['date'] >= (pd.Timestamp(latest_date) - pd.Timedelta(days=days - 1))]
snap_filtered = snapshot[snapshot['biz_group'].isin(selected_groups) & snapshot['biz_name'].isin(selected_biz)].copy()

k1, k2, k3, k4 = st.columns(4)
k1.metric("最新日期", str(latest_date))
k2.metric("覆盖业务数", f"{snap_filtered['biz_name'].nunique()}")
k3.metric("异常业务数", f"{int(snap_filtered['status'].isin(['🔴', '⚠️', '⚡']).sum())}")
k4.metric("总进审量", f"{int(snap_filtered['total_count'].fillna(0).sum()):,}")

c1, c2 = st.columns([1.8, 1.2])
with c1:
    trend_df = filtered.groupby('date', as_index=False).agg(total_count=('total_count', 'sum'))
    fig = px.line(trend_df, x='date', y='total_count', markers=True, title='总进审量趋势')
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=50, b=10), yaxis_title='进审量')
    st.plotly_chart(fig, use_container_width=True)
with c2:
    status_df = snap_filtered.groupby('status', as_index=False).size().sort_values('status')
    fig = px.bar(status_df, x='status', y='size', color='status', title='最新状态分布', text='size')
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=50, b=10), showlegend=False, xaxis_title='状态', yaxis_title='业务数')
    st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    push_df = filtered.groupby('date', as_index=False).agg(push_rate=('push_rate', 'mean'))
    fig = px.line(push_df, x='date', y='push_rate', markers=True, title='平均推审率趋势')
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10), yaxis_tickformat='.1%')
    st.plotly_chart(fig, use_container_width=True)
with c4:
    vio_df = filtered.groupby('date', as_index=False).agg(violation_rate=('violation_rate', 'mean'))
    fig = px.line(vio_df, x='date', y='violation_rate', markers=True, title='平均违规率趋势')
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10), yaxis_tickformat='.2%')
    st.plotly_chart(fig, use_container_width=True)

st.subheader('异常业务清单')
alerts = snap_filtered[snap_filtered['status'].isin(['🔴', '⚠️', '⚡'])].copy()
alerts['进审量'] = alerts['total_count'].map(num_text)
alerts['推审率'] = alerts['push_rate'].map(pct_text)
alerts['大盘违规率'] = alerts['violation_rate'].map(pct_text)
alerts['较7日均值偏差'] = alerts['total_vs_7d_pct'].map(lambda x: '-' if pd.isna(x) else f"{x * 100:+.1f}%")
st.dataframe(alerts[['biz_name', 'biz_group', 'status', '进审量', '推审率', '大盘违规率', '较7日均值偏差', 'source_file']].rename(columns={'biz_name': '业务', 'biz_group': '分组', 'status': '状态', 'source_file': '来源文件'}), use_container_width=True, hide_index=True)

st.subheader('业务明细')
latest_table = snap_filtered.copy().sort_values(['status', 'biz_group', 'biz_name'])
latest_table['进审量'] = latest_table['total_count'].map(num_text)
latest_table['推审率'] = latest_table['push_rate'].map(pct_text)
latest_table['大盘违规率'] = latest_table['violation_rate'].map(pct_text)
latest_table['7日均量'] = latest_table['total_7d_avg'].map(num_text)
latest_table['量级偏差'] = latest_table['total_vs_7d_pct'].map(lambda x: '-' if pd.isna(x) else f"{x * 100:+.1f}%")
st.dataframe(latest_table[['biz_name', 'biz_group', 'status', '进审量', '7日均量', '量级偏差', '推审率', '大盘违规率']].rename(columns={'biz_name': '业务', 'biz_group': '分组', 'status': '状态'}), use_container_width=True, hide_index=True)

st.subheader('单业务趋势')
focus_biz = st.selectbox('选择单业务查看趋势', sorted(snap_filtered['biz_name'].unique().tolist()))
focus_df = filtered[filtered['biz_name'] == focus_biz].copy().sort_values('date')
if not focus_df.empty:
    fig = px.line(focus_df, x='date', y=['total_count', 'total_7d_avg'], markers=True, title=f'{focus_biz} · 进审量 vs 7日均量')
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10), legend_title='指标')
    st.plotly_chart(fig, use_container_width=True)
    fig2 = px.line(focus_df, x='date', y=['push_rate', 'violation_rate'], markers=True, title=f'{focus_biz} · 推审率 / 违规率趋势')
    fig2.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10), yaxis_tickformat='.2%')
    st.plotly_chart(fig2, use_container_width=True)
