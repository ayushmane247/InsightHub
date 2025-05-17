# app_dashboard.py
# 📊 InsightHub Dashboard: Interactive Data Visualizations & Forecasting

import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from prophet import Prophet
from io import BytesIO
from data_handler import read_selected_sheet, get_sheet_names

# Set up the page configuration
st.set_page_config(page_title="📊 InsightHub Dashboard", layout="wide")

# Sidebar header
st.sidebar.header("📁 Upload Data File")

# File uploader in sidebar
uploaded_file = st.sidebar.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])

# If a file is uploaded
if uploaded_file:
    try:
        # If Excel, show sheet selection
        if uploaded_file.name.endswith(".xlsx"):
            sheets = get_sheet_names(uploaded_file)
            sheet = st.sidebar.selectbox("Select Excel Sheet", sheets)
            df = read_selected_sheet(uploaded_file, sheet)
        else:
            # If CSV, just read directly
            df = pd.read_csv(uploaded_file)

        st.title("📊 Interactive Sales Dashboard")
        st.markdown("Visualize and forecast your store sales data with ease!")

        # Show raw data preview
        with st.expander("🔍 Preview Raw Data"):
            st.dataframe(df)

        # Date column detection and conversion
        date_col = None
        for col in df.columns:
            if 'date' in col.lower():
                date_col = col
                break

        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.sort_values(date_col)
        else:
            st.warning("⚠️ No 'date' column found. Please ensure your data includes a date.")
            st.stop()

        # Filter by date range
        min_date, max_date = df[date_col].min(), df[date_col].max()
        start_date, end_date = st.sidebar.date_input("📅 Select Date Range", [min_date, max_date])
        mask = (df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))
        df = df.loc[mask]

        # Select sales value column
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        sales_col = st.sidebar.selectbox("💰 Choose Sales Column", numeric_cols)

        st.markdown(f"### 💹 Sales Trends for: **{sales_col}**")

        # 📈 Line Chart (Sales over Time)
        fig_line = px.line(df, x=date_col, y=sales_col, title="📈 Sales Over Time")
        st.plotly_chart(fig_line, use_container_width=True)

        # 📊 Bar Chart (Sales by Weekday)
        df['Weekday'] = df[date_col].dt.day_name()
        weekday_bar = df.groupby("Weekday")[sales_col].sum().sort_values(ascending=False)
        fig_bar = px.bar(x=weekday_bar.index, y=weekday_bar.values, title="🗓️ Sales by Weekday", labels={"x": "Day", "y": "Sales"})
        st.plotly_chart(fig_bar, use_container_width=True)

        # 🥧 Pie Chart (Optional Categorical Breakdown)
        cat_cols = df.select_dtypes(include='object').columns.tolist()
        selected_cat = st.sidebar.selectbox("🧮 Group Sales by", options=cat_cols)
        if selected_cat:
            cat_pie = df.groupby(selected_cat)[sales_col].sum().reset_index()
            fig_pie = px.pie(cat_pie, values=sales_col, names=selected_cat, title=f"🎯 Sales by {selected_cat}")
            st.plotly_chart(fig_pie, use_container_width=True)

        # 🔮 Forecasting using Prophet
        st.markdown("## 🔮 Forecast Future Sales")

        forecast_days = st.slider("Select forecast period (days)", 7, 90, 30)

        # Prepare data for Prophet
        prophet_df = df[[date_col, sales_col]].rename(columns={date_col: "ds", sales_col: "y"})
        model = Prophet()
        model.fit(prophet_df)

        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)

        fig_forecast = px.line(forecast, x='ds', y='yhat', title=f"📅 Forecast for next {forecast_days} days")
        st.plotly_chart(fig_forecast, use_container_width=True)

        # Optional: Download forecast data
        csv_data = forecast[['ds', 'yhat']].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Forecast CSV", csv_data, "forecast.csv", "text/csv")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
else:
    st.info("Please upload a file to begin visualizing your data.")
