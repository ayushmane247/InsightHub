import pandas as pd
import streamlit as st

@st.cache_data(show_spinner=False)
def get_excel_sheet_names(uploaded_file) -> list:
    """
    Returns a list of sheet names if the uploaded file is an Excel file,
    or an empty list otherwise.
    """
    try:
        # Excel files only
        if uploaded_file.name.endswith((".xlsx", ".xls")):
            # Use pd.ExcelFile to read sheet names without loading all data
            excel_file = pd.ExcelFile(uploaded_file)
            return excel_file.sheet_names
        else:
            return []
    except Exception:
        return []

@st.cache_data(show_spinner=False)
def load_and_preprocess_data(uploaded_file, sheet_name=None):
    """
    Loads data from CSV or Excel (optionally sheet_name),
    does basic preprocessing (drop empty rows/cols, reset index).
    Returns a pandas DataFrame or None on failure.
    """
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        else:
            return None

        # Basic preprocessing: drop fully empty rows/cols
        df.dropna(axis=0, how="all", inplace=True)
        df.dropna(axis=1, how="all", inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Optionally, other preprocessing steps can be added here

        return df
    except Exception:
        return None
