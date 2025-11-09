"""
Tests for user_behavior.py script
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from scripts.user_behavior import analyze_user_flow, analyze_navigation_paths, analyze_user_behavior


class TestUserBehavior:
    """Test user behavior analysis"""

    @patch('scripts.user_behavior.run_report')
    @patch('scripts.user_behavior.create_date_range')
    @patch('scripts.user_behavior.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_user_flow_success(self, mock_to_csv, mock_get_filename, mock_create_range, mock_run_report):
        """Test successful user flow analysis"""
        # Mock GA4 response with user flow data
        mock_response = Mock()
        mock_response.row_count = 3

        # Mock row data - user flow paths
        mock_row1 = Mock()
        mock_row1.dimension_values = [
            Mock(value="/"),              # pagePath
            Mock(value="/properties"),    # landingPage
            Mock(value="/contact")        # exitPage
        ]
        mock_row1.metric_values = [
            Mock(value="1000"),  # totalUsers
            Mock(value="1200"),  # sessions
            Mock(value="1500"),  # pageviews
            Mock(value="800"),   # entrances
            Mock(value="200")    # exits
        ]

        mock_row2 = Mock()
        mock_row2.dimension_values = [
            Mock(value="/properties"),    # pagePath
            Mock(value="/"),              # landingPage
            Mock(value="/contact")        # exitPage
        ]
        mock_row2.metric_values = [
            Mock(value="800"),   # totalUsers
            Mock(value="950"),   # sessions
            Mock(value="1200"),  # pageviews
            Mock(value="600"),   # entrances
            Mock(value="150")    # exits
        ]

        mock_row3 = Mock()
        mock_row3.dimension_values = [
            Mock(value="/contact"),       # pagePath
            Mock(value="/properties"),    # landingPage
            Mock(value="/thank-you")      # exitPage
        ]
        mock_row3.metric_values = [
            Mock(value="600"),   # totalUsers
            Mock(value="700"),   # sessions
            Mock(value="900"),   # pageviews
            Mock(value="400"),   # entrances
            Mock(value="100")    # exits
        ]

        mock_response.rows = [mock_row1, mock_row2, mock_row3]
        mock_run_report.return_value = mock_response

        # Mock date range
        mock_create_range.return_value = Mock()

        # Mock filename
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_user_flow("2025-11-01", "2025-11-07")

        # Should return results
        assert result is not None
        assert isinstance(result, dict)
        assert len(result) == 3  # Three pages analyzed
        assert "/" in result
        assert "/properties" in result
        assert "/contact" in result

        # Verify API was called with correct parameters
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args

        # Check dimensions include pagePath, landingPage, exitPage
        dimensions = call_args[1]["dimensions"]
        assert "pagePath" in dimensions
        assert "landingPage" in dimensions
        assert "exitPage" in dimensions

        # Check metrics
        metrics = call_args[1]["metrics"]
        assert "totalUsers" in metrics
        assert "sessions" in metrics
        assert "pageviews" in metrics
        assert "entrances" in metrics
        assert "exits" in metrics

    @patch('scripts.user_behavior.run_report')
    def test_analyze_user_flow_no_data(self, mock_run_report):
        """Test user flow analysis with no data"""
        mock_response = Mock()
        mock_response.row_count = 0
        mock_run_report.return_value = mock_response

        result = analyze_user_flow("2025-11-01", "2025-11-07")

        assert result is None

    @patch('scripts.user_behavior.run_report')
    @patch('scripts.user_behavior.create_date_range')
    @patch('scripts.user_behavior.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_navigation_paths_success(self, mock_to_csv, mock_get_filename, mock_create_range, mock_run_report):
        """Test successful navigation paths analysis"""
        # Mock GA4 response with navigation data
        mock_response = Mock()
        mock_response.row_count = 2

        # Mock row data - navigation paths
        mock_row1 = Mock()
        mock_row1.dimension_values = [
            Mock(value="/properties"),    # pagePath
            Mock(value="/")               # previousPagePath
        ]
        mock_row1.metric_values = [
            Mock(value="500"),   # totalUsers
            Mock(value="600")    # sessions
        ]

        mock_row2 = Mock()
        mock_row2.dimension_values = [
            Mock(value="/"),              # pagePath
            Mock(value="/properties")     # previousPagePath
        ]
        mock_row2.metric_values = [
            Mock(value="400"),   # totalUsers
            Mock(value="450")    # sessions
        ]

        mock_response.rows = [mock_row1, mock_row2]
        mock_run_report.return_value = mock_response

        # Mock date range
        mock_create_range.return_value = Mock()

        # Mock filename
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_navigation_paths("2025-11-01", "2025-11-07")

        # Should return results
        assert result is not None
        assert isinstance(result, dict)
        assert "transitions" in result
        assert "probabilities" in result

        # Verify API was called with correct parameters
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args

        # Check dimensions include pagePath, previousPagePath
        dimensions = call_args[1]["dimensions"]
        assert "pagePath" in dimensions
        assert "previousPagePath" in dimensions

        # Check metrics
        metrics = call_args[1]["metrics"]
        assert "totalUsers" in metrics
        assert "sessions" in metrics

    @patch('scripts.user_behavior.analyze_behavior_patterns')
    @patch('scripts.user_behavior.analyze_navigation_paths')
    @patch('scripts.user_behavior.analyze_user_flow')
    @patch('scripts.user_behavior.get_report_filename')
    @patch('pandas.DataFrame.to_csv')
    def test_analyze_user_behavior_all(self, mock_to_csv, mock_get_filename, mock_user_flow, mock_nav_paths, mock_behavior_patterns):
        """Test combined user behavior analysis"""
        mock_user_flow.return_value = {
            "/": {
                "total_users": 1000,
                "total_sessions": 1200,
                "total_pageviews": 1500,
                "total_entrances": 800,
                "total_exits": 200,
                "landing_pages": {},
                "exit_pages": {}
            }
        }
        mock_nav_paths.return_value = {"transitions": {}, "probabilities": {}}
        mock_behavior_patterns.return_value = {
            "organic": {
                "/": {"users": 500, "sessions": 600, "pageviews": 800, "avg_duration": 120.0, "bounce_rate": 0.3, "engagement_rate": 0.7}
            }
        }
        mock_get_filename.return_value = "/path/to/report.csv"

        result = analyze_user_behavior("all", "2025-11-01", "2025-11-07")

        # Should call all analysis functions
        mock_user_flow.assert_called_once_with("2025-11-01", "2025-11-07")
        mock_nav_paths.assert_called_once_with("2025-11-01", "2025-11-07")
        mock_behavior_patterns.assert_called_once_with("2025-11-01", "2025-11-07")

        # Should return combined results
        assert result is not None
        assert "flow" in result
        assert "paths" in result
        assert "behavior" in result

    def test_get_last_30_days_range(self):
        """Test date range calculation"""
        from scripts.user_behavior import get_last_30_days_range

        start_date, end_date = get_last_30_days_range()

        # Should return strings in YYYY-MM-DD format
        assert isinstance(start_date, str)
        assert isinstance(end_date, str)
        assert len(start_date) == 10  # YYYY-MM-DD
        assert len(end_date) == 10

        # End date should be yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        assert end_date == yesterday