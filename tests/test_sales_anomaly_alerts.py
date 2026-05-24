"""
Unit tests for sales_anomaly_alerts module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from modules.alerts.sales_anomaly_alerts import (
    detect_sales_anomalies,
    detect_product_level_anomalies,
    get_seasonal_adjusted_anomalies
)


class TestDetectSalesAnomalies:
    """Test cases for detect_sales_anomalies function."""
    
    def test_basic_zscore_detection(self):
        """Test basic z-score anomaly detection."""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        sales = [100] * 28 + [200, 50]  # Add anomalies
        
        df = pd.DataFrame({
            'date': dates,
            'sales': sales
        })
        
        anomalies = detect_sales_anomalies(df, z_score_threshold=2.0)
        
        assert len(anomalies) >= 2  # Should detect the anomalies
        assert all('anomaly_type' in alert for alert in anomalies)
        assert all('severity' in alert for alert in anomalies)
    
    def test_iqr_method(self):
        """Test IQR method for anomaly detection."""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        sales = [100] * 25 + [200, 300, 10, 5]  # Add outliers
        
        df = pd.DataFrame({
            'date': dates,
            'sales': sales
        })
        
        anomalies = detect_sales_anomalies(df, method='iqr')
        
        assert len(anomalies) >= 2  # Should detect outliers
        assert all(alert['method'] == 'iqr' for alert in anomalies)
    
    def test_mad_method(self):
        """Test MAD (Median Absolute Deviation) method."""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        sales = [100] * 27 + [250, 20, 10]  # Add anomalies
        
        df = pd.DataFrame({
            'date': dates,
            'sales': sales
        })
        
        anomalies = detect_sales_anomalies(df, method='mad')
        
        assert len(anomalies) >= 2
        assert all(alert['method'] == 'mad' for alert in anomalies)
    
    def test_no_anomalies(self):
        """Test when no anomalies are detected."""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        sales = [100 + np.random.normal(0, 5) for _ in range(30)]  # Normal data
        
        df = pd.DataFrame({
            'date': dates,
            'sales': sales
        })
        
        anomalies = detect_sales_anomalies(df, z_score_threshold=3.0)
        
        assert len(anomalies) == 0
    
    def test_missing_columns(self):
        """Test error handling for missing columns."""
        df = pd.DataFrame({'wrong_col': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Missing required columns"):
            detect_sales_anomalies(df)
    
    def test_invalid_threshold(self):
        """Test error handling for invalid threshold."""
        df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=10, freq='D'),
            'sales': [100] * 10
        })
        
        with pytest.raises(ValueError, match="must be positive"):
            detect_sales_anomalies(df, z_score_threshold=-1)
    
    def test_invalid_method(self):
        """Test error handling for invalid method."""
        df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=10, freq='D'),
            'sales': [100] * 10
        })
        
        with pytest.raises(ValueError, match="method must be"):
            detect_sales_anomalies(df, method='invalid')


class TestDetectProductLevelAnomalies:
    """Test cases for detect_product_level_anomalies function."""
    
    def test_product_level_detection(self):
        """Test product-level anomaly detection."""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        
        # Create data for multiple products
        data = []
        for i, product in enumerate(['P001', 'P002']):
            for date in dates:
                base_sales = 100 + (i * 50)
                sales = base_sales
                if date.day == 15:  # Add anomaly
                    sales = base_sales * 2
                data.append({
                    'product_id': product,
                    'date': date,
                    'sales': sales
                })
        
        df = pd.DataFrame(data)
        
        anomalies = detect_product_level_anomalies(df)
        
        assert len(anomalies) >= 2  # Should detect anomalies for both products
        assert all('product_id' in alert for alert in anomalies)
    
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        df = pd.DataFrame({
            'product_id': ['P001'] * 3,
            'date': pd.date_range(start='2024-01-01', periods=3, freq='D'),
            'sales': [100, 101, 102]
        })
        
        anomalies = detect_product_level_anomalies(df)
        
        assert len(anomalies) == 0  # Should skip due to insufficient data


class TestGetSeasonalAdjustedAnomalies:
    """Test cases for get_seasonal_adjusted_anomalies function."""
    
    def test_seasonal_adjustment(self):
        """Test seasonal adjustment anomaly detection."""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        # Create data with trend and spike
        sales = [100 + i * 2 for i in range(30)]
        sales[15] = 200  # Add spike
        
        df = pd.DataFrame({
            'date': dates,
            'sales': sales
        })
        
        anomalies = get_seasonal_adjusted_anomalies(df)
        
        assert len(anomalies) >= 1  # Should detect the spike
        assert all('deviation_pct' in alert for alert in anomalies)
    
    def test_missing_columns(self):
        """Test error handling for missing columns."""
        df = pd.DataFrame({'wrong_col': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Missing required columns"):
            get_seasonal_adjusted_anomalies(df)


if __name__ == "__main__":
    pytest.main([__file__])
