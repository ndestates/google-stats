# Google Ads API Credentials Setup Guide

This guide will walk you through obtaining all the necessary credentials to use the Google Ads API for creating and managing ads programmatically.

## Prerequisites

- A Google Ads account with administrative access
- A Google Cloud Platform (GCP) project
- Basic familiarity with Google Cloud Console

## Step 1: Get Your Google Ads Customer ID

### Method 1: From Google Ads UI
1. Sign in to your [Google Ads account](https://ads.google.com)
2. Look at the top right corner - you'll see your account number (e.g., "123-456-7890")
3. Remove the dashes to get your Customer ID: `1234567890`

### Method 2: From Google Ads API
If you have API access already, you can query it programmatically, but for initial setup, use Method 1.

**Your Customer ID**: `1234567890` (update this in your .env file)

## Step 2: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Give your project a name (e.g., "google-ads-api-project")
5. Click "Create"

## Step 3: Enable the Google Ads API

1. In your Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Ads API"
3. Click on "Google Ads API"
4. Click "Enable"

## Step 4: Create OAuth 2.0 Credentials

### Create Credentials
1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen:
   - User Type: External
   - App name: Your app name (e.g., "Google Ads API Tool")
   - User support email: Your email
   - Developer contact information: Your email
   - Click "Save and Continue" through the screens
4. For Application type, select "**Desktop application**" (not Web application)
   - **Important**: Desktop application type is required for the OAuth flow used by this script. Web applications require specific redirect URIs and are more complex to set up.
5. Give it a name (e.g., "Google Ads Desktop Client")
6. Click "Create"

### Get Client ID and Client Secret
After creation, you'll see:
- **Client ID**: A long string ending in `.googleusercontent.com`
- **Client Secret**: A shorter string

**Update your .env file:**
```env
GOOGLE_ADS_CLIENT_ID=your-actual-client-id.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=your-actual-client-secret
```

## Step 5: Get Your Developer Token

### Apply for a Developer Token
1. Go to the [Google Ads API Token page](https://developers.google.com/google-ads/api/docs/get-started/dev-token)
2. Sign in with your Google account that has Google Ads access
3. Fill out the application form:
   - **Basic Access**: Select this for most use cases
   - **Website URL**: Your website (e.g., https://www.ndestates.com/)
   - **Application Name**: Your app name
   - **Application Description**: Brief description of what you'll build
   - **Business Type**: Select appropriate category
   - **Programming Language**: Python
   - **Where will you use this?**: Select "My own software application"
4. Agree to terms and submit

### Approval Process
- Basic access tokens are usually approved within minutes to hours
- You'll receive an email with your developer token
- If you don't hear back, check your spam folder

**Your Developer Token**: A string like `ABcdeFGHijklMNopQRS` (36 characters)

**Update your .env file:**
```env
GOOGLE_ADS_DEVELOPER_TOKEN=your-actual-developer-token
```

## Step 6: Generate OAuth Refresh Token

### Create Authorization Script
Use the provided `get_google_ads_refresh_token.py` script which automatically loads your credentials from the `.env` file.

**Alternative**: If you prefer to create your own script, here's a template:

**Alternative**: If you prefer to create your own script, here's a template:

```python
#!/usr/bin/env python3
"""
OAuth flow to get refresh token for Google Ads API
"""

import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv('GOOGLE_ADS_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_ADS_CLIENT_SECRET')

def main():
    scopes = ['https://www.googleapis.com/auth/adwords']
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
                "auth_uri": "https://accounts.google.com/o/oauth/authorize",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=scopes
    )
    flow.run_local_server(port=8080)
    credentials = flow.credentials
    print("Refresh Token:", credentials.refresh_token)

if __name__ == "__main__":
    main()
```

### Important Notes

- **OAuth Client Type**: Make sure to select "Desktop application" when creating your OAuth client in Google Cloud Console. Web applications require specific redirect URIs and are more complex to set up.
- **Redirect URI**: The script uses `urn:ietf:wg:oauth:2.0:oob` which is automatically configured for desktop applications.
- **DDEV Environment**: The manual OAuth flow works reliably in containerized environments like DDEV.

**Update your .env file:**
```env
GOOGLE_ADS_REFRESH_TOKEN=your-actual-refresh-token
```

## Step 7: Test Your Credentials

### Install Dependencies
```bash
pip install google-ads google-auth-oauthlib
```

### Test Script
Create a simple test script:

```python
#!/usr/bin/env python3
"""
Test Google Ads API credentials
"""

from google.ads.googleads.client import GoogleAdsClient

def main():
    # Load credentials from dict (same format as our config)
    credentials = {
        "client_id": "your-client-id",
        "client_secret": "your-client-secret",
        "refresh_token": "your-refresh-token",
        "developer_token": "your-developer-token",
        "use_proto_plus": True,
    }

    try:
        client = GoogleAdsClient.load_from_dict(credentials)
        print("✅ Credentials are valid!")

        # Test basic API call
        customer_id = "1234567890"  # Your customer ID without dashes

        googleads_service = client.get_service("GoogleAdsService")
        query = """
            SELECT
                customer.id,
                customer.descriptive_name
            FROM customer
            LIMIT 1
        """

        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = customer_id
        request.query = query

        response = googleads_service.search(request=request)

        for row in response:
            print(f"Customer ID: {row.customer.id}")
            print(f"Customer Name: {row.customer.descriptive_name}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
```

## Complete .env File Example

After following all steps, your `.env` file should look like:

```env
# Google Analytics 4 Configuration
GA4_PROPERTY_ID=275378361
GA4_KEY_PATH=/var/www/html/.ddev/keys/ga4-page-analytics-cf93eb65ac26.json

# Google Search Console Configuration
GSC_SITE_URL=https://www.ndestates.com/
GSC_KEY_PATH=/var/www/html/.ddev/keys/ga4-page-analytics-cf93eb65ac26.json

# Google Ads API Configuration
GOOGLE_ADS_CUSTOMER_ID=1234567890
GOOGLE_ADS_CLIENT_ID=123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=ABCdefGHIjklMNOpqrsTUVwxyz
GOOGLE_ADS_REFRESH_TOKEN=1//0abcdefghijk-lMNOPQRSTUVWXYZ
GOOGLE_ADS_DEVELOPER_TOKEN=ABcdeFGHijklMNopQRS
```

## Troubleshooting

### Common Issues

1. **"Developer token is not approved"**
   - Wait for approval email or check spam
   - Ensure you're using Basic Access level

2. **"Invalid customer ID"**
   - Make sure to remove dashes from your Google Ads account number
   - Verify you have access to the account

3. **"Access denied"**
   - Ensure the Google account used for OAuth has Google Ads access
   - Check that the developer token is approved

4. **"Invalid scope"**
   - Use the correct scope: `https://www.googleapis.com/auth/adwords`

### Getting Help

- [Google Ads API Documentation](https://developers.google.com/google-ads/api)
- [Google Ads API Forum](https://groups.google.com/g/adwords-api)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/google-ads-api)

## Security Notes

- Never commit your `.env` file to version control
- Keep your credentials secure and don't share them
- Rotate refresh tokens periodically
- Use environment variables in production instead of .env files</content>
<parameter name="filePath">/home/nickd/projects/google-stats/GOOGLE_ADS_SETUP.md