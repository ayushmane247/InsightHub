# modules/forecast.py (SHOPKEEPER EDITION v2.1)

# Date: 2025-06-12
# Author: Data Insights Team
# Purpose:
#     Shopkeeper-friendly sales forecasting and inventory planning dashboard with:
#     - Automatic festival date detection
#     - Enhanced mobile experience
#     - Visual progress indicators
#     - Error-resistant implementation
# Features:
#     - Festival impact visualization (automatic detection for IN)
#     - Responsive design with bigger touch targets
#     - Animated progress spinners and completion bars
#     - Conversational error messages with quick fixes
#     - Inventory emergency status visualization
#     - Exportable recommendations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import holidays
from streamlit.components.v1 import html
import warnings

# Import the ForecastHelper class with robust error handling
try:
    from utils.forecast_helper import ForecastHelper
except ImportError as e:
    st.error(f"""🚨 Critical Error: Missing ForecastHelper. 
            Please ensure 'utils/forecast_helper.py' exists with the ForecastHelper class.
            Error details: {e}""")
    st.stop()

# --- Mobile-First CSS with Festival Styling ---
st.markdown("""
<style>
/* Base mobile styles */
@media (max-width: 600px) {
    .stSelectbox, .stSlider, .stNumberInput {
        width: 100% !important;
    }
    .stDataFrame {
        font-size: 12px !important;
    }
    /* Bigger tap targets */
    .stButton>button {
        padding: 12px 24px !important;
    }
    /* Stack columns vertically */
    .stHorizontalBlock {
        flex-direction: column;
    }
}

/* Festival tags */
.festival-tag {
    border-radius: 12px;
    padding: 4px 8px;
    font-size: 12px;
    background-color: #FFD700;
    color: #000;
    margin-right: 5px;
}

/* Progress indicators */
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
.spinner {
    animation: spin 1s linear infinite;
    display: inline-block;
    font-size: 24px;
}
.progress-container {
    width: 100%;
    background-color: #f3f3f3;
    border-radius: 10px;
    margin: 10px 0;
}
.progress-bar {
    height: 20px;
    border-radius: 10px;
    background-color: #4CAF50;
    text-align: center;
    line-height: 20px;
    color: white;
}

/* Emergency stock status */
.stock-critical {
    background-color: #FFCCCB !important;
    font-weight: bold;
}
.stock-warning {
    background-color: #FFE4B5 !important;
}
.stock-safe {
    background-color: #90EE90 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def detect_festival_dates(country='IN', years=1):
    """Auto-detect upcoming festivals with robust error handling"""
    try:
        country_holidays = holidays.CountryHoliday(country, years=[datetime.now().year, datetime.now().year+1])
        upcoming = []
        for date, name in sorted(country_holidays.items()):
            if date >= datetime.now().date():
                upcoming.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'name': name,
                    'days_away': (pd.Timestamp(date) - pd.Timestamp(datetime.now().date())).days
                })
        return pd.DataFrame(upcoming).head(5)  # Return next 5 festivals
    except Exception as e:
        st.warning(f"Couldn't load festival dates: {str(e)}")
        return pd.DataFrame()

def spinning_wheel():
    """Custom spinner for long operations"""
    return html("""
    <div style="text-align:center; margin:20px 0;">
        <div class="spinner">🌀</div>
        <p>Crunching your numbers...</p>
    </div>
    """)

def progress_bar(percent, message=""):
    """Animated completion bar with message"""
    return html(f"""
    <div style="margin:20px 0;">
        <p>{message}</p>
        <div class="progress-container">
            <div class="progress-bar" style="width:{percent}%">{percent}%</div>
        </div>
    </div>
    """)

def get_forecast_model_func(helper_instance, model_name):
    """Returns the appropriate forecast method with friendly names"""
    model_map = {
        "Prophet (Best for trends)": helper_instance.prophet_forecast,
        "Exponential Smoothing (Simple & fast)": helper_instance.exp_smoothing_forecast,
        "ARIMA (Stats geek's choice)": helper_instance.arima_forecast
    }
    return model_map.get(model_name)

def validate_forecast_data(fd):
    """Validate forecast data structure and convert dates"""
    if not fd or 'historical' not in fd or 'forecast' not in fd:
        return False
    
    if not pd.api.types.is_datetime64_any_dtype(fd['historical']['ds']):
        fd['historical']['ds'] = pd.to_datetime(fd['historical']['ds'])
    if not pd.api.types.is_datetime64_any_dtype(fd['forecast']['ds']):
        fd['forecast']['ds'] = pd.to_datetime(fd['forecast']['ds'])
    return True

def plot_shopkeeper_forecast(historical, forecast, product_name):
    """Enhanced visualization with festival markers"""
    # Validate input data
    required_cols = {
        'historical': ['ds', 'y'],
        'forecast': ['ds', 'yhat']
    }
    
    # Check historical data
    if not all(col in historical.columns for col in required_cols['historical']):
        st.error("Historical data missing required columns")
        return go.Figure()
    
    # Check forecast data - use 'yhat' if available, otherwise 'y'
    forecast_cols = ['ds']
    if 'yhat' in forecast.columns:
        forecast_cols.append('yhat')
    elif 'y' in forecast.columns:
        forecast_cols.append('y')
    else:
        st.error("Forecast data missing required columns (need either 'yhat' or 'y')")
        return go.Figure()

    # Convert dates to datetime
    try:
        historical['ds'] = pd.to_datetime(historical['ds'])
        forecast['ds'] = pd.to_datetime(forecast['ds'])
    except Exception as e:
        st.error(f"Date conversion failed: {str(e)}")
        return go.Figure()

    fig = go.Figure()
    
    # Historical (Thick solid line)
    fig.add_trace(go.Scatter(
        x=historical['ds'], y=historical['y'],
        name='Past Sales',
        line=dict(color='#4B8BBE', width=4),
        hovertemplate="<b>%{x|%d %b}</b>: %{y} sold<extra></extra>"
    ))
    
    # Forecast (Dashed)
    y_col = 'yhat' if 'yhat' in forecast.columns else 'y'
    fig.add_trace(go.Scatter(
        x=forecast['ds'], y=forecast[y_col],
        name='Predicted',
        line=dict(color='#FFA500', width=4, dash='dot'),
        hovertemplate="<b>%{x|%d %b}</b>: %{y} predicted<extra></extra>"
    ))
    
    

    # Add festival markers
    festivals = detect_festival_dates()
    if not festivals.empty:
        for _, fest in festivals.iterrows():
            try:
                fest_date = pd.Timestamp(fest['date'])
                # Highlight a 7-day window around the festival
                fig.add_vrect(
                    x0=fest_date - pd.Timedelta(days=3),
                    x1=fest_date + pd.Timedelta(days=3),
                    fillcolor="red",
                    opacity=0.15,
                    layer="below",
                    line_width=0,
                    annotation_text=fest['name'],
                    annotation_position="top left"
                )
                # Add a dashed line on the exact festival date
                fig.add_vline(
                    x=fest_date,
                    line_width=2,
                    line_dash="dash",
                    line_color="red"
                )
            except Exception as e:
                st.warning(f"Couldn't add festival marker: {str(e)}")
                continue
# ...existing code...

    # Add trend indicators
    last_actual = historical['y'].iloc[-1]
    first_forecast = forecast[y_col].iloc[0]
    
    if first_forecast > last_actual * 1.2:
        fig.add_annotation(text="📈 UP!", xref="paper", x=0.9, yref="paper", y=0.9,
                        font=dict(size=20, color="green"))
    elif first_forecast < last_actual * 0.8:
        fig.add_annotation(text="👇 DOWN", xref="paper", x=0.9, yref="paper", y=0.9,
                        font=dict(size=20, color="red"))
    
    # Formatting
    fig.update_layout(
        title=f"<b>{product_name}</b><br>Will sales go up or down?",
        plot_bgcolor='#FFF9F0',
        hovermode="x unified",
        font=dict(family="Arial")
    )
    return fig

def generate_stock_status_panel(daily_sales, safety_stock):
    """Visual inventory status indicator"""
    stock_days = safety_stock / daily_sales if daily_sales > 0 else 0
    
    if stock_days < 3:
        status = "Critical (<3 days)"
        color = "#C50303"
    elif stock_days < 7:
        status = "Low (<1 week)"
        color = "#FFA500"
    else:
        status = "Safe"
        color = "#2ECC71"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=stock_days,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Stock Status (Days)"},
        gauge={
            'axis': {'range': [None, 14]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 3], 'color': "#FFCCCB"},
                {'range': [3, 7], 'color': "#FFE4B5"},
                {'range': [7, 14], 'color': "#D5F5E3"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': stock_days
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig, status

# --- Main Page ---
def render():
    # --- Header with Festival Alert ---
    st.header("🛍️ Your Personal Inventory Crystal Ball")
    st.markdown("""
    Predict future sales *before they happen* and never run out of stock again.  
    Perfect for busy store owners who hate guessing games!
    """)
    
    # Festival Alert Banner
    festivals = detect_festival_dates()
    if not festivals.empty:
        next_fest = festivals.iloc[0]
        st.markdown(f"""
        <div style="background-color:black; padding:10px; border-radius:5px; margin-bottom:15px;">
            🎉 <b>{next_fest['name']}</b> coming in {next_fest['days_away']} days! 
            <span style="font-size:0.9em">(Sales usually 2-3x during festivals)</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- Data Validation ---
    if 'customer_data' not in st.session_state:
        st.warning("""
        ⚠️ No data uploaded yet!  
        Go to the <b>📤 Upload page</b> and upload your sales file.
        """, unsafe_allow_html=True)
        return

    df = st.session_state['customer_data'].copy()
    
    # --- Column Detection with Fuzzy Matching ---
    date_col = next((c for c in df.columns if 'date' in c.lower()), None)
    sales_col = next((c for c in df.columns if 'sale' in c.lower() or 'amount' in c.lower() or 'revenue' in c.lower()), None)
    product_col = next((c for c in df.columns if 'product' in c.lower() or 'item' in c.lower() or 'sku' in c.lower()), None)
    quantity_col = next((c for c in df.columns if 'qty' in c.lower() or 'quantity' in c.lower()), None)
    
    if not date_col or not sales_col:
        st.error("""
        ❌ Missing essential columns!  
        We need at least:  
        - A <b>date column</b> (like 'order_date')  
        - A <b>sales column</b> (like 'sale_amount')  
        """, unsafe_allow_html=True)
        return
    
    # --- Data Preparation ---
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce')
        df = df.dropna(subset=[date_col, sales_col])
        
        if df.empty:
            st.error("⚠️ No valid data after processing dates and sales values!")
            return
            
    except Exception as e:
        st.error(f"""
        ❌ Data processing error!  
        Couldn't convert:  
        - Dates: {date_col}  
        - Sales: {sales_col}  
        Error: {str(e)}  
        """)
        return
    
    # --- Forecasting Section ---
    st.subheader("🔮 Predict Future Sales")
    
    # Product selection
    product_options = ["All Products"] 
    if product_col:
        product_options.extend(df[product_col].unique().tolist())
    
    selected_product = st.selectbox(
        "Which product to forecast?",
        product_options,
        help="Forecast per product or all items together"
    )
    
    # Model selection with personality
    model_choice = st.selectbox(
        "🤖 Choose Your Forecasting Assistant",
        ["Prophet (Best for trends)", "Exponential Smoothing (Simple & fast)", "ARIMA (Stats geek's choice)"],
        index=0,
        help="Not sure? Start with Prophet → works for 90% of shops!"
    )
    
    forecast_horizon = st.slider(
        "How many days ahead?",
        min_value=7, max_value=90, value=30,
        help="7-30 days works best for most shops"
    )
    
    if st.button(f"🔮 Predict {selected_product} Sales", type="primary"):
        with st.status("🧮 Calculating... Brew some chai while we work!", expanded=True):
            # Show initial progress
            progress_placeholder = st.empty()
            progress_placeholder.markdown("""
            <div style="text-align:center">
                <div class="spinner">🌀</div>
                <p>Step 1/3: Preparing your data...</p>
                <div class="progress-container">
                    <div class="progress-bar" style="width:20%">20%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            helper = ForecastHelper()
            forecast_func = get_forecast_model_func(helper, model_choice)
            
            try:
                # Filter data
                if selected_product == "All Products":
                    df_filtered = df.groupby(date_col)[sales_col].sum().reset_index()
                else:
                    df_filtered = df[df[product_col] == selected_product].groupby(date_col)[sales_col].sum().reset_index()
                
                # Update progress
                progress_placeholder.markdown("""
                <div style="text-align:center">
                    <div class="spinner">🌀</div>
                    <p>Step 2/3: Training the model (this takes 10-15 seconds)...</p>
                    <div class="progress-container">
                        <div class="progress-bar" style="width:60%">60%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Generate forecast
                forecast_df, model_fit_info = forecast_func(
                    df_filtered.rename(columns={date_col: 'ds', sales_col: 'y'}),
                    forecast_days=forecast_horizon
                )
                
                # Final progress update
                progress_placeholder.markdown("""
                <div style="text-align:center">
                    <div class="spinner">🌀</div>
                    <p>Step 3/3: Making it shopkeeper-ready...</p>
                    <div class="progress-container">
                        <div class="progress-bar" style="width:90%">90%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Ensure historical and forecast have 'ds' and 'y' columns for plotting
                historical = df_filtered.rename(columns={date_col: 'ds', sales_col: 'y'})
                forecast = forecast_df.copy()
                if 'date' in forecast.columns:
                    forecast = forecast.rename(columns={'date': 'ds'})
                if 'yhat' not in forecast.columns and 'y' in forecast.columns:
                    forecast['yhat'] = forecast['y']

                st.session_state.forecast_data = {
                    'historical': historical,
                    'forecast': forecast,
                    'product': selected_product,
                    'model_info': model_fit_info
                }
                st.toast("Forecast ready!", icon="✅")
                
            except Exception as e:
                st.error(f"""
                🚧 Oops! The forecast engine coughed up a hairball.  
                **Quick fix:** Try reducing forecast days or pick another model.  
                *Tech details: {str(e)}*
                """)
                st.session_state.forecast_data = None

    # --- Results Display ---
    if 'forecast_data' in st.session_state and st.session_state.forecast_data:
        fd = st.session_state.forecast_data
        
        # Validate forecast data before use
        if not validate_forecast_data(fd):
            st.error("Invalid forecast data structure")
            return
        
        # Mobile-friendly tabs
        tab1, tab2, tab3 = st.tabs(["📈 Forecast", "📦 Inventory", "🎯 Action Plan"])
        
        with tab1:
            st.plotly_chart(
                plot_shopkeeper_forecast(fd['historical'], fd['forecast'], fd['product']),
                use_container_width=True
            )
            
            # Festival impact note
            st.markdown("""
            <div style="background-color:gray; padding:10px; border-radius:5px; margin-top:10px;">
                <b>💡 Festival Tip:</b> Red dashed lines show upcoming festivals when sales often spike.
                Stock up 3-4 days before these dates!
            </div>
            """, unsafe_allow_html=True)
            
            # Model components if available
            if fd.get('model_info'):
                try:
                    st.plotly_chart(fd['model_info'].plot_components(fd['forecast']), 
                                use_container_width=True)
                except:
                    pass
        
        with tab2:
            # Calculate inventory metrics
            daily_sales = fd['historical'].groupby('ds')['y'].mean().iloc[-30:].mean()
            safety_stock = daily_sales * 1.5  # Simple calculation
            
            # Stock Status Gauge
            gauge_fig, stock_status = generate_stock_status_panel(daily_sales, safety_stock)
            st.plotly_chart(gauge_fig, use_container_width=True)
            
            # Actionable recommendations
            rec_data = [{
                'Product': fd['product'],
                'Daily Sales': f"{daily_sales:.1f}",
                'Safety Stock': f"{safety_stock:.0f}",
                'Reorder At': f"{safety_stock * 1.2:.0f}",
                'Order Now': f"{safety_stock * 2:.0f}",
                'Status': stock_status
            }]
            
            # Apply status-based styling
            def style_status(val):
                if 'Critical' in val:
                    return 'background-color: #FFCCCB; font-weight: bold;'
                elif 'Low' in val:
                    return 'background-color: #FFE4B5;'
                return 'background-color: #D5F5E3;'
            
            st.dataframe(
                pd.DataFrame(rec_data).style.applymap(style_status, subset=['Status']),
                use_container_width=True
            )
        
        with tab3:
            st.subheader("📋 Recommended Actions")
            
            if 'Critical' in stock_status:
                st.markdown("""
                ⚠️ **Urgent Action Needed**  
                - Place order immediately for at least **{:.0f} units**  
                - Contact supplier about rush delivery  
                - Consider temporary price increase to manage demand  
                """.format(float(rec_data[0]['Order Now'])))
            else:
                st.markdown("""
                ✅ **Stock Levels OK**  
                - Next order of **{:.0f} units** recommended in {} days  
                - Check festival dates in forecast tab  
                """.format(float(rec_data[0]['Order Now']), 
                (float(rec_data[0]['Safety Stock']) - float(rec_data[0]['Reorder At'])) / daily_sales))
            
            # Export options
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📥 Save as Excel",
                    pd.DataFrame(rec_data).to_csv(index=False),
                    "inventory_recommendations.csv",
                    help="Share with your supplier"
                )
            with col2:
                if st.button("📲 Text to Supplier", help="Coming soon!"):
                    st.toast("Feature coming next month!", icon="🚀")

# --- Run ---
if __name__ == "__main__":
    # Local testing setup
    if 'customer_data' not in st.session_state:
        # Generate realistic dummy data
        dates = pd.date_range(start='2024-01-01', periods=180).tolist()
        products = ['Masala Chai', 'Biscuits', 'Toothpaste', 'Soap', 'Shampoo']
        
        data = {
            'order_date': dates * len(products),
            'product_name': sorted(products * len(dates)),
            'sale_amount': np.random.randint(5, 50, len(dates)*len(products)) * 
                        [1.2 if 'Masala' in p else 1.0 for p in sorted(products * len(dates))],
            'quantity': np.random.randint(1, 10, len(dates)*len(products))
        }
        
        # Add festival spikes
        diwali = pd.to_datetime('2024-11-12')
        for i, row in enumerate(data['order_date']):
            if abs((row - diwali).days) < 5:
                data['sale_amount'][i] *= 3
                data['quantity'][i] *= 2
        
        st.session_state['customer_data'] = pd.DataFrame(data)
        st.warning("Running with demo data - upload your own for accurate forecasts!")
    
    render()