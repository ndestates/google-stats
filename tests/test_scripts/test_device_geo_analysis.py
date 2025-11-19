"""
Tests for device_geo_analysis.py script
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from scripts.device_geo_analysis import analyze_device_performance, analyze_geographic_performance, analyze_device_geo


class TestDeviceGeoAnalysis:
    """Test device and geographic analysis"""

    @patch('scripts.device_geo_analysis.run_report')
    @patch('scripts.device_geo_analysis.create_date_range')
    @patch('scripts.device_geo_analysis.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_device_performance_success(self, mock_to_csv, mock_get_filename, mock_create_range, mock_run_report):
        """Test successful device performance analysis"""
        # Mock GA4 response with device data
        mock_response = Mock()
        mock_response.row_count = 2

        # Mock row data - desktop and mobile devices
        mock_row1 = Mock()
        mock_row1.dimension_values = [
            Mock(value="desktop"),  # deviceCategory
            Mock(value="Windows"),  # operatingSystem
            Mock(value="Chrome")    # browser
        ]
        mock_row1.metric_values = [
            Mock(value="1000"),  # totalUsers
            Mock(value="1200"),  # sessions
            Mock(value="5000"),  # screenPageViews
            Mock(value="0.25"),   # bounceRate
            Mock(value="180.5"),  # averageSessionDuration
            Mock(value="0.75")    # engagementRate
        ]

        mock_row2 = Mock()
        mock_row2.dimension_values = [
            Mock(value="mobile"),   # deviceCategory
            Mock(value="Android"),  # operatingSystem
            Mock(value="Chrome")    # browser
        ]
        mock_row2.metric_values = [
            Mock(value="800"),   # totalUsers
            Mock(value="900"),   # sessions
            Mock(value="3200"),  # screenPageViews
            Mock(value="0.35"),  # bounceRate
            Mock(value="120.0"), # averageSessionDuration
            Mock(value="0.65")   # engagementRate
        ]

        mock_response.rows = [mock_row1, mock_row2]
        mock_run_report.return_value = mock_response

        # Mock date range
        mock_create_range.return_value = Mock()

        # Mock filename
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_device_performance("2025-11-01", "2025-11-07")

        # Should return results
        assert result is not None
        assert "desktop" in result
        assert "mobile" in result
        assert len(result) == 2

        # Verify API was called with correct parameters
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args

        # Check dimensions include deviceCategory, operatingSystem, browser
        dimensions = call_args[1]["dimensions"]
        assert "deviceCategory" in dimensions
        assert "operatingSystem" in dimensions
        assert "browser" in dimensions

        # Check metrics
        metrics = call_args[1]["metrics"]
        assert "totalUsers" in metrics
        assert "sessions" in metrics
        assert "engagementRate" in metrics

    @patch('scripts.device_geo_analysis.run_report')
    def test_analyze_device_performance_no_data(self, mock_run_report):
        """Test device analysis with no data"""
        mock_response = Mock()
        mock_response.row_count = 0
        mock_run_report.return_value = mock_response

        result = analyze_device_performance("2025-11-01", "2025-11-07")

        assert result is None

    @patch('scripts.device_geo_analysis.run_report')
    @patch('scripts.device_geo_analysis.create_date_range')
    @patch('scripts.device_geo_analysis.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_geographic_performance_success(self, mock_to_csv, mock_get_filename, mock_create_range, mock_run_report):
        """Test successful geographic performance analysis"""
        # Mock GA4 response with geo data
        mock_response = Mock()
        mock_response.row_count = 2

        # Mock row data - different countries
        mock_row1 = Mock()
        mock_row1.dimension_values = [
            Mock(value="United States"),  # country
            Mock(value="California"),     # region
            Mock(value="San Francisco")   # city
        ]
        mock_row1.metric_values = [
            Mock(value="500"),   # totalUsers
            Mock(value="600"),   # sessions
            Mock(value="2500"),  # screenPageViews
            Mock(value="0.30"),  # bounceRate
            Mock(value="200.0"), # averageSessionDuration
            Mock(value="0.70")   # engagementRate
        ]

        mock_row2 = Mock()
        mock_row2.dimension_values = [
            Mock(value="United Kingdom"), # country
            Mock(value="England"),        # region
            Mock(value="London")          # city
        ]
        mock_row2.metric_values = [
            Mock(value="300"),   # totalUsers
            Mock(value="350"),   # sessions
            Mock(value="1400"),  # screenPageViews
            Mock(value="0.40"),  # bounceRate
            Mock(value="150.0"), # averageSessionDuration
            Mock(value="0.60")   # engagementRate
        ]

        mock_response.rows = [mock_row1, mock_row2]
        mock_run_report.return_value = mock_response

        # Mock date range
        mock_create_range.return_value = Mock()

        # Mock filename
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_geographic_performance("2025-11-01", "2025-11-07")

        # Should return results
        assert result is not None
        assert "United States" in result
        assert "United Kingdom" in result
        assert len(result) == 2

        # Verify API was called with correct parameters
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args

        # Check dimensions include country, region, city
        dimensions = call_args[1]["dimensions"]
        assert "country" in dimensions
        assert "region" in dimensions
        assert "city" in dimensions

    @patch('scripts.device_geo_analysis.analyze_device_performance')
    @patch('scripts.device_geo_analysis.analyze_geographic_performance')
    @patch('scripts.device_geo_analysis.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_device_geo_all(self, mock_to_csv, mock_get_filename, mock_geo_perf, mock_device_perf):
        """Test combined device and geo analysis"""
        mock_device_perf.return_value = {
            "desktop": {
                "total_users": 1000,
                "total_sessions": 1200,
                "total_pageviews": 5000,
                "avg_bounce_rate": 0.25,
                "avg_duration": 180.5,
                "avg_engagement": 0.75,
                "os_breakdown": {"Windows": 800},
                "browser_breakdown": {"Chrome": 900}
            }
        }
        mock_geo_perf.return_value = {
            "United States": {
                "total_users": 500,
                "total_sessions": 600,
                "total_pageviews": 2500,
                "avg_bounce_rate": 0.30,
                "avg_duration": 200.0,
                "regions": {"California": {"cities": {"San Francisco": {"users": 500, "sessions": 600, "pageviews": 2500}}, "users": 500, "sessions": 600, "pageviews": 2500}}
            }
        }
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_device_geo("all", "2025-11-01", "2025-11-07")

        # Should call both analysis functions
        mock_device_perf.assert_called_once_with("2025-11-01", "2025-11-07")
        mock_geo_perf.assert_called_once_with("2025-11-01", "2025-11-07")

        # Should return combined results
        assert result is not None
        assert "device" in result
        assert "geo" in result

    def test_get_last_30_days_range(self):
        """Test date range calculation"""
        from scripts.device_geo_analysis import get_last_30_days_range

        start_date, end_date = get_last_30_days_range()

        # Should return strings in YYYY-MM-DD format
        assert isinstance(start_date, str)
        assert isinstance(end_date, str)
        assert len(start_date) == 10  # YYYY-MM-DD
        assert len(end_date) == 10

        # End date should be yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        assert end_date == yesterday