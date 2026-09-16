import json
import os
import streamlit as st

class UserManager:
    def __init__(self, filepath: str = "users.json"):
        self.filepath = filepath

    def _load(self) -> dict:
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, users: dict):
        with open(self.filepath, "w") as f:
            json.dump(users, f, indent=4)

    def register(self, username: str, password: str) -> tuple[bool, str]:
        users = self._load()
        if username in users:
            return False, "Username already exists in surveyor registry!"
        users[username] = password
        self._save(users)
        return True, "Surveyor account registered successfully! Please login."

    def login(self, username: str, password: str) -> tuple[bool, str]:
        users = self._load()
        if username not in users:
            return False, "Username not found. Please check spelling or register."
        if users[username] != password:
            return False, "Incorrect password provided!"
        return True, "Authenticated successfully!"

class SessionManager:
    DEFAULTS = {
        "page": "login",
        "logged_in": False,
        "username": "",
        "google_api_key": "",
    }

    @classmethod
    def initialise(cls):
        for key, value in cls.DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def set(key: str, value):
        st.session_state[key] = value

    @staticmethod
    def get(key: str):
        return st.session_state.get(key)

    @staticmethod
    def navigate(page: str):
        st.session_state.page = page
        st.rerun()

    @staticmethod
    def logout():
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.google_api_key = ""
        st.session_state.page = "login"
        st.rerun()

class AuthPage:
    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager

    def render(self):
        page = SessionManager.get("page")
        if page == "login":
            self._render_login()
        elif page == "register":
            self._render_register()

    def _render_login(self):
        col1, col2, col3 = st.columns([1, 2.2, 1])
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h3 style='color:#7A0016; font-weight: 800; margin-bottom: 4px; letter-spacing: -0.5px;'>🔐 Surveyor Portal Login</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color:#64748B; font-size:13.5px; margin-bottom: 22px;'>Department of Estate Management & Valuation — University of Sri Jayewardenepura</p>", unsafe_allow_html=True)
            
            username = st.text_input("Username", placeholder="Enter your surveyor username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            if st.button("Authenticate & Access Workspace", use_container_width=True):
                if not username or not password:
                    st.error("Please enter both username and password!")
                else:
                    success, msg = self.user_manager.login(username, password)
                    if success:
                        SessionManager.set("logged_in", True)
                        SessionManager.set("username", username)
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown('<div style="text-align: center; margin-top: 15px;">', unsafe_allow_html=True)
            st.markdown("<span style='color:#64748B; font-size:13.5px;'>Need to register a new surveyor profile?</span>", unsafe_allow_html=True)
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            if st.button("🆕 Register New Surveyor Profile", use_container_width=True):
                SessionManager.navigate("register")
            st.markdown("</div>", unsafe_allow_html=True)

    def _render_register(self):
        col1, col2, col3 = st.columns([1, 2.2, 1])
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h3 style='color:#7A0016; font-weight: 800; margin-bottom: 4px; letter-spacing: -0.5px;'>🆕 Surveyor Registration</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color:#64748B; font-size:13.5px; margin-bottom: 22px;'>Create your authorized credentials profile to begin.</p>", unsafe_allow_html=True)
            
            username = st.text_input("Choose Username", placeholder="Choose a unique username", key="reg_username")
            password = st.text_input("Choose Password", type="password", placeholder="Choose a secure password", key="reg_password")
            confirm  = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="reg_confirm_password")
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            if st.button("Register Account Profile", use_container_width=True):
                if password != confirm:
                    st.error("Passwords do not match!")
                elif not username or not password:
                    st.error("Both username and password are required!")
                else:
                    success, msg = self.user_manager.register(username, password)
                    if success:
                        st.success(msg)
                        SessionManager.navigate("login")
                    else:
                        st.error(msg)
                        
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown('<div style="text-align: center; margin-top: 15px;">', unsafe_allow_html=True)
            if st.button("🔙 Back to Surveyor Login", use_container_width=True):
                SessionManager.navigate("login")
            st.markdown("</div>", unsafe_allow_html=True)