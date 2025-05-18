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
def login_ui():
    initialize_session()

    if is_authenticated():
        st.success(f"✅ Logged in as {st.session_state['username']}")
        return True

    st.markdown("## 🔐 Login to InsightHub")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    login_btn = st.button("Login")

    if login_btn:
        if verify_login(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password.")

    st.markdown("---")
    if st.checkbox("New user? Register here"):
        register_ui()

    return False

# -------------------------------
# 📝 Register UI
# -------------------------------
def register_ui():
    st.markdown("## 📝 Register New Account")
    new_username = st.text_input("Choose a username", key="reg_username")
    new_password = st.text_input("Choose a password", type="password", key="reg_password")
    confirm_password = st.text_input("Confirm password", type="password", key="reg_confirm")

    if st.button("Register"):
        if new_password != confirm_password:
            st.error("❌ Passwords do not match.")
        elif len(new_password) < 6:
            st.warning("⚠️ Password should be at least 6 characters.")
        elif register_user(new_username, new_password):
            st.success("✅ Registration successful! Please login.")
            st.rerun()
        else:
            st.error("❌ Username already exists.")
