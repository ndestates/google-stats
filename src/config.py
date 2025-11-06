"""
Google Analytics 4 Configuration Module
Handles environment variables and GA4 client setup
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GA4 Configuration
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")
GA4_KEY_PATH = os.getenv("GA4_KEY_PATH")

# Reports directory
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")

def validate_config():
    """Validate that all required environment variables are set"""
    if not GA4_PROPERTY_ID:
        raise ValueError("GA4_PROPERTY_ID environment variable is not set. Please check your .env file.")
    if not GA4_KEY_PATH:
        raise ValueError("GA4_KEY_PATH environment variable is not set. Please check your .env file.")
    if not os.path.exists(GA4_KEY_PATH):
        raise FileNotFoundError(f"GA4 service account key not found at {GA4_KEY_PATH}. Please check the path.")

def get_ga4_client():
    """Get authenticated GA4 client"""
    from google.analytics.data_v1beta import BetaAnalyticsDataClient

    # Set environment variable for authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GA4_KEY_PATH

    # Validate configuration
    validate_config()

    return BetaAnalyticsDataClient()