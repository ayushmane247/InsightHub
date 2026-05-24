"""
Unit tests for inventory_alerts module.
"""

import pytest
import pandas as pd
from modules.alerts.inventory_alerts import (
    calculate_inventory_status,
    get_low_stock_alerts,
    get_stockout_risk_alerts,
    combine_inventory_alerts
)


class TestCalculateInventoryStatus:
    """Test cases for calculate_inventory_status function."""
    
    def test_basic_calculation(self):
        """Test basic inventory status calculation."""
        stock_df = pd.DataFrame({
            'product_id': ['P001', 'P002', 'P003'],
            'product_name': ['Widget A', 'Widget B', 'Widget C'],
            'current_stock': [100, 50, 10]
        })
        
        sales_df = pd.DataFrame({
            'product_id': ['P001', 'P002', 'P003'],
            'avg_daily_sales': [10, 5, 2]
        })
        
        result = calculate_inventory_status(stock_df, sales_df, critical_stock_days=7)
        
        assert len(result) == 3
        assert 'days_until_stockout' in result.columns
        assert 'stockout_risk' in result.columns
        assert result.loc[0, 'days_until_stockout'] == 10.0  # 100/10
        assert result.loc[1, 'days_until_stockout'] == 10.0  # 50/5
        assert result.loc[2, 'days_until_stockout'] == 5.0   # 10/2
    
    def test_zero_sales(self):
        """Test handling of zero daily sales."""
        stock_df = pd.DataFrame({
            'product_id': ['P001'],
            'product_name': ['Widget A'],
            'current_stock': [100]
        })
        
        sales_df = pd.DataFrame({
            'product_id': ['P001'],
            'avg_daily_sales': [0]
        })
        
        result = calculate_inventory_status(stock_df, sales_df)
        
        assert result.loc[0, 'days_until_stockout'] is None
        assert result.loc[0, 'stockout_risk'] == 'Low'
    
    def test_missing_columns(self):
        """Test error handling for missing columns."""
        stock_df = pd.DataFrame({'product_id': ['P001']})
        sales_df = pd.DataFrame({'product_id': ['P001']})
        
        with pytest.raises(ValueError, match="Missing required columns"):
            calculate_inventory_status(stock_df, sales_df)
    
    def test_negative_values(self):
        """Test handling of negative stock values."""
        stock_df = pd.DataFrame({
            'product_id': ['P001'],
            'product_name': ['Widget A'],
            'current_stock': [-10]
        })
        
        sales_df = pd.DataFrame({
            'product_id': ['P001'],
            'avg_daily_sales': [5]
        })
        
        result = calculate_inventory_status(stock_df, sales_df)
        
        assert result.loc[0, 'days_until_stockout'] == -2.0
        assert result.loc[0, 'stockout_risk'] == 'Critical'


class TestGetLowStockAlerts:
    """Test cases for get_low_stock_alerts function."""
    
    def test_basic_alerts(self):
        """Test basic low stock alert generation."""
        stock_df = pd.DataFrame({
            'product_id': ['P001', 'P002', 'P003'],
            'product_name': ['Widget A', 'Widget B', 'Widget C'],
            'current_stock': [5, 15, 25]
        })
        
        alerts = get_low_stock_alerts(stock_df, low_stock_qty=10)
        
        assert len(alerts) == 1
        assert alerts[0]['product_id'] == 'P001'
        assert alerts[0]['current_stock'] == 5
        assert alerts[0]['alert_type'] == 'Low Stock'
    
    def test_empty_alerts(self):
        """Test when no products are below threshold."""
        stock_df = pd.DataFrame({
            'product_id': ['P001', 'P002'],
            'product_name': ['Widget A', 'Widget B'],
            'current_stock': [15, 20]
        })
        
        alerts = get_low_stock_alerts(stock_df, low_stock_qty=10)
        
        assert len(alerts) == 0
    
    def test_invalid_threshold(self):
        """Test error handling for negative threshold."""
        stock_df = pd.DataFrame({
            'product_id': ['P001'],
            'product_name': ['Widget A'],
            'current_stock': [5]
        })
        
        with pytest.raises(ValueError, match="must be non-negative"):
            get_low_stock_alerts(stock_df, low_stock_qty=-5)
    
    def test_missing_columns(self):
        """Test error handling for missing columns."""
        stock_df = pd.DataFrame({'product_id': ['P001']})
        
        with pytest.raises(ValueError, match="Missing required columns"):
            get_low_stock_alerts(stock_df, low_stock_qty=10)


class TestGetStockoutRiskAlerts:
    """Test cases for get_stockout_risk_alerts function."""
    
    def test_basic_alerts(self):
        """Test basic stockout risk alert generation."""
        inventory_df = pd.DataFrame({
            'product_id': ['P001', 'P002', 'P003'],
            'product_name': ['Widget A', 'Widget B', 'Widget C'],
            'current_stock': [10, 50, 100],
            'avg_daily_sales': [5, 10, 10],
            'days_until_stockout': [2, 5, 10],
            'stockout_risk': ['Critical', 'High', 'Medium'],
            'alert_required': [True, True, False]
        })
        
        alerts = get_stockout_risk_alerts(inventory_df)
        
        assert len(alerts) == 2  # Only high/critical risk
        assert alerts[0]['risk_level'] == 'Critical'
        assert alerts[1]['risk_level'] == 'High'
    
    def test_empty_alerts(self):
        """Test when no products require alerts."""
        inventory_df = pd.DataFrame({
            'product_id': ['P001'],
            'product_name': ['Widget A'],
            'current_stock': [100],
            'avg_daily_sales': [10],
            'days_until_stockout': [10],
            'stockout_risk': ['Low'],
            'alert_required': [False]
        })
        
        alerts = get_stockout_risk_alerts(inventory_df)
        
        assert len(alerts) == 0
    
    def test_missing_columns(self):
        """Test error handling for missing columns."""
        inventory_df = pd.DataFrame({'product_id': ['P001']})
        
        with pytest.raises(ValueError, match="Missing required columns"):
            get_stockout_risk_alerts(inventory_df)


class TestCombineInventoryAlerts:
    """Test cases for combine_inventory_alerts function."""
    
    def test_combined_alerts(self):
        """Test combining different types of alerts."""
        low_alerts = [
            {
                'product_id': 'P001',
                'product_name': 'Widget A',
                'current_stock': 5,
                'alert_type': 'Low Stock',
                'threshold': 10,
                'severity': 'Warning'
            }
        ]
        
        risk_alerts = [
            {
                'product_id': 'P002',
                'product_name': 'Widget B',
                'current_stock': 10,
                'avg_daily_sales': 5.0,
                'days_until_stockout': 2.0,
                'alert_type': 'Stockout Risk',
                'risk_level': 'Critical',
                'severity': 'Critical'
            }
        ]
        
        combined = combine_inventory_alerts(low_alerts, risk_alerts)
        
        assert len(combined) == 2
        assert combined[0]['severity'] == 'Critical'  # Should be first
        assert combined[1]['severity'] == 'Warning'
    
    def test_empty_combination(self):
        """Test combining empty lists."""
        combined = combine_inventory_alerts([], [])
        
        assert len(combined) == 0


if __name__ == "__main__":
    pytest.main([__file__])
