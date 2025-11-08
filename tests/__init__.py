"""
Test suite for Google Analytics 4 reporting platform
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add the project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test configuration
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture providing path to test data directory"""
    return TEST_DATA_DIR