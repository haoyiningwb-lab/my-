import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import numpy as np

# ================= 1. 安全配置 (从云端 Secrets 读取) =================
# 注意：在本地运行时，如果没配置 secrets.toml 会报错。
# 建议在本地测试时先手动填回字符串，上传 GitHub 前改回 st.secrets。
try:
    APP_ID = st.secrets["APP_ID"]
    APP_SECRET = st.secrets["APP_SECRET"]
except:
    # 这里的默认值仅供本地测试，部署时请通过 Streamlit 后台设置
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

# ================= 2. 权限校验模块 =================
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 数据作战指挥室")
        st.text_input("请输入授权码进入", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("授权码错误，请重新输入", type="password", on_change=password_entered, key="password")
        return False
    return True

def password_entered():
    if st.session_state["password"] == "666888": # 您可以自定义此密码
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False

# ================= 3. 核心业务逻辑 =================
if check_password():
    st.set_page_config(page_title="数据作战中心-V40云端版", layout="wide")

    # --- 飞书推送引擎 ---
    def get_token():
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        res = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}).json()
        return res.get("tenant_access_token")

    def send_report(webhook, biz_name, df_full, period):
        df_sorted = df_full.sort_values(df_full.columns[0])
        this_week = df_sorted.tail(7)
        last_week = df_sorted.iloc[-14:-7] if len(df_sorted) >= 14 else df_sorted.iloc[0:-7]
        
        target_metrics = ["总进审量", "驳回量", "违规率", "推审率"]
        fields = []
        vio_diff = 0
        
        for target in target_metrics:
            matches = [c for c in df_sorted.columns if target in str(c)]
            if matches:
                col = matches[0]
                tw_avg = pd.to_numeric(this_week[col], errors='coerce').fillna(0).mean()
                lw_avg = pd.to_numeric(last_week[col], errors='coerce').fillna(0).mean()
                f = 100 if ("率" in col and tw_avg <= 1.0) else 1
                tw, lw = tw_avg * f, lw_avg * f
                diff = tw - lw
                if "违规率" in target: vio_diff = diff
                fields.append({
                    "is_short": True,
                    "text": {"tag": "lark_md", "content": f"**{target}**\n本周均值: {tw:.2f}{'%' if f==100 else ''}\n差异: {'📈' if diff>0 else '📉'} {diff:+.2f}"}
                })

        card = {
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": f"📊 {biz_name} 作战简报"}, "template": "blue" if vio_diff <=0 else "red"},
            "elements": [{"tag": "div", "fields": fields}, {"tag": "hr"}, {"tag": "note", "elements": [{"tag": "plain_text", "content": f"周期: {period} (对比前一周均值)"}]}]
        }
        requests.post(webhook, json={"msg_type": "interactive", "card": card})

    @st.cache_data(ttl=60)
    def get_data(token, sid):
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{SPREADSHEET_TOKEN}/values/{sid}!A:Z?valueRenderOption=UnformattedValue"
        res = requests.get(url, headers=headers).json()
        return res.get("data", {}).get("valueRange", {}).get("values", [])

    # --- 侧边栏 ---
    st.sidebar.title("🎮 指挥控制台")
    mode = st.sidebar.radio("切换视图", ["单业务监控", "全业务大盘"])
    period = st.sidebar.select_slider("统计周期", options=["按天", "按周", "按月"], value="按周")
    days = {"按天": 1, "按周": 7, "按月": 30}[period]
    
    st.sidebar.divider()
    webhook = st.sidebar.text_input("飞书 Webhook")
    selected_biz = st.sidebar.multiselect("批量推送业务", list(SHEET_MAP.keys()))

    if st.sidebar.button("🚀 批量推送均值对比"):
        if not webhook: st.sidebar.error("请填入 Webhook")
        else:
            token = get_token()
            for b in selected_biz:
                raw = get_data(token, SHEET_MAP[b])
                if len(raw) > 1:
                    # 表头去重逻辑
                    counts, clean_h = {}, []
                    for c in raw[0]:
                        c_s = str(c) if c else "u"
                        counts[c_s] = counts.get(c_s, -1) + 1
                        clean_h.append(f"{c_s}.{counts[c_s]}" if counts[c_s] > 0 else c_s)
                    df_tmp = pd.DataFrame(raw[1:], columns=clean_h)
                    df_tmp['日期_idx'] = pd.to_datetime(df_tmp.iloc[:, 0], errors='coerce')
                    send_report(webhook, b, df_tmp.dropna(subset=['日期_idx']), period)
            st.sidebar.success("推送完成")

    # --- 主界面 ---
    if mode == "单业务监控":
        biz = st.sidebar.selectbox("预览业务", list(SHEET_MAP.keys()))
        token = get_token()
        raw = get_data(token, SHEET_MAP[biz])
        if len(raw) > 1:
            counts, clean_h = {}, []
            for c in raw[0]:
                c_s = str(c) if c else "u"
                counts[c_s] = counts.get(c_s, -1) + 1
                clean_h.append(f"{c_s}.{counts[c_s]}" if counts[c_s] > 0 else c_s)
            df = pd.DataFrame(raw[1:], columns=clean_h)
            df['日期_p'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            df = df.dropna(subset=['日期_p']).sort_values('日期_p')
            
            st.title(f"🛡️ {biz} 实时动态")
            df_plot = df.tail(max(7, days))
            cols_to_show = [c for c in clean_h if c != clean_h[0] and "u" not in c]
            user_cols = st.multiselect("指标选择", cols_to_show, default=cols_to_show[:4])
            
            for i in range(0, len(user_cols), 2):
                c_left, c_right = st.columns(2)
                for idx, col_ui in enumerate([c_left, c_right]):
                    if i + idx < len(user_cols):
                        dim = user_cols[i + idx]
                        y = pd.to_numeric(df_plot[dim], errors='coerce').fillna(0)
                        y_final = y * 100 if ("率" in dim and y.max() <= 1.0) else y
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df_plot['日期_p'], y=y_final, mode='lines+markers', line=dict(shape='spline', width=3)))
                        if len(y_final) > 1:
                            fig.add_hline(y=y_final.mean() + 2*y_final.std(), line_dash="dash", line_color="red")
                        fig.update_layout(title=f"【{dim}】走势", height=350, template="plotly_white")
                        col_ui.plotly_chart(fig, use_container_width=True)
    else:
        st.title(f"🌐 全业务对比 ({period})")
        # 大盘对比逻辑保持 V39 稳定性... (省略重复代码)
