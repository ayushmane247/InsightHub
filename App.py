# App.py

import streamlit as st
# --- Set Global Page Configuration (must be the very first Streamlit command) ---

st.set_page_config(
    page_title="InsightHub - Multidomain Data Analysis",
    page_icon="📊",
    layout="wide", # Use wide layout for a better dashboard experience
    initial_sidebar_state="collapsed" # Ensure sidebar is expanded by default
)

import pandas as pd
from datetime import datetime # Needed for session_state initialization if not in other pages
from PIL import Image # For adding the logo
import os # For checking file existence, useful for the logo path
from pages import Insights, Forecast, Alert_Centre # Import your page modules, removed Upload
from auth import login_ui, is_authenticated, logout
import numpy as np # Add numpy for potential NaN usage in upload logic

# 🔐 Login Check
if not login_ui():
    st.stop()

# --- Initialize session state for current page and data ---
if 'customer_data' not in st.session_state:
    st.session_state['customer_data'] = None
if 'data_uploaded_and_processed' not in st.session_state:
    st.session_state['data_uploaded_and_processed'] = False
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'Upload' # Default page on app launch
if 'upload_history' not in st.session_state: # Initialize upload history
    st.session_state['upload_history'] = []

# --- Custom Sidebar Header (Logo, Title, Styling) ---
with st.sidebar:
    # --- Logo and Main Title ---
    try:
        st.image("assets/insights.jpg", width=200, use_container_width=True)
    except FileNotFoundError:
        st.warning("Logo image not found. Please check the path 'D:\\project\\image_793f1a.jpg'.")
        st.markdown("<h1 style='color: #4CAF50;'>InsightHub 💡</h1>", unsafe_allow_html=True)

    st.markdown("<h3 style='text-align: center; color: #E0E0E0; margin-top: -15px;'>Store Operations</h3>", unsafe_allow_html=True)


    # --- New Sections: Settings & User Manual ---
    st.markdown("### Application Options") # A clear heading for these sections

    # Settings section (expandable)
    with st.expander("⚙️ Settings"):
        st.subheader("User Profile")
        st.write("Manage your profile and preferences.")
        if st.button("Edit Profile", key="btn_edit_profile"):
            st.info("Profile editing feature coming soon!") # Placeholder for future functionality
        
        st.subheader("User History")
        st.write("View your past activities and alerts.")
        if st.button("View User History", key="btn_view_user_history"):
            st.session_state['current_page'] = 'History' # Set page to history
            st.rerun() # Rerun to display history page

    # User Manual section
    st.markdown("### Resources")
    if st.button("📖 User Manual", key="btn_user_manual"):
        st.info("Opening user manual (feature coming soon!).") # Placeholder

    # Optional: Common footer or persistent elements at the very bottom of the sidebar
    st.markdown("---")
    st.caption(f"InsightHub v1.0")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if st.button("🔒 Logout", key="logout", help="Click to logout", use_container_width=True):
        logout()
        st.rerun()

# --- Upload Logic Function (moved from Upload.py) ---
def render_upload_page():
    st.title("⬆️ Data Upload")
    st.markdown("Please upload your sales and inventory data.")
    st.markdown("We'll try to auto-detect your columns, but you can always adjust them.")

    uploaded_file = st.file_uploader(
        "Choose an Excel or CSV file",
        type=["csv", "xlsx", "xls"]
    )

    df_raw = None

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                df_raw = pd.read_excel(uploaded_file)
            else:
                 st.error("Unsupported file type. Please upload a CSV, XLSX, or XLS file.")
                 st.session_state['customer_data'] = None
                 st.session_state['data_uploaded_and_processed'] = False
                 return


            if df_raw.empty:
                st.error("The uploaded file is empty. Please upload a file with data.")
                st.session_state['customer_data'] = None
                st.session_state['data_uploaded_and_processed'] = False
                return

            st.subheader("1. Raw Data Preview")
            st.dataframe(df_raw.head())

            # --- Auto-Detect Columns ---
            st.subheader("2. Auto-Detected & Mapped Columns (Adjust if needed)")

            available_cols = ['None'] + df_raw.columns.tolist()

            auto_date_col = 'None'
            auto_sales_col = 'None'
            auto_qty_col = 'None'
            auto_product_col = 'None'
            auto_stock_col = 'None'

            # Try to auto-detect Date Column
            date_keywords = ['date', 'Date', 'DATE', 'transaction_date', 'order_date', 'invoice_date', 'timestamp', 'created_at']
            for col in df_raw.columns:
                if any(keyword.lower() in str(col).lower() for keyword in date_keywords):
                    temp_series = pd.to_datetime(df_raw[col], errors='coerce')
                    if temp_series.notna().sum() / len(df_raw) > 0.7:
                        auto_date_col = col
                        break

            # Try to auto-detect Sales/Quantity Column
            sales_keywords = ['sales', 'Sales', 'revenue', 'Revenue', 'amount', 'Amount', 'price', 'total']
            qty_keywords = ['quantity', 'qty', 'items_sold', 'units']
            
            for col in df_raw.columns:
                if auto_sales_col == 'None' and any(keyword.lower() in str(col).lower() for keyword in sales_keywords):
                    temp_series = pd.to_numeric(df_raw[col], errors='coerce')
                    if temp_series.notna().sum() / len(df_raw) > 0.7 and (temp_series > 0).sum() / len(df_raw) > 0.5:
                        auto_sales_col = col
                if auto_qty_col == 'None' and any(keyword.lower() in str(col).lower() for keyword in qty_keywords):
                    temp_series = pd.to_numeric(df_raw[col], errors='coerce')
                    if temp_series.notna().sum() / len(df_raw) > 0.7 and (temp_series >= 0).sum() / len(df_raw) > 0.5:
                        auto_qty_col = col
            
            if auto_sales_col == 'None' and auto_qty_col != 'None':
                auto_sales_col = auto_qty_col
                if 'temp_warning_qty_as_sales' not in st.session_state or st.session_state.get('last_uploaded_file_name') != uploaded_file.name:
                    st.warning("Auto-detected 'Quantity' as 'Sales' fallback. Please confirm below.")
                    st.session_state['temp_warning_qty_as_sales'] = True
                    st.session_state['last_uploaded_file_name'] = uploaded_file.name

            # Try to auto-detect Product Column
            product_keywords = ['product', 'item', 'sku', 'product_name', 'item_name', 'description', 'category']
            for col in df_raw.columns:
                if auto_product_col == 'None' and any(keyword.lower() in str(col).lower() for keyword in product_keywords):
                    if df_raw[col].dtype == 'object' and df_raw[col].nunique() > 2 and df_raw[col].nunique() < len(df_raw) * 0.8:
                        auto_product_col = col
                        break
            
            # Try to auto-detect Current Stock Column
            stock_keywords = ['stock', 'current_stock', 'inventory', 'stock_on_hand', 'units_in_stock', 'stock_level']
            for col in df_raw.columns:
                if auto_stock_col == 'None' and any(keyword.lower() in str(col).lower() for keyword in stock_keywords):
                    temp_series = pd.to_numeric(df_raw[col], errors='coerce')
                    if temp_series.notna().sum() / len(df_raw) > 0.7 and (temp_series >= 0).sum() / len(df_raw) > 0.5:
                        auto_stock_col = col
                        break

            get_index = lambda col_val: available_cols.index(col_val) if col_val in available_cols else 0

            date_col_map = st.selectbox(
                "Select your 'Date' column:", 
                available_cols, 
                index=get_index(auto_date_col),
                key='date_col_map'
            )
            sales_col_map = st.selectbox(
                "Select your 'Sales/Revenue' column:", 
                available_cols, 
                index=get_index(auto_sales_col),
                key='sales_col_map'
            )
            quantity_col_map = st.selectbox(
                "Select your 'Quantity Sold' column (optional, will use sales if not specified):", 
                available_cols, 
                index=get_index(auto_qty_col),
                key='qty_col_map'
            )
            product_col_map = st.selectbox(
                "Select your 'Product Name/SKU' column (optional, 'All Products' if not selected):", 
                available_cols, 
                index=get_index(auto_product_col),
                key='product_col_map'
            )
            stock_col_map = st.selectbox(
                "Select your 'Current Stock' column (optional, will be inferred for alerts if not selected):", 
                available_cols, 
                index=get_index(auto_stock_col),
                key='stock_col_map'
            )

            if st.button("Process Data and Save"):
                if 'temp_warning_qty_as_sales' in st.session_state:
                    del st.session_state['temp_warning_qty_as_sales']

                cleaned_df = df_raw.copy()
                issues = []
                
                # --- Apply Mappings and Clean Data ---
                # Date Column
                if date_col_map != 'None':
                    cleaned_df['date'] = pd.to_datetime(cleaned_df[date_col_map], errors='coerce')
                    if cleaned_df['date'].isnull().all():
                        issues.append(f"❌ Date column '{date_col_map}' conversion failed for all rows. Check format (e.g., YYYY-MM-DD).")
                    else:
                        cleaned_df.dropna(subset=['date'], inplace=True)
                        if cleaned_df.empty:
                            issues.append("❌ No valid dates found after cleaning. Data is empty.")
                else:
                    issues.append("❌ 'Date' column is **required** for time-series analysis (Forecast, Alerts). Please select one.")

                # Sales Column
                if sales_col_map != 'None':
                    cleaned_df['sales'] = pd.to_numeric(cleaned_df[sales_col_map], errors='coerce')
                    if cleaned_df['sales'].isnull().any():
                        st.warning(f"⚠️ Some values in 'Sales/Revenue' column ('{sales_col_map}') could not be converted to numbers. They will be treated as 0.")
                    cleaned_df['sales'].fillna(0, inplace=True)
                else:
                    issues.append("❌ 'Sales/Revenue' column is **required** for sales analysis (Forecast, Alerts). Please select one.")

                # Quantity Column (Optional, fallback to sales if not provided)
                if quantity_col_map != 'None':
                    cleaned_df['quantity'] = pd.to_numeric(cleaned_df[quantity_col_map], errors='coerce')
                    if cleaned_df['quantity'].isnull().any():
                        st.warning(f"⚠️ Some values in 'Quantity Sold' column ('{quantity_col_map}') could not be converted to numbers. They will be treated as 0.")
                    cleaned_df['quantity'].fillna(0, inplace=True)
                else:
                    if 'sales' in cleaned_df.columns:
                        cleaned_df['quantity'] = cleaned_df['sales']
                        st.info("No 'Quantity Sold' column mapped. 'Sales' amount will be used as a proxy for quantity in some calculations.")
                    else:
                        cleaned_df['quantity'] = 0

                # Product Column (Optional, default to 'All Products')
                if product_col_map != 'None':
                    cleaned_df['product'] = cleaned_df[product_col_map].astype(str)
                else:
                    cleaned_df['product'] = 'All Products'
                    st.info("No 'Product Name/SKU' column mapped. All data will be treated as 'All Products'.")

                # Current Stock Column (Optional, will be inferred if not provided later)
                if stock_col_map != 'None':
                    cleaned_df['current_stock'] = pd.to_numeric(cleaned_df[stock_col_map], errors='coerce')
                else:
                    cleaned_df['current_stock'] = np.nan
                    st.info("No 'Current Stock' column mapped. Stock levels will be inferred for alerts, which may be less accurate.")

                if issues:
                    st.error("Please fix the following issues before proceeding:")
                    for issue in issues:
                        st.write(issue)
                    st.session_state['customer_data'] = None
                    st.session_state['data_uploaded_and_processed'] = False
                else:
                    if 'date' not in cleaned_df.columns or cleaned_df['date'].empty or \
                       'sales' not in cleaned_df.columns or cleaned_df['sales'].empty:
                        st.error("Essential 'Date' or 'Sales' data is missing or invalid even after mapping. Cannot proceed with analysis.")
                        st.session_state['customer_data'] = None
                        st.session_state['data_uploaded_and_processed'] = False
                    else:
                        processed_df = pd.DataFrame({
                            'date': cleaned_df['date'],
                            'sales': cleaned_df['sales'],
                            'quantity': cleaned_df['quantity'],
                            'product': cleaned_df['product'],
                            'current_stock': cleaned_df['current_stock']
                        })
                        
                        if processed_df['product'].isnull().all():
                            processed_df['product'] = 'All Products'

                        st.session_state['customer_data'] = processed_df
                        st.session_state['data_uploaded_and_processed'] = True

                        # Add to upload history
                        st.session_state['upload_history'].append({
                            'filename': uploaded_file.name,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'rows_processed': len(processed_df),
                            'original_columns': df_raw.columns.tolist(),
                            'mapped_columns': {
                                'date': date_col_map,
                                'sales': sales_col_map,
                                'quantity': quantity_col_map,
                                'product': product_col_map,
                                'current_stock': stock_col_map
                            }
                        })
                        
                        st.success("Data processed and saved successfully! You can now navigate to other analytics pages via sidebar.")
                        
                        st.subheader("3. Cleaned Data Preview")
                        st.dataframe(st.session_state['customer_data'].head())
                        st.write(f"Shape of cleaned data: {st.session_state['customer_data'].shape}")
                        st.write("Column types after cleaning:")
                        st.dataframe(st.session_state['customer_data'].dtypes.reset_index().rename(columns={'index': 'Column', 0: 'Data Type'}))

        except Exception as e:
            st.error(f"An error occurred during file processing: {e}. Please ensure the file format is correct and try again.")
            st.session_state['customer_data'] = None
            st.session_state['data_uploaded_and_processed'] = False
            
    elif st.session_state['customer_data'] is not None and st.session_state['data_uploaded_and_processed']:
        st.info("Data is already loaded and processed from a previous upload. You can upload a new file below to change it.")
        st.subheader("Current Loaded Data Preview")
        st.dataframe(st.session_state['customer_data'].head())
        st.write(f"Shape of current data: {st.session_state['customer_data'].shape}")
        st.write("Column types:")
        st.dataframe(st.session_state['customer_data'].dtypes.reset_index().rename(columns={'index': 'Column', 0: 'Data Type'}))

# --- Display Content Based on Page Selection (in the main area) ---
st.write("# InsightHub! 📊")
st.markdown("Your central hub for multidomain data analysis.")
st.markdown("---")

if st.session_state['current_page'] == "Upload":
    render_upload_page() # Call the new function
elif st.session_state['current_page'] == "Insights":
    if st.session_state['data_uploaded_and_processed']:
        Insights.render()
    else:
        st.warning("Please upload and process your data on the 'Upload' page first.")
elif st.session_state['current_page'] == "Forecast":
    if st.session_state['data_uploaded_and_processed']:
        Forecast.render()
    else:
        st.warning("Please upload and process your data on the 'Upload' page first.")
elif st.session_state['current_page'] == "Alert Centre":
    if st.session_state['data_uploaded_and_processed']:
        Alert_Centre.render()
    else:
        st.warning("Please upload and process your data on the 'Upload' page first.")
elif st.session_state['current_page'] == "History":
    # This block assumes you'll create a new 'History.py' module
    # or implement history display directly here.
    st.title("User History")
    if st.session_state['upload_history']:
        st.subheader("Data Upload History")
        for i, entry in enumerate(st.session_state['upload_history']):
            st.markdown(f"---")
            st.write(f"**Upload {i+1}**")
            st.write(f"**Filename:** {entry['filename']}")
            st.write(f"**Timestamp:** {entry['timestamp']}")
            st.write(f"**Rows Processed:** {entry['rows_processed']}")
            st.write(f"**Original Columns:** {', '.join(entry['original_columns'])}")
            st.write(f"**Mapped Columns:**")
            st.json(entry['mapped_columns'])
    else:
        st.info("No upload history yet.")