"""
Date: 2025-06-07 (or the date you complete it)
Author: Your Name / Your Team Name
Purpose:
    This module provides an "Insights Dashboard" for the InsightHub application.
    It analyzes uploaded store data (sales, products, inventory, etc.) to
    automatically generate actionable insights and recommendations for store owners.
    Key functionalities include:
    - Auto-detection of relevant columns (e.g., date, sales, product, quantity, profit).
    - Identification of sales trends (weekly, monthly changes).
    - Analysis of product performance (top/low performers, low-profit items).
    - Discovery of customer timing patterns (peak hours, weekend vs. weekday sales).
    - Generation of inventory optimization recommendations (fast/slow movers).
    - Detection of seasonal opportunities and sales anomalies.
    - Interactive Q&A to quickly access key insights.
Features:
    - Dynamic Insight Generation: Automatically provides recommendations based on data.
    - Smart Column Detection: Flexibly adapts to various column names in uploaded files.
    - Actionable Advice: Each insight comes with a clear recommendation for the store owner.
    - User-Friendly Interface: Utilizes Streamlit's expanders, metrics, and interactive elements.
    - Robust Error Handling: Manages missing data or non-numeric columns gracefully.
    - Session State Integration: Seamlessly uses data uploaded on the main app.py page.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from textwrap import dedent

    
def render_insight_card(title, description, recommendation, priority, impact_val=None, type_str=None):
    """Renders a single insight card with consistent styling."""
    icon = "💡"
    if priority == 1:
        icon = "🚨" # Critical alert
    elif priority == 2:
        icon = "📈" # Trend/Opportunity
    
    st.markdown(f"#### {icon} {title}")
    st.write(dedent(f"""
        **What's Happening**: {description}
        **🎯 Why it Matters**: {recommendation}
    """))

    if impact_val is not None:
        st.caption(f"Impact Score: {impact_val:.1f} (Higher is more significant)")
    st.markdown("---")


# --- StoreInsights Class (Core Logic) ---

class StoreInsights:
    def __init__(self, df):
        self.df = df.copy() # Work on a copy to avoid modifying the original df in session_state
        self.insights = []
        self._detect_columns()
        
    def _detect_columns(self):
        """Auto-detect common column names with fuzzy matching and standardize."""
        # Prioritized list of common names for each column
        col_mapping = {
            'date': ['date', 'timestamp', 'transaction_date', 'order_date'],
            'sales': ['sales', 'sale_amount', 'amount', 'revenue'],
            'product': ['product', 'item', 'product_name', 'item_name', 'sku'],
            'category': ['category', 'product_category', 'item_category'], # Added category
            'profit': ['profit', 'margin', 'net_profit'],
            'quantity': ['qty', 'quantity', 'units_sold'],
            'customer_id': ['customer_id', 'cust_id', 'customer_name'] # Added customer_id
        }

        # Fuzzy matching and assignment
        for attr, possible_names in col_mapping.items():
            found_col = None
            for name in possible_names:
                if name in self.df.columns:
                    found_col = name
                    break # Found exact match
                # Simple fuzzy match (case-insensitive contains)
                for df_col in self.df.columns:
                    if name.lower() in df_col.lower():
                        found_col = df_col
                        break
                if found_col:
                    break
            setattr(self, f"{attr}_col", found_col)

        # Ensure numeric types for calculations
        for col_attr in ['sales_col', 'profit_col', 'quantity_col']:
            col_name = getattr(self, col_attr)
            if col_name and pd.api.types.is_numeric_dtype(self.df[col_name]):
                self.df[col_name] = pd.to_numeric(self.df[col_name], errors='coerce')
                self.df.dropna(subset=[col_name], inplace=True) # Drop rows where numeric conversion failed
            elif col_name:
                 st.warning(f"Column '{col_name}' detected but is not numeric. Skipping numeric insights for this column.")
                 setattr(self, col_attr, None) # Set to None if not numeric

        # Convert date column and extract time features
        if self.date_col:
            try:
                self.df[self.date_col] = pd.to_datetime(self.df[self.date_col])
                self.df = self.df.set_index(self.date_col).sort_index() # Set date as index for time series ops
                self.df['day_of_week'] = self.df.index.day_name()
                self.df['hour'] = self.df.index.hour
                self.df['month'] = self.df.index.month
                self.df['week_of_year'] = self.df.index.isocalendar().week.astype(int)
                self.df['year'] = self.df.index.year
            except Exception as e:
                st.warning(f"Date column '{self.date_col}' could not be parsed: {e}. Time-based insights may be limited.")
                self.date_col = None # Disable date-based insights

    def generate_all_insights(self):
        """Run all insight detection methods"""
        if self.date_col and self.sales_col:
            self._sales_trend_analysis()
        if self.product_col and self.sales_col:
            self._product_performance()
        if self.date_col and self.sales_col: # timing insights also need date/sales
            self._customer_timing_insights() 
        if self.product_col and self.quantity_col: # inventory needs product & quantity
            self._inventory_recommendations()
        
        self._seasonal_opportunities() # Doesn't strictly need data, just checks current month
        
        if self.date_col and self.sales_col:
            self._detect_anomalies() # Needs date and sales for time series analysis
        
        # Sort insights: Priority (1=highest), then Impact (higher impact first)
        self.insights.sort(key=lambda x: (x.get('priority', 99), -x.get('impact', 0)), reverse=False) # Lower priority number is higher priority
        return self.insights
    
    def _sales_trend_analysis(self):
        """Identify meaningful sales trends"""
        
        # Ensure we have enough data for comparisons
        if self.df.index.empty or len(self.df.index.unique(level=0)) < 14:
            return # Not enough data for meaningful weekly comparison

        # Weekly comparison
        latest_date = self.df.index.max()
        recent_week_df = self.df[self.df.index > latest_date - pd.Timedelta(days=7)]
        prev_week_df = self.df[(self.df.index <= latest_date - pd.Timedelta(days=7)) &
                               (self.df.index > latest_date - pd.Timedelta(days=14))]
        
        if not recent_week_df.empty and not prev_week_df.empty:
            recent_sales = recent_week_df[self.sales_col].sum()
            prev_sales = prev_week_df[self.sales_col].sum()
            
            if prev_sales > 0:
                change = (recent_sales - prev_sales) / prev_sales * 100
                if abs(change) > 10: # Threshold for "significant"
                    description_text = f"Sales changed by {abs(change):.1f}% in the last 7 days compared to the previous 7 days."
                    recommendation_text = ""
                    priority_val = 2 # Default to trend
                    if change > 0:
                        recommendation_text = "Capitalize on this positive trend! Consider increasing staff or promoting popular items."
                    else:
                        recommendation_text = "Investigate reasons for the dip (e.g., promotions, competition, stock issues). Consider targeted marketing."
                        priority_val = 1 # Higher priority for negative trends
                    
                    self.insights.append({
                        "title": f"Sales {('Surge' if change > 0 else 'Dip')} Detected",
                        "description": description_text,
                        "recommendation": recommendation_text,
                        "priority": priority_val,
                        "impact": abs(change),
                        "type": "trend"
                    })
            else: # If previous week had zero sales, but recent week has sales
                if recent_sales > 0:
                     self.insights.append({
                        "title": "Sales Activity Initiated",
                        "description": "Sales have started in the last week, whereas the previous week had none.",
                        "recommendation": "Great start! Keep monitoring trends and ensure stock availability.",
                        "priority": 3,
                        "impact": recent_sales,
                        "type": "trend"
                    })
        
        # Month-over-month comparison (simple approach)
        if self.date_col:
            # Get data for the last two full months available in the dataset
            current_month_num = self.df.index.max().month
            current_year_num = self.df.index.max().year

            last_month_num = current_month_num - 1
            last_month_year = current_year_num
            if last_month_num == 0: # If current month is January, last month is December of previous year
                last_month_num = 12
                last_month_year -= 1

            current_month_sales = self.df[(self.df.index.month == current_month_num) & 
                                        (self.df.index.year == current_year_num)][self.sales_col].sum()
            last_month_sales = self.df[(self.df.index.month == last_month_num) & 
                                    (self.df.index.year == last_month_year)][self.sales_col].sum()
            
            if last_month_sales > 0:
                change = (current_month_sales - last_month_sales) / last_month_sales * 100
                if abs(change) > 15: # Threshold for "significant"
                    self.insights.append({
                        "title": "Monthly Sales Shift",
                        "description": f"Sales are {'up' if change > 0 else 'down'} by {abs(change):.1f}% compared to the previous month.",
                        "recommendation": "Analyze your monthly marketing efforts, product launches, or external factors that influenced this change.",
                        "priority": 3,
                        "impact": abs(change),
                        "type": "trend"
                    })
    
    def _product_performance(self):
        """Analyze product sales and profitability"""
        product_sales = self.df.groupby(self.product_col)[self.sales_col].sum().sort_values(ascending=False)
        
        if product_sales.empty:
            return

        top_products = product_sales.head(3)
        bottom_products = product_sales.tail(3)
        
        for product, sales in top_products.items():
            self.insights.append({
                "title": f"🚀 Top Performer: {product}",
                "description": f"This product generated **₹{sales:,.0f}** in sales, accounting for {sales/product_sales.sum()*100:.1f}% of your total revenue.",
                "recommendation": "Ensure this product is always in stock and prominently displayed. Consider upsell opportunities.",
                "priority": 3,
                "impact": sales/product_sales.sum()*100,
                "type": "product"
            })
            
        # Only add bottom products if they actually exist and have very low sales
        if len(product_sales) > 3 and bottom_products.sum() < product_sales.sum() * 0.05: # Only if they are a small % of total
            for product, sales in bottom_products.items():
                self.insights.append({
                    "title": f"📉 Low Performer: {product}",
                    "description": f"This product only brought in **₹{sales:,.0f}** in sales, which is just {sales/product_sales.sum()*100:.1f}% of total.",
                    "recommendation": "Consider bundling with popular items, offering promotional pricing, or phasing out if it doesn't align with store strategy.",
                    "priority": 2,
                    "impact": 100 - sales/product_sales.sum()*100, # Higher impact for worse performance
                    "type": "product"
                })
        
        # Profitability analysis
        if self.profit_col:
            product_profit = self.df.groupby(self.product_col)[self.profit_col].sum()
            if not product_profit.empty:
                low_profit_items = product_profit.nsmallest(3)
                
                # Filter out items with zero or negative profit if they dominate the low profit list
                meaningful_low_profit = low_profit_items[low_profit_items < product_profit.mean() * 0.1] # Significantly lower than average profit

                if not meaningful_low_profit.empty:
                    for product, profit in meaningful_low_profit.items():
                        self.insights.append({
                            "title": f"💸 Low Profit Item: {product}",
                            "description": f"This product generated only **₹{profit:,.0f}** in profit, indicating a very thin margin or even a loss.",
                            "recommendation": "Review supplier costs, adjust pricing, or consider if this item is necessary for customer footfall.",
                            "priority": 1, # High priority for low profit
                            "impact": abs(profit)/product_profit.sum()*100, # Impact based on how much it's pulling down profit
                            "type": "profit"
                        })
    
    def _customer_timing_insights(self):
        """Identify patterns in customer behavior timing"""
        if 'day_of_week' not in self.df.columns or 'hour' not in self.df.columns or not self.sales_col:
            return
            
        # Weekend vs weekday analysis
        # Using mean per transaction or per day might be more robust than sum
        sales_by_day_type = self.df.groupby(self.df.index.dayofweek.isin([5,6]))[self.sales_col].sum()
        
        if len(sales_by_day_type) == 2: # Check if both weekday and weekend sales exist
            weekend_sales = sales_by_day_type.get(True, 0) # True for weekend
            weekday_sales = sales_by_day_type.get(False, 0) # False for weekday

            if weekday_sales > 0 and weekend_sales > weekday_sales * 1.2: # 20% higher
                self.insights.append({
                    "title": "Weekend Sales Surge",
                    "description": f"Your weekend sales are significantly higher ({weekend_sales/weekday_sales:.1f}x) than weekday sales.",
                    "recommendation": "Optimize staff scheduling for weekends and run exclusive weekend promotions to maximize this peak.",
                    "priority": 2,
                    "impact": (weekend_sales - weekday_sales)/weekday_sales*100,
                    "type": "timing"
                })
            elif weekend_sales < weekday_sales * 0.8: # 20% lower
                 self.insights.append({
                    "title": "Weekend Sales Lag",
                    "description": f"Your weekend sales are lower ({weekend_sales/weekday_sales:.1f}x) than weekday sales, indicating a missed opportunity.",
                    "recommendation": "Consider special weekend offers, events, or extended hours to attract more customers.",
                    "priority": 2,
                    "impact": abs((weekend_sales - weekday_sales)/weekday_sales*100),
                    "type": "timing"
                })
            
        # Peak hours analysis
        hourly_sales = self.df.groupby('hour')[self.sales_col].sum()
        if not hourly_sales.empty:
            peak_hour = hourly_sales.idxmax()
            peak_sales_share = hourly_sales.max()/hourly_sales.sum()*100 if hourly_sales.sum() > 0 else 0
            
            if peak_sales_share > 20: # If one hour accounts for more than 20% of sales
                self.insights.append({
                    "title": "Peak Sales Hour Identified",
                    "description": f"The highest sales activity occurs between **{peak_hour}:00 and {peak_hour+1}:00**, accounting for {peak_sales_share:.1f}% of daily sales.",
                    "recommendation": "Ensure adequate staffing and smooth checkout during this period. Consider cross-selling strategies.",
                    "priority": 3,
                    "impact": peak_sales_share,
                    "type": "timing"
                })
        
    def _inventory_recommendations(self):
        """Generate inventory optimization suggestions"""
        if not self.product_col or not self.quantity_col:
            return
            
        # Calculate total quantity sold per product
        product_turnover = self.df.groupby(self.product_col)[self.quantity_col].sum().sort_values(ascending=False)
        
        if product_turnover.empty:
            return

        fast_movers = product_turnover.head(3).index.tolist()
        slow_movers = product_turnover.tail(3).index.tolist() # These are the truly slowest
        
        if fast_movers:
            self.insights.append({
                "title": "⚡️ High Demand Items",
                "description": f"Your fastest selling items (by quantity) include: {', '.join(fast_movers)}.",
                "recommendation": "Ensure you have adequate stock levels for these items to avoid missed sales. Consider ordering in bulk for better margins.",
                "priority": 2,
                "impact": product_turnover[fast_movers].sum()/product_turnover.sum()*100,
                "type": "inventory"
            })
        
        if len(product_turnover) > 3 and slow_movers: # Only if there are enough items to distinguish
            self.insights.append({
                "title": "🐢 Slow-Moving Stock Alert",
                "description": f"Items moving very slowly are: {', '.join(slow_movers)}. They might be tying up capital.",
                "recommendation": "Consider promotional bundles, prominent displays, or even markdowns to clear this inventory.",
                "priority": 1,
                "impact": 100 - product_turnover[slow_movers].sum()/product_turnover.sum()*100, # Higher impact for worse performance
                "type": "inventory"
            })
    
    def _seasonal_opportunities(self):
        """Identify seasonal trends and opportunities based on current month (hardcoded for now)"""
        # This will be more powerful if you have year-over-year data in the future
        current_month = datetime.now().month # Current month of the year
        
        seasonal_insights_data = {
            1: { # January
                "title": "Republic Day Opportunity",
                "description": "January typically sees increased spending around Republic Day (Jan 26th) and a post-holiday dip. Focus on necessities.",
                "recommendation": "Offer patriotic-themed bundles or essential grocery discounts.",
                "priority": 2, "impact": 20
            },
            3: { # March
                "title": "Holi Festival Preparations",
                "description": "March often brings increased sales for festive items, colors, and sweets around Holi.",
                "recommendation": "Stock up on festive essentials, color sets, and ingredients for traditional sweets.",
                "priority": 2, "impact": 25
            },
            4: { # April
                "title": "Summer Essentials Demand",
                "description": "Temperatures rise in April, increasing demand for cooling products, beverages, and lighter foods.",
                "recommendation": "Ensure adequate stock of cold drinks, ice creams, sun care products, and summer fruits.",
                "priority": 2, "impact": 30
            },
            7: { # July
                "title": "Monsoon Preparedness",
                "description": "July brings monsoon season, impacting outdoor activities but increasing demand for certain indoor essentials.",
                "recommendation": "Stock up on umbrellas, raincoats, instant hot beverages, and comfort foods.",
                "priority": 2, "impact": 15
            },
            8: { # August
                "title": "Independence Day & Festivals",
                "description": "August often has Independence Day (Aug 15th) and various regional festivals like Raksha Bandhan.",
                "recommendation": "Plan for patriotic merchandise, gift sets, and festive food items.",
                "priority": 2, "impact": 20
            },
            10: { # October
                "title": "Diwali & Festive Season Boom",
                "description": "October marks the beginning of the major festive season with Diwali, leading to significant consumer spending.",
                "recommendation": "Start festive displays, gift bundles, sweets, and household decor early to capture demand.",
                "priority": 1, "impact": 40 # High priority, high impact
            },
            12: { # December
                "title": "Year-End Holiday Rush",
                "description": "December brings Christmas and New Year's Eve, driving demand for party supplies, gifts, and seasonal treats.",
                "recommendation": "Focus on holiday-themed products, party essentials, and gift options.",
                "priority": 2, "impact": 35
            }
        }
        
        if current_month in seasonal_insights_data:
            self.insights.append({
                **seasonal_insights_data[current_month],
                "type": "seasonal"
            })
    
    def _detect_anomalies(self):
        """Identify unusual patterns in sales that need investigation"""
        daily_sales = self.df[self.sales_col].resample('D').sum()
        
        if len(daily_sales) < 7: # Need at least a week of data for meaningful anomaly detection
            return
            
        # Using a simple rolling mean and std for anomaly detection
        # You could use more sophisticated methods (e.g., IQR, z-score on residuals)
        rolling_mean = daily_sales.rolling(window=7).mean()
        rolling_std = daily_sales.rolling(window=7).std()
        
        # Calculate thresholds
        upper_bound = rolling_mean + 2 * rolling_std # 2 standard deviations above mean
        lower_bound = rolling_mean - 2 * rolling_std # 2 standard deviations below mean
        
        # Identify points outside the bounds
        anomalies = daily_sales[(daily_sales > upper_bound) | (daily_sales < lower_bound)]
        
        for date, sales in anomalies.items():
            is_high = sales > rolling_mean[date]
            self.insights.append({
                "title": f"🚨 Unusual Sales Day Detected: {date.strftime('%b %d, %Y')}",
                "description": f"Sales on this day were **₹{sales:,.0f}**, which is unusually {'high' if is_high else 'low'} compared to recent average (expected around ₹{rolling_mean[date]:,.0f}).",
                "recommendation": f"Investigate: Was there a special event, promotion, holiday, or perhaps a data entry error? {'Capitalize on the reason for high sales' if is_high else 'Address the cause for low sales'}.",
                "priority": 1, # Highest priority
                "impact": abs(sales - rolling_mean[date]), # Impact based on deviation from mean
                "type": "anomaly"
            })

# --- Streamlit UI Rendering ---

def render_insights_page(insights):
    """Render insights in Streamlit with interactive elements and clearer structure."""
    st.subheader("Actionable Insights & Recommendations")
    
    st.markdown("---")
    
    # 1. Priority Recommendations (Critical Warnings)
    priority_insights = [i for i in insights if i.get('priority', 99) == 1]
    if priority_insights:
        st.header("🚨 Urgent Attention Required!")
        for insight in priority_insights:
            st.warning(f"**{insight['title']}:** {insight['description']}")
            st.info(f"**📌 Action**: {insight['recommendation']}")
            st.markdown("---")
    
    # 2. Key Performance Indicators / Overall Trends
    st.header("📈 Key Performance Insights")
    trend_insights = [i for i in insights if i.get('type') == 'trend' and i.get('priority', 99) > 1]
    
    if trend_insights:
        st.subheader("Sales Trends at a Glance")
        cols = st.columns(len(trend_insights[:3]) if trend_insights else 1) # Display up to 3 metrics
        for i, insight in enumerate(trend_insights[:3]):
            if i < len(cols): # Ensure we don't go out of bounds if fewer insights than columns
                with cols[i]:
                    value_str = insight['description'].split('by')[-1].strip() # Extract value part
                    delta_value = f"{'↑' if 'up' in insight['description'] else '↓'} {abs(insight['impact']):.1f}%" if 'change' in insight['description'].lower() else None
                    st.metric(insight['title'], value=value_str, delta=delta_value)
                    st.caption(insight['recommendation'])
        st.markdown("---")

    # 3. Product & Inventory Specific Insights
    st.header("📦 Product & Stock Insights")
    product_and_inventory_insights = [
        i for i in insights if i.get('type') in ['product', 'profit', 'inventory'] and i.get('priority', 99) > 1
    ]
    if product_and_inventory_insights:
        for insight in product_and_inventory_insights:
            with st.expander(f"{'🚀' if 'Top Performer' in insight['title'] else '📉'} {insight['title']}"):
                st.write(insight['description'])
                st.info(f"**📌 Action**: {insight['recommendation']}")
        st.markdown("---")
    
    # 4. Timing & Seasonal Opportunities
    st.header("⏰ Timing & Seasonal Opportunities")
    timing_and_seasonal_insights = [
        i for i in insights if i.get('type') in ['timing', 'seasonal'] and i.get('priority', 99) > 1
    ]
    if timing_and_seasonal_insights:
        for insight in timing_and_seasonal_insights:
            with st.expander(f"{'☀️' if insight.get('type') == 'seasonal' else '⏱️'} {insight['title']}"):
                st.write(insight['description'])
                st.info(f"**📌 Action**: {insight['recommendation']}")
        st.markdown("---")

    # Interactive Q&A (Revisited)
    st.subheader("🤔 Ask InsightHub")
    st.write("Quickly find answers to common questions about your data.")
    
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        question = st.selectbox("Select a question or type your own", [
            "What are my top-selling products?",
            "What are my lowest-profit items?",
            "When are my peak sales hours?",
            "Are there any sales anomalies recently?",
            "Which items are moving slowly?",
            "Are there any current seasonal opportunities?"
        ], key="insight_question_select")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True) # Spacer for alignment
        if st.button("Get Answer", use_container_width=True, key="get_answer_btn"):
            answer_found = False
            if "top-selling products" in question:
                product_insights = [i for i in insights if i['type'] == 'product' and 'Top Performer' in i['title']]
                if product_insights:
                    st.success(f"**Top Products:** {product_insights[0]['description']} {product_insights[0]['recommendation']}")
                    answer_found = True
            elif "lowest-profit items" in question:
                profit_insights = [i for i in insights if i['type'] == 'profit' and 'Low Profit' in i['title']]
                if profit_insights:
                    st.warning(f"**Low Profit Items:** {profit_insights[0]['description']} {profit_insights[0]['recommendation']}")
                    answer_found = True
            elif "peak sales hours" in question:
                timing_insights = [i for i in insights if i['type'] == 'timing' and 'Peak Sales Hour' in i['title']]
                if timing_insights:
                    st.success(f"**Peak Hours:** {timing_insights[0]['description']} {timing_insights[0]['recommendation']}")
                    answer_found = True
            elif "sales anomalies" in question:
                anomaly_insights = [i for i in insights if i['type'] == 'anomaly']
                if anomaly_insights:
                    st.warning(f"**Anomalies:** {anomaly_insights[0]['description']} {anomaly_insights[0]['recommendation']}")
                    answer_found = True
            elif "moving slowly" in question:
                inventory_insights = [i for i in insights if i['type'] == 'inventory' and 'Slow-Moving' in i['title']]
                if inventory_insights:
                    st.warning(f"**Slow Movers:** {inventory_insights[0]['description']} {inventory_insights[0]['recommendation']}")
                    answer_found = True
            elif "seasonal opportunities" in question:
                seasonal_insights_filtered = [i for i in insights if i['type'] == 'seasonal']
                if seasonal_insights_filtered:
                    st.info(f"**Seasonal Tip:** {seasonal_insights_filtered[0]['description']} {seasonal_insights_filtered[0]['recommendation']}")
                    answer_found = True
            
            if not answer_found:
                st.info("No specific insight found for that question in the current data. Try uploading more comprehensive data!")

# --- Main Page Entry Point ---

def render():

    # Check if customer_data is in session_state (uploaded)
    if 'customer_data' in st.session_state and st.session_state['customer_data'] is not None:
        df = st.session_state['customer_data']
        
        # Ensure df is not empty after potential filtering in _detect_columns
        if df.empty:
            st.warning("The uploaded data is empty or became empty after initial processing. Please check your file.")
            return

        st.header("Unlocking Your Store's Hidden Potential! 💡")
        st.markdown(dedent("""
            Welcome to your **Insights Dashboard!** We've crunched your numbers to reveal
            actionable opportunities and alert you to potential issues.
            Dive in to discover trends, optimize stock, and boost your profits.
        """))
        st.markdown("---")

        with st.spinner("Analyzing your data... This might take a moment!"):
            analyzer = StoreInsights(df)
            insights = analyzer.generate_all_insights()
        
        if insights:
             render_insights_page(insights)
        else:
            st.info("No specific insights could be generated from your data at this time. Ensure your file contains 'date', 'sales', 'product', 'quantity', or 'profit' columns for richer analysis.")
    else:
        st.warning("No data uploaded yet. Please go to the **'Upload'** page to upload your sales and inventory file to unlock these insights!")
        # Optional: Add a button to navigate back or a link
        # if st.button("Go to Upload Page"):
        #    st.session_state.app_state = AppState.HOME_PAGE # Assuming AppState is defined
        #    st.experimental_rerun()

# --- For standalone testing (if you run this file directly) ---
if __name__ == "__main__":
    # Simulate st.session_state for testing this module directly
    if 'customer_data' not in st.session_state:
        st.session_state['customer_data'] = None

    st.sidebar.title("Test Data Options")
    use_sample = st.sidebar.checkbox("Use sample data for testing")

    if use_sample:
        dates = pd.date_range(end=datetime.today(), periods=90) # More data for better analysis
        sample_products = [
            "Milk", "Bread", "Eggs", "Rice (Basmati)", "Cooking Oil", 
            "Shampoo (Herbal)", "Soap (Sandalwood)", "Biscuits (Cream)", "Chips (Potato)", "Soda (Cola)",
            "Noodles (Instant)", "Detergent Powder", "Toothpaste", "Tea Leaves", "Coffee Powder"
        ]
        sample_categories = [
            "Dairy", "Bakery", "Staples", "Personal Care", "Snacks", "Beverages", "Instant Foods"
        ]
        
        # Create a more realistic sample data structure
        data = {
            'Date': np.random.choice(dates, 2000), # More rows
            'Product': np.random.choice(sample_products, 2000),
            'Category': np.random.choice(sample_categories, 2000), # Include category
            'Sales_Amount': np.random.normal(150, 70, 2000).clip(20, 500).astype(float), # Sales can be float
            'Quantity': np.random.randint(1, 6, 2000),
            'Profit': np.random.normal(30, 15, 2000).clip(5, 100).astype(float), # Profit as float
            'CustomerID': np.random.randint(1000, 2000, 2000) # Include CustomerID
        }
        
        df = pd.DataFrame(data)
        
        # Simulate weekend boost
        df['Sales_Amount'] = df.apply(lambda row: row['Sales_Amount'] * 1.5 if pd.to_datetime(row['Date']).weekday() in [5,6] else row['Sales_Amount'], axis=1)
        
        # Simulate one outlier day (very high sales)
        outlier_date = dates[np.random.randint(0, len(dates)-1)]
        df.loc[df['Date'] == outlier_date, 'Sales_Amount'] *= 4
        
        # Simulate a low-profit product
        df.loc[df['Product'] == "Soap (Sandalwood)", 'Profit'] = np.random.normal(5, 2, df[df['Product'] == "Soap (Sandalwood)"].shape[0]).clip(1, 10)


        st.session_state['customer_data'] = df
        st.sidebar.success("Sample data loaded into session_state.")
        
    if st.session_state['customer_data'] is not None:
        render()
    else:
        st.warning("No data to display. Please upload a file via the 'Upload' page or check 'Use sample data' in the sidebar if running this file directly.")