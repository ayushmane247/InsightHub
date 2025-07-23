# modules/alert_helper.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import zscore # For anomaly detection
# You'd typically put your Twilio/SMTP imports here if you were sending real alerts
# from twilio.rest import Client
# import smtplib
# from email.mime.text import MIMEText

class AlertHelper:
    """
    A helper class to encapsulate all alert generation and related logic for InsightHub.
    This includes inventory status, sales anomaly detection, and future notification methods.
    """
    def __init__(self, df):
        """
        Initializes the AlertHelper with the processed customer data.

        Args:
            df (pd.DataFrame): The cleaned and processed customer data DataFrame.
                               Must contain 'date', 'product', 'sales', 'quantity', 'current_stock' columns.
        """
        self.df = df.copy()
        
        # Ensure essential columns are present and correctly typed
        self._validate_and_prepare_data()

    def _validate_and_prepare_data(self):
        """Internal method to ensure data integrity for alert calculations."""
        # Ensure date column is datetime and sorted
        if 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')
            self.df.dropna(subset=['date'], inplace=True)
            self.df.sort_values(by='date', inplace=True)
        else:
            raise ValueError("DataFrame must contain a 'date' column.")

        # Ensure 'sales' column is numeric, fill NaNs as 0
        if 'sales' in self.df.columns:
            self.df['sales'] = pd.to_numeric(self.df['sales'], errors='coerce').fillna(0)
        elif 'quantity' in self.df.columns: # Fallback for sales if only quantity is available
            self.df['sales'] = pd.to_numeric(self.df['quantity'], errors='coerce').fillna(0)
        else:
            raise ValueError("DataFrame must contain 'sales' or 'quantity' column.")

        # Ensure 'quantity' column is numeric, fill NaNs as 0
        if 'quantity' not in self.df.columns:
            self.df['quantity'] = self.df['sales'] # Use sales as quantity if missing
        else:
            self.df['quantity'] = pd.to_numeric(self.df['quantity'], errors='coerce').fillna(0)

        # Ensure 'product' column exists, default to 'All Products' if missing
        if 'product' not in self.df.columns:
            self.df['product'] = 'All Products'
        else:
            self.df['product'] = self.df['product'].astype(str) # Ensure it's string type

        # Handle 'current_stock' (very important for inventory alerts)
        # This assumes 'current_stock' was handled in upload.py to be a numeric column
        # and likely represents the *latest* known stock for each product.
        if 'current_stock' not in self.df.columns:
             # If current_stock column was not explicitly mapped, or is all NaN,
             # we need a fallback or simulation for products
             # This means the upload.py's logic to create 'current_stock' needs to be robust.
             # For now, we'll ensure it's numeric and fill NaNs if they exist after the upload process.
            self.df['current_stock'] = np.nan # Ensure column exists if not present

        self.df['current_stock'] = pd.to_numeric(self.df['current_stock'], errors='coerce')
        # We will infer product-specific current stock in the calculate_inventory_status if needed.


    def calculate_inventory_status(self, product_current_stock_df, avg_daily_sales_data, critical_stock_days):
        """
        Calculates inventory status and stockout risk for products.
        
        Args:
            product_current_stock_df (pd.DataFrame): DataFrame with 'product' and 'current_stock'.
                                                     This should contain the LATEST known stock levels.
            avg_daily_sales_data (pd.DataFrame): DataFrame with 'product' and 'avg_daily_sales' (quantity).
            critical_stock_days (int): Threshold for critical stock in days.

        Returns:
            pd.DataFrame: A DataFrame with stockout risk and status for each product.
                          Columns: 'product', 'current_stock', 'avg_daily_sales', 
                                   'stockout_risk_days', 'is_critical', 'status_label'.
        """
        if product_current_stock_df.empty or avg_daily_sales_data.empty:
            return pd.DataFrame(columns=['product', 'current_stock', 'avg_daily_sales', 
                                         'stockout_risk_days', 'is_critical', 'status_label'])

        # Merge data for calculation
        inventory_data = product_current_stock_df.merge(
            avg_daily_sales_data, on='product', how='left'
        )
        
        # Fill NaN average daily sales with 0 to prevent issues, but indicate for status
        inventory_data['avg_daily_sales'].fillna(0, inplace=True)
        
        # Calculate stockout risk days
        # Avoid division by zero and handle cases where avg_daily_sales is 0
        inventory_data['stockout_risk_days'] = np.where(
            inventory_data['avg_daily_sales'] > 0,
            inventory_data['current_stock'] / inventory_data['avg_daily_sales'],
            np.inf # If no sales, stock lasts indefinitely (or out of stock if current_stock is 0)
        )
        
        # Handle cases where current stock is 0 but there are sales
        inventory_data.loc[(inventory_data['current_stock'] <= 0) & (inventory_data['avg_daily_sales'] > 0), 'stockout_risk_days'] = 0

        # Define status labels based on thresholds
        inventory_data['is_critical'] = (inventory_data['stockout_risk_days'] <= critical_stock_days) & (inventory_data['stockout_risk_days'] >= 0)
        
        inventory_data['status_label'] = 'Good Stock'
        inventory_data.loc[inventory_data['stockout_risk_days'] <= critical_stock_days, 'status_label'] = 'Critical Low Stock'
        inventory_data.loc[inventory_data['current_stock'] <= 0, 'status_label'] = 'Out of Stock' # Explicitly mark out of stock
        inventory_data.loc[(inventory_data['current_stock'] > 0) & (inventory_data['avg_daily_sales'] == 0) & (inventory_data['stockout_risk_days'] == np.inf), 'status_label'] = 'No Sales' # Product has stock but no sales

        # Clean up infinite values for display if needed
        inventory_data['stockout_risk_days'].replace([np.inf, -np.inf], np.nan, inplace=True)
        inventory_data['stockout_risk_days'] = inventory_data['stockout_risk_days'].round(1) # Round for cleaner display

        return inventory_data[['product', 'current_stock', 'avg_daily_sales', 'stockout_risk_days', 'is_critical', 'status_label']]


    def detect_sales_anomalies(self, sales_data, z_score_threshold=2.0):
        """
        Detects high and low sales anomalies using Z-score.
        
        Args:
            sales_data (pd.DataFrame): DataFrame with 'date' and 'sales' columns (daily aggregated).
            z_score_threshold (float): Z-score value above which a point is considered an anomaly.

        Returns:
            pd.DataFrame: Original sales data with anomaly flags and Z-scores.
        """
        if sales_data.empty or len(sales_data) < 2:
            return pd.DataFrame(columns=['date', 'sales', 'mean_sales', 'std_dev_sales', 'z_score', 'is_anomaly_high', 'is_anomaly_low'])

        # Calculate rolling mean and standard deviation to account for recent trends
        # Adjust window size as needed. A simple mean/std dev of all historical data might be too broad.
        window_size = min(7, len(sales_data)) # Use 7 days or less if data is short
        sales_data['mean_sales'] = sales_data['sales'].rolling(window=window_size, min_periods=1).mean()
        sales_data['std_dev_sales'] = sales_data['sales'].rolling(window=window_size, min_periods=1).std()
        
        # Replace 0 std_dev with a small value to avoid division by zero
        sales_data['std_dev_sales'] = sales_data['std_dev_sales'].replace(0, np.nan)
        
        # Calculate Z-score, handle NaN for std_dev_sales (e.g., if only one data point in window)
        sales_data['z_score'] = (sales_data['sales'] - sales_data['mean_sales']) / sales_data['std_dev_sales']
        sales_data['z_score'].fillna(0, inplace=True) # If std_dev is NaN, z_score is 0 (no anomaly)

        sales_data['is_anomaly_high'] = (sales_data['z_score'] > z_score_threshold)
        sales_data['is_anomaly_low'] = (sales_data['z_score'] < -z_score_threshold)

        return sales_data[['date', 'sales', 'mean_sales', 'std_dev_sales', 'z_score', 'is_anomaly_high', 'is_anomaly_low']]

    def identify_slow_moving_items(self, product_col, sales_col, slow_moving_sales_per_day):
        """
        Identifies products that are slow-moving based on average daily sales.

        Args:
            product_col (str): The name of the product column.
            sales_col (str): The name of the sales column.
            slow_moving_sales_per_day (float): Threshold for average daily sales below which
                                               an item is considered slow-moving.

        Returns:
            pd.DataFrame: DataFrame of slow-moving items with their average daily sales.
        """
        if self.df.empty:
            return pd.DataFrame(columns=[product_col, 'avg_daily_sales'])

        # Aggregate to daily sales per product
        product_daily_sales = self.df.groupby([product_col, 'date'])[sales_col].sum().reset_index()
        
        if product_daily_sales.empty:
            return pd.DataFrame(columns=[product_col, 'avg_daily_sales'])

        # Calculate average daily sales per product over the entire period
        avg_daily_sales_per_product = product_daily_sales.groupby(product_col)[sales_col].mean().reset_index()
        avg_daily_sales_per_product.rename(columns={sales_col: 'avg_daily_sales'}, inplace=True)

        slow_moving_items = avg_daily_sales_per_product[
            avg_daily_sales_per_product['avg_daily_sales'] < slow_moving_sales_per_day
        ].sort_values(by='avg_daily_sales')

        return slow_moving_items

    def filter_alerts(self, all_alerts, time_range=None, alert_type=None, severity=None, status=None, search_query=None):
        """
        Filters a list of alerts based on provided criteria.

        Args:
            all_alerts (list): A list of dictionaries, where each dictionary is an alert.
                               Each alert dict should have at least 'date' (datetime), 'type', 'severity', 'status', 'message'.
            time_range (str): 'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly', 'Custom'.
            alert_type (str): Specific type of alert (e.g., 'Stockout Risk', 'Sales Anomaly').
            severity (str): 'Critical', 'High', 'Medium', 'Low', 'Informational'.
            status (str): 'New', 'Acknowledged', 'Resolved', 'Dismissed'.
            search_query (str): Keyword to search within alert messages.

        Returns:
            list: A filtered list of alerts.
        """
        filtered_alerts = pd.DataFrame(all_alerts)

        if filtered_alerts.empty:
            return []

        # Convert 'alert_date' to datetime if it exists and isn't already
        if 'alert_date' in filtered_alerts.columns:
            filtered_alerts['alert_date'] = pd.to_datetime(filtered_alerts['alert_date'], errors='coerce')
            filtered_alerts.dropna(subset=['alert_date'], inplace=True)
            
            latest_date = filtered_alerts['alert_date'].max()
            
            if time_range:
                if time_range == 'Daily':
                    filtered_alerts = filtered_alerts[filtered_alerts['alert_date'].dt.date == latest_date.date()]
                elif time_range == 'Weekly':
                    start_date = latest_date - timedelta(weeks=1)
                    filtered_alerts = filtered_alerts[filtered_alerts['alert_date'] >= start_date]
                elif time_range == 'Monthly':
                    filtered_alerts = filtered_alerts[filtered_alerts['alert_date'].dt.month == latest_date.month]
                elif time_range == 'Quarterly':
                    filtered_alerts = filtered_alerts[filtered_alerts['alert_date'].dt.quarter == latest_date.quarter]
                elif time_range == 'Yearly':
                    filtered_alerts = filtered_alerts[filtered_alerts['alert_date'].dt.year == latest_date.year]
                # 'Custom' range will be handled directly in Alert_Centre.py if date inputs are used
        
        if alert_type and alert_type != "All":
            filtered_alerts = filtered_alerts[filtered_alerts['type'] == alert_type]

        if severity and severity != "All":
            filtered_alerts = filtered_alerts[filtered_alerts['severity'] == severity]

        if status and status != "All":
            filtered_alerts = filtered_alerts[filtered_alerts['status'] == status]

        if search_query:
            filtered_alerts = filtered_alerts[
                filtered_alerts['message'].str.contains(search_query, case=False, na=False)
            ]
        
        return filtered_alerts.to_dict(orient='records')


    # --- Future Notification Methods (Placeholders) ---
    def send_sms_alert(self, message, phone_number):
        """Sends an SMS alert using a configured SMS service."""
        # Replace with actual Twilio/SMS API integration
        # try:
        #     client = Client(os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN"))
        #     client.messages.create(
        #         to=phone_number,
        #         from_=os.environ.get("TWILIO_PHONE_NUMBER"),
        #         body=message
        #     )
        #     return True
        # except Exception as e:
        #     print(f"Error sending SMS: {e}")
        #     return False
        print(f"DEBUG: SMS alert (mock): '{message}' to {phone_number}") # For development
        return True # Simulate success

    def send_email_alert(self, subject, body, recipient_email):
        """Sends an email alert using a configured SMTP service."""
        # Replace with actual SMTP/Email API integration
        # try:
        #     msg = MIMEText(body)
        #     msg['Subject'] = subject
        #     msg['From'] = os.environ.get("EMAIL_USER")
        #     msg['To'] = recipient_email
        #     with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        #         smtp.login(os.environ.get("EMAIL_USER"), os.environ.get("EMAIL_PASS"))
        #         smtp.send_message(msg)
        #     return True
        # except Exception as e:
        #     print(f"Error sending email: {e}")
        #     return False
        print(f"DEBUG: Email alert (mock): '{subject}' to {recipient_email}") # For development
        return True # Simulate success

    # Add other alert-related functionalities here (e.g., supplier performance, custom alerts)