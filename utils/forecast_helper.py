# D:\project\utils\forecast_helper.py (UPDATED)

import streamlit as st
import pmdarima as pm
import pandas as pd
import numpy as np
import warnings
from scipy.stats import norm
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from prophet import Prophet # Import Prophet globally for the class
from statsmodels.tsa.api import ExponentialSmoothing # Import ExponentialSmoothing globally

# Suppress specific warnings from libraries like Prophet or statsmodels
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning) # Good to add for newer library versions

class ForecastHelper:
    """
    A helper class to encapsulate various sales forecasting and inventory planning functions.
    """
    def __init__(self):
        # No initial data or parameters are strictly needed here,
        # as most methods will take df_ts as an argument.
        # You could add default forecast_days, service_level etc. here if you wanted.
        pass

    def prophet_forecast(self, df_ts: pd.DataFrame, forecast_days: int) -> tuple[pd.DataFrame, any]:
        """
        Generates a sales forecast using Facebook Prophet.
        Expected df_ts to have 'ds' (datetime) and 'y' (numeric) columns.
        Returns forecast_df and the fitted Prophet model for components plotting.
        """
        # Data validation and cleaning (can be moved to a separate pre-processing method if needed)
        df_ts_copy = df_ts.copy() # Work on a copy to avoid modifying original outside the method
        df_ts_copy['ds'] = pd.to_datetime(df_ts_copy['ds'])
        df_ts_copy['y'] = pd.to_numeric(df_ts_copy['y'], errors='coerce')
        df_ts_copy.dropna(subset=['ds', 'y'], inplace=True)
        
        if df_ts_copy.empty or len(df_ts_copy) < 2:
            st.warning("Prophet: Not enough valid data points for forecasting (needs at least 2).")
            return pd.DataFrame(), None # Not enough data for Prophet

        try:
            model = Prophet(
                seasonality_mode='multiplicative',
                interval_width=0.95,
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False
            )
            # Add country holidays if desired (e.g., model.add_country_holidays(country_name='US'))
            
            model.fit(df_ts_copy)
            
            future = model.make_future_dataframe(periods=forecast_days)
            forecast = model.predict(future)
            
            forecast_df = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(columns={'ds': 'date'})
            return forecast_df, model # Return the model object for component plotting
        except Exception as e:
            st.error(f"Prophet forecast failed: {e}. Please check your data and model parameters.")
            return pd.DataFrame(), None

    def arima_forecast(self, df_ts: pd.DataFrame, forecast_days: int) -> tuple[pd.DataFrame, any]:
        """
        Generates a sales forecast using Auto ARIMA (pmdarima).
        Expected df_ts to have 'ds' (datetime) and 'y' (numeric) columns.
        Returns forecast_df and None for model_fit_info.
        """
        df_ts_copy = df_ts.copy()
        df_ts_copy['ds'] = pd.to_datetime(df_ts_copy['ds'])
        df_ts_copy['y'] = pd.to_numeric(df_ts_copy['y'], errors='coerce')
        df_ts_copy.dropna(subset=['ds', 'y'], inplace=True)
        
        if df_ts_copy.empty or len(df_ts_copy) < 5: # ARIMA needs more data points
            st.warning("ARIMA: Not enough valid data points for forecasting (needs at least 5).")
            return pd.DataFrame(), None

        # Aggregate to daily data if not already, as ARIMA works best on regular time series
        # Using fillna(0) ensures no NaNs for ARIMA which is strict
        df_ts_daily = df_ts_copy.set_index('ds')['y'].resample('D').sum().fillna(0).reset_index()
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore") # Suppress ARIMA specific warnings during model fitting
                model = pm.auto_arima(df_ts_daily['y'], 
                                    start_p=1, start_q=1,
                                    test='adf', 
                                    max_p=5, max_q=5,
                                    m=7, # Seasonality m=7 for weekly patterns
                                    d=None, # Let model determine 'd'
                                    seasonal=True, # Enable seasonal ARIMA
                                    start_P=0, D=0, # Initial seasonal orders
                                    trace=False,
                                    error_action='ignore', 
                                    suppress_warnings=True, 
                                    stepwise=True)
            
            forecast_values = model.predict(n_periods=forecast_days)
            
            last_date = df_ts_daily['ds'].max()
            forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days)
            
            forecast_df = pd.DataFrame({
                'date': forecast_dates,
                'yhat': forecast_values
            })
            return forecast_df, None # ARIMA model object is not directly used for plotting components
        except Exception as e:
            st.error(f"ARIMA forecast failed: {e}. Consider adjusting parameters or data.")
            return pd.DataFrame(), None

    def exp_smoothing_forecast(self, df_ts: pd.DataFrame, forecast_days: int) -> tuple[pd.DataFrame, any]:
        """
        Generates a sales forecast using Exponential Smoothing (Holt-Winters).
        Expected df_ts to have 'ds' (datetime) and 'y' (numeric) columns.
        Returns forecast_df and None for model_fit_info.
        """
        df_ts_copy = df_ts.copy()
        df_ts_copy['ds'] = pd.to_datetime(df_ts_copy['ds'])
        df_ts_copy['y'] = pd.to_numeric(df_ts_copy['y'], errors='coerce')
        df_ts_copy.dropna(subset=['ds', 'y'], inplace=True)
        
        if df_ts_copy.empty or len(df_ts_copy) < 2:
            st.warning("Exponential Smoothing: Not enough valid data points for forecasting (needs at least 2).")
            return pd.DataFrame(), None

        # Aggregate to daily data if not already
        df_ts_daily = df_ts_copy.set_index('ds')['y'].resample('D').sum().fillna(0)
        
        try:
            # Fit Exponential Smoothing model (Holt-Winters)
            fit_model = ExponentialSmoothing(
                df_ts_daily, 
                seasonal_periods=7, 
                trend='add', 
                seasonal='mul',
                initialization_method="estimated"
            ).fit()
            
            forecast_values = fit_model.forecast(forecast_days)
            
            forecast_df = pd.DataFrame({
                'date': forecast_values.index,
                'yhat': forecast_values.values
            })
            return forecast_df, None
        except Exception as e:
            st.error(f"Exponential Smoothing forecast failed: {e}. Please check your data.")
            return pd.DataFrame(), None

    # --- Forecast Accuracy Metrics (now methods of the class) ---

    def mean_absolute_error_custom(self, y_true, y_pred):
        """Calculates Mean Absolute Error."""
        return np.mean(np.abs(y_true - y_pred))

    def mean_absolute_percentage_error_custom(self, y_true, y_pred):
        """Calculates Mean Absolute Percentage Error (MAPE), handling zero actuals."""
        return np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1e-8))) * 100

    def rolling_forecast_accuracy(self, df_ts: pd.DataFrame, forecast_method: str, window: int = 60, horizon: int = 7) -> dict:
        """
        Calculates rolling forecast accuracy (MAE, MAPE) by simulating forecasts
        on a rolling window of historical data using a specified internal forecasting method.

        Args:
            df_ts (pd.DataFrame): Time series data with 'ds' and 'y' columns.
            forecast_method (str): The name of the forecasting method to use ("prophet", "arima", "exp_smoothing").
            window (int): The size of the historical data window to train the model on.
            horizon (int): The number of days to forecast into the future for each window.

        Returns:
            dict: A dictionary containing 'rolling_mae' and 'rolling_mape'.
        """
        # Select the correct internal method based on forecast_method string
        if forecast_method == "prophet":
            forecast_func = self.prophet_forecast
        elif forecast_method == "arima":
            forecast_func = self.arima_forecast
        elif forecast_method == "exp_smoothing":
            forecast_func = self.exp_smoothing_forecast
        else:
            return {'rolling_mae': np.nan, 'rolling_mape': np.nan, 'error': 'Invalid forecast method specified.'}

        all_actuals = []
        all_forecasts = []

        df_ts_copy = df_ts.copy()
        df_ts_copy['ds'] = pd.to_datetime(df_ts_copy['ds'])
        df_ts_copy['y'] = pd.to_numeric(df_ts_copy['y'], errors='coerce').fillna(0)
        df_ts_copy = df_ts_copy.sort_values('ds').reset_index(drop=True)

        if len(df_ts_copy) < (window + horizon):
            return {'rolling_mae': np.nan, 'rolling_mape': np.nan, 'error': 'Not enough data for rolling accuracy.'}

        for i in range(len(df_ts_copy) - window - horizon + 1):
            train_df = df_ts_copy.iloc[i : i + window]
            actual_period_start_date = train_df['ds'].max() + pd.Timedelta(days=1)
            actual_period_end_date = actual_period_start_date + pd.Timedelta(days=horizon - 1)
            
            actual_values_df = df_ts_copy[(df_ts_copy['ds'] >= actual_period_start_date) & (df_ts_copy['ds'] <= actual_period_end_date)]
            
            if actual_values_df.empty:
                continue

            try:
                forecast_df, _ = forecast_func(train_df, forecast_days=horizon)
                
                if forecast_df.empty:
                    continue

                merged_df = pd.merge(actual_values_df, forecast_df, 
                                     left_on='ds', right_on='date', how='inner')
                
                if not merged_df.empty:
                    all_actuals.extend(merged_df['y'].tolist())
                    all_forecasts.extend(merged_df['yhat'].tolist())

            except Exception as e:
                st.warning(f"Skipping a rolling forecast window due to error: {e}")
                continue

        if not all_actuals:
            return {'rolling_mae': np.nan, 'rolling_mape': np.nan, 'error': 'No valid forecasts generated for accuracy calculation.'}

        mae = self.mean_absolute_error_custom(np.array(all_actuals), np.array(all_forecasts))
        mape = self.mean_absolute_percentage_error_custom(np.array(all_actuals), np.array(all_forecasts))
        
        return {'rolling_mae': mae, 'rolling_mape': mape}

    # --- Inventory Planning Functions (now methods of the class) ---

    def calculate_safety_stock(self, avg_daily_sales: float, std_daily_sales: float, lead_time: int, service_level: float) -> float:
        """
        Calculates safety stock based on daily sales variability and lead time.
        """
        if std_daily_sales <= 0 or lead_time <= 0 or service_level <= 0 or service_level >= 1:
            st.warning("Safety Stock: Invalid input for calculation (std_dev, lead_time must be > 0, service_level between 0 and 1). Returning 0.")
            return 0.0

        z_score = norm.ppf(service_level)
        std_dev_lead_time = std_daily_sales * np.sqrt(lead_time)
        safety_stock = z_score * std_dev_lead_time
        return max(0.0, safety_stock)

    def calculate_reorder_point(self, avg_daily_sales: float, lead_time: int, safety_stock: float) -> float:
        """
        Calculates the reorder point.
        """
        if avg_daily_sales < 0 or lead_time < 0:
            st.warning("Reorder Point: Invalid input for calculation (avg_daily_sales, lead_time must be >= 0). Returning 0.")
            return 0.0
        
        reorder_point = (avg_daily_sales * lead_time) + safety_stock
        return max(0.0, reorder_point)

    def calculate_order_quantity(self, avg_daily_sales: float, target_stock_days: int, current_stock: float = 0, safety_stock: float = 0) -> float:
        """
        Calculates a suggested order quantity to reach a target stock level.
        """
        if avg_daily_sales < 0 or target_stock_days < 0:
            st.warning("Order Quantity: Invalid input for calculation (avg_daily_sales, target_stock_days must be >= 0). Returning 0.")
            return 0.0

        suggested_qty = (avg_daily_sales * target_stock_days) + safety_stock
        return max(0.0, suggested_qty)


# --- Example Usage (for testing this helper module directly) ---
if __name__ == '__main__':
    print("--- Testing utils/forecast_helper.py (Class Methods) ---")

    # Instantiate the helper
    helper = ForecastHelper()

    # 1. Dummy Data Generation
    dates = pd.to_datetime(pd.date_range(start='2023-01-01', periods=100, freq='D'))
    sales = np.random.randint(50, 200, size=100) + np.sin(np.arange(100) / 10) * 30 + np.random.normal(0, 5, size=100)
    sales = np.round(np.maximum(0, sales), 2) # Ensure non-negative
    
    sample_df_ts = pd.DataFrame({'ds': dates, 'y': sales})
    
    print("\nSample Time Series Data Head:")
    print(sample_df_ts.head())

    # 2. Test Forecasting Models
    forecast_days = 7

    print(f"\n--- Testing Prophet Forecast for {forecast_days} days ---")
    prophet_fcst, prophet_model = helper.prophet_forecast(sample_df_ts.copy(), forecast_days)
    if not prophet_fcst.empty:
        print(prophet_fcst)
    else:
        print("Prophet forecast failed or not enough data.")

    print(f"\n--- Testing ARIMA Forecast for {forecast_days} days ---")
    arima_fcst, _ = helper.arima_forecast(sample_df_ts.copy(), forecast_days)
    if not arima_fcst.empty:
        print(arima_fcst)
    else:
        print("ARIMA forecast failed or not enough data.")

    print(f"\n--- Testing Exponential Smoothing Forecast for {forecast_days} days ---")
    exp_smooth_fcst, _ = helper.exp_smoothing_forecast(sample_df_ts.copy(), forecast_days)
    if not exp_smooth_fcst.empty:
        print(exp_smooth_fcst)
    else:
        print("Exponential Smoothing forecast failed or not enough data.")

    # 3. Test Rolling Forecast Accuracy
    print("\n--- Testing Rolling Forecast Accuracy (Prophet) ---")
    accuracy_results = helper.rolling_forecast_accuracy(sample_df_ts.copy(), "prophet", window=60, horizon=7)
    print(f"Rolling MAE: {accuracy_results.get('rolling_mae', 'N/A'):.2f}")
    print(f"Rolling MAPE: {accuracy_results.get('rolling_mape', 'N/A'):.2f}%")
    if 'error' in accuracy_results: print(f"Error: {accuracy_results['error']}")

    # 4. Test Inventory Planning Functions
    print("\n--- Testing Inventory Planning Functions ---")
    avg_daily = 100.5
    std_daily = 20.0
    lead_t = 5
    svc_lvl = 0.95

    ss = helper.calculate_safety_stock(avg_daily, std_daily, lead_t, svc_lvl)
    rp = helper.calculate_reorder_point(avg_daily, lead_t, ss)
    oq = helper.calculate_order_quantity(avg_daily, 30, safety_stock=ss)

    print(f"Avg Daily Sales: {avg_daily}")
    print(f"Lead Time: {lead_t} days")
    print(f"Service Level: {svc_lvl*100}%")
    print(f"Calculated Safety Stock: {ss:.2f}")
    print(f"Calculated Reorder Point: {rp:.2f}")
    print(f"Suggested Order Quantity (30-day coverage): {oq:.2f}")