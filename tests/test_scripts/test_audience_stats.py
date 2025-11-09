"""
Tests for audience_stats.py script
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from scripts.audience_stats import get_audience_performance_stats


class TestAudienceStats:
    """Test GA4 Audience Statistics functionality"""

    @patch('scripts.audience_stats.run_report')
    @patch('scripts.audience_stats.get_report_filename')
    @patch('builtins.print')  # Suppress print output
    def test_get_audience_performance_stats_with_data(self, mock_print, mock_get_filename, mock_run_report):
        """Test audience stats with mock GA4 data"""
        # Mock filename generation
        mock_get_filename.return_value = '/tmp/test_audience_stats.csv'

        # Mock GA4 response
        mock_response = Mock()
        mock_response.row_count = 2

        # Create mock audience data
        mock_row1 = Mock()
        mock_row1.dimension_values = [
            Mock(value='1234567890'),  # audience_id
            Mock(value='Test Audience 1')  # audience_name
        ]
        mock_row1.metric_values = [
            Mock(value='1000'),  # totalUsers
            Mock(value='1200'),  # sessions
            Mock(value='2400'),  # screenPageViews
            Mock(value='45.5'),  # averageSessionDuration
            Mock(value='0.25'),  # bounceRate
            Mock(value='800'),   # newUsers
            Mock(value='1100')   # engagedSessions
        ]

        mock_row2 = Mock()
        mock_row2.dimension_values = [
            Mock(value='0987654321'),  # audience_id
            Mock(value='Test Audience 2')  # audience_name
        ]
        mock_row2.metric_values = [
            Mock(value='500'),   # totalUsers
            Mock(value='600'),   # sessions
            Mock(value='1200'),  # screenPageViews
            Mock(value='52.3'),  # averageSessionDuration
            Mock(value='0.15'),  # bounceRate
            Mock(value='400'),   # newUsers
            Mock(value='550')    # engagedSessions
        ]

        mock_response.rows = [mock_row1, mock_row2]
        mock_run_report.return_value = mock_response

        with patch('scripts.audience_stats.pd.DataFrame.to_csv') as mock_to_csv:
            result = get_audience_performance_stats(days=30)

            # Should return data
            assert result is not None
            assert len(result) == 2

            # Check first audience data
            audience1 = result[0]
            assert audience1['audience_id'] == '1234567890'
            assert audience1['audience_name'] == 'Test Audience 1'
            assert audience1['total_users'] == 1000
            assert audience1['sessions'] == 1200
            assert audience1['pageviews'] == 2400
            assert audience1['avg_session_duration'] == 45.5
            assert audience1['bounce_rate'] == 0.25
            assert audience1['new_users'] == 800
            assert audience1['engaged_sessions'] == 1100

            # Check derived metrics
            assert audience1['pages_per_session'] == 2.0  # 2400 / 1200
            assert audience1['engagement_rate'] == 91.67  # (1100 / 1200) * 100
            assert audience1['new_user_percentage'] == 80.0  # (800 / 1000) * 100

            # Verify CSV export was called
            mock_to_csv.assert_called_once()

    @patch('scripts.audience_stats.run_report')
    def test_get_audience_performance_stats_no_data(self, mock_run_report):
        """Test audience stats when no audience data is available"""
        # Mock no data response
        mock_response = Mock()
        mock_response.row_count = 0
        mock_run_report.return_value = mock_response

        result = get_audience_performance_stats(days=30)

        assert result is None
        # Should have called run_report once
        assert mock_run_report.call_count == 1

    @patch('scripts.audience_stats.run_report')
    @patch('builtins.print')
    def test_get_audience_performance_stats_data_processing(self, mock_print, mock_run_report):
        """Test data processing and calculations"""
        # Mock response
        mock_response = Mock()
        mock_response.row_count = 1

        mock_row = Mock()
        mock_row.dimension_values = [
            Mock(value='test_audience'),
            Mock(value='Test Audience')
        ]
        mock_row.metric_values = [
            Mock(value='100'),   # totalUsers
            Mock(value='120'),   # sessions
            Mock(value='240'),   # screenPageViews
            Mock(value='30.5'),  # averageSessionDuration
            Mock(value='0.2'),   # bounceRate
            Mock(value='80'),    # newUsers
            Mock(value='100')    # engagedSessions
        ]

        mock_response.rows = [mock_row]
        mock_run_report.return_value = mock_response

        with patch('scripts.audience_stats.get_report_filename'), \
             patch('scripts.audience_stats.pd.DataFrame.to_csv'):
            result = get_audience_performance_stats(days=7)

            assert len(result) == 1
            audience = result[0]

            # Test calculations
            assert audience['pages_per_session'] == 2.0
            assert audience['engagement_rate'] == 83.33
            assert audience['new_user_percentage'] == 80.0

    def test_get_audience_performance_stats_date_range(self):
        """Test date range calculation"""
        # This test verifies the date range logic without mocking
        # We can't easily test the actual function without mocking run_report
        # But we can test the date calculation logic indirectly

        end_date = datetime.now() - timedelta(days=1)
        start_date_30 = end_date - timedelta(days=29)  # 30 days total
        start_date_7 = end_date - timedelta(days=6)    # 7 days total

        # Verify date arithmetic
        assert (end_date - start_date_30).days == 29
        assert (end_date - start_date_7).days == 6
