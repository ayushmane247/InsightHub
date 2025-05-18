import pandas as pd
import streamlit as st

# -----------------------------
# 📥 FILE READERS
# -----------------------------
def get_sheet_names(uploaded_file):
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        return excel_file.sheet_names
    except Exception:
        return []

def read_selected_sheet(uploaded_file, sheet_name=None):
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        else:
            raise ValueError("Unsupported file type.")
        return df
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")

# -----------------------------
# 🧼 DATA CLEANING HELPERS
# -----------------------------
def clean_column_names(df):
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    return df

def convert_dates(df):
    for col in df.columns:
        if "date" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass
    return df

def convert_numeric(df):
    for col in df.select_dtypes(include='object').columns:
        try:
            df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors='ignore')
        except Exception:
            continue
    return df

# -----------------------------
# 🏪 DOMAIN-SPECIFIC PREPROCESSING
# -----------------------------
def preprocess_store_sales(df):
    df = clean_column_names(df)
    df = convert_dates(df)
    df = convert_numeric(df)

    # Rename columns if required for consistency
    rename_map = {
        "order_date": "date",
        "shipment_date": "ship_date",
        "order_status": "status",
        "total_amount": "revenue",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Drop empty or useless columns
    df = df.dropna(how="all", axis=1)
    df = df.dropna(how="any", axis=0)

    return df

# -----------------------------
# 🚀 Placeholder for More Domains
# -----------------------------
def preprocess_game_sales(df):
    # TODO: Implement game sales-specific preprocessing
    return df

def preprocess_movie_ratings(df):
    # TODO: Implement movie ratings-specific preprocessing
    return df
