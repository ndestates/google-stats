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

# Google Search Console Configuration
GSC_SITE_URL = os.getenv("GSC_SITE_URL")
GSC_KEY_PATH = os.getenv("GSC_KEY_PATH")

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

def validate_gsc_config():
    """Validate that GSC environment variables are set"""
    if not GSC_SITE_URL:
        raise ValueError("GSC_SITE_URL environment variable is not set. Please check your .env file.")
    if not GSC_KEY_PATH:
        raise ValueError("GSC_KEY_PATH environment variable is not set. Please check your .env file.")
    # Don't raise error if key file doesn't exist - let the script handle it gracefully

def get_ga4_admin_client():
    """Get authenticated GA4 Admin API client"""
    from google.analytics.admin_v1beta import AnalyticsAdminServiceClient

    # Set environment variable for authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GA4_KEY_PATH

    # Validate configuration
    validate_config()

    return AnalyticsAdminServiceClient()

def get_ga4_client():
    """Get authenticated GA4 Data API client"""
    from google.analytics.data_v1beta import BetaAnalyticsDataClient

    # Set environment variable for authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GA4_KEY_PATH

    # Validate configuration
    validate_config()

    return BetaAnalyticsDataClient()

def get_gsc_client():
    """Get authenticated Google Search Console client"""
    from googleapiclient.discovery import build
    from google.oauth2 import service_account

    # Validate GSC configuration
    validate_gsc_config()

    # Check if key file exists
    if not os.path.exists(GSC_KEY_PATH):
        raise FileNotFoundError(f"GSC service account key not found at {GSC_KEY_PATH}. Please check the path.")

    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(
        GSC_KEY_PATH,
        scopes=['https://www.googleapis.com/auth/webmasters.readonly']
    )

    return build('webmasters', 'v3', credentials=credentials)