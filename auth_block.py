import streamlit as st
import hashlib
from datetime import datetime, timedelta

class AuthBlock:
    def __init__(self):
        # ✅ LƯU HASH THAY VÌ PLAINTEXT
        self.admin_hash = st.secrets.get("admin_password_hash", "")  # ← SHA256 hash
        
        # ✅ User DB cũng dùng hash
        users_raw = st.secrets.get("users", {})
        self.users_db = {u: hashlib.sha256(p.encode()).hexdigest() 
                        for u, p in users_raw.items()}
        
        self.tiers = st.secrets.get("user_tiers", {})
        limits = st.secrets.get("usage_limits", {})
        self.default_limit = limits.get("default_daily_limit", 30000)
        self.premium_limit = limits.get("premium_daily_limit", 500000)

        # ✅ KHỞI TẠO SESSION
        if 'user_logged_in' not in st.session_state: 
            st.session_state.user_logged_in = False
        if 'usage_tracking' not in st.session_state: 
            st.session_state.usage_tracking = {}
        
        # ✅ THÊM: RATE LIMITING
        if 'login_attempts' not in st.session_state:
            st.session_state.login_attempts = {}

    def _hash_password(self, password):
        """Hash password bằng SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _check_rate_limit(self, identifier="global"):
        """Kiểm tra số lần đăng nhập thất bại"""
        now = datetime.now()
        attempts = st.session_state.login_attempts.get(identifier, [])
        
        # Xóa các lần thử cũ hơn 15 phút
        attempts = [t for t in attempts if now - t < timedelta(minutes=15)]
        st.session_state.login_attempts[identifier] = attempts
        
        # Giới hạn 5 lần thử trong 15 phút
        if len(attempts) >= 5:
            wait_seconds = int((attempts[-1] + timedelta(minutes=15) - now).total_seconds())
            return False, wait_seconds
        
        return True, 0

    def login(self, password):
        if not password: 
            return False
        
        # ✅ KIỂM TRA RATE LIMIT
        allowed, wait_time = self._check_rate_limit()
        if not allowed:
            st.error(f"🚫 Quá nhiều lần đăng nhập sai. Vui lòng chờ {wait_time}s.")
            return False
        
        password_hash = self._hash_password(password)
        
        # Kiểm tra admin
        if password_hash == self.admin_hash:
            self._set_session("Admin", True, True)
            # ✅ Reset rate limit khi login thành công
            st.session_state.login_attempts["global"] = []
            return True
        
        # Kiểm tra user thường
        for u, p_hash in self.users_db.items():
            if password_hash == p_hash:
                is_vip = (self.tiers.get(u, "default") == "premium")
                self._set_session(u, False, is_vip)
                st.session_state.login_attempts["global"] = []
                return True
        
        # ✅ GHI NHẬN LẦN THỬ SAI
        if "global" not in st.session_state.login_attempts:
            st.session_state.login_attempts["global"] = []
        st.session_state.login_attempts["global"].append(datetime.now())
        
        return False

    def _set_session(self, u, admin, vip):
        st.session_state.user_logged_in = True
        st.session_state.current_user = u
        st.session_state.is_admin = admin
        st.session_state.is_vip = vip

    # ✅ THÊM 2 HÀM NÀY (CHỊ ĐANG THIẾU)
    def check_quota(self):
        """Kiểm tra user còn quota không"""
        # VIP user không bị giới hạn
        if st.session_state.get('is_vip', False): 
            return True
        
        u = st.session_state.get('current_user')
        if not u: 
            return False
        
        today = datetime.now().strftime("%Y-%m-%d")
        current = st.session_state.usage_tracking.get(u, {}).get(today, 0)
        
        return current < self.default_limit

    def track(self, count):
        """Ghi nhận usage của user"""
        # VIP user không cần track
        if st.session_state.get('is_vip', False): 
            return
        
        u = st.session_state.get('current_user')
        if u:
            today = datetime.now().strftime("%Y-%m-%d")
            
            if u not in st.session_state.usage_tracking: 
                st.session_state.usage_tracking[u] = {}
            
            cur = st.session_state.usage_tracking[u].get(today, 0)
            st.session_state.usage_tracking[u][today] = cur + count
