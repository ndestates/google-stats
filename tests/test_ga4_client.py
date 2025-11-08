"""
Tests for GA4 client module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.ga4_client import (
    create_date_range,
    create_dimensions,
    create_metrics,
    run_report,
    get_yesterday_date,
    get_last_30_days_range,
    get_report_filename
)


class TestGA4Client:
    """Test GA4 client functions"""

    def test_create_date_range(self):
        """Test date range creation"""
        start_date = "2025-11-01"
        end_date = "2025-11-07"
        date_range = create_date_range(start_date, end_date)

        assert date_range.start_date == start_date
        assert date_range.end_date == end_date

    def test_create_dimensions(self):
        """Test dimension creation"""
        dimension_names = ["pagePath", "sessionSourceMedium", "deviceCategory"]
        dimensions = create_dimensions(dimension_names)

        assert len(dimensions) == 3
        assert dimensions[0].name == "pagePath"
        assert dimensions[1].name == "sessionSourceMedium"
        assert dimensions[2].name == "deviceCategory"

    def test_create_metrics(self):
        """Test metric creation"""
        metric_names = ["totalUsers", "sessions", "screenPageViews", "bounceRate"]
        metrics = create_metrics(metric_names)

        assert len(metrics) == 4
        assert metrics[0].name == "totalUsers"
        assert metrics[1].name == "sessions"
        assert metrics[2].name == "screenPageViews"
        assert metrics[3].name == "bounceRate"

    def test_get_yesterday_date(self):
        """Test yesterday date calculation"""
        yesterday = get_yesterday_date()
        expected = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        assert yesterday == expected
        assert len(yesterday) == 10  # YYYY-MM-DD format

    def test_get_last_30_days_range(self):
        """Test 30-day date range calculation"""
        start_date, end_date = get_last_30_days_range()

        # Should be 30 days total (29 days back from yesterday)
        expected_end = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        expected_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        assert end_date == expected_end
        assert start_date == expected_start

    def test_get_report_filename(self):
        """Test report filename generation"""
        report_type = "page_traffic"
        date_suffix = "2025-11-01_to_2025-11-07"

        filename = get_report_filename(report_type, date_suffix)

        assert "page_traffic" in filename
        assert "2025-11-01_to_2025-11-07" in filename
        assert filename.endswith(".csv")

    @patch('src.ga4_client.get_ga4_client')
    def test_run_report_success(self, mock_get_client, mock_ga4_response):
        """Test successful report execution"""
        mock_client = Mock()
        mock_client.run_report.return_value = mock_ga4_response
        mock_get_client.return_value = mock_client

        dimensions = ["pagePath", "sessionSourceMedium"]
        metrics = ["totalUsers", "sessions"]
        date_ranges = [create_date_range("2025-11-01", "2025-11-07")]

        response = run_report(dimensions, metrics, date_ranges)

        assert response.row_count == 3
        mock_client.run_report.assert_called_once()

        # Verify the request structure
        call_args = mock_client.run_report.call_args[0][0]
        assert len(call_args.dimensions) == 2
        assert len(call_args.metrics) == 2
        assert len(call_args.date_ranges) == 1

    @patch('src.ga4_client.get_ga4_client')
    def test_run_report_with_order_by(self, mock_get_client, mock_ga4_response):
        """Test report execution with ordering"""
        from google.analytics.data_v1beta.types import OrderBy

        mock_client = Mock()
        mock_client.run_report.return_value = mock_ga4_response
        mock_get_client.return_value = mock_client

        dimensions = ["pagePath"]
        metrics = ["totalUsers", "sessions"]
        date_ranges = [create_date_range("2025-11-01", "2025-11-07")]
        order_bys = [OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)]

        response = run_report(dimensions, metrics, date_ranges, order_bys)

        assert response.row_count == 3
        call_args = mock_client.run_report.call_args[0][0]
        assert len(call_args.order_bys) == 1

    @patch('src.ga4_client.get_ga4_client')
    def test_run_report_with_limit(self, mock_get_client, mock_ga4_response):
        """Test report execution with row limit"""
        mock_client = Mock()
        mock_client.run_report.return_value = mock_ga4_response
        mock_get_client.return_value = mock_client

        dimensions = ["pagePath"]
        metrics = ["totalUsers"]
        date_ranges = [create_date_range("2025-11-01", "2025-11-07")]

        response = run_report(dimensions, metrics, date_ranges, limit=100)

        call_args = mock_client.run_report.call_args[0][0]
        assert call_args.limit == 100

    @patch('src.ga4_client.get_ga4_client')
    def test_run_report_api_error(self, mock_get_client):
        """Test report execution with API error"""
        mock_client = Mock()
        mock_client.run_report.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        dimensions = ["pagePath"]
        metrics = ["totalUsers"]
        date_ranges = [create_date_range("2025-11-01", "2025-11-07")]

        with pytest.raises(Exception, match="API Error"):
            run_report(dimensions, metrics, date_ranges)