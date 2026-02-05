import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import numpy as np

# ================= 1. 基础配置 =================
APP_ID = "cli_a9e59cab76381bb5"
APP_SECRET = "Q9qlFjw4QAQjtqHjW7f1Gb0Eyirl1bsP"
SPREADSHEET_TOKEN = "WLx3svmwbhycaNtk5iicasXXnwU"

SHEET_MAP = {
    "头像用户资料": "y7kzwF", "融媒体短文本": "GtVLME", "融媒体长文本": "NRKJly",
    "steam昵称简介": "xPVsS9", "steam头像封面": "Jtwn2Q", "战绩昵称": "GGReON",
    "战绩头像": "VzOCwD", "国内小镇照片": "21ftlq", "国外小镇照片": "jmtEsW",
    "国内小镇舆情": "VzPUt6", "国外小镇舆情": "AWY7ob", "国内小镇书籍": "ofWaUP",
    "国外小镇书籍": "Bj5ksr"
}

st.set_page_config(page_title="数据作战中心-V39全能版", layout="wide")

# ================= 2. 核心推送引擎 (均值对比逻辑) =================

def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    try:
        res = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}).json()
        return res.get("tenant_access_token")
    except: return None

def send_dashboard_report(webhook, biz_name, df_full, period_label):
    """计算本周vs上周均值，推送差异对比报表"""
    df_sorted = df_full.sort_values(df_full.columns[0])
    this_week = df_sorted.tail(7)
    last_week = df_sorted.iloc[-14:-7] if len(df_sorted) >= 14 else df_sorted.iloc[0:-7]

    if this_week.empty: return False

    target_metrics = ["总进审量", "驳回量", "违规率", "推审率"]
    results = []
    
    for target in target_metrics:
        matches = [c for c in df_sorted.columns if target in str(c)]
        if matches:
            col = matches[0]
            tw_avg = pd.to_numeric(this_week[col], errors='coerce').fillna(0).mean()
            lw_avg = pd.to_numeric(last_week[col], errors='coerce').fillna(0).mean()
            # 比例转换
            factor = 100 if ("率" in col and tw_avg <= 1.0) else 1
            tw_avg_f, lw_avg_f = tw_avg * factor, lw_avg * factor
            diff = tw_avg_f - lw_avg_f
            unit = "%" if "率" in col else ""
            results.append({"name": target, "tw": tw_avg_f, "lw": lw_avg_f, "diff": diff, "unit": unit})

    # 智能总结图标
    vio_res = next((r for r in results if "违规率" in r['name']), {"diff": 0})
    status_icon = "🟢" if vio_res['diff'] <= 0 else "🔴"

    # 构建仪表盘字段
    card_fields = []
    for r in results:
        trend = "📈" if r['diff'] > 0 else "📉"
        card_fields.append({
            "is_short": True,
            "text": {"tag": "lark_md", "content": f"**{r['name']}**\n本周均值: {r['tw']:.2f}{r['unit']}\n差异: {trend} **{r['diff']:+.2f}{r['unit']}**"}
        })

    card = {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": f"🛡️ {biz_name} 作战简报 ({period_label})"}, "template": "blue"},
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**🤖 业务动态总结：**\n{status_icon} 违规率环比波动: {vio_res['diff']:+.2f}%"}},
            {"tag": "hr"},
            {"tag": "div", "fields": card_fields},
            {"tag": "note", "elements": [{"tag": "plain_text", "content": f"对比周期: 最近7天 vs 前7天平均值"}]}
        ]
    }
    requests.post(webhook, json={"msg_type": "interactive", "card": card})
    return True

# ================= 3. 数据处理引擎 =================

@st.cache_data(ttl=60)
def get_feishu_data(token, sheet_id):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{SPREADSHEET_TOKEN}/values/{sheet_id}!A:Z?valueRenderOption=UnformattedValue"
    try:
        res = requests.get(url, headers=headers).json()
        return res.get("data", {}).get("valueRange", {}).get("values", [])
    except: return []

# ================= 4. 侧边栏及批量推送控制 =================

st.sidebar.title("🎮 作战控制面板")
page_mode = st.sidebar.radio("功能切换", ["单业务深度监控", "全业务大盘对比"])

st.sidebar.divider()
st.sidebar.subheader("📅 时间维度自定义")
view_period = st.sidebar.select_slider("主面板统计范围", options=["按天", "按周", "按月"], value="按周")
days_map = {"按天": 1, "按周": 7, "按月": 30}

st.sidebar.divider()
st.sidebar.subheader("🤖 批量推送配置")
webhook_url = st.sidebar.text_input("飞书 Webhook 地址")
selected_biz_list = st.sidebar.multiselect("选择推送业务线", list(SHEET_MAP.keys()), default=[list(SHEET_MAP.keys())[0]])

if st.sidebar.button("🚀 一键推送已选业务对比简报"):
    if not webhook_url: st.sidebar.error("请填入 Webhook")
    else:
        token = get_tenant_access_token()
        progress = st.sidebar.progress(0)
        for i, b_name in enumerate(selected_biz_list):
            raw = get_feishu_data(token, SHEET_MAP[b_name])
            if len(raw) > 1:
                # 修复核心：列名去重
                counts, clean_h = {}, []
                for c in raw[0]:
                    c_s = str(c) if c else "u"
                    counts[c_s] = counts.get(c_s, -1) + 1
                    clean_h.append(f"{c_s}.{counts[c_s]}" if counts[c_s] > 0 else c_s)
                df_tmp = pd.DataFrame(raw[1:], columns=clean_h)
                df_tmp['日期_idx'] = pd.to_datetime(df_tmp.iloc[:, 0], errors='coerce')
                df_tmp = df_tmp.dropna(subset=['日期_idx']).sort_values('日期_idx')
                send_dashboard_report(webhook_url, b_name, df_tmp, view_period)
            progress.progress((i + 1) / len(selected_biz_list))
        st.sidebar.success(f"已推送 {len(selected_biz_list)} 份报表")

# ================= 5. 主页面可视化 =================

if page_mode == "单业务深度监控":
    current_label = st.sidebar.selectbox("预览对象", list(SHEET_MAP.keys()))
    token = get_tenant_access_token()
    if token:
        raw_data = get_feishu_data(token, SHEET_MAP[current_label])
        if len(raw_data) > 1:
            # 去重处理
            counts, clean_h = {}, []
            for c in raw_data[0]:
                c_s = str(c) if c else "u"
                counts[c_s] = counts.get(c_s, -1) + 1
                clean_h.append(f"{c_s}.{counts[c_s]}" if counts[c_s] > 0 else c_s)
            
            df = pd.DataFrame(raw_data[1:], columns=clean_h)
            df['日期_plot'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            df = df.dropna(subset=['日期_plot']).sort_values('日期_plot')
            
            st.title(f"🛡️ {current_label} 态势监控")
            df_plot = df.tail(max(7, days_map[view_period]))
            valid_cols = [c for c in clean_h if c != clean_h[0] and "u" not in str(c)]
            user_selection = st.multiselect("指标查看", options=valid_cols, default=valid_cols[:4] if len(valid_cols)>=4 else valid_cols)
            
            for i in range(0, len(user_selection), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(user_selection):
                        dim = user_selection[i + j]
                        y_val = pd.to_numeric(df_plot[dim], errors='coerce').fillna(0)
                        display_y = y_val * 100 if ("率" in dim and y_val.max() <= 1.0) else y_val
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df_plot['日期_plot'], y=display_y, mode='lines+markers', line=dict(shape='spline', color='#007BFF', width=3)))
                        # 找回预警线
                        if len(display_y) > 1:
                            threshold = display_y.mean() + 2 * display_y.std()
                            fig.add_hline(y=threshold, line_dash="dash", line_color="red", annotation_text="预警水位")
                        fig.update_layout(title=f"【{dim}】趋势走向", height=380, template="plotly_white")
                        cols[j].plotly_chart(fig, use_container_width=True)

elif page_mode == "全业务大盘对比":
    st.title(f"🌐 全业务违规率对比 ({view_period})")
    token = get_tenant_access_token()
    all_biz_list = []
    if token:
        with st.spinner("聚合全业务大盘中..."):
            for name, sid in SHEET_MAP.items():
                data = get_feishu_data(token, sid)
                if len(data) > 1:
                    # 修正点：统一变量名为 counts
                    counts, clean_h = {}, []
                    for c in data[0]:
                        c_s = str(c) if c else "u"
                        counts[c_s] = counts.get(c_s, -1) + 1
                        clean_h.append(f"{c_s}.{counts[c_s]}" if counts[c_s] > 0 else c_s)
                    
                    try:
                        temp_df = pd.DataFrame(data[1:], columns=clean_h)
                        temp_df['日期_tmp'] = pd.to_datetime(temp_df.iloc[:, 0], errors='coerce')
                        temp_df = temp_df.dropna(subset=['日期_tmp']).sort_values('日期_tmp').tail(days_map[view_period])
                        
                        rate_cols = [c for c in temp_df.columns if "违规率" in str(c)]
                        if rate_cols:
                            val = pd.to_numeric(temp_df[rate_cols[0]], errors='coerce').fillna(0).reset_index(drop=True)
                            final_val = val * 100 if val.max() <= 1.0 else val
                            d_arr = temp_df['日期_tmp'].reset_index(drop=True).to_numpy().flatten()
                            all_biz_list.append(pd.DataFrame({'日期': d_arr, '数值': final_val, '业务': [name]*len(d_arr)}))
                    except: continue

        if all_biz_list:
            compare_df = pd.concat(all_biz_list, ignore_index=True)
            fig_comp = px.line(compare_df, x='日期', y='数值', color='业务', template="plotly_white")
            fig_comp.update_traces(line_shape='spline', hovertemplate='违规率: %{y:.2f}%<extra></extra>')
            fig_comp.update_layout(height=600, yaxis=dict(ticksuffix="%"), hovermode="x unified")
            st.plotly_chart(fig_comp, use_container_width=True)
