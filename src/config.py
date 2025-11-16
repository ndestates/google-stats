"""
Google Analytics 4 Configuration Module
Handles environment variables and GA4 client setup
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GA4 Configuration
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")
GA4_KEY_PATH = os.getenv("GA4_KEY_PATH")

# Property Information (optional - for PDF customization)
PROPERTY_NAME = os.getenv("PROPERTY_NAME", "")
PROPERTY_ADDRESS = os.getenv("PROPERTY_ADDRESS", "")

def get_company_logo_path():
    """Get the stored company logo path from admin settings"""
    try:
        settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "uploads", "settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                logo_path = settings.get('company_logo')
                if logo_path:
                    # Convert relative path to absolute path
                    full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", logo_path)
                    if os.path.exists(full_path):
                        return full_path
    except Exception:
        pass
    return None

def get_default_property_info():
    """Get default property information from admin settings"""
    try:
        settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "uploads", "settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                return {
                    'name': settings.get('default_property_name', ''),
                    'address': settings.get('default_property_address', '')
                }
    except Exception:
        pass
    return {'name': '', 'address': ''}

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

# Google Ads Configuration
GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
GOOGLE_ADS_CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
GOOGLE_ADS_CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
GOOGLE_ADS_REFRESH_TOKEN = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")

def load_google_ads_config():
    """Load Google Ads configuration for client initialization"""
    config = {
        "client_id": GOOGLE_ADS_CLIENT_ID,
        "client_secret": GOOGLE_ADS_CLIENT_SECRET,
        "refresh_token": GOOGLE_ADS_REFRESH_TOKEN,
        "developer_token": GOOGLE_ADS_DEVELOPER_TOKEN,
        "use_proto_plus": True,
    }
    return config if all(config.values()) else None

def get_google_ads_client():
    """Get authenticated Google Ads API client"""
    try:
        from google.ads.googleads.client import GoogleAdsClient

        config = load_google_ads_config()
        if not config:
            raise ValueError("Google Ads configuration not found. Please check your .env file.")

        client = GoogleAdsClient.load_from_dict(config)
        return client
    except ImportError:
        raise ImportError("Google Ads API not available. Install with: pip install google-ads")
    except Exception as e:
        raise Exception(f"Could not initialize Google Ads client: {e}")