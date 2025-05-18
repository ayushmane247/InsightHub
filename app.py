import streamlit as st
import pandas as pd
from data_handler import read_selected_sheet, get_sheet_names, preprocess_store_sales

st.set_page_config(page_title="InsightHub Dashboard", layout="wide")

# Sidebar navigation
st.sidebar.title("InsightHub Menu")
menu = st.sidebar.radio("Go to", ["Home", "Upload Data", "Trends & Summary", "ML Predictor", "Plots & Graphs"])

# CSS Styling for hover effects & buttons
st.markdown("""
<style>
    .stButton>button {
        background: linear-gradient(90deg, #00ffff 0%, #00b3b3 100%);
        color: black;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.75em 1.5em;
        transition: transform 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #00b3b3 0%, #00ffff 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def load_and_preprocess():
    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
    if uploaded_file:
        sheet_names = get_sheet_names(uploaded_file)
        sheet = None
        if sheet_names:
            sheet = st.selectbox("Select sheet", sheet_names)
        try:
            df = read_selected_sheet(uploaded_file, sheet)
            df = preprocess_store_sales(df)
            st.success("File loaded and preprocessed successfully!")
            st.dataframe(df.head(10))
            return df
        except Exception as e:
            st.error(f"Error: {e}")
    return None

# Home page
if menu == "Home":
    st.title("👋 Welcome to InsightHub")
    st.write("""
        This is your all-in-one multi-domain data analysis platform.
        
        Use the sidebar to navigate through data upload, explore trends, build ML models, and visualize insights.
    """)

# Upload Data page
elif menu == "Upload Data":
    st.header("Upload your data")
    df = load_and_preprocess()
    if df is not None:
        st.write("Data preview:")
        st.dataframe(df.head())

# Trends & Summary
elif menu == "Trends & Summary":
    st.header("Trends & Summary")
    st.info("Upload data first on the Upload Data page.")
    # Placeholder for actual summary logic and charts

# ML Predictor
elif menu == "ML Predictor":
    st.header("Machine Learning Predictor")
    st.info("ML functionality coming soon!")

# Plots & Graphs
elif menu == "Plots & Graphs":
    st.header("Visualizations")
    st.info("Visualizations will appear here after data upload.")

