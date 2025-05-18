import pandas as pd
import plotly.express as px
import streamlit as st

def generate_sales_trend_chart(df, date_col='Order Date', sales_col='Sales'):
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(by=date_col)
    trend_df = df.groupby(df[date_col].dt.to_period('M'))[sales_col].sum().reset_index()
    trend_df[date_col] = trend_df[date_col].dt.to_timestamp()
    
    fig = px.line(trend_df, x=date_col, y=sales_col, title='📈 Monthly Sales Trend')
    return fig

def generate_status_pie_chart(df, status_col='Order Status'):
    status_counts = df[status_col].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig = px.pie(status_counts, names='Status', values='Count',
                 title='📦 Order Status Distribution',
                 color_discrete_sequence=px.colors.qualitative.Set3)
    return fig

def generate_top_products_chart(df, product_col='Product Name', sales_col='Sales', top_n=10):
    top_products = df.groupby(product_col)[sales_col].sum().nlargest(top_n).reset_index()
    fig = px.bar(top_products, x=product_col, y=sales_col,
                 title=f'🏆 Top {top_n} Products by Sales',
                 color=sales_col, text=sales_col)
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def generate_sales_by_region_chart(df, region_col='Region', sales_col='Sales'):
    region_sales = df.groupby(region_col)[sales_col].sum().reset_index()
    fig = px.bar(region_sales, x=region_col, y=sales_col,
                 title='🌍 Sales by Region',
                 color=sales_col, text=sales_col)
    return fig

def generate_time_filtered_data(df, date_col='Order Date', start_date=None, end_date=None):
    df[date_col] = pd.to_datetime(df[date_col])
    if start_date:
        df = df[df[date_col] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df[date_col] <= pd.to_datetime(end_date)]
    return df

def show_visualizations(df):
    st.subheader("📊 Interactive Dashboards")
    
    # Optional date filter
    if 'Order Date' in df.columns:
        with st.expander("🗓️ Filter by Date Range"):
            min_date = pd.to_datetime(df['Order Date']).min()
            max_date = pd.to_datetime(df['Order Date']).max()
            start_date = st.date_input("Start Date", min_date)
            end_date = st.date_input("End Date", max_date)
            df = generate_time_filtered_data(df, 'Order Date', start_date, end_date)
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(generate_sales_trend_chart(df), use_container_width=True)
    with col2:
        st.plotly_chart(generate_status_pie_chart(df), use_container_width=True)

    st.plotly_chart(generate_top_products_chart(df), use_container_width=True)
    st.plotly_chart(generate_sales_by_region_chart(df), use_container_width=True)
