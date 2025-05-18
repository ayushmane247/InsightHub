import streamlit as st
import pandas as pd
from data_handler import read_selected_sheet, get_sheet_names, preprocess_store_sales
from login_handler import login, is_authenticated
from plot_generator import (
    show_order_trend,
    show_status_breakdown,
)

# App config
st.set_page_config(page_title="InsightHub Dashboard", layout="wide")

# Load external CSS
with open("streamlit_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def handle_file_upload_and_preprocess():
    file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
    if file:
        try:
            sheet_names = get_sheet_names(file)
            selected_sheet = st.selectbox("Select sheet", sheet_names) if sheet_names else None
            df = read_selected_sheet(file, selected_sheet)
            processed_df = preprocess_store_sales(df)
            st.success("File loaded and preprocessed successfully!")
            st.dataframe(processed_df.head(10))
            return processed_df
        except Exception as e:
            st.error(f"Error loading data: {e}")
    else:
        st.info("Please upload a CSV or Excel file.")
    return None

def render_dashboard():
    if "is_logged_in" not in st.session_state:
        st.session_state["is_logged_in"] = False

    if not st.session_state["is_logged_in"]:
        login()
        if is_authenticated():
            st.session_state["is_logged_in"] = True
            st.experimental_rerun()
        return

    st.sidebar.title("InsightHub Menu")
    page = st.sidebar.radio("Go to", ["Home", "Upload Data", "Trends & Summary", "ML Predictor", "Plots & Graphs"])

    with st.container():
        if page == "Home":
            st.header("👋 Welcome to InsightHub")
            st.write("""
                This is your all-in-one multi-domain data analysis platform.
                Use the sidebar to navigate through data upload, explore trends, build ML models, and visualize insights.
            """)

        elif page == "Upload Data":
            st.header("Upload your data")
            data = handle_file_upload_and_preprocess()
            if data is not None:
                st.write("Data preview:")
                st.dataframe(data.head())

        elif page == "Trends & Summary":
            st.header("Trends & Summary")
            data = handle_file_upload_and_preprocess()
            if data is not None:
                st.subheader("Order Trends Over Time")
                show_order_trend(data)
                st.subheader("Order Status Breakdown")
                show_status_breakdown(data)
            else:
                st.info("Upload data first on the Upload Data page.")

        elif page == "ML Predictor":
            st.header("Machine Learning Predictor")
            st.info("ML Predictor module coming soon. Upload data to enable.")

        elif page == "Plots & Graphs":
            st.header("Visualizations")
            data = handle_file_upload_and_preprocess()
            if data is not None:
                st.subheader("Your Visualizations")
                show_order_trend(data)
                show_status_breakdown(data)
            else:
                st.info("Upload data first on the Upload Data page.")

if __name__ == "__main__":
    render_dashboard()
# This code is a Streamlit application that serves as a dashboard for data analysis and visualization.
# It includes features for user authentication, data upload, preprocessing, and various visualizations.