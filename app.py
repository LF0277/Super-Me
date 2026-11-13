import streamlit as st
import pandas as pd
from datetime import datetime
import json
import time
from openai import OpenAI

st.set_page_config(page_title="Super Me", page_icon="logo.png", layout="centered")

st.markdown("""
<style>
/* 隐藏默认UI */
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.block-container { padding-top: 1rem; padding-bottom: 5rem; padding-left: 1rem; padding-right: 1rem; max-width: 500px; }
.stApp { background-color: #050505; color: #FFFFFF; font-family: -apple-system, sans-serif;}

/* 顶部 Logo 样式 */
.logo-container { text-align: center; margin-bottom: 20px; margin-top: 10px;}
.logo-container img { width: 120px; border-radius: 50%; box-shadow: 0 0 20px rgba(212, 175, 55, 0.4); }

/* 赛博朋克霓虹卡片 */
.asset-card { 
    padding: 22px; border-radius: 24px; margin-bottom: 15px; position: relative; overflow: hidden;
    background: linear-gradient(135deg, #111 0%, #000 100%);
    border: 1px solid #D4AF37;
    box-shadow: inset 0 0 20px rgba(212, 175, 55, 0.05), 0 8px 20px rgba(0, 0, 0, 0.8);
    display: flex; flex-direction: column; gap: 12px;
}
/* 卡片背后的霓虹光晕 */
.asset-card::before {
    content: ''; position: absolute; top: -50%; right: -20%; width: 150px; height: 150px;
    background: radial-gradient(circle, rgba(212, 175, 55, 0.15) 0%, transparent 70%);
    border-radius: 50%; z-index: 0;
}
.asset-header { color: #D4AF37; font-size: 14px; font-weight: 600; z-index: 1; display: flex; gap: 8px;}
.asset-value { font-size: 38px; font-weight: 800; margin: 0; color: #FFF; letter-spacing: 1px; z-index: 1; text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);}

/* 折叠面板样式优化 */
[data-testid="stExpander"] {
    background: linear-gradient(180deg, #0A0A0A 0%, #111 100%);
    border: 1px solid #333; border-radius: 15px; margin-bottom: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
}
[data-testid="stExpander"] summary { color: #D4AF37; font-weight: bold; }

/* 自定义黑金表格 */
.cyber-table { width: 100%; border-collapse: collapse; }
.cyber-table th { color: #666; font-size: 12px; padding: 10px 8px; border-bottom: 1px solid #222; text-align: left; }
.cyber-table td { color: #E2E8F0; font-size: 13px; padding: 12px 8px; border-bottom: 1px solid #111; }
.cyber-table tr:last-child td { border-bottom: none; }

/* 标签页美化 */
.stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; border-bottom: none; margin-bottom: 15px; display: flex; justify-content: space-between; }
.stTabs [data-baseweb="tab"] { background-color: #0A0A0A; border-radius: 12px; border: 1px solid #222; color: #666; padding: 12px 0px; flex: 1; text-align: center; transition: all 0.3s; }
.stTabs [aria-selected="true"] { background: linear-gradient(180deg, #1A1A1A 0%, #0A0A0A 100%) !important; color: #D4AF37 !important; border: 1px solid #D4AF37; box-shadow: 0 0 15px rgba(212, 175, 55, 0.2); font-weight: bold; }

/* 输入框与按钮 */
[data-testid="stTextInput"] input { background-color: #0A0A0A !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; border-radius: 12px !important; padding: 12px !important;}
.stButton>button, [data-testid="stFormSubmitButton"]>button { background: linear-gradient(90deg, #B8860B 0%, #D4AF37 100%) !important; color: #000 !important; border: none !important; border-radius: 12px !important; font-weight: bold !important; padding: 10px !important;}

/* 底部占位，防止被浏览器底栏挡住 */
.bottom-spacer { height: 80px; }
</style>
""", unsafe_allow_html=True)

# 🚨 渲染你的绝美 Logo（限制宽度并居中）
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image("logo.png", width=120)
st.markdown('</div>', unsafe_allow_html=True)

client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

# 数据初始化
if "finance_df" not in st.session_state:
    st.session_state.finance_df = pd.DataFrame({"日期": pd.Series(dtype='object'), "时间": pd.Series(dtype='object'), "账户": pd.Series(dtype='object'), "类型": pd.Series(dtype='object'), "事项": pd.Series(dtype='object'), "金额": pd.Series(dtype='float64')})
if "plan_df" not in st.session_state:
    st.session_state.plan_df = pd.DataFrame({"日期": pd.Series(dtype='object'), "时间": pd.Series(dtype='object'), "计划事项": pd.Series(dtype='object'), "状态": pd.Series(dtype='object')})

now = datetime.now()
today_str = now.strftime("%Y-%m-%d")

# 智能指令
with st.form("ai_form", clear_on_submit=True):
    user_input = st.text_input("指令", placeholder="例如：招商存款5万 / 今晚8点学英语", label_visibility="collapsed")
    submit_btn = st.form_submit_button("⚡ 执行指令", use_container_width=True)

if submit_btn and user_input:
    with st.spinner('AI 解析中...'):
        SYSTEM = f"""当前时间 {today_str}。提取信息并输出JSON：
        {{ "type": "finance或plan", "date": "YYYY-MM-DD", "time": "HH:MM", "account": "招商银行/微信/支付宝/现金/日常", 
        "action": "收入/支出/欠款", "amount": 0.0, "detail": "事项" }}"""
        try:
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_input}], response_format={"type": "json_object"}, temperature=0)
            res = json.loads(resp.choices[0].message.content)
            date_val = res.get("date", today_str)
            time_val = res.get("time", now.strftime("%H:%M"))
            
            if res.get("type") == "finance":
                new_row = pd.DataFrame([{"日期": date_val, "时间": time_val, "账户": res.get("account", "日常"), "类型": res.get("action", "支出"), "事项": res.get("detail", user_input), "金额": float(res.get("amount", 0.0))}])
                st.session_state.finance_df = pd.concat([st.session_state.finance_df, new_row], ignore_index=True)
            else:
                new_row = pd.DataFrame([{"日期": date_val, "时间": time_val, "计划事项": res.get("detail", user_input), "状态": "未完成"}])
                st.session_state.plan_df = pd.concat([st.session_state.plan_df, new_row], ignore_index=True)
            st.rerun()
        except Exception as e: st.error(f"识别失败：{e}")

# 资产统计
total_asset, sum_income, sum_expense = 0.0, 0.0, 0.0
for _, row in st.session_state.finance_df.iterrows():
    if pd.isna(row["类型"]) or pd.isna(row["金额"]): continue
    if row["类型"] == "收入":
        total_asset += float(row["金额"]); sum_income += float(row["金额"])
    elif row["类型"] in ["支出", "欠款"]:
        sum_expense += float(row["金额"]); total_asset -= float(row["金额"])

st.markdown(f'''
<div class="asset-card"><div class="asset-header">💳 总资产</div><div class="asset-value">¥ {total_asset:.2f}</div></div>
<div class="asset-card"><div class="asset-header">💵 收入</div><div class="asset-value">¥ {sum_income:.2f}</div></div>
<div class="asset-card"><div class="asset-header">💸 支出</div><div class="asset-value">¥ {sum_expense:.2f}</div></div>
''', unsafe_allow_html=True)

# 标签页
tab1, tab2 = st.tabs(["财务流水", "日常计划"])

# --- 财务流水折叠 ---
with tab1:
    if st.session_state.finance_df.empty:
        st.markdown("<p style='text-align:center; color:#666;'>暂无记录</p>", unsafe_allow_html=True)
    else:
        dates = st.session_state.finance_df["日期"].unique()
        dates = sorted(dates, reverse=True)
        for d in dates:
            day_df = st.session_state.finance_df[st.session_state.finance_df["日期"] == d]
            day_sum = day_df["金额"].sum()
            title = f"📅 {d} ( {'今日' if d == today_str else '历史'} ) - 合计: ¥{day_sum:.2f}"
            
            with st.expander(title, expanded=(d == today_str)):
                html_table = '<table class="cyber-table"><tr><th>时间</th><th>账户</th><th>类型</th><th>事项</th><th>金额</th></tr>'
                for _, row in day_df.iterrows():
                    color = "#a9bfa6" if row["类型"] == "收入" else "#d9a494"
                    sign = "+" if row["类型"] == "收入" else "-"
                    html_table += f'<tr><td>{row["时间"]}</td><td>{row["账户"]}</td><td>{row["类型"]}</td><td>{row["事项"][:6]}</td><td style="color:{color}">{sign}{row["金额"]:.2f}</td></tr>'
                html_table += '</table>'
                st.markdown(html_table, unsafe_allow_html=True)

# --- 日常计划折叠 ---
with tab2:
    if st.session_state.plan_df.empty:
        st.markdown("<p style='text-align:center; color:#666;'>暂无计划</p>", unsafe_allow_html=True)
    else:
        dates = st.session_state.plan_df["日期"].unique()
        dates = sorted(dates, reverse=True)
        for d in dates:
            day_df = st.session_state.plan_df[st.session_state.plan_df["日期"] == d]
            title = f"📅 {d} ( {'今日' if d == today_str else '历史'} ) 计划"
            with st.expander(title, expanded=(d == today_str)):
                html_table = '<table class="cyber-table"><tr><th>时间</th><th>计划事项</th><th>状态</th></tr>'
                for _, row in day_df.iterrows():
                    html_table += f'<tr><td>{row["时间"]}</td><td>{row["计划事项"]}</td><td style="color:#D4AF37">{row["状态"]}</td></tr>'
                html_table += '</table>'
                st.markdown(html_table, unsafe_allow_html=True)

# 底部留白，防止被手机底栏遮挡
st.markdown('<div class="bottom-spacer"></div>', unsafe_allow_html=True)
