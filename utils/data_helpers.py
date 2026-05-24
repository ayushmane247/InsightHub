import pandas as pd
import streamlit as st
from datetime import datetime

def safe_dataframe_display(df, max_rows=100):
    """Convert problematic dtypes for Streamlit display"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    df_display = df.copy()
    
    # Handle datetime columns
    for col in df_display.columns:
        if pd.api.types.is_datetime64_any_dtype(df_display[col]):
            df_display[col] = df_display[col].dt.strftime('%Y-%m-%d')
        elif df_display[col].dtype == 'object':
            # Convert mixed types to string
            df_display[col] = df_display[col].astype(str)
    
    return df_display.head(max_rows)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def process_uploaded_data(df_raw, column_mappings):
    """Cached data processing to avoid recomputation"""
    try:
        # Apply your existing data cleaning logic here
        # but with better error handling
        cleaned_df = df_raw.copy()
        
        # Date conversion with multiple format support
        if column_mappings.get('date') and column_mappings['date'] != 'None':
            date_col = column_mappings['date']
            cleaned_df['date'] = pd.to_datetime(cleaned_df[date_col], errors='coerce')
            
        # Sales conversion
        if column_mappings.get('sales') and column_mappings['sales'] != 'None':
            sales_col = column_mappings['sales']
            cleaned_df['sales'] = pd.to_numeric(cleaned_df[sales_col], errors='coerce')
            
        return cleaned_df, True
    except Exception as e:
        st.error(f"Data processing failed: {str(e)}")
        return None, False