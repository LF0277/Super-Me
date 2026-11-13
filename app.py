import streamlit as st
import pandas as pd
from datetime import datetime
import json
import time
from openai import OpenAI

# 设置页面为手机端尺寸，居中显示
st.set_page_config(page_title="Super Me", page_icon="👑", layout="centered")

st.markdown("""
<style>
/* 彻底隐藏所有 Streamlit 默认元素，让页面看起来像纯正的 APP */
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.block-container { padding-top: 2rem; padding-bottom: 5rem; padding-left: 1rem; padding-right: 1rem; max-width: 500px; }
.stApp { background-color: #050505; color: #E2E8F0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;}

/* 资产卡片：大圆角，金色渐变边框，内发光 */
.asset-card { padding: 20px 25px; border-radius: 20px; background: linear-gradient(145deg, #0A0A0A 0%, #151515 100%); margin-bottom: 15px; position: relative; display: flex; flex-direction: column; gap: 10px; border: 1px solid #D4AF37; box-shadow: inset 0 0 15px rgba(212, 175, 55, 0.1), 0 5px 15px rgba(0, 0, 0, 0.5); }
.asset-header { color: #A0AEC0; font-size: 13px; display: flex; align-items: center; gap: 8px;}
.asset-value { font-size: 32px; font-weight: 500; margin: 0; color: #FFF; letter-spacing: 0.5px;}

/* 标签页 (金色药丸按钮) */
.stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; border-bottom: none; margin-bottom: 15px; display: flex; justify-content: space-between; }
.stTabs [data-baseweb="tab"] { background-color: #0A0A0A; border-radius: 12px; border: 1px solid #222; color: #A0AEC0; padding: 10px 0px; flex: 1; text-align: center; transition: all 0.3s ease; }
.stTabs [aria-selected="true"] { background: linear-gradient(180deg, #1A1A1A 0%, #0A0A0A 100%) !important; color: #D4AF37 !important; border: 1px solid #D4AF37; box-shadow: 0 0 15px rgba(212, 175, 55, 0.3); font-weight: bold; }

/* 表格外框美化 */
[data-testid="stDataFrame"] { border: 1px solid #333; border-radius: 12px; overflow: hidden; box-shadow: 0 0 15px rgba(0, 0, 0, 0.5); }

/* 统一按钮与输入框 */
[data-testid="stTextInput"] input { background-color: #0A0A0A !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; }
.stButton>button, [data-testid="stFormSubmitButton"]>button { background: linear-gradient(90deg, #B8860B 0%, #D4AF37 100%) !important; color: #000 !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; }

/* 底部导航栏 */
.bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #0A0A0A; border-top: 1px solid #333; display: flex; justify-content: space-around; padding: 10px 0; z-index: 1000; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# 🚨 注意这里：云端读取密钥的安全写法！
client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

# 数据初始化
if "finance_df" not in st.session_state:
    st.session_state.finance_df = pd.DataFrame({"时间": pd.Series(dtype='datetime64[ns]'), "账户": pd.Series(dtype='object'), "类型": pd.Series(dtype='object'), "事项": pd.Series(dtype='object'), "金额": pd.Series(dtype='float64')})

now = datetime.now()

# 1. AI 控制台
with st.form("ai_form", clear_on_submit=True):
    user_input = st.text_input("对 AI 下达指令：", placeholder="例如：招商存款5万 / 今晚8点学英语", label_visibility="collapsed")
    submit_btn = st.form_submit_button("⚡ 执行指令", use_container_width=True)

if submit_btn and user_input:
    with st.spinner('AI 正在解析...'):
        today = datetime.now().strftime("%Y-%m-%d %H:%M")
        SYSTEM = f"""当前时间 {today}。提取信息并输出JSON：
        {{ "time": "YYYY-MM-DD HH:MM", "account": "招商银行/微信/支付宝/现金/日常", 
        "action": "收入/支出/欠款", "amount": 0.0, "detail": "事项" }}"""
        try:
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_input}], response_format={"type": "json_object"}, temperature=0)
            res = json.loads(resp.choices[0].message.content)
            
            new_row = pd.DataFrame([{"时间": pd.to_datetime(res.get("time", today)), "账户": res.get("account", "日常"), "类型": res.get("action", "支出"), "事项": res.get("detail", user_input), "金额": float(res.get("amount", 0.0))}])
            st.session_state.finance_df = pd.concat([st.session_state.finance_df, new_row], ignore_index=True)
            st.rerun()
        except Exception as e: st.error(f"AI 识别失败：{e}")

# 2. 黑金资产卡片
total_asset, sum_income_d, sum_expense_d = 0.0, 0.0, 0.0
for _, row in st.session_state.finance_df.iterrows():
    if pd.isna(row["类型"]) or pd.isna(row["金额"]): continue
    t, amt, dt = row["类型"], float(row["金额"]), row["时间"]
    if t in ["收入", "设定余额"]: total_asset += amt
    if t == "收入" and pd.notna(dt) and dt.date() == now.date(): sum_income_d += amt
    if t in ["支出", "代付款", "月付", "欠款"] and pd.notna(dt) and dt.date() == now.date(): sum_expense_d += amt

st.markdown(f'''
<div class="asset-card"><div class="asset-header">📄 总资产</div><div class="asset-value">¥ {total_asset:.2f}</div></div>
<div class="asset-card"><div class="asset-header">💵 收入</div><div class="asset-value">¥ {sum_income_d:.2f}</div></div>
<div class="asset-card"><div class="asset-header">💸 支出</div><div class="asset-value">¥ {sum_expense_d:.2f}</div></div>
''', unsafe_allow_html=True)

# 3. 表格区
tab1, = st.tabs(["财务流水明细"])
with tab1:
    edited_finance = st.data_editor(
        st.session_state.finance_df, use_container_width=True, num_rows="dynamic",
        column_config={
            "时间": st.column_config.DatetimeColumn("时间", format="YYYY-MM-DD HH:mm"),
            "账户": st.column_config.SelectboxColumn("账户", options=["招商银行", "微信", "支付宝", "现金", "日常"]),
            "类型": st.column_config.SelectboxColumn("类型", options=["收入", "支出", "欠款"]),
            "事项": st.column_config.TextColumn("事项"),
            "金额": st.column_config.NumberColumn("金额", min_value=0, format="¥%.2f")
        }, key="fin_editor"
    )
    if not edited_finance.equals(st.session_state.finance_df):
        st.session_state.finance_df = edited_finance; st.rerun()

# 4. 底部装饰
st.markdown("""
<div class="bottom-nav">
    <div style="text-align: center; color: #D4AF37;"><div style="font-size:20px;">🏠</div><div style="font-size:10px;">首页</div></div>
    <div style="text-align: center; color: #555;"><div style="font-size:20px;">📊</div><div style="font-size:10px;">统计</div></div>
</div>
<div style="margin-bottom: 60px;"></div>
""", unsafe_allow_html=True)
