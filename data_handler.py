import pandas as pd

# --- File Purpose ---
# This module handles the data preprocessing and cleaning for store sales data.
# Functions here read Excel/CSV files, standardize column names, handle missing data,
# detect date columns, and aggregate sales data by date.

def preprocess_store_sales(file):
    """
    Reads sales data from an Excel or CSV file, cleans it, standardizes columns,
    and returns aggregated daily sales data as a DataFrame.
    
    Args:
        file (UploadedFile or str): Path or uploaded file object
    
    Returns:
        pd.DataFrame: Cleaned and aggregated sales data by date
    """
    # Read data depending on file type
    if file.name.endswith('.xlsx'):
        df = pd.read_excel(file)
    elif file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        raise ValueError("Unsupported file format")

    # Standardize column names to lowercase and strip spaces
    df.columns = df.columns.str.lower().str.strip()

    # Basic cleaning: drop rows with missing essential columns (e.g., date or sales)
    if 'date' not in df.columns:
        raise ValueError("Missing 'date' column in data")

    df = df.dropna(subset=['date'])

    # Convert 'date' column to datetime type
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Remove rows with invalid dates
    df = df.dropna(subset=['date'])

    # Fill missing sales with 0 (assuming 'amount' is the sales column)
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    else:
        df['amount'] = 0

    # Aggregate data by date summing the sales amounts
    daily_sales = df.groupby('date').agg({'amount': 'sum'}).reset_index()

    return daily_sales
