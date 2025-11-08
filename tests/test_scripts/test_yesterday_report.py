"""
Tests for yesterday_report.py script
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from scripts.yesterday_report import get_yesterday_report


class TestYesterdayReport:
    """Test yesterday report generation"""

    @patch('scripts.yesterday_report.run_report')
    @patch('scripts.yesterday_report.create_date_range')
    @patch('scripts.yesterday_report.get_yesterday_date')
    @patch('scripts.yesterday_report.create_yesterday_report_pdf')
    def test_get_yesterday_report_success(self, mock_pdf, mock_get_date, mock_create_range, mock_run_report, mock_ga4_response):
        """Test successful yesterday report generation"""
        mock_run_report.return_value = mock_ga4_response
        mock_get_date.return_value = "2025-11-07"
        mock_create_range.return_value = Mock()

        result = get_yesterday_report()

        # Should not return anything (prints to console)
        assert result is None

        # Verify API was called with correct parameters
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args

        # Check dimensions include pagePath, sessionSourceMedium, sessionCampaignName
        dimensions = call_args[1]["dimensions"]
        assert "pagePath" in dimensions
        assert "sessionSourceMedium" in dimensions
        assert "sessionCampaignName" in dimensions

        # Check metrics
        metrics = call_args[1]["metrics"]
        assert "totalUsers" in metrics
        assert "sessions" in metrics
        assert "screenPageViews" in metrics
        assert "averageSessionDuration" in metrics
        assert "bounceRate" in metrics

        # Check date range (should be yesterday to yesterday)
        mock_create_range.assert_called_once_with("2025-11-07", "2025-11-07")

    @patch('scripts.yesterday_report.run_report')
    @patch('scripts.yesterday_report.create_date_range')
    @patch('scripts.yesterday_report.get_yesterday_date')
    def test_get_yesterday_report_no_data(self, mock_get_date, mock_create_range, mock_run_report, mock_empty_ga4_response):
        """Test yesterday report with no data"""
        mock_run_report.return_value = mock_empty_ga4_response
        mock_get_date.return_value = "2025-11-07"
        mock_create_range.return_value = Mock()

        result = get_yesterday_report()

        assert result is None

    @patch('scripts.yesterday_report.run_report')
    @patch('scripts.yesterday_report.create_date_range')
    @patch('scripts.yesterday_report.get_yesterday_date')
    @patch('scripts.yesterday_report.create_yesterday_report_pdf')
    def test_yesterday_report_data_processing(self, mock_pdf, mock_get_date, mock_create_range, mock_run_report, mock_ga4_response):
        """Test data processing in yesterday report"""
        mock_run_report.return_value = mock_ga4_response
        mock_get_date.return_value = "2025-11-07"
        mock_create_range.return_value = Mock()

        get_yesterday_report()

        # Verify the report processes the mock data correctly
        # The function should handle 3 rows of data from mock_ga4_response
        # Each row should be processed into page_data structure

        # This is mainly a smoke test - the actual data processing assertions
        # would require capturing print output or mocking file writes

    @patch('scripts.yesterday_report.get_yesterday_date')
    def test_yesterday_date_calculation(self, mock_get_date):
        """Test that yesterday date is calculated correctly"""
        # This test verifies the date calculation logic
        expected_yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Call the actual function (not mocked)
        from scripts.yesterday_report import get_yesterday_report
        # We can't easily test the full function without mocking,
        # but we can test the date helper function

        actual_yesterday = mock_get_date.return_value
        mock_get_date.assert_not_called()  # Should call the real function

        # Test the imported function directly
        from src.ga4_client import get_yesterday_date
        real_yesterday = get_yesterday_date()
        assert real_yesterday == expected_yesterday

    @patch('scripts.yesterday_report.run_report')
    @patch('scripts.yesterday_report.create_date_range')
    @patch('scripts.yesterday_report.get_yesterday_date')
    @patch('scripts.yesterday_report.create_yesterday_report_pdf')
    def test_yesterday_report_ordering(self, mock_pdf, mock_get_date, mock_create_range, mock_run_report, mock_ga4_response):
        """Test that yesterday report uses correct ordering"""
        from google.analytics.data_v1beta.types import OrderBy

        mock_run_report.return_value = mock_ga4_response
        mock_get_date.return_value = "2025-11-07"
        mock_create_range.return_value = Mock()

        get_yesterday_report()

        # Verify ordering is correct
        call_args = mock_run_report.call_args
        order_bys = call_args[1]["order_bys"]

        assert len(order_bys) == 2
        # First order by pagePath ascending, then by totalUsers descending
        assert order_bys[0].dimension.dimension_name == "pagePath"
        assert not order_bys[0].desc
        assert order_bys[1].metric.metric_name == "totalUsers"
        assert order_bys[1].desc