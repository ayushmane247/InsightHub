import streamlit as st
import base64
import os

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Make sure the image file is in the same directory as app.py
IMAGE_PATH = os.path.join(os.path.dirname(__file__), "bg.jpg")

# Get base64 of the image
img_base64 = get_base64_of_bin_file(IMAGE_PATH)

# Page config
st.set_page_config(page_title="InsightHub Home", layout="wide", initial_sidebar_state="collapsed")

# CSS with embedded base64 background image
page_bg_img = f"""
<style>
.stApp {{
    background-image: url("data:image/jpg;base64,{img_base64}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}
.big-title {{
    font-size: 3rem;
    color: white;
    text-shadow: 2px 2px 5px #000;
    margin-bottom: 20px;
    text-align: center;
}}
.login-box {{
    background-color: rgba(255, 255, 255, 0.85);
    padding: 2rem;
    border-radius: 1rem;
    max-width: 400px;
    margin: 0 auto;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}}
</style>
"""

st.markdown(page_bg_img, unsafe_allow_html=True)

# Title
st.markdown("<div class='big-title'>👋 Welcome to InsightHub</div>", unsafe_allow_html=True)

# Login Box UI
with st.container():
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)

    st.subheader("🔐 Login to Start")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("🚀 Continue to InsightHub"):
        if username and password:
            st.success("Login successful! Please go to 📊 Dashboard tab in the sidebar.")
            st.markdown("✅ You can now access the full app from the sidebar.")
        else:
            st.error("Please enter both username and password.")

    st.markdown("</div>", unsafe_allow_html=True)
