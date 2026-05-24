"""
Slow-moving products detection module for inventory optimization.

This module provides functions to identify products with low sales velocity
using various criteria and thresholds.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional
import logging
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)


def identify_slow_moving_items(
    df: pd.DataFrame,
    product_col: str = 'product_id',
    sales_col: str = 'sales',
    quantity_col: str = 'quantity',
    date_col: str = 'date',
    days_threshold: int = 30,
    min_sales_threshold: float = 10.0,
    method: str = 'sales_rate'
) -> List[Dict[str, Union[str, float, int]]]:
    """
    Identify slow-moving products based on sales velocity.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing sales data
        
    product_col : str, optional
        Name of the product column. Default is 'product_id'
        
    sales_col : str, optional
        Name of the sales column. Default is 'sales'
        
    quantity_col : str, optional
        Name of the quantity column. Default is 'quantity'
        
    date_col : str, optional
        Name of the date column. Default is 'date'
        
    days_threshold : int, optional
        Number of days to consider for analysis. Default is 30
        
    min_sales_threshold : float, optional
        Minimum sales threshold per day. Default is 10.0
        
    method : str, optional
        Method for slow-moving detection ('sales_rate', 'quantity_rate', 'days_since_sale')
        
    Returns
    -------
    List[Dict[str, Union[str, float, int]]]
        List of slow-moving product alerts containing:
        - 'product_id': Product identifier
        - 'total_sales': Total sales in period
        - 'total_quantity': Total quantity sold
        - 'days_active': Days with sales
        - 'avg_daily_sales': Average daily sales
        - 'avg_daily_quantity': Average daily quantity
        - 'days_since_last_sale': Days since last sale
        - 'alert_type': Type of alert ('Slow Moving')
        - 'severity': Alert severity
        - 'threshold_used': Threshold value used
        
    Raises
    ------
    ValueError
        If required columns are missing or invalid parameters
    """
    required_cols = {product_col, sales_col, quantity_col, date_col}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")
    
    if days_threshold <= 0:
        raise ValueError("days_threshold must be positive")
    
    if min_sales_threshold < 0:
        raise ValueError("min_sales_threshold must be non-negative")
    
    if method not in ['sales_rate', 'quantity_rate', 'days_since_sale']:
        raise ValueError("method must be 'sales_rate', 'quantity_rate', or 'days_since_sale'")
    
    # Create a copy to avoid modifying original data
    df = df.copy()
    
    # Ensure date column is datetime
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Ensure numeric columns
    df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce')
    df[quantity_col] = pd.to_numeric(df[quantity_col], errors='coerce')
    
    # Remove NaN values
    df = df.dropna(subset=[sales_col, quantity_col])
    
    # Filter for recent data
    cutoff_date = datetime.now() - timedelta(days=days_threshold)
    df = df[df[date_col] >= cutoff_date]
    
    if len(df) == 0:
        logger.warning("No data available for slow-moving analysis")
        return []
    
    # Group by product
    product_stats = df.groupby(product_col).agg({
        sales_col: ['sum', 'count', 'mean'],
        quantity_col: ['sum', 'mean'],
        date_col: ['max', 'min']
    }).reset_index()
    
    # Flatten column names
    product_stats.columns = [
        product_col,
        'total_sales',
        'days_active',
        'avg_daily_sales',
        'total_quantity',
        'avg_daily_quantity',
        'last_sale_date',
        'first_sale_date'
    ]
    
    # Calculate days since last sale
    product_stats['days_since_last_sale'] = (
        datetime.now() - pd.to_datetime(product_stats['last_sale_date'])
    ).dt.days
    
    # Calculate average daily rates
    product_stats['analysis_days'] = (
        datetime.now() - pd.to_datetime(product_stats['first_sale_date'])
    ).dt.days + 1
    
    product_stats['avg_daily_sales'] = (
        product_stats['total_sales'] / product_stats['analysis_days']
    )
    product_stats['avg_daily_quantity'] = (
        product_stats['total_quantity'] / product_stats['analysis_days']
    )
    
    # Identify slow-moving products based on method
    if method == 'sales_rate':
        slow_movers = product_stats[
            product_stats['avg_daily_sales'] < min_sales_threshold
        ]
    elif method == 'quantity_rate':
        slow_movers = product_stats[
            product_stats['avg_daily_quantity'] < min_sales_threshold
        ]
    elif method == 'days_since_sale':
        slow_movers = product_stats[
            product_stats['days_since_last_sale'] > min_sales_threshold
        ]
    
    # Create alert dictionaries
    alerts = []
    for _, row in slow_movers.iterrows():
        # Determine severity based on how slow the product is
        if method == 'sales_rate':
            severity_score = row['avg_daily_sales'] / min_sales_threshold
        elif method == 'quantity_rate':
            severity_score = row['avg_daily_quantity'] / min_sales_threshold
        else:  # days_since_sale
            severity_score = min_sales_threshold / row['days_since_last_sale']
        
        if severity_score < 0.1:
            severity = "Critical"
        elif severity_score < 0.3:
            severity = "High"
        elif severity_score < 0.6:
            severity = "Medium"
        else:
            severity = "Low"
        
        alert = {
            'product_id': str(row[product_col]),
            'total_sales': float(row['total_sales']),
            'total_quantity': int(row['total_quantity']),
            'days_active': int(row['days_active']),
            'avg_daily_sales': float(row['avg_daily_sales']),
            'avg_daily_quantity': float(row['avg_daily_quantity']),
            'days_since_last_sale': int(row['days_since_last_sale']),
            'alert_type': 'Slow Moving',
            'severity': severity,
            'threshold_used': min_sales_threshold,
            'method': method
        }
        alerts.append(alert)
    
    logger.info(f"Identified {len(alerts)} slow-moving products using {method} method")
    
    return alerts


def get_zero_velocity_products(
    df: pd.DataFrame,
    product_col: str = 'product_id',
    date_col: str = 'date',
    days_threshold: int = 30
) -> List[Dict[str, Union[str, int]]]:
    """
    Identify products with zero sales velocity.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing sales data
        
    product_col : str, optional
        Name of the product column
        
    date_col : str, optional
        Name of the date column
        
    days_threshold : int, optional
        Number of days to check for zero sales
        
    Returns
    -------
    List[Dict[str, Union[str, int]]]
        List of zero velocity product alerts
    """
    required_cols = {product_col, date_col}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")
    
    # Get all products
    all_products = set(df[product_col].unique())
    
    # Get products with sales in the period
    cutoff_date = datetime.now() - timedelta(days=days_threshold)
    recent_sales = df[pd.to_datetime(df[date_col]) >= cutoff_date]
    active_products = set(recent_sales[product_col].unique())
    
    # Zero velocity products
    zero_velocity_products = all_products - active_products
    
    alerts = []
    for product_id in zero_velocity_products:
        alert = {
            'product_id': str(product_id),
            'alert_type': 'Zero Velocity',
            'severity': 'Critical',
            'days_without_sale': days_threshold,
            'threshold_used': days_threshold
        }
        alerts.append(alert)
    
    logger.info(f"Identified {len(alerts)} zero velocity products")
    
    return alerts


def get_stagnant_inventory(
    df: pd.DataFrame,
    product_col: str = 'product_id',
    quantity_col: str = 'quantity',
    date_col: str = 'date',
    days_threshold: int = 60,
    max_quantity_threshold: int = 5
) -> List[Dict[str, Union[str, int, float]]]:
    """
    Identify products with stagnant inventory (low sales despite stock).
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing sales data
        
    product_col : str, optional
        Name of the product column
        
    quantity_col : str, optional
        Name of the quantity column
        
    date_col : str, optional
        Name of the date column
        
    days_threshold : int, optional
        Number of days to analyze
        
    max_quantity_threshold : int, optional
        Maximum quantity sold to be considered stagnant
        
    Returns
    -------
    List[Dict[str, Union[str, int, float]]]
        List of stagnant inventory alerts
    """
    required_cols = {product_col, quantity_col, date_col}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")
    
    # Filter for recent data
    cutoff_date = datetime.now() - timedelta(days=days_threshold)
    df = df[pd.to_datetime(df[date_col]) >= cutoff_date]
    
    # Group by product
    product_totals = df.groupby(product_col)[quantity_col].sum().reset_index()
    
    # Find stagnant products
    stagnant_products = product_totals[
        product_totals[quantity_col] <= max_quantity_threshold
    ]
    
    alerts = []
    for _, row in stagnant_products.iterrows():
        alert = {
            'product_id': str(row[product_col]),
            'total_quantity_sold': int(row[quantity_col]),
            'alert_type': 'Stagnant Inventory',
            'severity': 'High',
            'days_analyzed': days_threshold,
            'max_quantity_threshold': max_quantity_threshold
        }
        alerts.append(alert)
    
    logger.info(f"Identified {len(alerts)} stagnant inventory products")
    
    return alerts
