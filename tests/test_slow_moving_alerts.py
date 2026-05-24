"""
Unit tests for slow_moving_alerts module.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from modules.alerts.slow_moving_alerts import (
    identify_slow_moving_items,
    get_zero_velocity_products,
    get_stagnant_inventory
)


class TestIdentifySlowMovingItems:
    """Test cases for identify_slow_moving_items function."""
    
    def test_basic_identification(self):
        """Test basic slow-moving item identification."""
        data = {
            'product_id': ['P001', 'P002', 'P003', 'P004'],
            'sales': [5, 2, 0, 1],
            'quantity': [10, 20, 30, 5],
            'date': pd.date_range(start='2024-01-01', periods=4)
        }
        df = pd.DataFrame(data)
        
        slow_movers = identify_slow_moving_items(df, min_sales_threshold=3)
        
        assert len(slow_movers) == 2  # P002 and P003 should be identified as slow movers
        assert all(alert['alert_type'] == 'Slow Moving' for alert in slow_movers)
    
    def test_no_slow_movers(self):
        """Test when no slow-moving items are detected."""
        data = {
            'product_id': ['P001', 'P002'],
            'sales': [10, 15],
            'quantity': [10, 20],
            'date': pd.date_range(start='2024-01-01', periods=2)
        }
        df = pd.DataFrame(data)
        
        slow_movers = identify_slow_moving_items(df, min_sales_threshold=5)
        
        assert len(slow_movers) == 0  # No slow movers should be detected
    
    def test_invalid_threshold(self):
        """Test error handling for invalid threshold."""
        data = {
            'product_id': ['P001'],
            'sales': [10],
            'quantity': [10],
            'date': pd.date_range(start='2024-01-01', periods=1)
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="must be non-negative"):
            identify_slow_moving_items(df, min_sales_threshold=-1)
    
    def test_missing_columns(self):
        """Test error handling for missing columns."""
        df = pd.DataFrame({'wrong_col': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Missing required columns"):
            identify_slow_moving_items(df)


class TestGetZeroVelocityProducts:
    """Test cases for get_zero_velocity_products function."""
    
    def test_identification(self):
        """Test identification of zero velocity products."""
        data = {
            'product_id': ['P001', 'P002', 'P003'],
            'date': pd.date_range(start='2024-01-01', periods=30),
            'sales': [0, 0, 0]
        }
        df = pd.DataFrame(data)
        
        zero_velocity = get_zero_velocity_products(df)
        
        assert len(zero_velocity) == 3  # All products should be identified as zero velocity
    
    def test_non_zero_velocity(self):
        """Test when no zero velocity products are detected."""
        data = {
            'product_id': ['P001', 'P002'],
            'date': pd.date_range(start='2024-01-01', periods=30),
            'sales': [1] * 30
        }
        df = pd.DataFrame(data)
        
        zero_velocity = get_zero_velocity_products(df)
        
        assert len(zero_velocity) == 0  # No zero velocity products should be detected


class TestGetStagnantInventory:
    """Test cases for get_stagnant_inventory function."""
    
    def test_identification(self):
        """Test identification of stagnant inventory."""
        data = {
            'product_id': ['P001', 'P002', 'P003'],
            'quantity': [5, 0, 3],
            'date': pd.date_range(start='2024-01-01', periods=30)
        }
        df = pd.DataFrame(data)
        
        stagnant = get_stagnant_inventory(df, max_quantity_threshold=2)
        
        assert len(stagnant) == 2  # P002 and P003 should be identified as stagnant
    
    def test_no_stagnant_inventory(self):
        """Test when no stagnant inventory is detected."""
        data = {
            'product_id': ['P001', 'P002'],
            'quantity': [10, 20],
            'date': pd.date_range(start='2024-01-01', periods=30)
        }
        df = pd.DataFrame(data)
        
        stagnant = get_stagnant_inventory(df, max_quantity_threshold=5)
        
        assert len(stagnant) == 0  # No stagnant inventory should be detected


if __name__ == "__main__":
    pytest.main([__file__])
