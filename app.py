import streamlit as st
from data_handler import preprocess_store_sales
import pandas as pd

# --- File Purpose ---
# Main Streamlit app that provides an interface for users to upload sales data,
# clean it, visualize trends, filter data by date, and download cleaned results.

st.set_page_config(page_title="InsightHub - Sales Data Analysis", layout="wide")

st.title("📊 InsightHub: Sales Data Cleaning & Visualization")
st.markdown("Upload your store sales data, clean it, and get insightful visualizations!")

uploaded_file = st.file_uploader("Upload Excel or CSV sales data", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        sales_data = preprocess_store_sales(uploaded_file)

        st.subheader("Cleaned & Aggregated Sales Data")
        st.dataframe(sales_data)

        min_date, max_date = sales_data['date'].min(), sales_data['date'].max()
        date_range = st.date_input(
            "Filter by Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        filtered_data = sales_data[
            (sales_data['date'] >= pd.to_datetime(date_range[0])) &
            (sales_data['date'] <= pd.to_datetime(date_range[1]))
        ]

        st.subheader("Visualizations")
        vis_type = st.selectbox("Choose Visualization Type", ['Line Chart', 'Bar Chart', 'Area Chart'])

        if vis_type == 'Line Chart':
            st.line_chart(filtered_data.set_index('date'))
        elif vis_type == 'Bar Chart':
            st.bar_chart(filtered_data.set_index('date'))
        elif vis_type == 'Area Chart':
            st.area_chart(filtered_data.set_index('date'))

        csv_data = filtered_data.to_csv(index=False).encode('utf-8')

        st.download_button(
            "📥 Download Cleaned Data CSV",
            data=csv_data,
            file_name='cleaned_sales_data.csv',
            mime='text/csv'
        )

    except Exception as e:
        st.error(f"Error processing file: {e}")

else:
    st.info("Upload an Excel or CSV file to start analyzing your sales data.")
