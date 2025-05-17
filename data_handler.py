"""
data_handler.py

This module handles:
- Reading and preprocessing store sales data
- Supporting both CSV and multi-sheet Excel files
- Sheet selection logic for Excel files
- Generating summary statistics
"""

import pandas as pd


# 📥 Read selected sheet from Excel or CSV
def read_selected_sheet(uploaded_file, sheet_name=None):
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            # Read specific sheet from Excel
            xls = pd.ExcelFile(uploaded_file)
            df = pd.read_excel(xls, sheet_name=sheet_name or xls.sheet_names[0])
        else:
            raise ValueError("Unsupported file format. Only .xlsx and .csv allowed.")
        return df
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")


# 📄 Get all sheet names in uploaded Excel file
def get_sheet_names(uploaded_file):
    try:
        if uploaded_file.name.endswith(".xlsx"):
            xls = pd.ExcelFile(uploaded_file)
            return xls.sheet_names
        else:
            return []  # No sheets in CSV
    except Exception as e:
        raise ValueError(f"Could not extract sheet names: {e}")


# 🧹 Preprocess uploaded sales data
def preprocess_store_sales(df):
    try:
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        # Rename common date columns to 'date'
        for col in df.columns:
            if "date" in col or "order_date" in col or "year" in col:
                df.rename(columns={col: "date"}, inplace=True)
                break

        # Ensure 'date' column exists
        if "date" not in df.columns:
            raise ValueError("Missing 'date' column in data")

        # Convert to datetime
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        # Sort by date
        df = df.sort_values("date")

        # Optionally convert 'amount' or 'sales' column to numeric
        for col in ["amount", "sales", "global_sales"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Clean missing values
        df = df.dropna()

        return df

    except Exception as e:
        raise ValueError(f"Error during preprocessing: {e}")


# 📊 Summary of top-selling products or categories
def get_top_categories(df, category_col="product", metric_col="amount", top_n=5):
    try:
        if category_col in df.columns and metric_col in df.columns:
            summary = df.groupby(category_col)[metric_col].sum().sort_values(ascending=False).head(top_n)
            return summary.reset_index()
        else:
            raise ValueError(f"Missing columns '{category_col}' or '{metric_col}' for summary")
    except Exception as e:
        raise ValueError(f"Error generating top category summary: {e}")


# 📈 Daily or Weekly aggregation
def aggregate_sales_over_time(df, time_unit="D", metric_col="amount"):
    try:
        df = df.set_index("date")
        resampled = df.resample(time_unit).sum(numeric_only=True).reset_index()
        return resampled
    except Exception as e:
        raise ValueError(f"Error aggregating sales over time: {e}")
