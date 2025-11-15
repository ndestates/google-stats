# OAuth Setup Quick Visual Guide

## Step 1: Google Cloud Console
```
APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client IDs
└── Application type: Web application
    ├── Name: Google Ads API Client
    └── Authorized redirect URIs:
        ├── https://developers.google.com/oauthplayground
        ├── urn:ietf:wg:oauth:2.0:oob
        └── http://localhost
```

## Step 2: OAuth Playground
```
1. Go to: https://developers.google.com/oauthplayground/
2. Gear icon → Settings:
   ├── OAuth flow: Server-side
   ├── OAuth endpoints: Google
   └── Access type: Offline
3. Enter Client ID & Secret
4. Select scopes: https://www.googleapis.com/auth/adwords
5. Authorize APIs → Sign in → Accept
6. Exchange authorization code for tokens
7. Copy refresh_token to .env file
```

## Step 3: Environment Variables (.env)
```
GOOGLE_ADS_CUSTOMER_ID=1234567890
GOOGLE_ADS_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=your_client_secret
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
```

## Step 4: Test Connection
```bash
python scripts/test_google_ads_auth.py
```

## Common Issues & Solutions

| Error | Solution |
|-------|----------|
| redirect_uri_mismatch | Add correct redirect URIs to OAuth client |
| invalid_client | Check Client ID/Secret are correct |
| access_denied | Sign in with account that has Google Ads access |
| Developer token required | Apply for Google Ads API access in console |