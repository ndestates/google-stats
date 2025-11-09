"""
Tests for technical_performance.py script
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from scripts.technical_performance import analyze_load_performance, analyze_errors_events, analyze_technical_performance


class TestTechnicalPerformance:
    """Test technical performance analysis"""

    @patch('scripts.technical_performance.run_report')
    @patch('scripts.technical_performance.create_date_range')
    @patch('scripts.technical_performance.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_load_performance_success(self, mock_to_csv, mock_get_filename, mock_create_range, mock_run_report):
        """Test successful load performance analysis"""
        # Mock GA4 response with performance data
        mock_response = Mock()
        mock_response.row_count = 2

        # Mock row data - page load performance
        mock_row1 = Mock()
        mock_row1.dimension_values = [
            Mock(value="/"),        # pagePath
            Mock(value="desktop")   # deviceCategory
        ]
        mock_row1.metric_values = [
            Mock(value="800"),   # totalUsers
            Mock(value="950"),   # sessions
            Mock(value="0.75"),  # engagementRate
            Mock(value="180.0"), # averageSessionDuration
            Mock(value="0.25")   # bounceRate
        ]

        mock_row2 = Mock()
        mock_row2.dimension_values = [
            Mock(value="/valuations"),  # pagePath
            Mock(value="mobile")        # deviceCategory
        ]
        mock_row2.metric_values = [
            Mock(value="600"),   # totalUsers
            Mock(value="700"),   # sessions
            Mock(value="0.65"),  # engagementRate
            Mock(value="120.0"), # averageSessionDuration
            Mock(value="0.35")   # bounceRate
        ]

        mock_response.rows = [mock_row1, mock_row2]
        mock_run_report.return_value = mock_response

        # Mock date range
        mock_create_range.return_value = Mock()

        # Mock filename
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_load_performance("2025-11-01", "2025-11-07")

        # Should return results
        assert result is not None
        assert isinstance(result, dict)
        assert len(result) == 2  # Two pages analyzed
        assert "/" in result
        assert "/valuations" in result

        # Verify API was called with correct parameters
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args

        # Check dimensions include pagePath, deviceCategory
        dimensions = call_args[1]["dimensions"]
        assert "pagePath" in dimensions
        assert "deviceCategory" in dimensions

        # Check metrics
        metrics = call_args[1]["metrics"]
        assert "totalUsers" in metrics
        assert "sessions" in metrics
        assert "engagementRate" in metrics

    @patch('scripts.technical_performance.run_report')
    def test_analyze_load_performance_no_data(self, mock_run_report):
        """Test load performance analysis with no data"""
        mock_response = Mock()
        mock_response.row_count = 0
        mock_run_report.return_value = mock_response

        result = analyze_load_performance("2025-11-01", "2025-11-07")

        assert result is None

    @patch('scripts.technical_performance.run_report')
    @patch('scripts.technical_performance.create_date_range')
    @patch('scripts.technical_performance.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_error_events_success(self, mock_to_csv, mock_get_filename, mock_create_range, mock_run_report):
        """Test successful error events analysis"""
        # Mock GA4 response with event data
        mock_response = Mock()
        mock_response.row_count = 2

        # Mock row data - custom events
        mock_row1 = Mock()
        mock_row1.dimension_values = [
            Mock(value="form_submit"),  # eventName
            Mock(value="/contact")      # pagePath
        ]
        mock_row1.metric_values = [
            Mock(value="50"),    # eventCount
            Mock(value="45"),    # totalUsers
            Mock(value="0.90")   # eventValue
        ]

        mock_row2 = Mock()
        mock_row2.dimension_values = [
            Mock(value="404_error"),    # eventName
            Mock(value="/missing-page") # pagePath
        ]
        mock_row2.metric_values = [
            Mock(value="25"),    # eventCount
            Mock(value="25"),    # totalUsers
            Mock(value="0.0")    # eventValue
        ]

        mock_response.rows = [mock_row1, mock_row2]
        mock_run_report.return_value = mock_response

        # Mock date range
        mock_create_range.return_value = Mock()

        # Mock filename
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_errors_events("2025-11-01", "2025-11-07")

        # Should return results
        assert result is not None
        assert isinstance(result, dict)
        assert len(result) == 2  # Two events analyzed
        assert "form_submit" in result
        assert "404_error" in result

        # Verify API was called with correct parameters
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args

        # Check dimensions include eventName, pagePath
        dimensions = call_args[1]["dimensions"]
        assert "eventName" in dimensions
        assert "pagePath" in dimensions

        # Check metrics
        metrics = call_args[1]["metrics"]
        assert "eventCount" in metrics
        assert "totalUsers" in metrics

    @patch('scripts.technical_performance.analyze_errors_events')
    @patch('scripts.technical_performance.analyze_load_performance')
    @patch('scripts.technical_performance.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_technical_performance_all(self, mock_to_csv, mock_get_filename, mock_load_perf, mock_error_events):
        """Test combined technical performance analysis"""
        mock_load_perf.return_value = {
            "/": {
                "total_users": 1000,
                "total_sessions": 1200,
                "avg_engagement": 0.75,
                "avg_duration": 180.0,
                "avg_bounce": 0.25,
                "devices": {"desktop": {"sessions": 950, "engagement": 0.75, "duration": 180.0, "bounce": 0.25, "users": 800}}
            }
        }
        mock_error_events.return_value = {
            "404_error": {
                "total_count": 25,
                "total_users": 25,
                "total_value": 0.0,
                "pages": {"/missing-page": 25}
            }
        }
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_technical_performance("all", "2025-11-01", "2025-11-07")

        # Should call both analysis functions
        mock_load_perf.assert_called_once_with("2025-11-01", "2025-11-07")
        mock_error_events.assert_called_once_with("2025-11-01", "2025-11-07")

        # Should return combined results
        assert result is not None
        assert "performance" in result
        assert "events" in result

    def test_get_last_30_days_range(self):
        """Test date range calculation"""
        from scripts.technical_performance import get_last_30_days_range

        start_date, end_date = get_last_30_days_range()

        # Should return strings in YYYY-MM-DD format
        assert isinstance(start_date, str)
        assert isinstance(end_date, str)
        assert len(start_date) == 10  # YYYY-MM-DD
        assert len(end_date) == 10

        # End date should be yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        assert end_date == yesterday