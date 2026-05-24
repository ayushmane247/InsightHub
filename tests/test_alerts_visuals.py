"""
Unit tests for alerts_visuals module.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go
from modules.alerts.alerts_visuals import (
    plot_sales_trend_for_anomaly,
    plot_inventory_status,
    create_alert_summary_chart
)


class TestPlotSalesTrendForAnomaly:
    """Test cases for plot_sales_trend_for_anomaly function."""
    
    def test_basic_plot_creation(self):
        """Test basic plot creation."""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        sales = [100 + i * 2 for i in range(30)]
        
        df = pd.DataFrame({
            'date': dates,
            'sales': sales
        })
        
        fig = plot_sales_trend_for_anomaly(df, '2024-01-15')
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 2  # Line plot + anomaly marker
    
    def test_empty_data(self):
        """Test handling of empty data."""
        df = pd.DataFrame({
            'date': [],
            'sales': []
        })
        
        fig = plot_sales_trend_for_anomaly(df, '2024-01-15')
        
        assert isinstance(fig, go.Figure)


class TestPlotInventoryStatus:
    """Test cases for plot_inventory_status function."""
    
    def test_basic_plot_creation(self):
        """Test basic plot creation."""
        inventory_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B', 'Product C'],
            'current_stock': [100, 50, 10],
            'stockout_risk': ['Low', 'Medium', 'High']
        })
        
        fig = plot_inventory_status(inventory_df)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 3  # One bar for each product
    
    def test_empty_data(self):
        """Test handling of empty data."""
        inventory_df = pd.DataFrame({
            'product_name': [],
            'current_stock': [],
            'stockout_risk': []
        })
        
        fig = plot_inventory_status(inventory_df)
        
        assert isinstance(fig, go.Figure)


class TestCreateAlertSummaryChart:
    """Test cases for create_alert_summary_chart function."""
    
    def test_basic_chart_creation(self):
        """Test basic chart creation."""
        alerts = [
            {'alert_type': 'Low Stock', 'severity': 'High'},
            {'alert_type': 'Stockout Risk', 'severity': 'Critical'},
            {'alert_type': 'Low Stock', 'severity': 'Medium'}
        ]
        
        fig = create_alert_summary_chart(alerts)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 2  # Should have bars for each alert type
    
    def test_empty_alerts(self):
        """Test handling of empty alerts."""
        alerts = []
        
        fig = create_alert_summary_chart(alerts)
        
        assert isinstance(fig, go.Figure)
    
    def test_single_alert(self):
        """Test handling of single alert."""
        alerts = [{'alert_type': 'Low Stock', 'severity': 'High'}]
        
        fig = create_alert_summary_chart(alerts)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1


if __name__ == "__main__":
    pytest.main([__file__])
