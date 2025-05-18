import streamlit as st
from login_handler import login_ui, logout
from file_upload_ui import file_upload_flow
from plot_generator import show_visualizations
from ml_predictor import ml_predict

def render_dashboard():
    st.sidebar.title("📂 InsightHub Menu")
    page = st.sidebar.radio(
        "Go to",
        ["🏠 Home", "📁 Upload Data", "📈 Trends", "🤖 ML Predictor", "📊 Visualizations", "🚪 Logout"],
        index=0,
        key="menu_radio"
    )

    if page == "🚪 Logout":
        logout()
        st.experimental_rerun()

    if page == "🏠 Home":
        st.header("👋 Welcome to InsightHub")
        st.markdown(
            """
            Your all-in-one multi-domain data analysis platform.  
            Navigate using the sidebar to:
            - Upload datasets
            - Explore trends
            - Predict outcomes using ML
            - Visualize insights
            """
        )

    elif page == "📁 Upload Data":
        st.header("Upload your Data")
        data = file_upload_flow(key="upload")
        if data is not None:
            st.subheader("🔍 Data Preview")
            st.dataframe(data.head())

    elif page == "📈 Trends":
        st.header("Trends & Insights")
        data = file_upload_flow(key="trends")
        if data is not None:
            show_visualizations(data)

    elif page == "🤖 ML Predictor":
        st.header("Machine Learning Predictor")
        data = file_upload_flow(key="ml")
        if data is not None:
            ml_predict(data)
        else:
            st.info("Upload data to use ML predictor.")

    elif page == "📊 Visualizations":
        st.header("Custom Visualizations")
        data = file_upload_flow(key="viz")
        if data is not None:
            show_visualizations(data)

def main():
    # Call your login UI first - implement user sessions etc. inside login_ui()
    if login_ui():
        render_dashboard()

if __name__ == "__main__":
    main()
