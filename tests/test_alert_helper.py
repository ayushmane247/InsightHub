"""
Unit tests for alert_helper module.
"""

import pytest
from modules.alerts.alert_helper import (
    filter_alerts,
    aggregate_alerts,
    sort_alerts,
    format_alert_summary,
    validate_alert_data,
    merge_alerts
)


class TestFilterAlerts:
    """Test cases for filter_alerts function."""
    
    def test_basic_filtering(self):
        """Test basic alert filtering."""
        alerts = [
            {'alert_type': 'Low Stock', 'severity': 'High', 'product_id': 'P001'},
            {'alert_type': 'Stockout Risk', 'severity': 'Critical', 'product_id': 'P002'},
            {'alert_type': 'Low Stock', 'severity': 'Medium', 'product_id': 'P003'}
        ]
        
        filtered = filter_alerts(alerts, alert_type='Low Stock')
        
        assert len(filtered) == 2
        assert all(alert['alert_type'] == 'Low Stock' for alert in filtered)
    
    def test_severity_filtering(self):
        """Test severity-based filtering."""
        alerts = [
            {'alert_type': 'Low Stock', 'severity': 'High'},
            {'alert_type': 'Stockout Risk', 'severity': 'Critical'},
            {'alert_type': 'Low Stock', 'severity': 'Medium'}
        ]
        
        filtered = filter_alerts(alerts, severity='Critical')
        
        assert len(filtered) == 1
        assert filtered[0]['severity'] == 'Critical'
    
    def test_search_filtering(self):
        """Test search query filtering."""
        alerts = [
            {'product_id': 'P001', 'product_name': 'Widget A'},
            {'product_id': 'P002', 'product_name': 'Widget B'},
            {'product_id': 'P003', 'product_name': 'Gadget C'}
        ]
        
        filtered = filter_alerts(alerts, search_query='Widget')
        
        assert len(filtered) == 2
        assert all('Widget' in str(alert) for alert in filtered)
    
    def test_empty_alerts(self):
        """Test handling of empty alerts."""
        filtered = filter_alerts([])
        
        assert len(filtered) == 0


class TestAggregateAlerts:
    """Test cases for aggregate_alerts function."""
    
    def test_basic_aggregation(self):
        """Test basic alert aggregation."""
        alerts = [
            {'alert_type': 'Low Stock', 'severity': 'High'},
            {'alert_type': 'Stockout Risk', 'severity': 'Critical'},
            {'alert_type': 'Low Stock', 'severity': 'Medium'}
        ]
        
        aggregated = aggregate_alerts(alerts)
        
        assert aggregated['total_alerts'] == 3
        assert 'Low Stock' in aggregated['by_type']
        assert 'Stockout Risk' in aggregated['by_type']
    
    def test_empty_alerts(self):
        """Test handling of empty alerts."""
        aggregated = aggregate_alerts([])
        
        assert aggregated['total_alerts'] == 0
        assert aggregated['by_type'] == {}
        assert aggregated['by_severity'] == {}


class TestSortAlerts:
    """Test cases for sort_alerts function."""
    
    def test_severity_sorting(self):
        """Test sorting by severity."""
        alerts = [
            {'severity': 'Medium'},
            {'severity': 'Critical'},
            {'severity': 'High'}
        ]
        
        sorted_alerts = sort_alerts(alerts, sort_by='severity')
        
        assert sorted_alerts[0]['severity'] == 'Critical'
        assert sorted_alerts[1]['severity'] == 'High'
        assert sorted_alerts[2]['severity'] == 'Medium'
    
    def test_product_id_sorting(self):
        """Test sorting by product ID."""
        alerts = [
            {'product_id': 'P003'},
            {'product_id': 'P001'},
            {'product_id': 'P002'}
        ]
        
        sorted_alerts = sort_alerts(alerts, sort_by='product_id', ascending=True)
        
        assert sorted_alerts[0]['product_id'] == 'P001'
        assert sorted_alerts[1]['product_id'] == 'P002'
        assert sorted_alerts[2]['product_id'] == 'P003'


class TestFormatAlertSummary:
    """Test cases for format_alert_summary function."""
    
    def test_basic_summary(self):
        """Test basic alert summary formatting."""
        alerts = [
            {'alert_type': 'Low Stock', 'severity': 'High'},
            {'alert_type': 'Stockout Risk', 'severity': 'Critical'}
        ]
        
        summary = format_alert_summary(alerts)
        
        assert summary['total_alerts'] == 2
        assert summary['critical_count'] == 1
        assert summary['high_count'] == 1
        assert 'Found 2 alerts including 1 critical' in summary['summary_text']
    
    def test_empty_summary(self):
        """Test handling of empty alerts."""
        summary = format_alert_summary([])
        
        assert summary['total_alerts'] == 0
        assert summary['summary_text'] == 'No alerts found'


class TestValidateAlertData:
    """Test cases for validate_alert_data function."""
    
    def test_valid_alert(self):
        """Test validation of valid alert data."""
        alert = {'alert_type': 'Low Stock', 'severity': 'High'}
        
        assert validate_alert_data(alert) is True
    
    def test_invalid_alert(self):
        """Test validation of invalid alert data."""
        alert = {'wrong_field': 'value'}
        
        assert validate_alert_data(alert) is False
    
    def test_non_dict_alert(self):
        """Test validation of non-dictionary alert."""
        alert = "not a dict"
        
        assert validate_alert_data(alert) is False


class TestMergeAlerts:
    """Test cases for merge_alerts function."""
    
    def test_basic_merge(self):
        """Test basic alert merging."""
        alerts1 = [{'product_id': 'P001'}]
        alerts2 = [{'product_id': 'P002'}]
        
        merged = merge_alerts(alerts1, alerts2)
        
        assert len(merged) == 2
        assert merged[0]['product_id'] == 'P001'
        assert merged[1]['product_id'] == 'P002'
    
    def test_empty_merge(self):
        """Test merging with empty lists."""
        merged = merge_alerts([], [])
        
        assert len(merged) == 0
    
    def test_invalid_input(self):
        """Test handling of invalid input."""
        merged = merge_alerts("not a list", [])
        
        assert len(merged) == 0


if __name__ == "__main__":
    pytest.main([__file__])
