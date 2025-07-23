# pages/Alert_Centre.py

"""
Date: 2025-06-07
Author: Your Name / Your Team Name
Purpose:
    This module, 'Alert_Centre.py', serves as the central hub for generating and
    displaying actionable alerts for the store owner within the InsightHub application.
    It synthesizes data from sales, inventory, and forecast modules to provide
    timely notifications on critical business aspects.

Features:
    - Stockout Risk Alerts: Warns about products likely to run out based on forecast and current stock.
    - Low Stock Alerts: Notifies when product inventory levels drop below a safe threshold.
    - High Sales Anomaly Alerts: Identifies unusual spikes in sales that may require investigation or
      signal new trends.
    - Low Sales Anomaly Alerts: Highlights unexpected dips in sales, potentially indicating issues
      or requiring promotional action.
    - Slow-Moving Item Alerts: Identifies products with low turnover, indicating potential overstocking.
    - Supplier Performance Alerts: (Placeholder, requires supplier data integration)
    - Customizable Alert Thresholds: Allows store owners to define what constitutes a critical alert.
    - In-App Notification Display: Integrates with Streamlit to show alerts directly in the dashboard.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from textwrap import dedent
import warnings
warnings.filterwarnings('ignore') # Suppress warnings if any from underlying libraries

# --- Import AlertHelper from modules ---
try:
    from utils.alert_helper import AlertHelper
except ImportError as e:
    st.error(f"Error loading AlertHelper: {e}. Please ensure 'modules/alert_helper.py' exists and contains the AlertHelper class.")
    st.stop() # Stop execution if helpers aren't found

# --- Constants and Default Thresholds ---
DEFAULT_CRITICAL_STOCK_DAYS = 5      # Days of stock remaining for critical alert
DEFAULT_LOW_STOCK_THRESHOLD_QTY = 10 # Absolute quantity for low stock alert
DEFAULT_SALES_ANOMALY_ZSCORE = 2.0   # Z-score for anomaly detection (how many std deviations from mean)
DEFAULT_SLOW_MOVING_THRESHOLD_SALES_PER_DAY = 1.0 # E.g., less than 1 sale per day on average


# --- Helper for Visualization ---
def plot_sales_trend_for_anomaly(df, anomaly_date, sales_col='sales'):
    """Generates a simple line chart for sales trend with anomaly highlighted."""
    fig = go.Figure()
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])

    # Filter data for a recent period around the anomaly
    plot_start_date = anomaly_date - timedelta(days=14)
    plot_end_date = anomaly_date + timedelta(days=7) # Show a bit after the anomaly
    
    relevant_df = df[(df['date'] >= plot_start_date) & (df['date'] <= plot_end_date)]

    if relevant_df.empty:
        return go.Figure() # Return empty if no data

    fig.add_trace(go.Scatter(x=relevant_df['date'], y=relevant_df[sales_col], mode='lines+markers', name='Sales'))
    
    # Highlight the anomaly point
    anomaly_data = relevant_df[relevant_df['date'] == anomaly_date]
    if not anomaly_data.empty:
        fig.add_trace(go.Scatter(
            x=anomaly_data['date'], 
            y=anomaly_data[sales_col], 
            mode='markers', 
            marker=dict(size=10, color='red', symbol='star'), 
            name='Anomaly'
        ))

    fig.update_layout(
        height=200, 
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Date",
        yaxis_title="Sales",
        showlegend=False,
        hovermode="x unified"
    )
    return fig

def plot_inventory_status(product_data):
    """Generates a simple bar chart for inventory status."""
    fig = go.Figure()
    
    # Ensure current_stock and avg_daily_sales are numeric
    product_data['current_stock'] = pd.to_numeric(product_data['current_stock'])
    product_data['avg_daily_sales'] = pd.to_numeric(product_data['avg_daily_sales'])

    # Data for bar chart
    products = [product_data['product']]
    current_stock = [product_data['current_stock']]
    
    fig.add_trace(go.Bar(
        x=products,
        y=current_stock,
        name='Current Stock',
        marker_color='skyblue'
    ))
    
    # Add a line for the average daily sales as a reference
    fig.add_trace(go.Scatter(
        x=products,
        y=[product_data['avg_daily_sales']],
        mode='lines',
        name='Avg Daily Sales',
        line=dict(color='orange', dash='dot')
    ))

    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Product",
        yaxis_title="Quantity",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# --- Main Page Render Function ---
def render():
    """
    Main entry point for the Alert Centre page.
    Handles data retrieval from session state and orchestrates the display of alerts.
    """

    st.title("🔔 Alert Centre")
    st.markdown(dedent("""
        Your central hub for important operational alerts!
        Stay on top of critical stock levels, sales anomalies, and inventory issues.
    """))
    st.markdown("---")

    # Retrieve cleaned data from session state
    if 'customer_data' not in st.session_state or st.session_state['customer_data'] is None:
        st.warning("No data uploaded yet. Please go to the **'Upload'** page to upload your sales and inventory file to enable alerts.")
        return

    df = st.session_state['customer_data'].copy() # Work on a copy to avoid modifying original session state data directly for debugging purposes

    if df.empty:
        st.warning("The uploaded data is empty or became empty after initial processing. Please check your file.")
        return

    # Define standard column names for consistency
    date_col = 'date'
    product_col = 'product'
    sales_col = 'sales'
    qty_col = 'quantity'
    stock_col = 'current_stock' # This needs to be a column in your data or inferred

    # --- Data Robustness Checks and Fallbacks (Minimized as AlertHelper handles some internally) ---
    if date_col not in df.columns or df[date_col].isnull().all():
        st.error(f"Required column '{date_col}' missing or empty. Cannot proceed with time-series analysis for alerts.")
        return
    
    if sales_col not in df.columns and qty_col not in df.columns:
        st.error(f"Neither '{sales_col}' nor '{qty_col}' found. Sales-based alerts will not function.")
        return

    # Ensure 'product' column exists
    if product_col not in df.columns:
        st.info("No 'product' column found. Product-specific alerts will be limited, grouping all sales as 'All Products'.")
        df[product_col] = 'All Products' # Create a dummy product for aggregation

    # --- Current Stock Handling (Crucial for inventory alerts) ---
    product_current_stock_df = st.session_state.get('product_current_stock_df', pd.DataFrame())

    if product_current_stock_df.empty:
        if stock_col in df.columns and not df[stock_col].isnull().all():
            df[stock_col] = pd.to_numeric(df[stock_col], errors='coerce')
            product_current_stock_df = df.sort_values(date_col).groupby(product_col)[stock_col].last().reset_index()
            product_current_stock_df.rename(columns={stock_col: 'current_stock'}, inplace=True)
            product_current_stock_df.dropna(subset=['current_stock'], inplace=True)
        
        if product_current_stock_df.empty:
            st.warning(f"'{stock_col}' column not found or is empty in your data. Simulating 'Current Stock' for demonstration purposes. For accurate inventory, ensure your data includes current stock levels.")
            if product_col in df.columns and qty_col in df.columns and df[qty_col].sum() > 0:
                daily_quantity_sold = df.groupby([date_col, product_col])[qty_col].sum().reset_index()
                avg_daily_qty_sold = daily_quantity_sold.groupby(product_col)[qty_col].mean().reset_index()
                avg_daily_qty_sold.rename(columns={qty_col: 'avg_daily_quantity_sold'}, inplace=True)

                product_current_stock_df = pd.DataFrame({product_col: df[product_col].unique()})
                product_current_stock_df = product_current_stock_df.merge(avg_daily_qty_sold, on=product_col, how='left')
                product_current_stock_df['current_stock'] = (product_current_stock_df['avg_daily_quantity_sold'] * 7).fillna(50)
                product_current_stock_df = product_current_stock_df[[product_col, 'current_stock']]
            else:
                st.info("Insufficient data to even simulate 'Current Stock'. Inventory alerts will be limited.")
                product_current_stock_df = pd.DataFrame({product_col: df[product_col].unique(), 'current_stock': 0})
    
    st.session_state['product_current_stock_df'] = product_current_stock_df


    # Set up sidebar for alert configuration
    with st.sidebar:
        st.header("Alert Configuration")
        st.markdown("Set thresholds for what constitutes a critical alert.")

        st.subheader("Inventory Alerts")
        critical_stock_days = st.number_input(
            "Critical Stock (days remaining)",
            min_value=1, max_value=30, value=DEFAULT_CRITICAL_STOCK_DAYS, step=1,
            help="Alert if product stock is projected to last less than this many days."
        )
        low_stock_qty = st.number_input(
            "Low Stock Quantity",
            min_value=1, max_value=100, value=DEFAULT_LOW_STOCK_THRESHOLD_QTY, step=1,
            help="Alert if actual stock quantity for any product drops below this number."
        )
        slow_moving_sales_per_day = st.number_input(
            "Slow-Moving Item (avg sales/day)",
            min_value=0.1, max_value=5.0, value=DEFAULT_SLOW_MOVING_THRESHOLD_SALES_PER_DAY, step=0.1,
            help="Alert if a product's average daily sales is less than this value (indicating slow turnover)."
        )

        st.subheader("Sales Anomaly Alerts")
        anomaly_zscore = st.slider(
            "Sales Anomaly Sensitivity (Z-score)",
            min_value=1.0, max_value=4.0, value=DEFAULT_SALES_ANOMALY_ZSCORE, step=0.1,
            help="Higher value means less sensitive (fewer alerts for larger deviations). Z-score of 2 means 2 standard deviations from mean."
        )

        forecast_horizon_days = st.session_state.get('forecast_horizon', 14) # Default to 14 if not set


    # --- Initialize AlertHelper with the main DataFrame ---
    alert_manager = AlertHelper(df)

    # --- Generate ALL Alerts (before filtering) ---
    all_alerts_raw = [] # Store raw alerts with all details

    # 1. Stockout Risk Alerts
    if not st.session_state['product_current_stock_df'].empty and sales_col in df.columns:
        daily_product_sales_qty = df.groupby([date_col, product_col])[qty_col].sum().reset_index()
        avg_daily_qty_sold_per_product = daily_product_sales_qty.groupby(product_col)[qty_col].mean().reset_index()
        avg_daily_qty_sold_per_product.rename(columns={qty_col: 'avg_daily_sales'}, inplace=True)

        critical_stock_alerts_df = alert_manager.calculate_inventory_status(
            product_current_stock_df=st.session_state['product_current_stock_df'],
            avg_daily_sales_data=avg_daily_qty_sold_per_product,
            critical_stock_days=critical_stock_days
        )

        for index, row in critical_stock_alerts_df[critical_stock_alerts_df['is_critical']].iterrows():
            message = f"**{row[product_col]}**: Critical stock! Estimated **{row['stockout_risk_days']:.0f} days** of stock remaining. Current: {row['current_stock']:.0f}, Avg Daily Sales: {row['avg_daily_sales']:.1f}."
            all_alerts_raw.append({
                "alert_date": datetime.now(), # Use current date for immediate alerts
                "type": "Stockout Risk",
                "severity": "Critical",
                "status": "New",
                "product": row[product_col],
                "message": message,
                "summary": f"Product '{row[product_col]}' is at critical low stock.",
                "details": row.to_dict(),
                "viz_type": "inventory_bar"
            })
    
    # 2. Low Stock Alerts
    if not st.session_state['product_current_stock_df'].empty:
        low_stock_items = st.session_state['product_current_stock_df'][
            st.session_state['product_current_stock_df']['current_stock'] <= low_stock_qty
        ]
        for index, row in low_stock_items.iterrows():
            message = f"**{row[product_col]}**: Low stock! Only **{row['current_stock']:.0f} units** remaining."
            all_alerts_raw.append({
                "alert_date": datetime.now(),
                "type": "Low Stock",
                "severity": "High",
                "status": "New",
                "product": row[product_col],
                "message": message,
                "summary": f"Product '{row[product_col]}' has dropped to low inventory levels.",
                "details": row.to_dict(),
                "viz_type": "inventory_bar"
            })

    # 3. Sales Anomaly Alerts (High and Low)
    if date_col in df.columns and sales_col in df.columns and len(df[date_col].unique()) > 1:
        df_daily_sales_total = df.groupby(date_col)[sales_col].sum().reset_index()
        df_daily_sales_total.columns = ['date', 'sales']

        anomalies_df = alert_manager.detect_sales_anomalies(df_daily_sales_total, z_score_threshold=anomaly_zscore)

        for index, row in anomalies_df[anomalies_df['is_anomaly_high']].iterrows():
            date_str = row['date'].strftime('%Y-%m-%d')
            message = f"**{date_str}**: Sales of ₹{row['sales']:.0f} were significantly higher than expected (Z-score: {row['z_score']:.1f})."
            all_alerts_raw.append({
                "alert_date": row['date'],
                "type": "High Sales Anomaly",
                "severity": "Medium",
                "status": "New",
                "product": "All Products", # Anomalies are total sales
                "message": message,
                "summary": f"Unusually high sales detected on {date_str}.",
                "details": row.to_dict(),
                "viz_type": "sales_trend"
            })
        for index, row in anomalies_df[anomalies_df['is_anomaly_low']].iterrows():
            date_str = row['date'].strftime('%Y-%m-%d')
            message = f"**{date_str}**: Sales of ₹{row['sales']:.0f} were significantly lower than expected (Z-score: {row['z_score']:.1f})."
            all_alerts_raw.append({
                "alert_date": row['date'],
                "type": "Low Sales Anomaly",
                "severity": "High", # Low sales often more critical than high
                "status": "New",
                "product": "All Products",
                "message": message,
                "summary": f"Significant drop in sales detected on {date_str}.",
                "details": row.to_dict(),
                "viz_type": "sales_trend"
            })

    # 4. Slow-Moving Item Alerts
    if product_col in df.columns and sales_col in df.columns and len(df[product_col].unique()) > 0:
        slow_moving_items = alert_manager.identify_slow_moving_items(
            product_col=product_col,
            sales_col=sales_col,
            slow_moving_sales_per_day=slow_moving_sales_per_day
        )
        for index, row in slow_moving_items.iterrows():
            message = f"**{row[product_col]}**: Average daily sales of only **{row['avg_daily_sales']:.1f}**."
            all_alerts_raw.append({
                "alert_date": datetime.now(),
                "type": "Slow-Moving Item",
                "severity": "Low",
                "status": "New",
                "product": row[product_col],
                "message": message,
                "summary": f"Product '{row[product_col]}' is selling very slowly.",
                "details": row.to_dict(),
                "viz_type": "inventory_bar" # Can use similar bar chart or just text
            })
            
    # --- Store raw alerts in session state (important for re-filtering) ---
    st.session_state['all_alerts_raw'] = all_alerts_raw

    # --- Filtering UI ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Alerts")
    
    # Extract unique values for filters
    alert_types = sorted(list(set([a['type'] for a in all_alerts_raw])))
    alert_types.insert(0, "All")
    
    severities = sorted(list(set([a['severity'] for a in all_alerts_raw])))
    severities = ['All', 'Critical', 'High', 'Medium', 'Low', 'Informational'] # Order them explicitly
    
    statuses = sorted(list(set([a['status'] for a in all_alerts_raw])))
    statuses.insert(0, "All")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        selected_type = st.selectbox("Alert Type", options=alert_types)
    with col2:
        selected_severity = st.selectbox("Severity", options=severities)
    
    selected_status = st.sidebar.selectbox("Status", options=statuses)
    
    time_range_options = ['All Time', 'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly', 'Custom Range']
    selected_time_range = st.sidebar.selectbox("Time Range", options=time_range_options)

    start_date, end_date = None, None
    if selected_time_range == 'Custom Range':
        col3, col4 = st.sidebar.columns(2)
        with col3:
            start_date = st.date_input("Start Date", value=df[date_col].min(), min_value=df[date_col].min(), max_value=df[date_col].max())
        with col4:
            end_date = st.date_input("End Date", value=df[date_col].max(), min_value=df[date_col].min(), max_value=df[date_col].max())
        if start_date > end_date:
            st.sidebar.error("Start date must be before end date.")
            start_date, end_date = None, None # Invalidate custom range

    search_query = st.sidebar.text_input("Search Alerts", placeholder="e.g., 'stock', 'sales drop'")

    # Apply filters using AlertHelper
    with st.spinner("Applying filters..."):
        filtered_alerts = alert_manager.filter_alerts(
            all_alerts_raw,
            time_range=selected_time_range if selected_time_range != 'All Time' else None,
            alert_type=selected_type if selected_type != 'All' else None,
            severity=selected_severity if selected_severity != 'All' else None,
            status=selected_status if selected_status != 'All' else None,
            search_query=search_query
        )

        # Apply custom date range filter manually if selected
        if selected_time_range == 'Custom Range' and start_date and end_date:
            filtered_alerts_df = pd.DataFrame(filtered_alerts)
            if not filtered_alerts_df.empty:
                filtered_alerts_df['alert_date'] = pd.to_datetime(filtered_alerts_df['alert_date'])
                filtered_alerts_df = filtered_alerts_df[
                    (filtered_alerts_df['alert_date'].dt.date >= start_date) &
                    (filtered_alerts_df['alert_date'].dt.date <= end_date)
                ]
                filtered_alerts = filtered_alerts_df.to_dict(orient='records')
            else:
                filtered_alerts = [] # No alerts if empty after previous filters

    st.header("Filtered Alerts")
    
    if not filtered_alerts:
        st.info("No alerts match your current filter criteria.")
    else:
        st.metric("Total Filtered Alerts", len(filtered_alerts))
        
        # Grouping alerts
        # Sort by severity (Critical > High > Medium > Low > Informational)
        severity_order = {'Critical': 5, 'High': 4, 'Medium': 3, 'Low': 2, 'Informational': 1}
        filtered_alerts.sort(key=lambda x: (severity_order.get(x['severity'], 0), x['alert_date']), reverse=True)

        grouped_alerts = {}
        for alert in filtered_alerts:
            group_key = f"{alert['type']} - {alert['severity']}"
            if alert.get('product') and alert['product'] != 'All Products': # Group by product for inventory/slow-moving
                group_key += f" (Product: {alert['product']})"
            grouped_alerts.setdefault(group_key, []).append(alert)

        for group_key, alerts_in_group in grouped_alerts.items():
            # Use an expander for each group
            with st.expander(f"**{group_key}** ({len(alerts_in_group)} alerts)"):
                for alert in alerts_in_group:
                    st.markdown(f"**Type**: {alert['type']} | **Severity**: {alert['severity']} | **Status**: {alert['status']}")
                    if alert.get('product') and alert['product'] != 'All Products':
                         st.markdown(f"**Product**: {alert['product']}")
                    if alert.get('alert_date'):
                         st.markdown(f"**Date**: {alert['alert_date'].strftime('%Y-%m-%d')}")
                    
                    st.markdown(f"**Summary**: {alert['summary']}")
                    st.markdown(f"**Message**: {alert['message']}")

                    # Add visualizations based on viz_type
                    if alert.get('viz_type') == 'sales_trend':
                        sales_anomaly_date = alert['alert_date']
                        # Ensure df_daily_sales_total is available for plotting
                        df_daily_sales_total = df.groupby(date_col)[sales_col].sum().reset_index()
                        df_daily_sales_total.columns = ['date', 'sales']
                        st.plotly_chart(plot_sales_trend_for_anomaly(df_daily_sales_total, sales_anomaly_date, sales_col), use_container_width=True)
                        st.markdown("💡 *Trend showing sales around the anomaly date.*")
                    elif alert.get('viz_type') == 'inventory_bar':
                        # For inventory alerts, use the details from the alert to plot
                        product_name_for_plot = alert['product']
                        if product_name_for_plot != 'All Products': # Only plot if a specific product
                            product_row = st.session_state['product_current_stock_df'][st.session_state['product_current_stock_df']['product'] == product_name_for_plot]
                            if not product_row.empty:
                                current_stock_val = product_row['current_stock'].iloc[0]
                                avg_daily_sales_val = alert['details'].get('avg_daily_sales', 0) # Get from details if available
                                
                                # Create a dummy DataFrame for plot_inventory_status
                                plot_df = pd.DataFrame({
                                    'product': [product_name_for_plot],
                                    'current_stock': [current_stock_val],
                                    'avg_daily_sales': [avg_daily_sales_val]
                                })
                                st.plotly_chart(plot_inventory_status(plot_df.iloc[0]), use_container_width=True)
                                st.markdown("💡 *Comparison of current stock vs. average daily sales.*")
                            else:
                                st.info(f"No current stock data available for plotting {product_name_for_plot}.")
                        else:
                            st.info("Visualizations for 'All Products' inventory alerts are not yet available.")
                    
                    st.markdown("---") # Separator for individual alerts within a group

        st.markdown("### Suggested Actions:")
        st.info(dedent("""
            - **Stockout Risks**: Prioritize reordering for flagged products. Review lead times with suppliers.
            - **Low Stock**: Initiate reorders, especially for fast-moving items.
            - **High Sales Anomalies**: Investigate reasons (promotions, events) to replicate success. Adjust future forecasts.
            - **Low Sales Anomalies**: Analyze root causes (competition, seasonality, issues) and consider corrective actions (promotions, marketing).
            - **Slow-Moving Items**: Explore marketing campaigns, discounts, bundling, or re-evaluation of product positioning.
        """))

    st.markdown("---")
    st.markdown("💡 Remember to regularly review your data and adjust alert thresholds to match your business needs.")


# --- Run the module directly for testing ---
if __name__ == "__main__":
    if 'customer_data' not in st.session_state:
        st.session_state['customer_data'] = pd.DataFrame({
            'date': pd.to_datetime(pd.date_range(start='2024-01-01', periods=100, freq='D').tolist() * 3),
            'product': ['Product A'] * 100 + ['Product B'] * 100 + ['Product C'] * 100,
            'sales': np.random.randint(5, 50, 300),
            'quantity': np.random.randint(1, 10, 300),
            'current_stock': np.nan
        })
        st.session_state['customer_data'].loc[st.session_state['customer_data']['product'] == 'Product A', 'current_stock'] = np.random.randint(1, 5, len(st.session_state['customer_data'][st.session_state['customer_data']['product'] == 'Product A']))
        st.session_state['customer_data'].loc[st.session_state['customer_data']['date'] == '2024-03-15', 'sales'] = 200
        st.session_state['customer_data'].loc[st.session_state['customer_data']['date'] == '2024-03-16', 'sales'] = 5
        st.session_state['customer_data'].loc[st.session_state['customer_data']['product'] == 'Product C', 'sales'] = np.random.randint(1, 3, len(st.session_state['customer_data'][st.session_state['customer_data']['product'] == 'Product C']))
        
        if 'product_current_stock_df' not in st.session_state:
            simulated_stock_data = []
            for product_name in st.session_state['customer_data']['product'].unique():
                last_stock = st.session_state['customer_data'].loc[st.session_state['customer_data']['product'] == product_name, 'current_stock'].dropna().iloc[-1] if not st.session_state['customer_data'].loc[st.session_state['customer_data']['product'] == product_name, 'current_stock'].dropna().empty else np.nan
                
                if pd.isna(last_stock):
                    daily_qty_sold = st.session_state['customer_data'].loc[st.session_state['customer_data']['product'] == product_name].groupby('date')['quantity'].sum().mean()
                    inferred_stock = max(0, daily_qty_sold * np.random.randint(3, 10))
                    simulated_stock_data.append({'product': product_name, 'current_stock': inferred_stock})
                else:
                    simulated_stock_data.append({'product': product_name, 'current_stock': last_stock})
            
            st.session_state['product_current_stock_df'] = pd.DataFrame(simulated_stock_data)
            st.session_state['product_current_stock_df'].fillna(0, inplace=True)
            st.session_state['product_current_stock_df'].loc[st.session_state['product_current_stock_df']['product'] == 'Product C', 'current_stock'] = 15
            st.session_state['product_current_stock_df'].loc[st.session_state['product_current_stock_df']['product'] == 'Product A', 'current_stock'] = 3

    render()