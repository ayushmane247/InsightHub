"""
Alerts visualization module for displaying alert data using Plotly.

This module provides functions to create visualizations for sales trends,
inventory status, and other alert-related data.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Union

def plot_sales_trend_for_anomaly(df: pd.DataFrame, anomaly_date: str, sales_col: str = 'sales') -> go.Figure:
    """
    Plot sales trend highlighting anomalies.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing sales data with a date column and sales values.
        
    anomaly_date : str
        The date of the anomaly to highlight.
        
    sales_col : str, optional
        Name of the sales column. Default is 'sales'.
        
    Returns
    -------
    go.Figure
        Plotly figure object showing sales trend with highlighted anomaly.
    """
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Create the figure
    fig = px.line(df, x='date', y=sales_col, title='Sales Trend with Anomaly Highlighted')
    
    # Highlight the anomaly
    anomaly_date = pd.to_datetime(anomaly_date)
    fig.add_trace(go.Scatter(
        x=[anomaly_date],
        y=[df[df['date'] == anomaly_date][sales_col].values[0]],
        mode='markers',
        marker=dict(color='red', size=10),
        name='Anomaly'
    ))
    
    return fig


def plot_inventory_status(inventory_df: pd.DataFrame) -> go.Figure:
    """
    Plot inventory status including stock levels and risk levels.
    
    Parameters
    ----------
    inventory_df : pd.DataFrame
        DataFrame containing inventory status with columns:
        - 'product_name': Name of the product
        - 'current_stock': Current stock level
        - 'stockout_risk': Risk level ('Low', 'Medium', 'High', 'Critical')
        
    Returns
    -------
    go.Figure
        Plotly figure object showing inventory status.
    """
    # Create a bar chart for inventory status
    fig = px.bar(inventory_df, 
                 x='product_name', 
                 y='current_stock', 
                 color='stockout_risk',
                 title='Inventory Status',
                 labels={'current_stock': 'Current Stock', 'product_name': 'Product'},
                 color_discrete_map={
                     'Critical': 'red',
                     'High': 'orange',
                     'Medium': 'yellow',
                     'Low': 'green'
                 })
    
    return fig


def create_alert_summary_chart(alerts: List[Dict[str, Union[str, int]]]) -> go.Figure:
    """
    Create a summary chart of alerts by type and severity.
    
    Parameters
    ----------
    alerts : List[Dict[str, Union[str, int]]]
        List of alert dictionaries containing alert types and severities.
        
    Returns
    -------
    go.Figure
        Plotly figure object showing alert summary.
    """
    # Convert alerts to DataFrame
    alert_df = pd.DataFrame(alerts)
    
    # Group by alert type and severity
    summary = alert_df.groupby(['alert_type', 'severity']).size().reset_index(name='count')
    
    # Create a bar chart for alert summary
    fig = px.bar(summary, 
                 x='alert_type', 
                 y='count', 
                 color='severity', 
                 title='Alert Summary by Type and Severity',
                 labels={'count': 'Number of Alerts', 'alert_type': 'Alert Type'})
    
    return fig
