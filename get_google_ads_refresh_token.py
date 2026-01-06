#!/usr/bin/env python3
"""
OAuth flow to get refresh token for Google Ads API
Designed to run in DDEV environment
Loads credentials from .env file

Usage:
    ddev exec python3 get_google_ads_refresh_token.py
    # or
    python3 get_google_ads_refresh_token.py (if running outside DDEV)
"""

import os
import sys
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
CLIENT_ID = os.getenv('GOOGLE_ADS_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_ADS_CLIENT_SECRET')

def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Error: GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET must be set in .env file")
        print("Please update your .env file with the actual values from Google Cloud Console")
        print("\nExample:")
        print("GOOGLE_ADS_CLIENT_ID=123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com")
        print("GOOGLE_ADS_CLIENT_SECRET=ABCdefGHIjklMNOpqrsTUVwxyz")
        return

    print("🔑 Using Client ID:", CLIENT_ID[:50] + "..." if CLIENT_ID else "Not set")
    print("🔐 Client Secret loaded:", "Yes" if CLIENT_SECRET else "No")

    # OAuth scopes for Google Ads API
    scopes = ['https://www.googleapis.com/auth/adwords']

    # Create flow with desktop application configuration (recommended for Google Ads API)
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=scopes
    )

    print("\n🌐 Starting OAuth flow...")
    print("This script will generate an authorization URL for you to visit manually.")
    print("This approach works reliably in DDEV and other containerized environments.")

    try:
        # Generate authorization URL manually
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            include_granted_scopes='true'
        )

        print("\n🔗 Authorization URL:")
        print("=" * 80)
        print(auth_url)
        print("=" * 80)

        print("\n📋 Instructions:")
        print("1. Copy the URL above")
        print("2. Open it in your browser (on your host machine, not in DDEV)")
        print("3. Sign in with your Google Ads account")
        print("4. Grant the requested permissions")
        print("5. You'll be redirected to a blank page with an authorization code in the URL")
        print("6. Copy the authorization code from the URL (it will look like: 4/0AeaYSHC... )")
        print("7. Paste it here when prompted")

        auth_code = input("\nEnter authorization code: ").strip()

        if not auth_code:
            print("❌ No authorization code provided.")
            return

        # Exchange the authorization code for tokens
        print("\n🔄 Exchanging authorization code for tokens...")
        flow.fetch_token(code=auth_code)

        credentials = flow.credentials

        print("\n✅ Authorization successful!")
        print("=" * 80)
        print("Access Token:", credentials.token)
        print("Refresh Token:", credentials.refresh_token)
        print("Token Expires:", credentials.expiry)
        print("=" * 80)

        print("\n📋 Copy the Refresh Token above to your .env file:")
        print("GOOGLE_ADS_REFRESH_TOKEN=" + str(credentials.refresh_token))

        print("\n⚠️  Important: Update your .env file with the refresh token above!")
        print("Then restart any running services that use these credentials.")

    except Exception as e:
        print(f"❌ Error during OAuth flow: {e}")
        print("\nTroubleshooting:")
        print("- Make sure your Google Cloud OAuth credentials are correct")
        print("- Ensure your Google account has access to Google Ads")
        print("- Check that the OAuth consent screen is configured")
        print("- Verify your developer token is approved")
        print("- Make sure the redirect URI matches what you configured in Google Cloud Console")

if __name__ == "__main__":
    main()