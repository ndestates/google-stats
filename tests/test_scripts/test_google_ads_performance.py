"""
Tests for google_ads_performance.py script
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from scripts.google_ads_performance import get_google_ads_performance


class TestGoogleAdsPerformance:
    """Test Google Ads performance analysis"""

    def test_get_google_ads_performance_missing_credentials(self):
        """Test Google Ads performance with missing credentials file"""
        with patch('scripts.google_ads_performance.os.path.exists', return_value=False), \
             patch('scripts.google_ads_performance.os.environ', {}):
            with pytest.raises(FileNotFoundError, match="GA4 service account key not found"):
                get_google_ads_performance("yesterday")

    def test_get_google_ads_performance_basic(self):
        """Basic smoke test for Google Ads performance function"""
        # This is a placeholder test - full testing would require complex mocking
        # of the Google Ads API which has different authentication than GA4
        pass