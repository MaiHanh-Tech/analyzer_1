import streamlit as st
import hashlib
from datetime import datetime

class AuthBlock:
    def __init__(self):
        self.admin_pass = st.secrets.get("admin_password", "")
        self.users_db = st.secrets.get("users", {})
        self.tiers = st.secrets.get("user_tiers", {})
        limits = st.secrets.get("usage_limits", {})
        self.default_limit = limits.get("default_daily_limit", 30000)
        self.premium_limit = limits.get("premium_daily_limit", 500000)

        if 'user_logged_in' not in st.session_state: st.session_state.user_logged_in = False
        if 'usage_tracking' not in st.session_state: st.session_state.usage_tracking = {}

    def login(self, password):
        if not password: return False
        if password == self.admin_pass:
            self._set_session("Admin", True, True)
            return True
        for u, p in self.users_db.items():
            if password == p:
                is_vip = (self.tiers.get(u, "default") == "premium")
                self._set_session(u, False, is_vip)
                return True
        return False

    def _set_session(self, u, admin, vip):
        st.session_state.user_logged_in = True
        st.session_state.current_user = u
        st.session_state.is_admin = admin
        st.session_state.is_vip = vip

    def check_quota(self):
        if st.session_state.get('is_vip', False): return True
        u = st.session_state.get('current_user')
        if not u: return False
        today = datetime.now().strftime("%Y-%m-%d")
        current = st.session_state.usage_tracking.get(u, {}).get(today, 0)
        return current < self.default_limit

    def track(self, count):
        if st.session_state.get('is_vip', False): return
        u = st.session_state.get('current_user')
        if u:
            today = datetime.now().strftime("%Y-%m-%d")
            if u not in st.session_state.usage_tracking: st.session_state.usage_tracking[u] = {}
            cur = st.session_state.usage_tracking[u].get(today, 0)
            st.session_state.usage_tracking[u][today] = cur + count
