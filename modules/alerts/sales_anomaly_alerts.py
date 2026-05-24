"""
Sales anomaly detection module for identifying unusual sales patterns.

This module provides functions to detect sales anomalies using statistical methods
like z-score and IQR-based outlier detection.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple
import logging

# Set up logging
logger = logging.getLogger(__name__)


def detect_sales_anomalies(
    df_daily_sales_total: pd.DataFrame,
    z_score_threshold: float = 2.5,
    method: str = 'zscore',
    date_col: str = 'date',
    sales_col: str = 'sales'
) -> List[Dict[str, Union[str, float, int]]]:
    """
    Detect sales anomalies using statistical methods.
    
    Parameters
    ----------
    df_daily_sales_total : pd.DataFrame
        DataFrame containing daily sales data with columns:
        - date_col: Date of sales
        - sales_col: Daily sales amount
        
    z_score_threshold : float, optional
        Z-score threshold for anomaly detection. Default is 2.5
        
    method : str, optional
        Method for anomaly detection ('zscore', 'iqr', 'mad'). Default is 'zscore'
        
    date_col : str, optional
        Name of the date column. Default is 'date'
        
    sales_col : str, optional
        Name of the sales column. Default is 'sales'
        
    Returns
    -------
    List[Dict[str, Union[str, float, int]]]
        List of anomaly alerts containing:
        - 'date': Date of anomaly
        - 'sales': Actual sales value
        - 'expected_sales': Expected sales value
        - 'deviation': Deviation from expected
        - 'deviation_pct': Percentage deviation
        - 'anomaly_type': Type of anomaly ('High Sales', 'Low Sales')
        - 'severity': Alert severity
        - 'method': Detection method used
        
    Raises
    ------
    ValueError
        If required columns are missing or invalid parameters
    """
    # Validate inputs
    required_cols = {date_col, sales_col}
    if not required_cols.issubset(df_daily_sales_total.columns):
        missing = required_cols - set(df_daily_sales_total.columns)
        raise ValueError(f"Missing required columns: {missing}")
    
    if z_score_threshold <= 0:
        raise ValueError("z_score_threshold must be positive")
    
    if method not in ['zscore', 'iqr', 'mad']:
        raise ValueError("method must be 'zscore', 'iqr', or 'mad'")
    
    # Create a copy to avoid modifying original data
    df = df_daily_sales_total.copy()
    
    # Ensure date column is datetime
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Ensure sales column is numeric
    df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce')
    
    # Remove any NaN values
    df = df.dropna(subset=[sales_col])
    
    if len(df) < 7:
        logger.warning("Insufficient data for anomaly detection")
        return []
    
    # Calculate expected sales based on method
    if method == 'zscore':
        expected_sales = df[sales_col].mean()
        std_sales = df[sales_col].std()
        z_scores = (df[sales_col] - expected_sales) / std_sales
        
        anomalies = df[abs(z_scores) > z_score_threshold]
        
    elif method == 'iqr':
        Q1 = df[sales_col].quantile(0.25)
        Q3 = df[sales_col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        anomalies = df[(df[sales_col] < lower_bound) | (df[sales_col] > upper_bound)]
        expected_sales = df[sales_col].median()
        
    elif method == 'mad':
        median = df[sales_col].median()
        mad = np.median(np.abs(df[sales_col] - median))
        modified_z_scores = 0.6745 * (df[sales_col] - median) / mad
        
        anomalies = df[abs(modified_z_scores) > z_score_threshold]
        expected_sales = median
    
    # Create alert dictionaries
    alerts = []
    for _, row in anomalies.iterrows():
        actual_sales = float(row[sales_col])
        deviation = actual_sales - expected_sales
        deviation_pct = (deviation / expected_sales * 100) if expected_sales != 0 else float('inf')
        
        anomaly_type = "High Sales" if actual_sales > expected_sales else "Low Sales"
        
        # Determine severity based on deviation magnitude
        abs_deviation_pct = abs(deviation_pct)
        if abs_deviation_pct > 100:
            severity = "Critical"
        elif abs_deviation_pct > 50:
            severity = "High"
        elif abs_deviation_pct > 25:
            severity = "Medium"
        else:
            severity = "Low"
        
        alert = {
            'date': str(row[date_col].date()),
            'sales': actual_sales,
            'expected_sales': float(expected_sales),
            'deviation': float(deviation),
            'deviation_pct': float(deviation_pct),
            'anomaly_type': anomaly_type,
            'severity': severity,
            'method': method
        }
        alerts.append(alert)
    
    logger.info(f"Detected {len(alerts)} sales anomalies using {method} method")
    
    return alerts


def detect_product_level_anomalies(
    df_product_sales: pd.DataFrame,
    product_col: str = 'product_id',
    sales_col: str = 'sales',
    date_col: str = 'date',
    z_score_threshold: float = 2.0
) -> List[Dict[str, Union[str, float, int]]]:
    """
    Detect anomalies at the product level.
    
    Parameters
    ----------
    df_product_sales : pd.DataFrame
        DataFrame containing product-level sales data
        
    product_col : str, optional
        Name of the product column. Default is 'product_id'
        
    sales_col : str, optional
        Name of the sales column. Default is 'sales'
        
    date_col : str, optional
        Name of the date column. Default is 'date'
        
    z_score_threshold : float, optional
        Z-score threshold for anomaly detection. Default is 2.0
        
    Returns
    -------
    List[Dict[str, Union[str, float, int]]]
        List of product-level anomaly alerts
    """
    required_cols = {product_col, sales_col, date_col}
    if not required_cols.issubset(df_product_sales.columns):
        missing = required_cols - set(df_product_sales.columns)
        raise ValueError(f"Missing required columns: {missing}")
    
    # Group by product and detect anomalies
    all_alerts = []
    
    for product_id in df_product_sales[product_col].unique():
        product_data = df_product_sales[df_product_sales[product_col] == product_id].copy()
        
        if len(product_data) < 7:
            continue
            
        # Detect anomalies for this product
        product_alerts = detect_sales_anomalies(
            product_data,
            z_score_threshold=z_score_threshold,
            date_col=date_col,
            sales_col=sales_col
        )
        
        # Add product information to alerts
        for alert in product_alerts:
            alert['product_id'] = str(product_id)
            all_alerts.append(alert)
    
    return all_alerts


def get_seasonal_adjusted_anomalies(
    df: pd.DataFrame,
    date_col: str = 'date',
    sales_col: str = 'sales',
    window: int = 7
) -> List[Dict[str, Union[str, float, int]]]:
    """
    Detect anomalies using seasonal adjustment (moving average).
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with daily sales data
        
    date_col : str, optional
        Name of the date column
        
    sales_col : str, optional
        Name of the sales column
        
    window : int, optional
        Moving average window size. Default is 7 days
        
    Returns
    -------
    List[Dict[str, Union[str, float, int]]]
        List of seasonally adjusted anomaly alerts
    """
    required_cols = {date_col, sales_col}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col)
    
    # Calculate moving average
    df['moving_avg'] = df[sales_col].rolling(window=window, center=True).mean()
    
    # Calculate deviation from moving average
    df['deviation'] = df[sales_col] - df['moving_avg']
    df['deviation_pct'] = (df['deviation'] / df['moving_avg'] * 100).abs()
    
    # Detect anomalies (deviation > 50% from moving average)
    anomalies = df[df['deviation_pct'] > 50].dropna()
    
    alerts = []
