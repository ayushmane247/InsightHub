"""
Alert helper module for filtering and aggregating alerts.

This module provides utility functions for filtering, sorting, and aggregating
alerts across different alert types.
"""

import pandas as pd
from typing import List, Dict, Union, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)


def filter_alerts(
    alerts: List[Dict[str, Union[str, int, float]]],
    time_range: str = '30d',
    alert_type: str = 'all',
    severity: str = 'all',
    status: str = 'all',
    search_query: str = ''
) -> List[Dict[str, Union[str, int, float]]]:
    """
    Filter alerts by various criteria.
    
    Parameters
    ----------
    alerts : List[Dict[str, Union[str, int, float]]]
        List of alert dictionaries
        
    time_range : str, optional
        Time range to filter by ('7d', '30d', '90d', 'all'). Default is '30d'
        
    alert_type : str, optional
        Type of alert to filter by ('all', 'Low Stock', 'Stockout Risk', 
        'Sales Anomaly', 'Slow Moving'). Default is 'all'
        
    severity : str, optional
        Severity to filter by ('all', 'Critical', 'High', 'Medium', 'Low'). 
        Default is 'all'
        
    status : str, optional
        Status to filter by ('all', 'Active', 'Resolved', 'Acknowledged'). 
        Default is 'all'
        
    search_query : str, optional
        Search query to filter by product name or ID. Default is ''
        
    Returns
    -------
    List[Dict[str, Union[str, int, float]]]
        Filtered list of alerts
    """
    if not isinstance(alerts, list):
        raise ValueError("alerts must be a list of dictionaries")
    
    filtered_alerts = alerts.copy()
    
    # Filter by alert type
    if alert_type != 'all':
        filtered_alerts = [
            alert for alert in filtered_alerts 
            if alert.get('alert_type') == alert_type
        ]
    
    # Filter by severity
    if severity != 'all':
        filtered_alerts = [
            alert for alert in filtered_alerts 
            if alert.get('severity') == severity
        ]
    
    # Filter by status
    if status != 'all':
        filtered_alerts = [
            alert for alert in filtered_alerts 
            if alert.get('status', 'Active') == status
        ]
    
    # Filter by search query
    if search_query:
        search_lower = search_query.lower()
        filtered_alerts = [
            alert for alert in filtered_alerts
            if search_lower in str(alert.get('product_id', '')).lower() or
               search_lower in str(alert.get('product_name', '')).lower()
        ]
    
    logger.info(f"Filtered {len(filtered_alerts)} alerts from {len(alerts)} total")
    
    return filtered_alerts


def aggregate_alerts(alerts: List[Dict[str, Union[str, int, float]]]) -> Dict[str, any]:
    """
    Aggregate alerts by type and severity.
    
    Parameters
    ----------
    alerts : List[Dict[str, Union[str, int, float]]]
        List of alert dictionaries
        
    Returns
    -------
    Dict[str, any]
        Dictionary containing:
        - 'total_alerts': Total number of alerts
        - 'by_type': Count by alert type
        - 'by_severity': Count by severity
        - 'by_type_severity': Count by type and severity combination
    """
    if not isinstance(alerts, list):
        raise ValueError("alerts must be a list of dictionaries")
    
    if not alerts:
        return {
            'total_alerts': 0,
            'by_type': {},
            'by_severity': {},
            'by_type_severity': {}
        }
    
    # Convert to DataFrame for easier aggregation
    alert_df = pd.DataFrame(alerts)
    
    # Count by type
    by_type = alert_df['alert_type'].value_counts().to_dict()
    
    # Count by severity
    by_severity = alert_df['severity'].value_counts().to_dict()
    
    # Count by type and severity
    by_type_severity = alert_df.groupby(['alert_type', 'severity']).size().to_dict()
    
    result = {
        'total_alerts': len(alerts),
        'by_type': by_type,
        'by_severity': by_severity,
        'by_type_severity': by_type_severity
    }
    
    logger.info(f"Aggregated {len(alerts)} alerts")
    
    return result


def sort_alerts(
    alerts: List[Dict[str, Union[str, int, float]]],
    sort_by: str = 'severity',
    ascending: bool = False
) -> List[Dict[str, Union[str, int, float]]]:
    """
    Sort alerts by specified criteria.
    
    Parameters
    ----------
    alerts : List[Dict[str, Union[str, int, float]]]
        List of alert dictionaries
        
    sort_by : str, optional
        Field to sort by ('severity', 'date', 'product_id'). Default is 'severity'
        
    ascending : bool, optional
        Whether to sort in ascending order. Default is False
        
    Returns
    -------
    List[Dict[str, Union[str, int, float]]]
        Sorted list of alerts
    """
    if not isinstance(alerts, list):
        raise ValueError("alerts must be a list of dictionaries")
    
    if not alerts:
        return []
    
    # Define severity order for sorting
    severity_order = {
        'Critical': 0,
        'High': 1,
        'Medium': 2,
        'Low': 3
    }
    
    def sort_key(alert):
        if sort_by == 'severity':
            return severity_order.get(alert.get('severity', 'Low'), 4)
        elif sort_by == 'date':
            return alert.get('date', '')
        elif sort_by == 'product_id':
            return alert.get('product_id', '')
        else:
            return alert.get(sort_by, '')
    
    sorted_alerts = sorted(alerts, key=sort_key, reverse=not ascending)
    
    logger.info(f"Sorted {len(alerts)} alerts by {sort_by}")
    
    return sorted_alerts


def format_alert_summary(alerts: List[Dict[str, Union[str, int, float]]]) -> Dict[str, any]:
    """
    Format alert summary for display.
    
    Parameters
    ----------
    alerts : List[Dict[str, Union[str, int, float]]]
        List of alert dictionaries
        
    Returns
    -------
    Dict[str, any]
        Formatted alert summary with human-readable information
    """
    if not isinstance(alerts, list):
        raise ValueError("alerts must be a list of dictionaries")
    
    if not alerts:
        return {
            'summary_text': 'No alerts found',
            'critical_count': 0,
            'high_count': 0,
            'medium_count': 0,
            'low_count': 0,
            'top_alerts': []
        }
    
    # Aggregate data
    aggregated = aggregate_alerts(alerts)
    
    # Create summary text
    total_alerts = aggregated['total_alerts']
    critical_count = aggregated['by_severity'].get('Critical', 0)
    high_count = aggregated['by_severity'].get('High', 0)
    medium_count = aggregated['by_severity'].get('Medium', 0)
    low_count = aggregated['by_severity'].get('Low', 0)
    
    summary_text = f"Found {total_alerts} alerts"
    if critical_count > 0:
        summary_text += f" including {critical_count} critical"
    
    # Get top alerts (sorted by severity)
    top_alerts = sort_alerts(alerts, sort_by='severity', ascending=False)[:5]
    
    result = {
        'summary_text': summary_text,
        'critical_count': critical_count,
        'high_count': high_count,
        'medium_count': medium_count,
        'low_count': low_count,
        'top_alerts': top_alerts,
        'total_alerts': total_alerts
    }
    
    return result


def validate_alert_data(alert: Dict[str, Union[str, int, float]]) -> bool:
    """
    Validate alert data structure and required fields.
    
    Parameters
    ----------
    alert : Dict[str, Union[str, int, float]]
        Alert dictionary to validate
        
    Returns
    -------
    bool
        True if alert is valid, False otherwise
    """
    required_fields = ['alert_type', 'severity']
    
    if not isinstance(alert, dict):
        return False
    
    for field in required_fields:
        if field not in alert:
            return False
    
    return True


def merge_alerts(*alert_lists: List[Dict[str, Union[str, int, float]]]) -> List[Dict[str, Union[str, int, float]]]:
    """
    Merge multiple alert lists into a single list.
    
    Parameters
    ----------
    *alert_lists : List[Dict[str, Union[str, int, float]]]
        Variable number of alert lists to merge
        
    Returns
    -------
    List[Dict[str, Union[str, int, float]]]
        Combined list of all alerts
    """
    all_alerts = []
    
    for alert_list in alert_lists:
        if isinstance(alert_list, list):
            all_alerts.extend(alert_list)
    
    logger.info(f"Merged {len(all_alerts)} total alerts")
    
    return all_alerts
