import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.express as px
import markdown
import json
import re
from streamlit_agraph import agraph, Node, Edge, Config
import sys
import time

# --- IMPORT CÁC META-BLOCKS DÙNG CHUNG ---
from auth_block import AuthBlock
from ai_core import AI_Core
from voice_block import Voice_Engine
from prompts import DEBATE_PERSONAS, BOOK_ANALYSIS_PROMPT


# Fix lỗi asyncio trên Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- 1. CẤU HÌNH TRANG (PHẢI Ở DÒNG ĐẦU TIÊN) ---
st.set_page_config(page_title="The Cognitive Weaver", layout="wide", page_icon="💎")

# ==========================================
# 🌍 BỘ TỪ ĐIỂN ĐA NGÔN NGỮ (ĐƯA LÊN ĐẦU ĐỂ TRÁNH LỖI)
# ==========================================
TRANS = {
    "vi": {
        "title": "🕸️ Người Dệt Nhận Thức",
        "login_title": "🔐 Đăng Nhập Hệ Thống",
        "login_btn": "Đăng Nhập",
        "pass_placeholder": "Nhập mật khẩu truy cập...",
        "wrong_pass": "Sai mật khẩu!",
        "logout": "Đăng Xuất",
        "welcome": "Xin chào",
        "role_admin": "Quản Trị Viên",
        "role_user": "Thành Viên",
        "lang_select": "Ngôn ngữ / Language / 语言",
        # Tabs
        "tab1": "📚 Phân Tích Sách",
        "tab2": "✍️ Dịch Giả",
        "tab3": "🗣️ Tranh Biện",
        "tab4": "🎙️ Phòng Thu AI",
        "tab5": "⏳ Nhật Ký",
        # Tab 1
        "t1_header": "Trợ lý Nghiên cứu & Knowledge Graph",
        "t1_up_excel": "1. Kết nối Kho Sách (Excel)",
        "t1_up_doc": "2. Tài liệu mới (PDF/Docx)",
        "t1_btn": "🚀 PHÂN TÍCH NGAY",
        "t1_connect_ok": "✅ Đã kết nối {n} cuốn sách.",
        "t1_analyzing": "Đang phân tích {name}...",
        "t1_graph_title": "🪐 Vũ Trụ Sách",
        # Tab 2
        "t2_header": "Dịch Thuật Đa Chiều",
        "t2_input": "Nhập văn bản cần dịch:",
        "t2_target": "Dịch sang:",
        "t2_style": "Phong cách:",
        "t2_btn": "✍️ Dịch Ngay",
        "t2_styles": ["Mặc định", "Hàn lâm/Học thuật", "Văn học/Cảm xúc", "Đời thường", "Kinh tế", "Kiếm hiệp"],
        # Tab 3
        "t3_header": "Đấu Trường Tư Duy",
        "t3_persona_label": "Chọn Đối Thủ:",
        "t3_input": "Nhập chủ đề tranh luận...",
        "t3_clear": "🗑️ Xóa Chat",
        # Tab 4
        "t4_header": "🎙️ Phòng Thu AI Đa Ngôn Ngữ",
        "t4_voice": "Chọn Giọng:",
        "t4_speed": "Tốc độ:",
        "t4_btn": "🔊 TẠO AUDIO",
        "t4_dl": "⬇️ TẢI MP3",
        # Tab 5
        "t5_header": "Nhật Ký & Lịch Sử",
        "t5_refresh": "🔄 Tải lại Lịch sử",
        "t5_empty": "Chưa có dữ liệu lịch sử.",
        "t5_chart": "📈 Biểu đồ Cảm xúc",
    },
    "en": {
        "title": "🕸️ The Cognitive Weaver",
        "login_title": "🔐 System Login",
        "login_btn": "Login",
        "pass_placeholder": "Enter password...",
        "wrong_pass": "Wrong password!",
        "logout": "Logout",
        "welcome": "Welcome",
        "role_admin": "Admin",
        "role_user": "Member",
        "lang_select": "Language",
        "tab1": "📚 Book Analysis",
        "tab2": "✍️ Translator",
        "tab3": "🗣️ Debater",
        "tab4": "🎙️ AI Studio",
        "tab5": "⏳ History",
        "t1_header": "Research Assistant & Knowledge Graph",
        "t1_up_excel": "1. Connect Book Database (Excel)",
        "t1_up_doc": "2. New Documents (PDF/Docx)",
        "t1_btn": "🚀 ANALYZE NOW",
        "t1_connect_ok": "✅ Connected {n} books.",
        "t1_analyzing": "Analyzing {name}...",
        "t1_graph_title": "🪐 Book Universe",
        "t2_header": "Multidimensional Translator",
        "t2_input": "Enter text to translate:",
        "t2_target": "Translate to:",
        "t2_style": "Style:",
        "t2_btn": "✍️ Translate",
        "t2_styles": ["Default", "Academic", "Literary/Emotional", "Casual", "Business", "Wuxia/Martial Arts"],
        "t3_header": "Thinking Arena",
        "t3_persona_label": "Choose Opponent:",
        "t3_input": "Enter debate topic...",
        "t3_clear": "🗑️ Clear Chat",
        "t4_header": "🎙️ Multilingual AI Studio",
        "t4_voice": "Select Voice:",
        "t4_speed": "Speed:",
        "t4_btn": "🔊 GENERATE AUDIO",
        "t4_dl": "⬇️ DOWNLOAD MP3",
        "t5_header": "Logs & History",
        "t5_refresh": "🔄 Refresh History",
        "t5_empty": "No history data found.",
        "t5_chart": "📈 Emotion Chart",
    },
    "zh": {
        "title": "🕸️ 认知编织者 (The Cognitive Weaver)",
        "login_title": "🔐 系统登录",
        "login_btn": "登录",
        "pass_placeholder": "请输入密码...",
        "wrong_pass": "密码错误！",
        "logout": "登出",
        "welcome": "你好",
        "role_admin": "管理员",
        "role_user": "成员",
        "lang_select": "语言",
        "tab1": "📚 书籍分析",
        "tab2": "✍️ 翻译专家",
        "tab3": "🗣️ 辩论场",
        "tab4": "🎙️ AI 录音室",
        "tab5": "⏳ 历史记录",
        "t1_header": "研究助手 & 知识图谱",
        "t1_up_excel": "1. 连接书库 (Excel)",
        "t1_up_doc": "2. 上传新文档 (PDF/Docx)",
        "t1_btn": "🚀 立即分析",
        "t1_connect_ok": "✅ 已连接 {n} 本书。",
        "t1_analyzing": "正在分析 {name}...",
        "t1_graph_title": "🪐 书籍宇宙",
        "t2_header": "多维翻译",
        "t2_input": "输入文本:",
        "t2_target": "翻译成:",
        "t2_style": "风格:",
        "t2_btn": "✍️ 翻译",
        "t2_styles": ["默认", "学术", "文学/情感", "日常", "商业", "武侠"],
        "t3_header": "思维竞技场",
        "t3_persona_label": "选择对手:",
        "t3_input": "输入辩论主题...",
        "t3_clear": "🗑️ 清除聊天",
        "t4_header": "🎙️ AI 多语言录音室",
        "t4_voice": "选择声音:",
        "t4_speed": "语速:",
        "t4_btn": "🔊 生成音频",
        "t4_dl": "⬇️ 下载 MP3",
        "t5_header": "日志 & 历史",
        "t5_refresh": "🔄 刷新历史",
        "t5_empty": "暂无历史数据。",
        "t5_chart": "📈 情绪图表",
    }
}

# Hàm lấy text theo ngôn ngữ (Đặt ở đây để Main có thể gọi ngay)
def T(key):
    lang = st.session_state.get('lang', 'vi')
    return TRANS.get(lang, TRANS['vi']).get(key, key)


# --- KHỞI TẠO CÔNG CỤ ĐẶC THÙ CỦA WEAVER ---
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def doc_file(uploaded_file):
    if not uploaded_file: return ""
    ext = uploaded_file.name.split('.')[-1].lower()
    try:
        if ext == "pdf":
            reader = PdfReader(uploaded_file)
            return "\n".join([page.extract_text() for page in reader.pages])
        elif ext == "docx":
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext in ["txt", "md", "html"]:
            return str(uploaded_file.read(), "utf-8")
    except: return ""
    return ""

# --- LOGIC GSHEET (NHẬT KÝ VĨNH VIỄN) ---
def connect_gsheet():
    try:
        if "gcp_service_account" not in st.secrets: return None
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open("AI_History_Logs").sheet1
    except: return None

def tai_lich_su_tu_sheet():
    try:
        sheet = connect_gsheet()
        if sheet:
            data = sheet.get_all_records()
            my_user = st.session_state.get("current_user", "")
            if st.session_state.get("is_admin", False): return data
            return [item for item in data if item.get("User") == my_user]
    except: return []
    return []

# --- HÀM CHẠY CHÍNH CỦA MODULE ---
def run():
    # Khởi tạo Trưởng phòng
    ai = AI_Core()
    voice = Voice_Engine()
    auth = AuthBlock()
    
    st.header("🧠 The Cognitive Weaver (Người Dệt Nhận Thức)")

    # Tabs (Giữ nguyên cấu trúc 5 Tab của chị)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 Phân Tích Sách", 
        "✍️ Dịch Giả", 
        "🗣️ Tranh Biện (Uncle Mode)", 
        "🎙️ Phòng Thu AI", 
        "⏳ Nhật Ký"
    ])

    # === TAB 1: RAG & KNOWLEDGE GRAPH ===
    with tab1:
        st.subheader("Trợ lý Nghiên cứu & Knowledge Graph")
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1: file_excel = st.file_uploader("1. Kho Sách (Excel)", type="xlsx", key="w_excel")
        with c2: uploaded_files = st.file_uploader("2. Tài liệu mới", accept_multiple_files=True, key="w_docs")
        with c3: st.write(""); btn_run = st.button("🚀 PHÂN TÍCH NGAY", type="primary")

        if btn_run and uploaded_files:
            vec = load_embedding_model()
            has_db = False
            if file_excel:
                df_db = pd.read_excel(file_excel).dropna(subset=["Tên sách"])
                db_embs = vec.encode([f"{r['Tên sách']} {str(r.get('CẢM NHẬN',''))}" for _, r in df_db.iterrows()])
                has_db = True
                st.success(f"✅ Kết nối {len(df_db)} cuốn sách.")

            for f in uploaded_files:
                text = doc_file(f)
                link = ""
                if has_db:
                    q = vec.encode([text[:2000]])
                    sc = cosine_similarity(q, db_embs)[0]
                    idx = np.argsort(sc)[::-1][:3]
                    for i in idx:
                        if sc[i] > 0.35: link += f"- {df_db.iloc[i]['Tên sách']} ({sc[i]*100:.0f}%)\n"

                with st.spinner(f"Đang dệt nhận thức cho {f.name}..."):
                    prompt = f"Phân tích tài liệu: {f.name}. Liên quan: {link}. Nội dung: {text[:20000]}"
                    # Dùng AI Core có Cache để tiết kiệm quota
                    res = ai.analyze_static(prompt, BOOK_ANALYSIS_PROMPT)
                    st.markdown(f"### 📄 {f.name}")
                    st.markdown(res)
                    # Lưu log
                    if connect_gsheet():
                         connect_gsheet().append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Phân Tích", f.name, res[:5000], st.session_state.current_user, 0, "Neutral"])

    # === TAB 2: DỊCH THUẬT ĐA CHIỀU ===
    with tab2:
        st.subheader("Dịch Thuật Chuyên Sâu")
        txt = st.text_area("Nhập văn bản cần dịch:", height=150)
        c_l, c_s, c_b = st.columns([1,1,1])
        with c_l: target_lang = st.selectbox("Dịch sang:", ["Tiếng Việt", "English", "Chinese", "French", "Japanese"])
        with c_s: style = st.selectbox("Phong cách:", ["Mặc định", "Hàn lâm", "Văn học", "Kinh tế", "Kiếm hiệp"])
        if st.button("✍️ Dịch Ngay") and txt:
            with st.spinner("AI đang chuyển ngữ..."):
                p = f"Dịch văn bản sau sang {target_lang} với phong cách {style}. Nếu sang Trung phải có Pinyin. Văn bản: {txt}"
                res = ai.generate(p, model_type="pro")
                st.markdown(res)

    # === TAB 3: ĐẤU TRƯỜNG TƯ DUY (UNCLE MODE) ===
    with tab3:
        st.subheader("Đấu Trường Tư Duy")
        # Chọn chế độ: Solo hoặc Hội đồng
        mode = st.radio("Chọn chế độ:", ["👤 Solo (User vs AI)", "⚔️ Debate (AI vs AI)"], horizontal=True, key="mode_select_tab3")

        
        st.divider()

        # --- CHẾ ĐỘ 1: SOLO (user vs AI) ---
        if mode == "👤 Solo (User vs AI)":
            # Dùng Container để cô lập không gian ID
            with st.container():
                c1, c2 = st.columns([3, 1])
                with c1: 
                    p_sel = st.selectbox(T("t3_persona_label"), list(personas.keys()), key="solo_persona_select")
                with c2: 
                    st.write(""); st.write("")
                    if st.button(T("t3_clear"), key="btn_clr_solo"): 
                        st.session_state.chat_history = []
                        st.rerun()

                # Hiển thị lịch sử chat
                for m in st.session_state.chat_history:
                    st.chat_message(m["role"]).markdown(m["content"])
                
                # Input Chat (Key duy nhất)
                if q := st.chat_input(T("t3_input"), key="chat_input_solo"):
                    st.chat_message("user").markdown(q)
                    st.session_state.chat_history.append({"role":"user", "content":q})
                    
                    # Logic gọi AI
                    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-5:]])
                    prompt = f"""
                    VAI TRÒ CỦA BẠN: {personas[p_sel]}
                    LỊCH SỬ CHAT: {history_text}
                    NGƯỜI DÙNG NÓI: "{q}"
                    YÊU CẦU: Phân tích sâu, phản biện sắc sảo, và trả lời bằng ngôn ngữ của người dùng.
                    """
                    
                    res = run_gemini_safe(model.generate_content, prompt)
                    if res:
                        st.chat_message("assistant").markdown(res.text)
                        st.session_state.chat_history.append({"role":"assistant", "content":res.text})
                        luu_lich_su_vinh_vien("Tranh Biện Solo", f"Vs {p_sel}: {q}", res.text)

        # --- CHẾ ĐỘ 2: DEBATE (AI vs AI) ---
        else:
            with st.container():
                st.info("💡 Hướng dẫn: Chọn 2-3 triết gia, đặt chủ đề và xem họ 'đấu võ mồm'.")
                
                participants = st.multiselect("Chọn các Đấu Thủ (Tối đa 3):", list(personas.keys()), default=["⚖️ Immanuel Kant", "🔥 Nietzsche"], key="multi_select_battle")
                topic = st.text_input("Chủ đề Tranh Luận:", placeholder="Ví dụ: Tiền có mua được hạnh phúc không?", key="topic_input_battle")
                
                if "battle_logs" not in st.session_state: st.session_state.battle_logs = []

                col_start, col_clear = st.columns([1, 5])
                with col_start:
                    start_battle = st.button("🔥 KHAI CHIẾN", type="primary", key="btn_start_battle", disabled=(len(participants) < 2))
                with col_clear:
                    if st.button("🗑️ Xóa Bàn", key="btn_clr_battle"):
                        st.session_state.battle_logs = []; st.rerun()

                # Logic chạy vòng lặp tranh luận (3 Vòng)
                if start_battle and topic and len(participants) > 1:
                    st.session_state.battle_logs = []
                    st.session_state.battle_logs.append(f"**📢 CHỦ TỌA:** Khai mạc tranh luận về: *'{topic}'*")
                    
                    with st.status("Hội đồng đang tranh luận nảy lửa (3 vòng)...") as status:
                        for round_num in range(1, 4):
                            status.update(label=f"🔄 Vòng {round_num}/3 đang diễn ra...")
                            
                            for i, p_name in enumerate(participants):
                                if round_num == 1:
                                    p_prompt = f"Bạn là {p_name}. Chủ đề: {topic}. Đưa ra quan điểm đầu tiên."
                                else:
                                    target_index = (i - 1 + len(participants)) % len(participants)
                                    target_name = participants[target_index]
                                    last_speech = ""
                                    for log in reversed(st.session_state.battle_logs):
                                        if log.startswith(f"**{target_name}:**"):
                                            last_speech = log.replace(f"**{target_name}:** ", "")
                                            break
                                    p_prompt = f"VAI TRÒ: {p_name}. PHẢN BÁC: \"{target_name}\" vừa nói: \"{last_speech}\". Yêu cầu: Phản bác lại lập luận đó theo triết lý của bạn."
                                
                                # SỬ DỤNG HÀM AN TOÀN + SLEEP NHIỀU HƠN
                                res = run_gemini_safe(model.generate_content, p_prompt)
                                if res:
                                    reply = res.text
                                    st.session_state.battle_logs.append(f"**{p_name}:** {reply}")
                                    time.sleep(4) # Tăng lên 4 giây để tránh lỗi ResourceExhausted

                        status.update(label="✅ Tranh luận kết thúc! (Đã chạy 3 vòng)", state="complete")
                        
                        full_log = "\n\n".join(st.session_state.battle_logs)
                        luu_lich_su_vinh_vien("Hội Đồng Tranh Biện", topic, full_log)
                        st.toast("💾 Đã lưu biên bản cuộc họp vào Nhật Ký!", icon="✅")
                        
                # Hiển thị kết quả trận đấu
                for log in st.session_state.battle_logs:
                    st.markdown(log)
                    st.markdown("---")

    # === TAB 4: PHÒNG THU AI (FULL 6 GIỌNG) ===
    with tab4:
        st.subheader("🎙️ Phòng Thu AI Đa Ngôn Ngữ")
        c_in, c_ctrl = st.columns([3, 1])
        with c_in: inp_v = st.text_area("Văn bản cần đọc:", height=200, key="v_input")
        with c_ctrl:
            v_choice = st.selectbox("Chọn Giọng:", list(voice.VOICE_OPTIONS.keys()))
            speed_v = st.slider("Tốc độ:", -50, 50, 0)
        
        if st.button("🔊 TẠO AUDIO") and inp_v:
            with st.spinner("Đang tải giọng đọc..."):
                path = voice.speak(inp_v, voice_key=v_choice, speed=speed_v)
                if path:
                    st.audio(path)
                    with open(path, "rb") as f:
                        st.download_button("⬇️ Tải xuống MP3", f, "audio.mp3")

    # === TAB 5: NHẬT KÝ (Lấy từ GSheet) ===
    with tab5:
        st.subheader("⏳ Lịch Sử Hoạt Động")
        if st.button("🔄 Tải lại Nhật ký"):
            st.session_state.history_cloud = tai_lich_su_tu_sheet()
            st.rerun()
        
        data = st.session_state.get("history_cloud", [])
        if data:
            df_h = pd.DataFrame(data)
            # Vẽ biểu đồ cảm xúc nếu có data
            if "SentimentScore" in df_h.columns:
                fig = px.line(df_h, x="Time", y="SentimentScore", title="📈 Biểu đồ trạng thái tư duy")
                st.plotly_chart(fig, use_container_width=True)
            
            for item in reversed(data):
                with st.expander(f"⏰ {item.get('Time')} | {item.get('Type')} | {item.get('Title')}"):
                    st.markdown(item.get("Content"))
        else:
            st.info("Chưa có dữ liệu lịch sử.")

if __name__ == "__main__":
    run()
