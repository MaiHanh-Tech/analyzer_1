import streamlit as st
import json
import re

# 1. CẤU HÌNH TRANG (DÒNG ĐẦU TIÊN)
st.set_page_config(page_title="Super AI System", layout="wide", page_icon="🏢")

# 2. KHỐI BẢO MẬT
try:
    from auth_block import AuthBlock
    auth = AuthBlock()
except ImportError:
    st.error("❌ Thiếu file 'auth_block.py'. Hãy tạo file này trước!")
    st.stop()

# 3. MÀN HÌNH ĐĂNG NHẬP
if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = False

if not st.session_state.user_logged_in:
    st.title("🔐 Đăng Nhập Hệ Thống")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        pwd = st.text_input("Nhập mật khẩu quản trị:", type="password")
        
        if st.button("Đăng Nhập", use_container_width=True):
            # Hàm này sẽ check Hash trong secrets.toml
            if auth.login(pwd): 
                st.success("Đang vào hệ thống...")
                st.rerun()
            else:
                st.error("Sai mật khẩu hoặc tài khoản bị khóa!")
    st.stop() 

# 4. GIAO DIỆN CHÍNH (CHỈ HIỆN KHI ĐÚNG MẬT KHẨU)
with st.sidebar:
    st.title("🗂️ DANH MỤC ỨNG DỤNG")
    st.info(f"👤 User: **{st.session_state.current_user}**")
    
    app_choice = st.radio("Chọn Module:", [
        "💰 1. Cognitive Weaver (Sách & Graph)", 
        "🌏 2. AI Translator (Dịch thuật)",
        "🧠 3. CFO Controller (Tài chính)"
    ])
    
    st.divider()
    if st.button("Đăng Xuất"):
        st.session_state.user_logged_in = False
        st.rerun()

# 5. ĐIỀU HƯỚNG
try:
    if app_choice == "💰 1. Cognitive Weaver (Sách & Graph)":
        import module_weaver
        module_weaver.run()
         
    elif app_choice == "🌏 2. AI Translator (Dịch thuật)":
        import module_translator
        module_translator.run()
        
    elif app_choice == "🧠 3. CFO Controller (Tài chính)":
        import module_cfo
        module_cfo.run()
        
except ImportError as e:
    st.error(f"⚠️ Lỗi import module: {e}")
