import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup
from streamlit_agraph import agraph, Node, Edge, Config
import plotly.express as px
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import re

# --- IMPORT CÁC META-BLOCKS ---
from ai_core import AI_Core
from voice_block import Voice_Engine
from prompts import DEBATE_PERSONAS, BOOK_ANALYSIS_PROMPT
# from auth_block import AuthBlock # (Không cần import vì app.py đã handle login)

# --- CÁC HÀM PHỤ TRỢ (GIỮ NGUYÊN) ---
@st.cache_resource
def load_models():
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

# --- DATABASE GOOGLE SHEET ---
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

def luu_lich_su(loai, tieu_de, noi_dung):
    thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = st.session_state.get("current_user", "Unknown")
    try:
        sheet = connect_gsheet()
        # Lưu thêm cột Sentiment giả định để không lỗi
        if sheet: sheet.append_row([thoi_gian, loai, tieu_de, noi_dung, user, 0.0, "Neutral"])
    except: pass

def tai_lich_su():
    try:
        sheet = connect_gsheet()
        if sheet: return sheet.get_all_records()
    except: return []
    return []

# --- HÀM CHÍNH: RUN() ---
def run():
    # Khởi tạo các Block
    ai = AI_Core()
    voice = Voice_Engine()
    
    st.header("🧠 The Cognitive Weaver (Người Dệt Nhận Thức)")
    
    # 5 TABS ĐẦY ĐỦ
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📚 Sách & Graph", "✍️ Dịch Giả", "🗣️ Tranh Biện", "🎙️ Phòng Thu", "⏳ Nhật Ký"])

    # === TAB 1: RAG & GRAPH ===
    with tab1:
        st.subheader("Trợ lý Nghiên cứu & Knowledge Graph")
        
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1: file_excel = st.file_uploader("1. Kết nối Kho Sách (Excel)", type="xlsx", key="w_t1_ex")
        with c2: uploaded_files = st.file_uploader("2. Tài liệu mới (PDF/Docx)", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="w_t1_doc")
        with c3: 
            st.write("")
            st.write("")
            btn_run = st.button("🚀 PHÂN TÍCH NGAY", type="primary", use_container_width=True)

        if btn_run and uploaded_files:
            vec = load_models()
            db, df = None, None
            has_db = False
            
            if file_excel:
                try:
                    df = pd.read_excel(file_excel).dropna(subset=["Tên sách"])
                    db = vec.encode([f"{r['Tên sách']} {str(r.get('CẢM NHẬN',''))}" for _, r in df.iterrows()])
                    has_db = True
                    st.success(f"✅ Đã kết nối {len(df)} cuốn sách.")
                except: st.error("Lỗi đọc Excel.")

            for f in uploaded_files:
                text = doc_file(f)
                link = ""
                if has_db:
                    q = vec.encode([text[:2000]])
                    sc = cosine_similarity(q, db)[0]
                    idx = np.argsort(sc)[::-1][:3]
                    for i in idx:
                        if sc[i] > 0.35: link += f"- {df.iloc[i]['Tên sách']} ({sc[i]*100:.0f}%)\n"

                with st.spinner(f"Đang phân tích {f.name}..."):
                    prompt = f"Phân tích tài liệu '{f.name}'. Liên quan: {link}\nNội dung: {text[:30000]}"
                    # Dùng AI Core (Cache)
                    res = ai.analyze_static(text, BOOK_ANALYSIS_PROMPT)
                    
                    st.markdown(f"### 📄 {f.name}")
                    st.markdown(res)
                    st.markdown("---")
                    luu_lich_su("Phân Tích Sách", f.name, res[:200])

        # VẼ GRAPH (AGRAPH)
        if file_excel:
            try:
                with st.expander("🪐 Vũ Trụ Sách (Book Universe)", expanded=False):
                    vec = load_models()
                    if "book_embs" not in st.session_state:
                         st.session_state.book_embs = vec.encode(df["Tên sách"].tolist())
                    
                    embs = st.session_state.book_embs
                    sim = cosine_similarity(embs)
                    nodes, edges = [], []
                    
                    max_nodes = st.slider("Số lượng sách hiển thị:", 5, len(df), min(50, len(df)))
                    threshold = st.slider("Độ tương đồng nối dây:", 0.0, 1.0, 0.45)

                    for i in range(max_nodes):
                        nodes.append(Node(id=str(i), label=df.iloc[i]["Tên sách"], size=20, color="#FFD166"))
                        for j in range(i+1, max_nodes):
                            if sim[i,j]>threshold: edges.append(Edge(source=str(i), target=str(j), color="#118AB2"))
                    
                    config = Config(width=900, height=600, directed=False, physics=True, collapsible=False)
                    agraph(nodes, edges, config)
            except: pass

    # === TAB 2: DỊCH GIẢ (GIỮ NGUYÊN TỪ CŨ) ===
    with tab2:
        st.subheader("Dịch Thuật Đa Chiều")
        txt = st.text_area("Nhập văn bản cần dịch:", height=150, key="w_t2_inp")
        c_l, c_s, c_b = st.columns([1,1,1])
        with c_l: target_lang = st.selectbox("Dịch sang:", ["Tiếng Việt", "English", "Chinese", "French", "Japanese"], key="w_t2_lang")
        with c_s: style = st.selectbox("Phong cách:", ["Mặc định", "Hàn lâm", "Văn học", "Kinh tế", "Kiếm hiệp"], key="w_t2_style")
        
        if st.button("✍️ Dịch Ngay", key="w_t2_btn") and txt:
            with st.spinner("AI đang chuyển ngữ..."):
                p = f"Dịch văn bản sau sang {target_lang} với phong cách {style}. Nếu sang Trung phải có Pinyin. Văn bản: {txt}"
                res = ai.generate(p, model_type="pro")
                st.markdown(res)
                luu_lich_su("Dịch Thuật", f"{target_lang} - {style}", txt[:50])

    # === TAB 3: TRANH BIỆN (DÙNG PROMPTS.PY) ===
    with tab3:
        st.subheader("Đấu Trường Tư Duy")
        mode = st.radio("Chế độ:", ["👤 Solo (Chị vs AI)", "⚔️ Đại Chiến (AI vs AI)"], horizontal=True, key="w_t3_mode")
        
        if "weaver_chat" not in st.session_state: st.session_state.weaver_chat = []

        # --- CHẾ ĐỘ 1: SOLO ---
        if mode == "👤 Solo (Chị vs AI)":
            c1, c2 = st.columns([3, 1])
            with c1: persona = st.selectbox("Chọn Đối Thủ:", list(DEBATE_PERSONAS.keys()), key="w_t3_solo_p")
            with c2: 
                if st.button("🗑️ Xóa Chat", key="w_t3_clr"): 
                    st.session_state.weaver_chat = []
                    st.rerun()

            for msg in st.session_state.weaver_chat:
                st.chat_message(msg["role"]).write(msg["content"])

            if prompt := st.chat_input("Nhập chủ đề..."):
                st.chat_message("user").write(prompt)
                st.session_state.weaver_chat.append({"role": "user", "content": prompt})
                
                with st.chat_message("assistant"):
                    sys = DEBATE_PERSONAS[persona]
                    with st.spinner(f"{persona} đang nghĩ..."):
                        res = ai.generate(prompt, model_type="flash", system_instruction=sys)
                        st.write(res)
                        st.session_state.weaver_chat.append({"role": "assistant", "content": res})
                        luu_lich_su("Tranh Biện Solo", persona, prompt)

        # --- CHẾ ĐỘ 2: ĐẠI CHIẾN (AI vs AI) ---
        else:
            st.info("💡 Chọn tối đa 3 nhân vật để họ tự cãi nhau.")
            participants = st.multiselect(
                "Chọn Hội Đồng Tranh Biện:", 
                list(DEBATE_PERSONAS.keys()), 
                default=[list(DEBATE_PERSONAS.keys())[0], list(DEBATE_PERSONAS.keys())[1]],
                key="w_t3_multi_p"
            )
            topic = st.text_input("Chủ đề tranh luận:", key="w_t3_topic")
            
            if st.button("🔥 KHAI CHIẾN", key="w_t3_start") and topic:
                st.session_state.weaver_chat = []
                st.session_state.weaver_chat.append({"role": "system", "content": f"📢 **CHỦ TỌA:** Bắt đầu tranh luận về: *{topic}*"})
                st.chat_message("system").write(f"📢 **CHỦ TỌA:** Bắt đầu tranh luận về: *{topic}*")
                
                with st.status("Cuộc chiến đang diễn ra (3 vòng)...") as status:
                    for round_num in range(1, 4):
                        status.update(label=f"🔄 Vòng {round_num}/3...")
                        for p_name in participants:
                            if len(st.session_state.weaver_chat) > 1:
                                last_msg = st.session_state.weaver_chat[-1]['content']
                                p_prompt = f"VAI TRÒ: {p_name}. ĐỐI THỦ NÓI: '{last_msg}'. PHẢN BIỆN LẠI NGAY. Chủ đề gốc: {topic}."
                            else:
                                p_prompt = f"VAI TRÒ: {p_name}. Chủ đề: {topic}. Quan điểm mở màn."
                            
                            res = ai.generate(p_prompt, model_type="flash", system_instruction=DEBATE_PERSONAS[p_name])
                            st.session_state.weaver_chat.append({"role": "assistant", "content": f"**{p_name}:** {res}"})
                            with st.chat_message("assistant"): st.write(f"**{p_name}:** {res}")
                            time.sleep(5) 
                luu_lich_su("Tranh Biện Hội Đồng", topic, str(st.session_state.weaver_chat))
                st.success("Kết thúc!")

            # Hiện lịch sử cũ của Đại chiến
            for msg in st.session_state.weaver_chat:
                if msg["role"] != "user": # User không tham gia
                    st.chat_message(msg["role"]).write(msg["content"])

    # === TAB 4: PHÒNG THU AI (FULL 6 GIỌNG) ===
    with tab4:
        st.subheader("🎙️ Phòng Thu AI Đa Ngôn Ngữ")
        c_in, c_ctrl = st.columns([3, 1])
        with c_in: inp_v = st.text_area("Văn bản cần đọc:", height=200, key="w_t4_input")
        with c_ctrl:
            v_choice = st.selectbox("Chọn Giọng:", list(voice.VOICE_OPTIONS.keys()), key="w_t4_sel")
            speed_v = st.slider("Tốc độ:", -50, 50, 0, key="w_t4_spd")
        
        if st.button("🔊 TẠO AUDIO", key="w_t4_btn") and inp_v:
            with st.spinner("Đang tải giọng đọc..."):
                path = voice.speak(inp_v, voice_key=v_choice, speed=speed_v)
                if path:
                    st.audio(path)
                    with open(path, "rb") as f:
                        st.download_button("⬇️ Tải xuống MP3", f, "audio.mp3")
                    luu_lich_su("Tạo Audio", v_choice, inp_v[:50])

    # === TAB 5: NHẬT KÝ ===
    with tab5:
        st.subheader("⏳ Lịch Sử Hoạt Động")
        if st.button("🔄 Tải lại Nhật ký", key="w_t5_btn"):
            data = tai_lich_su()
            if data:
                df_h = pd.DataFrame(data)
                st.dataframe(df_h)
            else:
                st.info("Chưa có dữ liệu.")
