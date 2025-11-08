"""
Tests for social_media_timing.py script
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from scripts.social_media_timing import analyze_social_timing, categorize_social_source, is_social_source


class TestSocialMediaTiming:
    """Test social media timing analysis"""

    def test_categorize_social_source_facebook(self):
        """Test Facebook source categorization"""
        assert categorize_social_source("facebook / catalog") == "Facebook"
        assert categorize_social_source("m.facebook.com / referral") == "Facebook"
        assert categorize_social_source("facebook / fb_ads") == "Facebook"

    def test_categorize_social_source_google_social(self):
        """Test Google Social source categorization"""
        assert categorize_social_source("google.com / social") == "Google Social"

    def test_categorize_social_source_other(self):
        """Test other social sources"""
        assert categorize_social_source("twitter.com / social") == "Twitter/X"
        assert categorize_social_source("instagram.com / social") == "Instagram"
        assert categorize_social_source("linkedin.com / social") == "LinkedIn"

    def test_categorize_social_source_non_social(self):
        """Test non-social sources"""
        assert categorize_social_source("google / organic") == "Non-Social"
        assert categorize_social_source("direct / (none)") == "Non-Social"

    def test_is_social_source(self):
        """Test social source detection"""
        assert is_social_source("facebook / catalog") == True
        assert is_social_source("google.com / social") == True
        assert is_social_source("google / organic") == False

    @patch('scripts.social_media_timing.run_report')
    @patch('scripts.social_media_timing.create_date_range')
    @patch('scripts.social_media_timing.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_social_timing_success(self, mock_to_csv, mock_get_filename, mock_create_range, mock_run_report):
        """Test successful social media timing analysis"""
        # Mock GA4 response with social media data
        mock_response = Mock()
        mock_response.row_count = 2

        # Mock row data - Facebook at hour 19, Google Social at hour 16
        mock_row1 = Mock()
        mock_row1.dimension_values = [
            Mock(value="19"),  # hour
            Mock(value="facebook / catalog"),  # source_medium
            Mock(value="Social")  # channel_grouping
        ]
        mock_row1.metric_values = [
            Mock(value="100"),  # totalUsers
            Mock(value="80"),   # newUsers
            Mock(value="120"),  # sessions
            Mock(value="110"),  # engagedSessions
            Mock(value="500"),  # screenPageViews
            Mock(value="180.5"), # averageSessionDuration
            Mock(value="0.15"),  # bounceRate
            Mock(value="0.85")   # engagementRate
        ]

        mock_row2 = Mock()
        mock_row2.dimension_values = [
            Mock(value="16"),  # hour
            Mock(value="google.com / social"),  # source_medium
            Mock(value="Social")  # channel_grouping
        ]
        mock_row2.metric_values = [
            Mock(value="50"),   # totalUsers
            Mock(value="40"),   # newUsers
            Mock(value="60"),   # sessions
            Mock(value="55"),   # engagedSessions
            Mock(value="250"),  # screenPageViews
            Mock(value="160.0"), # averageSessionDuration
            Mock(value="0.20"),  # bounceRate
            Mock(value="0.80")   # engagementRate
        ]

        mock_response.rows = [mock_row1, mock_row2]
        mock_run_report.return_value = mock_response

        # Mock date range
        mock_create_range.return_value = Mock()

        # Mock filenames
        mock_get_filename.side_effect = [
            "/path/to/detailed_report.csv",
            "/path/to/summary_report.csv"
        ]

        result = analyze_social_timing(days_back=7)

        # Should return filenames
        assert result is not None
        assert len(result) == 2

        # Verify API was called with correct parameters
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args

        # Check dimensions include hour, sessionSourceMedium, sessionDefaultChannelGrouping
        dimensions = call_args[1]["dimensions"]
        assert "hour" in dimensions
        assert "sessionSourceMedium" in dimensions
        assert "sessionDefaultChannelGrouping" in dimensions

        # Check metrics
        metrics = call_args[1]["metrics"]
        assert "totalUsers" in metrics
        assert "sessions" in metrics
        assert "engagedSessions" in metrics
        assert "engagementRate" in metrics

        # Verify CSV files were created
        assert mock_to_csv.call_count == 2

    @patch('scripts.social_media_timing.run_report')
    def test_analyze_social_timing_no_data(self, mock_run_report):
        """Test analysis with no data"""
        mock_response = Mock()
        mock_response.row_count = 0
        mock_run_report.return_value = mock_response

        result = analyze_social_timing(days_back=7)

        assert result is None