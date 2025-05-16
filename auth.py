import streamlit as st

# --- File Purpose ---
# Simple user authentication module for Streamlit app.
# Supports login/logout with hardcoded credentials for demo purposes.

# For real applications, replace with secure user management.

def login():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.subheader("User Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            # Example hardcoded credentials
            if username == "admin" and password == "password123":
                st.session_state.logged_in = True
                st.success("Logged in successfully!")
            else:
                st.error("Invalid username or password")
        return False
    else:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.experimental_rerun()
        return True
