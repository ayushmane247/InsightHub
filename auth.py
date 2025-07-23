import streamlit as st
import hashlib
import json
import os

USERS_FILE = "users.json"

# -------------------------------
# 🔐 Password Hashing
# -------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------------------
# 📁 Load & Save Users
# -------------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    # Ensure default admin user exists
    if "admin" not in users:
        users["admin"] = hash_password("1234")
        save_users(users)
    return users

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# -------------------------------
# 🧾 Register User
# -------------------------------
def register_user(username: str, password: str) -> bool:
    users = load_users()
    if username in users:
        return False  # already exists
    users[username] = hash_password(password)
    save_users(users)
    return True

# -------------------------------
# ✅ Verify Login
# -------------------------------
def verify_login(username: str, password: str) -> bool:
    users = load_users()
    return users.get(username) == hash_password(password)

# -------------------------------
# 🔐 Logout & Session Check
# -------------------------------
def logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

def is_authenticated() -> bool:
    return st.session_state.get("logged_in", False)

def initialize_session():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""

# -------------------------------
# 🔐 Login UI
# -------------------------------
import streamlit as st

def login_ui():
    initialize_session()

    if is_authenticated():
        st.success(f"✅ Logged in as {st.session_state['username']}")
        return True

    # Centered layout
    with st.container():
        st.markdown(
            """
            <div style='text-align: center;'>
                <h2>🔐 Welcome to <span style='color:#4CAF50;'>InsightHub</span></h2>
                <p style='font-size:16px; color:gray;'>Login to access your dashboard</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Stylish login form
        st.markdown("### 👤 Login")

        col1, col2 = st.columns([1, 1])
        with col1:
            username = st.text_input("Username", key="login_username", placeholder="Enter username")
        with col2:
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter password")

        login_btn = st.button("🚀 Login", use_container_width=True)

        if login_btn:
            if verify_login(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

        st.markdown("---")

        # New user checkbox
        if st.checkbox("🆕 New user? Create an account"):
            register_ui()

    return False


# -------------------------------
# 📝 Register UI
# -------------------------------
def register_ui():
    if "register_success" not in st.session_state:
        st.session_state["register_success"] = False

    if st.session_state["register_success"]:
        st.success("✅ Registration successful! Please login.")
        # Clear registration fields
        st.session_state["reg_username"] = ""
        st.session_state["reg_password"] = ""
        st.session_state["reg_confirm"] = ""
        st.session_state["register_success"] = False  # Reset for next time
        return

    st.markdown(
        """
        <div style='text-align: center;'>
            <h3>📝 Create a New Account</h3>
            <p style='font-size:14px; color:gray;'>Fill the form below to register</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        new_username = st.text_input("Choose a username", key="reg_username", placeholder="e.g. john_doe")
    with col2:
        new_password = st.text_input("Choose a password", type="password", key="reg_password", placeholder="Minimum 6 characters")

    confirm_password = st.text_input("Confirm password", type="password", key="reg_confirm", placeholder="Re-enter password")

    if st.button("📝 Register", use_container_width=True):
        if new_password != confirm_password:
            st.error("❌ Passwords do not match.")
        elif len(new_password) < 6:
            st.warning("⚠️ Password should be at least 6 characters.")
            return
        elif register_user(new_username, new_password):
            st.session_state["register_success"] = True
            st.rerun()
        else:
            st.error("❌ Username already exists.")