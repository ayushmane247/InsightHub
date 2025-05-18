import streamlit as st
from excel_utils import get_excel_sheet_names, load_and_preprocess_data

def file_upload_flow(label="Choose CSV or Excel file", key=None):
    uploaded_file = st.file_uploader(label, type=["csv", "xlsx"], key=key)
    data = None

    if uploaded_file:
        try:
            sheet_names = get_excel_sheet_names(uploaded_file)
            if sheet_names:
                selected_sheet = st.selectbox("Select sheet", sheet_names, key=f"{key}_sheet_select" if key else None)
                if selected_sheet:
                    data = load_and_preprocess_data(uploaded_file, selected_sheet)
            else:
                # Probably a CSV with no sheets
                data = load_and_preprocess_data(uploaded_file, sheet_name=None)

            if data is not None:
                st.success("✅ File loaded and preprocessed!")
            else:
                st.error("❌ Failed to load data from the file.")
        except Exception as e:
            st.error(f"Error loading file: {e}")
    else:
        st.info("📁 Please upload a CSV or Excel file.")
    return data
