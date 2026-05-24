"""
Inventory-based alerts module for stockout risk and low stock detection.

This module provides functions to calculate inventory status and generate alerts
based on current stock levels, sales velocity, and critical thresholds.
"""

import pandas as pd
from typing import Dict, List, Union, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)


def calculate_inventory_status(
    product_current_stock_df: pd.DataFrame,
    avg_daily_sales_data: pd.DataFrame,
    critical_stock_days: int = 7
) -> pd.DataFrame:
    """
    Calculate inventory status including stockout risk and days until stockout.
    
    Parameters
    ----------
    product_current_stock_df : pd.DataFrame
        DataFrame containing current stock information with columns:
        - 'product_id': Unique identifier for products
        - 'product_name': Name of the product
        - 'current_stock': Current available stock quantity
        
    avg_daily_sales_data : pd.DataFrame
        DataFrame containing average daily sales information with columns:
        - 'product_id': Unique identifier for products
        - 'avg_daily_sales': Average daily sales quantity
        
    critical_stock_days : int, optional
        Number of days of stock remaining that triggers a critical alert.
        Default is 7 days.
        
    Returns
    -------
    pd.DataFrame
        DataFrame with inventory status including:
        - 'product_id': Product identifier
        - 'product_name': Product name
        - 'current_stock': Current stock level
        - 'avg_daily_sales': Average daily sales
        - 'days_until_stockout': Estimated days until stock runs out
        - 'stockout_risk': Risk level ('Low', 'Medium', 'High', 'Critical')
        - 'alert_required': Boolean indicating if alert should be triggered
        
    Raises
    ------
    ValueError
        If required columns are missing from input DataFrames
    """
    # Validate inputs
    required_stock_cols = {'product_id', 'product_name', 'current_stock'}
    required_sales_cols = {'product_id', 'avg_daily_sales'}
    
    if not required_stock_cols.issubset(product_current_stock_df.columns):
        missing = required_stock_cols - set(product_current_stock_df.columns)
        raise ValueError(f"Missing required columns in product_current_stock_df: {missing}")
    
    if not required_sales_cols.issubset(avg_daily_sales_data.columns):
        missing = required_sales_cols - set(avg_daily_sales_data.columns)
        raise ValueError(f"Missing required columns in avg_daily_sales_data: {missing}")
    
    # Merge dataframes
    inventory_df = pd.merge(
        product_current_stock_df,
        avg_daily_sales_data,
        on='product_id',
        how='inner'
    )
    
    # Handle missing values
    inventory_df['current_stock'] = pd.to_numeric(inventory_df['current_stock'], errors='coerce').fillna(0)
    inventory_df['avg_daily_sales'] = pd.to_numeric(inventory_df['avg_daily_sales'], errors='coerce').fillna(0)
    
    # Calculate days until stockout
    inventory_df['days_until_stockout'] = inventory_df.apply(
        lambda row: float('inf') if row['avg_daily_sales'] == 0 
        else row['current_stock'] / row['avg_daily_sales'],
        axis=1
    )
    
    # Determine stockout risk level
    def get_risk_level(days: float) -> str:
        """Determine risk level based on days until stockout."""
        if days <= 0:
            return "Critical"
        elif days <= critical_stock_days:
            return "High"
        elif days <= critical_stock_days * 2:
            return "Medium"
        else:
            return "Low"
    
    inventory_df['stockout_risk'] = inventory_df['days_until_stockout'].apply(get_risk_level)
    
    # Determine if alert is required
    inventory_df['alert_required'] = inventory_df['stockout_risk'].isin(['High', 'Critical'])
    
    # Round days until stockout for display
    inventory_df['days_until_stockout'] = inventory_df['days_until_stockout'].replace(
        float('inf'), None
    ).round(2)
    
    logger.info(f"Calculated inventory status for {len(inventory_df)} products")
    
    return inventory_df


def get_low_stock_alerts(
    product_current_stock_df: pd.DataFrame,
    low_stock_qty: int
) -> List[Dict[str, Union[str, int, float]]]:
    """
    Generate low stock alerts based on absolute quantity thresholds.
    
    Parameters
    ----------
    product_current_stock_df : pd.DataFrame
        DataFrame containing current stock information with columns:
        - 'product_id': Unique identifier for products
        - 'product_name': Name of the product
        - 'current_stock': Current available stock quantity
        
    low_stock_qty : int
        Threshold quantity below which products are considered low stock
        
    Returns
    -------
    List[Dict[str, Union[str, int, float]]]
        List of alert dictionaries containing:
        - 'product_id': Product identifier
        - 'product_name': Product name
        - 'current_stock': Current stock level
        - 'alert_type': Type of alert ('Low Stock')
        - 'threshold': The threshold value used
        - 'severity': Alert severity ('Warning')
        
    Raises
    ------
    ValueError
        If required columns are missing from input DataFrame
    """
    # Validate inputs
    required_cols = {'product_id', 'product_name', 'current_stock'}
    
    if not required_cols.issubset(product_current_stock_df.columns):
        missing = required_cols - set(product_current_stock_df.columns)
        raise ValueError(f"Missing required columns in product_current_stock_df: {missing}")
    
    if low_stock_qty < 0:
        raise ValueError("low_stock_qty must be non-negative")
    
    # Filter for low stock products
    low_stock_df = product_current_stock_df[
        pd.to_numeric(product_current_stock_df['current_stock'], errors='coerce') <= low_stock_qty
    ].copy()
    
    # Create alert dictionaries
    alerts = []
    for _, row in low_stock_df.iterrows():
        alert = {
            'product_id': str(row['product_id']),
            'product_name': str(row['product_name']),
            'current_stock': int(row['current_stock']) if pd.notna(row['current_stock']) else 0,
            'alert_type': 'Low Stock',
            'threshold': low_stock_qty,
            'severity': 'Warning'
        }
        alerts.append(alert)
    
    logger.info(f"Generated {len(alerts)} low stock alerts")
    
    return alerts


def get_stockout_risk_alerts(
    inventory_status_df: pd.DataFrame
) -> List[Dict[str, Union[str, int, float]]]:
    """
    Generate stockout risk alerts from inventory status data.
    
    Parameters
    ----------
    inventory_status_df : pd.DataFrame
        DataFrame from calculate_inventory_status() containing inventory status
        
    Returns
    -------
    List[Dict[str, Union[str, int, float]]]
        List of alert dictionaries containing:
        - 'product_id': Product identifier
        - 'product_name': Product name
        - 'current_stock': Current stock level
        - 'avg_daily_sales': Average daily sales
        - 'days_until_stockout': Estimated days until stockout
        - 'alert_type': Type of alert ('Stockout Risk')
        - 'risk_level': Risk level ('High', 'Critical')
        - 'severity': Alert severity based on risk level
        
    Raises
    ------
    ValueError
        If required columns are missing from input DataFrame
    """
    # Validate inputs
    required_cols = {
        'product_id', 'product_name', 'current_stock', 
        'avg_daily_sales', 'days_until_stockout', 'stockout_risk'
    }
    
    if not required_cols.issubset(inventory_status_df.columns):
        missing = required_cols - set(inventory_status_df.columns)
        raise ValueError(f"Missing required columns in inventory_status_df: {missing}")
    
    # Filter for high/critical risk products
    risk_alerts_df = inventory_status_df[
        inventory_status_df['alert_required'] == True
    ].copy()
    
    # Create alert dictionaries
    alerts = []
    for _, row in risk_alerts_df.iterrows():
        severity_map = {
            'High': 'Warning',
            'Critical': 'Critical'
        }
        
        alert = {
            'product_id': str(row['product_id']),
            'product_name': str(row['product_name']),
            'current_stock': int(row['current_stock']),
            'avg_daily_sales': float(row['avg_daily_sales']),
            'days_until_stockout': float(row['days_until_stockout']) if pd.notna(row['days_until_stockout']) else 0.0,
            'alert_type': 'Stockout Risk',
            'risk_level': str(row['stockout_risk']),
            'severity': severity_map.get(str(row['stockout_risk']), 'Unknown')
        }
        alerts.append(alert)
    
    logger.info(f"Generated {len(alerts)} stockout risk alerts")
    
    return alerts


def combine_inventory_alerts(
    low_stock_alerts: List[Dict[str, Union[str, int, float]]],
    stockout_risk_alerts: List[Dict[str, Union[str, int, float]]]
) -> List[Dict[str, Union[str, int, float]]]:
    """
    Combine low stock and stockout risk alerts into a single list.
    
    Parameters
    ----------
    low_stock_alerts : List[Dict[str, Union[str, int, float]]]
        List of low stock alerts from get_low_stock_alerts()
    stockout_risk_alerts : List[Dict[str, Union[str, int, float]]]
        List of stockout risk alerts from get_stockout_risk_alerts()
        
    Returns
    -------
    List[Dict[str, Union[str, int, float]]]
        Combined list of all inventory alerts, sorted by severity
    """
    # Combine alerts
    all_alerts = low_stock_alerts + stockout_risk_alerts
    
    # Sort by severity (Critical first, then Warning)
    severity_order = {'Critical': 0, 'Warning': 1}
    all_alerts.sort(key=lambda x: severity_order.get(x.get('severity', 'Warning'), 2))
    
    logger.info(f"Combined {len(all_alerts)} total inventory alerts")
    
    return all_alerts
