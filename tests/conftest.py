"""
Pytest configuration and fixtures for Google Analytics testing
"""

import os
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

# Mock GA4 API response structure
@pytest.fixture
def mock_ga4_response():
    """Mock GA4 RunReportResponse with sample data"""
    mock_response = Mock()
    mock_response.row_count = 3

    # Create mock rows
    mock_row1 = Mock()
    mock_row1.dimension_values = [
        Mock(value="/home"),  # pagePath
        Mock(value="google / organic"),  # sessionSourceMedium
        Mock(value="(not set)")  # sessionCampaignName
    ]
    mock_row1.metric_values = [
        Mock(value="100"),  # totalUsers
        Mock(value="120"),  # sessions
        Mock(value="150"),  # screenPageViews
        Mock(value="45.5"),  # averageSessionDuration
        Mock(value="0.35"),  # bounceRate
        Mock(value="0.65")   # engagementRate
    ]

    mock_row2 = Mock()
    mock_row2.dimension_values = [
        Mock(value="/properties"),
        Mock(value="google / cpc"),
        Mock(value="spring_campaign")
    ]
    mock_row2.metric_values = [
        Mock(value="75"),
        Mock(value="80"),
        Mock(value="95"),
        Mock(value="120.0"),
        Mock(value="0.25"),
        Mock(value="0.75")
    ]

    mock_row3 = Mock()
    mock_row3.dimension_values = [
        Mock(value="/contact"),
        Mock(value="direct / (none)"),
        Mock(value="(not set)")
    ]
    mock_row3.metric_values = [
        Mock(value="50"),
        Mock(value="55"),
        Mock(value="60"),
        Mock(value="30.0"),
        Mock(value="0.45"),
        Mock(value="0.55")
    ]

    mock_response.rows = [mock_row1, mock_row2, mock_row3]
    return mock_response

@pytest.fixture
def mock_empty_ga4_response():
    """Mock GA4 response with no data"""
    mock_response = Mock()
    mock_response.row_count = 0
    mock_response.rows = []
    return mock_response

@pytest.fixture
def mock_ga4_client():
    """Mock GA4 client for testing"""
    with patch('src.config.get_ga4_client') as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_ga4_client_class():
    """Mock GA4 client class for testing"""
    with patch('google.analytics.data_v1beta.BetaAnalyticsDataClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        yield mock_client_class

@pytest.fixture
def sample_date_ranges():
    """Sample date ranges for testing"""
    return {
        'yesterday': ('2025-11-07', '2025-11-07'),
        'last_7_days': ('2025-11-01', '2025-11-07'),
        'last_30_days': ('2025-10-09', '2025-11-07'),
        'custom_range': ('2025-10-01', '2025-10-31')
    }

@pytest.fixture
def temp_reports_dir(tmp_path):
    """Temporary directory for test reports"""
    reports_dir = tmp_path / "test_reports"
    reports_dir.mkdir()
    return str(reports_dir)

@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables and file paths"""
    with patch.dict(os.environ, {
        'GOOGLE_APPLICATION_CREDENTIALS': '/fake/path/to/credentials.json'
    }), \
    patch('src.config.REPORTS_DIR', '/tmp/test_reports'), \
    patch('src.config.GA4_PROPERTY_ID', '123456789'), \
    patch('src.config.GA4_KEY_PATH', '/fake/path/to/credentials.json'), \
    patch('os.path.exists', return_value=True):
        yield

# Test data fixtures
@pytest.fixture
def sample_page_data():
    """Sample page traffic data for testing"""
    return {
        '/home': {
            'pagePath': '/home',
            'title': 'Homepage',
            'totalUsers': 100,
            'sessions': 120,
            'screenPageViews': 150,
            'averageSessionDuration': 45.5,
            'bounceRate': 0.35,
            'engagementRate': 0.65
        },
        '/properties': {
            'pagePath': '/properties',
            'title': 'Properties Page',
            'totalUsers': 75,
            'sessions': 80,
            'screenPageViews': 95,
            'averageSessionDuration': 120.0,
            'bounceRate': 0.25,
            'engagementRate': 0.75
        }
    }

@pytest.fixture
def sample_channel_data():
    """Sample channel performance data"""
    return {
        'Organic Search': {
            'sessions': 500,
            'users': 450,
            'pageviews': 1200,
            'avg_duration': 85.5,
            'bounce_rate': 0.32,
            'engagement_rate': 0.68
        },
        'Direct': {
            'sessions': 300,
            'users': 280,
            'pageviews': 400,
            'avg_duration': 65.0,
            'bounce_rate': 0.45,
            'engagement_rate': 0.55
        },
        'Paid Search': {
            'sessions': 200,
            'users': 180,
            'pageviews': 350,
            'avg_duration': 95.0,
            'bounce_rate': 0.28,
            'engagement_rate': 0.72
        }
    }