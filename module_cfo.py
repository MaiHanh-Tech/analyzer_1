import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
import time

# Import các Block dùng chung (để dùng AI)
from ai_core import AI_Core
# (Nếu chị chưa có file ai_core.py thì nó sẽ báo lỗi, đảm bảo chị đã tạo nó ở bước trước)

# --- CÁC HÀM XỬ LÝ DỮ LIỆU ---
def tao_data_full_kpi():
    dates = pd.date_range(start="2023-01-01", periods=24, freq="ME")
    df = pd.DataFrame({"Tháng": dates})
    np.random.seed(42)
    df["Doanh Thu"] = np.random.randint(5000, 8000, 24) * 1000000
    df["Giá Vốn"] = df["Doanh Thu"] * 0.6 
    df["CP Lương"] = np.random.randint(500, 800, 24) * 1000000
    df["CP Marketing"] = df["Doanh Thu"] * 0.1
    df["CP Khác"] = np.random.randint(100, 200, 24) * 1000000
    df["Chi Phí VH"] = df["CP Lương"] + df["CP Marketing"] + df["CP Khác"]
    df["Lợi Nhuận ST"] = df["Doanh Thu"] - df["Giá Vốn"] - df["Chi Phí VH"]
    df["Dòng Tiền Thực"] = df["Lợi Nhuận ST"] * 0.8
    df["Công Nợ Phải Thu"] = np.random.randint(1000, 2000, 24) * 1000000
    df["Hàng Tồn Kho Tổng"] = np.random.randint(1000, 2000, 24) * 1000000
    df["TS Ngắn Hạn"] = np.random.randint(2000, 3000, 24) * 1000000
    df["Nợ Ngắn Hạn"] = np.random.randint(1000, 1500, 24) * 1000000
    df["Vốn Chủ Sở Hữu"] = np.random.randint(5000, 6000, 24) * 1000000
    # Gài bẫy cho ML
    df.loc[20, "Chi Phí VH"] = 3000000000 
    return df

def tinh_chi_so(df):
    try:
        df["Current Ratio"] = df["TS Ngắn Hạn"] / df["Nợ Ngắn Hạn"].replace(0, 1)
        df["Gross Margin"] = (df["Doanh Thu"] - df["Giá Vốn"]) / df["Doanh Thu"].replace(0, 1) * 100
        df["ROS"] = df["Lợi Nhuận ST"] / df["Doanh Thu"].replace(0, 1) * 100
    except: pass
    return df

def phat_hien_gian_lan(df):
    iso = IsolationForest(contamination=0.05, random_state=42)
    col = "Chi Phí VH" if "Chi Phí VH" in df.columns else df.columns[1]
    df['Anomaly'] = iso.fit_predict(df[[col]])
    return df[df['Anomaly'] == -1]

# --- HÀM CHÍNH (ĐỂ APP.PY GỌI) ---
def run():
    # Khởi tạo AI
    ai = AI_Core()

    st.header("💰 CFO Controller Dashboard")
    
    # Sidebar riêng của Module này
    with st.sidebar:
        st.markdown("---")
        st.write("🔧 **Cấu hình CFO**")
        if st.button("🔄 Tải lại dữ liệu mẫu"):
            st.session_state.df_fin = tao_data_full_kpi()
            st.rerun()
            
    # Init Data
    if 'df_fin' not in st.session_state:
        st.session_state.df_fin = tao_data_full_kpi()
    
    df = tinh_chi_so(st.session_state.df_fin.copy())
    last = df.iloc[-1]

    # Tabs
    t1, t2, t3, t4 = st.tabs(["📊 KPIs & Sức Khỏe", "📉 Phân Tích Chi Phí", "🕵️ Rủi Ro & Check", "🔮 Dự Báo & What-If"])

    # TAB 1: KPI
    with t1:
        st.subheader("Sức khỏe Tài chính Tháng gần nhất")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Doanh Thu", f"{last['Doanh Thu']/1e9:.1f} tỷ")
        k2.metric("Lợi Nhuận ST", f"{last['Lợi Nhuận ST']/1e9:.1f} tỷ")
        k3.metric("ROS", f"{last.get('ROS',0):.1f}%")
        k4.metric("Dòng Tiền", f"{last['Dòng Tiền Thực']/1e9:.1f} tỷ")
        
        st.line_chart(df.set_index("Tháng")[["Doanh Thu", "Lợi Nhuận ST"]])

    # TAB 2: CHI PHÍ & AI
    with t2:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.plotly_chart(px.bar(df, x="Tháng", y=["Giá Vốn", "Chi Phí VH"], title="Cấu trúc Chi phí"), use_container_width=True)
        with c2:
            st.write("🤖 **Trợ lý Phân tích:**")
            q = st.text_input("Hỏi về chi phí...")
            if q:
                with st.spinner("AI đang soi số liệu..."):
                    # Gửi data tháng cuối cho AI
                    context = f"Dữ liệu tháng cuối: Doanh thu {last['Doanh Thu']}, Giá vốn {last['Giá Vốn']}, CP {last['Chi Phí VH']}."
                    res = ai.generate(q, system_instruction=f"Bạn là Kế toán trưởng. Phân tích dựa trên: {context}")
                    st.write(res)

    # TAB 3: RỦI RO & CROSS-CHECK
    with t3:
        c_risk, c_check = st.columns(2)
        with c_risk:
            st.subheader("Quét Gian Lận (ML)")
            if st.button("🔍 Quét ngay"):
                bad = phat_hien_gian_lan(df)
                if not bad.empty:
                    st.error(f"Phát hiện {len(bad)} tháng bất thường!")
                    st.dataframe(bad)
                else:
                    st.success("Dữ liệu sạch.")
        
        with c_check:
            st.subheader("Cross-Check (Đối chiếu)")
            val_a = st.number_input("Số liệu Thuế (Tờ khai):", value=100.0)
            val_b = st.number_input("Số liệu Sổ cái (ERP):", value=105.0)
            if st.button("So khớp"):
                diff = val_b - val_a
                if diff != 0:
                    st.warning(f"Lệch: {diff}. Rủi ro truy thu thuế!")
                else:
                    st.success("Khớp!")

    # TAB 4: WHAT-IF
    with t4:
        st.subheader("🎛️ What-If Analysis")
        st.caption("Giả lập kịch bản: Nếu thay đổi đầu vào thì Lợi nhuận ra sao?")
        
        base_rev = last['Doanh Thu']
        base_profit = last['Lợi Nhuận ST']
        
        c_s1, c_s2 = st.columns(2)
        with c_s1: delta_price = st.slider("Tăng/Giảm Giá Bán (%)", -20, 20, 0)
        with c_s2: delta_cost = st.slider("Tăng/Giảm Chi Phí (%)", -20, 20, 0)
        
        new_rev = base_rev * (1 + delta_price/100)
        # Giả sử chi phí biến đổi theo doanh thu + chi phí cố định
        new_profit = base_profit + (new_rev - base_rev) - (last['Chi Phí VH'] * delta_cost/100)
        
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("Lợi Nhuận Gốc", f"{base_profit/1e9:.2f} tỷ")
        col_res2.metric("Lợi Nhuận Mới", f"{new_profit/1e9:.2f} tỷ", delta=f"{(new_profit - base_profit)/1e9:.2f} tỷ")
