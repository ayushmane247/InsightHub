import streamlit as st
import pandas as pd
from data_handler import preprocess_store_sales

# --- File Purpose ---
# Secondary Streamlit app for demonstrating a placeholder ML prediction feature.
# Loads cleaned sales data and provides a simple future sales forecast using basic logic.

st.title("🔮 InsightHub: Sales Forecasting")

uploaded_file = st.file_uploader("Upload cleaned sales data CSV for prediction", type=['csv'])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df['date'] = pd.to_datetime(df['date'])

        st.subheader("Uploaded Sales Data")
        st.dataframe(df)

        # Simple prediction logic: next 7 days sales = average of last 7 days
        recent_avg = df['amount'].tail(7).mean()
        future_dates = pd.date_range(start=df['date'].max() + pd.Timedelta(days=1), periods=7)

        forecast_df = pd.DataFrame({
            'date': future_dates,
            'predicted_amount': [recent_avg] * 7
        })

        st.subheader("7-Day Sales Forecast (Simple Moving Average)")
        st.line_chart(forecast_df.set_index('date')['predicted_amount'])

    except Exception as e:
        st.error(f"Error during prediction: {e}")

else:
    st.info("Upload a cleaned sales data CSV file to see future sales prediction.")
