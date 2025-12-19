import streamlit as st
import time

# --- 1. TRIỆU HỒI CÁC TRƯỞNG PHÒNG (IMPORT BLOCKS) ---
# Chị phải đảm bảo 4 file kia nằm cùng thư mục với file app.py này nhé
try:
    from auth_block import AuthBlock
    from ai_core import AI_Core
    from voice_block import Voice_Engine
    from prompts import DEBATE_PERSONAS, UNCLE_SYSTEM_PROMPT
except ImportError as e:
    st.error(f"❌ Lỗi: Thiếu các file Meta-blocks. Hãy đảm bảo chị đã tạo đủ 4 file: auth_block.py, ai_core.py, voice_block.py, prompts.py. Chi tiết: {e}")
    st.stop()

# --- 2. CẤU HÌNH TRANG ---
st.set_page_config(page_title="The Cognitive Weaver", layout="wide", page_icon="💎")

# --- 3. KHỞI TẠO (INIT) ---
# Gọi các "Trưởng phòng" dậy để chuẩn bị làm việc
auth = AuthBlock()
ai = AI_Core()
voice = Voice_Engine()

# --- 4. LUỒNG ĐĂNG NHẬP (GATEKEEPER) ---
def check_login_status():
    if 'user_logged_in' not in st.session_state:
        st.session_state.user_logged_in = False

    if not st.session_state.user_logged_in:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.title("🔐 Đăng Nhập Hệ Thống")
            pwd = st.text_input("Nhập mật khẩu:", type="password")
            if st.button("Đăng Nhập", use_container_width=True):
                # Gọi Auth Block để kiểm tra
                if auth.login(pwd):
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("Sai mật khẩu!")
        return False # Chưa đăng nhập
    return True # Đã đăng nhập

# --- 5. GIAO DIỆN CHÍNH (MAIN APP) ---
def main_app():
    # --- Sidebar: Thông tin User ---
    with st.sidebar:
        st.write(f"👤 User: **{st.session_state.current_user}**")
        if st.session_state.is_vip:
            st.success("🌟 VIP Member (Unlimited)")
        else:
            # Kiểm tra quota từ Auth Block
            used, limit, _ = auth.check_quota() # Giả sử auth_block trả về status
            # Nếu auth_block của chị chưa có hàm check_quota trả về số, chị có thể bỏ qua dòng progress
            st.info("Trạng thái: Standard User")
            
        if st.button("Đăng xuất"):
            st.session_state.user_logged_in = False
            st.rerun()

    # --- Header ---
    st.title("💎 Người Dệt Nhận Thức (The Cognitive Weaver)")
    st.caption("Hệ thống tích hợp Đa mô hình: RAG, Debate, Voice")

    # --- TẠO 3 TAB CHỨC NĂNG ---
    tab1, tab2, tab3 = st.tabs(["📚 Phân Tích Sách (RAG)", "🗣️ Tranh Biện (Uncle Mode)", "🎙️ Phòng Thu AI"])

    # ==================================================
    # TAB 1: PHÂN TÍCH SÁCH (Sử dụng AI Core + Cache)
    # ==================================================
    with tab1:
        st.header("Trợ lý Đọc & Phân tích Tài liệu")
        uploaded_file = st.file_uploader("Tải lên tài liệu (TXT/MD)...", type=['txt', 'md'])
        
        if uploaded_file:
            # Đọc nội dung file
            file_text = uploaded_file.read().decode("utf-8")
            st.text_area("Nội dung xem trước:", file_text[:500] + "...", height=100)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🚀 Phân tích Tóm tắt"):
                    if auth.check_quota(): # Kiểm tra tiền
                        with st.spinner("AI đang đọc sách..."):
                            # Gọi hàm có Cache trong AI Core
                            res = ai.analyze_static(file_text, "Tóm tắt các ý chính và bài học quan trọng.")
                            st.markdown(res)
                            auth.track(len(file_text)) # Trừ tiền
                    else:
                        st.error("Hết Quota hôm nay!")

            with col_b:
                if st.button("🕵️ Phân tích Phản biện"):
                    if auth.check_quota():
                        with st.spinner("AI đang soi lỗi..."):
                            res = ai.analyze_static(file_text, "Tìm các lỗ hổng logic và phản biện lại tác giả.")
                            st.markdown(res)
                            auth.track(len(file_text))
                    else:
                        st.error("Hết Quota!")

    # ==================================================
    # TAB 2: TRANH BIỆN (Sử dụng AI Core + Prompts)
    # ==================================================
    with tab2:
        st.header("Đấu Trường Tư Duy (Real-time Debate)")
        
        # Chọn nhân vật từ file prompts.py
        c1, c2 = st.columns([3, 1])
        with c1:
            # Lấy danh sách nhân vật từ file prompts
            persona_name = st.selectbox("Chọn Đối Thủ:", list(DEBATE_PERSONAS.keys()))
        with c2:
            if st.button("🗑️ Xóa Chat"):
                st.session_state.chat_history = []
                st.rerun()

        # Khởi tạo lịch sử chat
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Hiển thị lịch sử cũ
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        # Ô nhập liệu
        if user_input := st.chat_input("Nhập luận điểm của bạn..."):
            # 1. Kiểm tra Quota trước
            if not auth.check_quota():
                st.error("🚫 Hết Quota! Vui lòng quay lại mai.")
            else:
                # 2. Hiện câu hỏi User
                st.chat_message("user").write(user_input)
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # 3. AI Trả lời
                with st.chat_message("assistant"):
                    # Lấy System Prompt của nhân vật đã chọn
                    sys_instruction = DEBATE_PERSONAS[persona_name]
                    
                    with st.spinner(f"{persona_name} đang suy ngẫm..."):
                        # Gọi AI Core (Hàm này đã có sẵn cơ chế Retry/Lì đòn)
                        # Dùng Flash cho nhanh
                        response = ai.generate(
                            prompt=user_input, 
                            model_type="flash", 
                            system_instruction=sys_instruction
                        )
                        
                        st.write(response)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        
                        # Trừ tiền (Tính cả câu hỏi và câu trả lời)
                        auth.track(len(user_input) + len(response))

    # ==================================================
    # TAB 3: PHÒNG THU (Sử dụng Voice Block)
    # ==================================================
    with tab3:
        st.header("Phòng Thu AI (Text-to-Speech)")
        
        text_to_speak = st.text_area("Nhập văn bản cần đọc:", height=150)
        
        c_v1, c_v2 = st.columns(2)
        with c_v1:
            lang_choice = st.selectbox("Ngôn ngữ:", ["Tiếng Việt", "Tiếng Anh", "Tiếng Trung"])
            # Map tên ngôn ngữ sang mã mà voice_block hiểu
            lang_map = {"Tiếng Việt": "vi", "Tiếng Anh": "en", "Tiếng Trung": "zh"}
            
        with c_v2:
            speed = st.slider("Tốc độ đọc:", -50, 50, 0)

        if st.button("🔊 Đọc Ngay", type="primary"):
            if text_to_speak:
                with st.spinner("Đang thu âm..."):
                    # Gọi Voice Engine
                    audio_path = voice.speak(
                        text_to_speak, 
                        lang=lang_map[lang_choice], 
                        speed=speed
                    )
                    
                    if audio_path:
                        st.audio(audio_path)
                        st.success("Đã tạo xong file âm thanh!")
                    else:
                        st.error("Lỗi tạo âm thanh. Vui lòng thử lại.")

# --- CHẠY ỨNG DỤNG ---
if __name__ == "__main__":
    # Chỉ chạy App chính nếu đã đăng nhập
    if check_login_status():
        main_app()
