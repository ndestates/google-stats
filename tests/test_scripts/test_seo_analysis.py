"""
Tests for seo_analysis.py script
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from scripts.seo_analysis import analyze_organic_traffic, analyze_keyword_performance, analyze_seo_health, analyze_seo_performance


class TestSEOAnalysis:
    """Test SEO analysis functions"""

    @patch('scripts.seo_analysis.run_report')
    @patch('scripts.seo_analysis.create_date_range')
    @patch('scripts.seo_analysis.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_organic_traffic_success(self, mock_to_csv, mock_get_filename, mock_create_range, mock_run_report):
        """Test successful organic traffic analysis"""
        # Mock GA4 response with organic traffic data
        mock_response = Mock()
        mock_response.row_count = 2

        # Mock row data - organic search traffic
        mock_row1 = Mock()
        mock_row1.dimension_values = [
            Mock(value="Organic Search"),  # sessionDefaultChannelGrouping
            Mock(value="/")                # pagePath
        ]
        mock_row1.metric_values = [
            Mock(value="1500"),  # totalUsers
            Mock(value="1800"),  # sessions
            Mock(value="7500"),  # pageviews
            Mock(value="240.5"), # averageSessionDuration
            Mock(value="0.25"),  # bounceRate
            Mock(value="0.75")   # engagementRate
        ]

        mock_row2 = Mock()
        mock_row2.dimension_values = [
            Mock(value="Organic Search"),      # sessionDefaultChannelGrouping
            Mock(value="/valuations")          # pagePath
        ]
        mock_row2.metric_values = [
            Mock(value="800"),   # totalUsers
            Mock(value="950"),   # sessions
            Mock(value="3200"),  # pageviews
            Mock(value="180.0"), # averageSessionDuration
            Mock(value="0.35"),  # bounceRate
            Mock(value="0.65")   # engagementRate
        ]

        mock_response.rows = [mock_row1, mock_row2]
        mock_run_report.return_value = mock_response

        # Mock date range
        mock_create_range.return_value = Mock()

        # Mock filename
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_organic_traffic("2025-11-01", "2025-11-07")

        # Should return results
        assert result is not None
        assert "channels" in result
        assert "organic_pages" in result
        assert "Organic Search" in result["channels"]

        # Verify API was called with correct parameters
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args

        # Check dimensions include sessionDefaultChannelGrouping, pagePath
        dimensions = call_args[1]["dimensions"]
        assert "sessionDefaultChannelGrouping" in dimensions
        assert "pagePath" in dimensions

        # Check metrics
        metrics = call_args[1]["metrics"]
        assert "totalUsers" in metrics
        assert "sessions" in metrics
        assert "engagementRate" in metrics

    @patch('scripts.seo_analysis.run_report')
    def test_analyze_organic_traffic_no_data(self, mock_run_report):
        """Test organic traffic analysis with no data"""
        mock_response = Mock()
        mock_response.row_count = 0
        mock_run_report.return_value = mock_response

        result = analyze_organic_traffic("2025-11-01", "2025-11-07")

        assert result is None

    @patch('scripts.seo_analysis.run_report')
    @patch('scripts.seo_analysis.create_date_range')
    @patch('scripts.seo_analysis.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_keyword_performance_success(self, mock_to_csv, mock_get_filename, mock_create_range, mock_run_report):
        """Test successful keyword performance analysis"""
        # Mock GA4 response with keyword data
        mock_response = Mock()
        mock_response.row_count = 2

        # Mock row data - keyword performance
        mock_row1 = Mock()
        mock_row1.dimension_values = [
            Mock(value="(not set)"),  # pagePath
            Mock(value="real estate jersey"),  # firstUserGoogleAdsKeyword
            Mock(value="Organic Search")        # sessionDefaultChannelGrouping
        ]
        mock_row1.metric_values = [
            Mock(value="200"),   # totalUsers
            Mock(value="250"),   # sessions
            Mock(value="800"),   # screenPageViews
            Mock(value="180.0"), # averageSessionDuration
            Mock(value="0.30"),  # bounceRate
            Mock(value="0.70")   # engagementRate
        ]

        mock_row2 = Mock()
        mock_row2.dimension_values = [
            Mock(value="/valuations"),          # pagePath
            Mock(value="property valuation"),   # firstUserGoogleAdsKeyword
            Mock(value="Organic Search")        # sessionDefaultChannelGrouping
        ]
        mock_row2.metric_values = [
            Mock(value="150"),   # totalUsers
            Mock(value="180"),   # sessions
            Mock(value="600"),   # screenPageViews
            Mock(value="200.0"), # averageSessionDuration
            Mock(value="0.25"),  # bounceRate
            Mock(value="0.75")   # engagementRate
        ]

        mock_response.rows = [mock_row1, mock_row2]
        mock_run_report.return_value = mock_response

        # Mock date range
        mock_create_range.return_value = Mock()

        # Mock filename
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_keyword_performance("2025-11-01", "2025-11-07")

        # Should return results
        assert result is not None
        assert isinstance(result, dict)
        assert len(result) >= 1  # At least one keyword theme

        # Verify API was called with correct parameters
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args

        # Check dimensions include pagePath, sessionDefaultChannelGrouping
        dimensions = call_args[1]["dimensions"]
        assert "pagePath" in dimensions
        assert "sessionDefaultChannelGrouping" in dimensions

    @patch('scripts.seo_analysis.run_report')
    @patch('scripts.seo_analysis.create_date_range')
    @patch('scripts.seo_analysis.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_seo_health_success(self, mock_to_csv, mock_get_filename, mock_create_range, mock_run_report):
        """Test successful SEO health analysis"""
        # Mock GA4 response with SEO health data
        mock_response = Mock()
        mock_response.row_count = 2

        # Mock row data - SEO health metrics
        mock_row1 = Mock()
        mock_row1.dimension_values = [
            Mock(value="/"),      # pagePath
            Mock(value="Organic Search")  # sessionDefaultChannelGrouping
        ]
        mock_row1.metric_values = [
            Mock(value="1000"),  # totalUsers
            Mock(value="1200"),  # sessions
            Mock(value="4800"),  # screenPageViews
            Mock(value="220.0"), # averageSessionDuration
            Mock(value="0.28"),  # bounceRate
            Mock(value="0.72")   # engagementRate
        ]

        mock_row2 = Mock()
        mock_row2.dimension_values = [
            Mock(value="/properties"),  # pagePath
            Mock(value="Organic Search")  # sessionDefaultChannelGrouping
        ]
        mock_row2.metric_values = [
            Mock(value="600"),   # totalUsers
            Mock(value="700"),   # sessions
            Mock(value="2100"),  # screenPageViews
            Mock(value="180.0"), # averageSessionDuration
            Mock(value="0.35"),  # bounceRate
            Mock(value="0.65")   # engagementRate
        ]

        mock_response.rows = [mock_row1, mock_row2]
        mock_run_report.return_value = mock_response

        # Mock date range
        mock_create_range.return_value = Mock()

        # Mock filename
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_seo_health("2025-11-01", "2025-11-07")

        # Should return results
        assert result is not None
        assert "device_health" in result
        assert "page_health" in result

    @patch('scripts.seo_analysis.analyze_organic_traffic')
    @patch('scripts.seo_analysis.analyze_keyword_performance')
    @patch('scripts.seo_analysis.analyze_seo_health')
    @patch('scripts.seo_analysis.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_seo_performance_all(self, mock_to_csv, mock_get_filename, mock_seo_health, mock_keyword_perf, mock_organic_traffic):
        """Test combined SEO analysis"""
        mock_organic_traffic.return_value = {"channels": {"Organic Search": {"users": 1000, "sessions": 1200, "pageviews": 5000, "avg_duration": 180.5, "bounce_rate": 0.25, "engagement_rate": 0.75}}, "organic_pages": {"/": {"users": 1000, "sessions": 1200, "pageviews": 5000, "avg_duration": 180.5, "bounce_rate": 0.25, "engagement_rate": 0.75}}}
        mock_keyword_perf.return_value = {"General Property": {"sessions": 500, "users": 400, "pageviews": 2000, "avg_duration": 150.0, "bounce_rate": 0.30, "pages": ["/properties"]}}
        mock_seo_health.return_value = {"device_health": {"desktop": {"sessions": 800, "avg_duration": 200.0, "bounce_rate": 0.25, "engagement_rate": 0.75}}, "page_health": {"/": {"sessions": 800, "avg_duration": 200.0, "bounce_rate": 0.25}}}
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_seo_performance("all", "2025-11-01", "2025-11-07")

        # Should call all analysis functions
        mock_organic_traffic.assert_called_once_with("2025-11-01", "2025-11-07")
        mock_keyword_perf.assert_called_once_with("2025-11-01", "2025-11-07")
        mock_seo_health.assert_called_once_with("2025-11-01", "2025-11-07")

        # Should return combined results
        assert result is not None
        assert "organic" in result
        assert "keywords" in result
        assert "health" in result

    def test_get_last_30_days_range(self):
        """Test date range calculation"""
        from scripts.seo_analysis import get_last_30_days_range

        start_date, end_date = get_last_30_days_range()

        # Should return strings in YYYY-MM-DD format
        assert isinstance(start_date, str)
        assert isinstance(end_date, str)
        assert len(start_date) == 10  # YYYY-MM-DD
        assert len(end_date) == 10

        # End date should be yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        assert end_date == yesterday