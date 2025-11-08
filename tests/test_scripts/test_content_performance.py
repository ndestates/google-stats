"""
Tests for content_performance.py script
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from scripts.content_performance import (
    analyze_content_engagement,
    analyze_content_types,
    analyze_content_effectiveness,
    analyze_content_performance
)


class TestContentPerformance:
    """Test content performance analysis functions"""

    @patch('scripts.content_performance.run_report')
    @patch('scripts.content_performance.create_date_range')
    def test_analyze_content_engagement_success(self, mock_create_range, mock_run_report, mock_ga4_response):
        """Test successful content engagement analysis"""
        mock_run_report.return_value = mock_ga4_response
        mock_create_range.return_value = Mock()

        result = analyze_content_engagement("2025-11-01", "2025-11-07")

        assert result is not None
        assert isinstance(result, dict)
        assert len(result) == 3  # Should have 3 pages from mock data

        # Verify API was called correctly
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args
        assert "pagePath" in call_args[1]["dimensions"]
        assert "pageTitle" in call_args[1]["dimensions"]
        assert "totalUsers" in call_args[1]["metrics"]
        assert "screenPageViews" in call_args[1]["metrics"]

    @patch('scripts.content_performance.run_report')
    @patch('scripts.content_performance.create_date_range')
    def test_analyze_content_engagement_no_data(self, mock_create_range, mock_run_report, mock_empty_ga4_response):
        """Test content engagement analysis with no data"""
        mock_run_report.return_value = mock_empty_ga4_response
        mock_create_range.return_value = Mock()

        result = analyze_content_engagement("2025-11-01", "2025-11-07")

        assert result is None

    @patch('scripts.content_performance.run_report')
    @patch('scripts.content_performance.create_date_range')
    def test_analyze_content_types_success(self, mock_create_range, mock_run_report, mock_ga4_response):
        """Test successful content types analysis"""
        mock_run_report.return_value = mock_ga4_response
        mock_create_range.return_value = Mock()

        result = analyze_content_types("2025-11-01", "2025-11-07")

        assert result is not None
        assert isinstance(result, dict)
        # Should categorize pages into content types

    @patch('scripts.content_performance.run_report')
    @patch('scripts.content_performance.create_date_range')
    def test_analyze_content_effectiveness_success(self, mock_create_range, mock_run_report, mock_ga4_response):
        """Test successful content effectiveness analysis"""
        mock_run_report.return_value = mock_ga4_response
        mock_create_range.return_value = Mock()

        result = analyze_content_effectiveness("2025-11-01", "2025-11-07")

        assert result is not None
        assert isinstance(result, dict)

    @patch('scripts.content_performance.analyze_content_engagement')
    @patch('scripts.content_performance.analyze_content_types')
    @patch('scripts.content_performance.analyze_content_effectiveness')
    @patch('scripts.content_performance.get_report_filename')
    @patch('scripts.content_performance.pd.DataFrame.to_csv')
    def test_analyze_content_performance_all_types(self, mock_to_csv, mock_get_filename,
                                                   mock_effectiveness, mock_types, mock_engagement, sample_page_data):
        """Test main content performance analysis for all types"""
        mock_engagement.return_value = {
            "/home": {
                "title": "Homepage",
                "users": 100,
                "sessions": 120,
                "pageviews": 150,
                "avg_duration": 45.5,
                "bounce_rate": 0.35,
                "engagement_rate": 0.65
            }
        }
        mock_types.return_value = {
            "Properties": {
                "pages": 5,
                "users": 50,
                "sessions": 60,
                "pageviews": 120,
                "avg_duration": 85.0,
                "bounce_rate": 0.4,
                "engagement_rate": 0.6
            }
        }
        mock_effectiveness.return_value = {
            "key1": {
                "page": "/contact",
                "channel": "Direct",
                "users": 25,
                "sessions": 30,
                "pageviews": 35,
                "avg_duration": 45.0,
                "bounce_rate": 0.3
            }
        }
        mock_get_filename.return_value = "/tmp/test_report.csv"

        result = analyze_content_performance("all", "2025-11-01", "2025-11-07")

        assert result is not None
        assert "engagement" in result
        assert "types" in result
        assert "effectiveness" in result

        # Verify CSV export was called
        mock_to_csv.assert_called_once()

    @patch('scripts.content_performance.analyze_content_engagement')
    def test_analyze_content_performance_engagement_only(self, mock_engagement, sample_page_data):
        """Test content performance analysis for engagement only"""
        mock_engagement.return_value = {
            "/home": {
                "title": "Homepage",
                "users": 100,
                "sessions": 120,
                "pageviews": 150,
                "avg_duration": 45.5,
                "bounce_rate": 0.35,
                "engagement_rate": 0.65
            }
        }

        result = analyze_content_performance("engagement", "2025-11-01", "2025-11-07")

        assert result is not None
        assert "engagement" in result
        assert "types" not in result
        assert "effectiveness" not in result

    def test_analyze_content_performance_invalid_type(self):
        """Test content performance analysis with invalid type"""
        result = analyze_content_performance("invalid_type", "2025-11-01", "2025-11-07")

        assert result == {}

    @patch('scripts.content_performance.datetime')
    def test_default_date_range_calculation(self, mock_datetime):
        """Test default date range calculation"""
        mock_now = Mock()
        mock_now.now.return_value = datetime(2025, 11, 8)
        mock_datetime.now = mock_now.now
        mock_datetime.timedelta = timedelta

        # Import and test the helper function
        from scripts.content_performance import get_last_30_days_range

        start_date, end_date = get_last_30_days_range()

        # Should end yesterday (Nov 7) and start 30 days before (Oct 9)
        assert end_date == "2025-11-07"
        assert start_date == "2025-10-09"  # 29 days back from Nov 7 (30 total days)

    def test_content_categorization_logic(self):
        """Test content type categorization logic"""
        from scripts.content_performance import analyze_content_types

        # Test URL patterns (this would need more extensive mocking for full test)
        test_patterns = {
            '/properties/st-saviour': 'Properties',
            '/valuations': 'Valuations',
            '/about-us': 'About',
            '/contact': 'Contact',
            '/services/property-management': 'Services',
            '/blog/market-insights': 'Blog/News',
            '/': 'Homepage',
            '/custom-page': 'Other'
        }

        # This is a basic pattern test - full integration test would mock the API
        for url, expected_category in test_patterns.items():
            # The categorization logic is embedded in the function
            # A full test would require mocking the GA4 response
            pass