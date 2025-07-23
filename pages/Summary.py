import streamlit as st
import pandas as pd
from datetime import datetime

def render():
    st.header("📝 Store Summary (At a Glance)")
    df = st.session_state.get("customer_data", None)
    if df is None or df.empty:
        st.info("No data available. Please upload your sales/inventory file first.")
        return

    # Auto-detect columns
    sales_col = next((c for c in df.columns if 'sale' in c.lower() or 'amount' in c.lower() or 'revenue' in c.lower()), None)
    profit_col = next((c for c in df.columns if 'profit' in c.lower()), None)
    product_col = next((c for c in df.columns if 'product' in c.lower()), None)
    date_col = next((c for c in df.columns if 'date' in c.lower()), None)

    st.markdown("### 📊 Key Numbers")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sales", f"₹{df[sales_col].sum():,.0f}" if sales_col else "N/A")
    with col2:
        st.metric("Total Profit", f"₹{df[profit_col].sum():,.0f}" if profit_col else "N/A")
    with col3:
        st.metric("Total Transactions", f"{len(df):,}")

    if product_col and sales_col:
        top_product = df.groupby(product_col)[sales_col].sum().idxmax()
        top_sales = df.groupby(product_col)[sales_col].sum().max()
        st.success(f"🏆 Top Product: **{top_product}** (₹{top_sales:,.0f} sales)")

    # Week-on-week trend (if date available)
    if date_col and sales_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df['week'] = df[date_col].dt.isocalendar().week
        latest_week = df['week'].max()
        prev_week = latest_week - 1
        sales_latest = df[df['week'] == latest_week][sales_col].sum()
        sales_prev = df[df['week'] == prev_week][sales_col].sum()
        delta = sales_latest - sales_prev
        pct = (delta / sales_prev * 100) if sales_prev else 0
        st.metric(f"Sales This Week (W{latest_week})", f"₹{sales_latest:,.0f}", f"{pct:+.1f}% vs last week")

    # Urgent alerts (if any)
    if product_col and sales_col:
        low_sales = df.groupby(product_col)[sales_col].sum().nsmallest(1)
        for prod, val in low_sales.items():
            if val < 0.05 * df[sales_col].sum():
                st.warning(f"⚠️ Low Sales Alert: {prod} only ₹{val:,.0f} sold. Consider a promo or review stock!")

    st.markdown("---")
    st.caption("For detailed insights, visit the Insights or Forecast pages.")

# For standalone testing
if __name__ == "__main__":
    if 'customer_data' not in st.session_state:
        st.session_state['customer_data'] = pd.DataFrame()
    render()