import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import lightgbm as lgb
import streamlit as st

class AdvancedForecastHelper:
    def __init__(self):
        self.models = {}
        self.feature_importance = {}
    
    def create_features(self, df):
        """Create time-based and lag features"""
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Time-based features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_month_end'] = (df['date'].dt.day >= 25).astype(int)
        
        # Lag features
        for lag in [1, 7, 14, 30]:
            df[f'sales_lag_{lag}'] = df['sales'].shift(lag)
        
        # Rolling statistics
        for window in [7, 14, 30]:
            df[f'sales_rolling_mean_{window}'] = df['sales'].rolling(window).mean()
            df[f'sales_rolling_std_{window}'] = df['sales'].rolling(window).std()
        
        return df
    
    def lightgbm_forecast(self, df, forecast_days=30):
        """LightGBM-based forecasting with feature importance"""
        try:
            # Prepare features
            df_features = self.create_features(df)
            df_features = df_features.dropna()
            
            if len(df_features) < 50:
                raise ValueError("Need at least 50 days of data for ML forecasting")
            
            # Prepare training data
            feature_cols = [col for col in df_features.columns 
                          if col not in ['date', 'sales'] and not col.startswith('sales_lag')]
            
            X = df_features[feature_cols].fillna(0)
            y = df_features['sales']
            
            # Split for validation
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Train LightGBM
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            params = {
                'objective': 'regression',
                'metric': 'mae',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': -1
            }
            
            model = lgb.train(
                params,
                train_data,
                valid_sets=[val_data],
                num_boost_round=100,
                callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
            )
            
            # Store feature importance
            self.feature_importance['lightgbm'] = dict(zip(
                feature_cols, 
                model.feature_importance()
            ))
            
            # Generate forecasts
            last_date = df['date'].max()
            forecast_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=forecast_days,
                freq='D'
            )
            
            # Create forecast features (simplified)
            forecast_features = []
            for date in forecast_dates:
                features = {
                    'day_of_week': date.dayofweek,
                    'month': date.month,
                    'quarter': date.quarter,
                    'is_weekend': int(date.dayofweek >= 5),
                    'is_month_end': int(date.day >= 25)
                }
                # Add rolling features from recent data
                recent_sales = df['sales'].tail(30).mean()
                for window in [7, 14, 30]:
                    features[f'sales_rolling_mean_{window}'] = recent_sales
                    features[f'sales_rolling_std_{window}'] = df['sales'].tail(window).std()
                
                forecast_features.append(features)
            
            forecast_df = pd.DataFrame(forecast_features)
            forecast_df = forecast_df.reindex(columns=feature_cols, fill_value=0)
            
            # Predict
            predictions = model.predict(forecast_df)
            
            # Create result dataframe
            result_df = pd.DataFrame({
                'ds': forecast_dates,
                'yhat': np.maximum(predictions, 0)  # Ensure non-negative
            })
            
            # Calculate validation metrics
            val_pred = model.predict(X_val)
            mae = mean_absolute_error(y_val, val_pred)
            rmse = np.sqrt(mean_squared_error(y_val, val_pred))
            
            model_info = {
                'model_type': 'LightGBM',
                'mae': mae,
                'rmse': rmse,
                'feature_importance': self.feature_importance['lightgbm']
            }
            
            return result_df, model_info
            
        except Exception as e:
            st.error(f"LightGBM forecasting failed: {str(e)}")
            return None, None