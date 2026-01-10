"""
Google Analytics 4 Configuration Module
Handles environment variables and GA4 client setup

Enhanced with database-backed encrypted credential storage for improved security.
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if we should use database credentials (recommended for production)
USE_DATABASE_CREDENTIALS = os.getenv("USE_DATABASE_CREDENTIALS", "false").lower() == "true"

# GA4 Configuration
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")
GA4_KEY_PATH = os.getenv("GA4_KEY_PATH")  # Legacy file-based path (fallback)

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

# Credential manager singleton
_credential_manager = None

def get_credential_manager():
    """Get or create credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        try:
            from src.credential_manager import DatabaseCredentialManager
            _credential_manager = DatabaseCredentialManager()
        except Exception as e:
            # If database credentials fail, we'll fall back to file-based
            pass
    return _credential_manager

def get_ga4_credentials_path():
    """
    Get GA4 credentials path - from database or file
    
    Returns path to credential file (temporary if from database)
    """
    if USE_DATABASE_CREDENTIALS:
        try:
            manager = get_credential_manager()
            if manager:
                return manager.get_credential_as_temp_file("GA4 Service Account", "google_token")
        except Exception as e:
            print(f"⚠️  Database credential retrieval failed, falling back to file: {e}")
    
    # Fall back to file-based credential
    if not GA4_KEY_PATH:
        raise ValueError("GA4_KEY_PATH environment variable is not set and database credentials not available.")
    if not os.path.exists(GA4_KEY_PATH):
        raise FileNotFoundError(f"GA4 service account key not found at {GA4_KEY_PATH}")
    
    return GA4_KEY_PATH

def validate_config():
    """Validate that all required environment variables are set"""
    if not GA4_PROPERTY_ID:
        raise ValueError("GA4_PROPERTY_ID environment variable is not set. Please check your .env file.")
    
    # Try to get credentials (will raise error if neither database nor file available)
    try:
        get_ga4_credentials_path()
    except Exception as e:
        raise ValueError(f"GA4 credentials not available: {e}")

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

    # Validate configuration
    validate_config()
    
    # Get credentials path (from database or file)
    cred_path = get_ga4_credentials_path()
    
    # Set environment variable for authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

    return AnalyticsAdminServiceClient()

def get_ga4_client():
    """Get authenticated GA4 Data API client"""
    from google.analytics.data_v1beta import BetaAnalyticsDataClient

    # Validate configuration
    validate_config()
    
    # Get credentials path (from database or file)
    cred_path = get_ga4_credentials_path()
    
    # Set environment variable for authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

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
GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID")  # Your target account ID (no hyphens in queries)
GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
GOOGLE_ADS_JSON_KEY_PATH = os.getenv("GOOGLE_ADS_JSON_KEY_PATH")  # New: path to your service account JSON key
GOOGLE_ADS_LOGIN_CUSTOMER_ID = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")  # Usually your manager account ID (required for service accounts)

def load_google_ads_config():
    """Load Google Ads configuration for service account authentication"""
    if not all([GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_JSON_KEY_PATH, GOOGLE_ADS_LOGIN_CUSTOMER_ID]):
        raise ValueError("Missing required Google Ads service account config in .env file.")
    
    config = {
        "developer_token": GOOGLE_ADS_DEVELOPER_TOKEN,
        "json_key_file_path": GOOGLE_ADS_JSON_KEY_PATH,
        "login_customer_id": GOOGLE_ADS_LOGIN_CUSTOMER_ID,  # Manager account ID
        "use_proto_plus": True,
    }
    return config

def get_google_ads_client():
    """Get authenticated Google Ads API client using service account"""
    try:
        from google.ads.googleads.client import GoogleAdsClient

        config = load_google_ads_config()
        client = GoogleAdsClient.load_from_dict(config)
        return client
    except ImportError:
        raise ImportError("Google Ads API not available. Install with: pip install google-ads")
    except Exception as e:
        raise Exception(f"Could not initialize Google Ads client: {e}")