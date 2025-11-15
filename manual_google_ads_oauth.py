#!/usr/bin/env python3
"""
Manual Google Ads OAuth Flow Script
Use this when OAuth Playground doesn't work in your environment.
"""

import os
import sys
import json
import requests
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import (
    GOOGLE_ADS_CLIENT_ID,
    GOOGLE_ADS_CLIENT_SECRET
)

# OAuth Configuration
SCOPES = ['https://www.googleapis.com/auth/adwords']
REDIRECT_URI = 'http://localhost:8080/oauth2callback'
AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Parse authorization code from URL
        if 'code' in self.path:
            query = self.path.split('?', 1)[1]
            params = parse_qs(query)
            if 'code' in params:
                self.server.auth_code = params['code'][0]
                self.wfile.write(b'<h1>Authorization successful!</h1><p>You can close this window.</p>')
                return

        self.wfile.write(b'<h1>Authorization failed</h1>')

    def log_message(self, format, *args):
        # Suppress server logs
        pass

def get_authorization_url():
    """Generate the authorization URL"""
    params = {
        'client_id': GOOGLE_ADS_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join(SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    return f"{AUTH_URL}?{urlencode(params)}"

def exchange_code_for_tokens(auth_code):
    """Exchange authorization code for access and refresh tokens"""
    data = {
        'client_id': GOOGLE_ADS_CLIENT_ID,
        'client_secret': GOOGLE_ADS_CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }

    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    return response.json()

def main():
    print("🔐 Manual Google Ads OAuth Setup")
    print("=" * 40)

    # Check if credentials are configured
    if not GOOGLE_ADS_CLIENT_ID or not GOOGLE_ADS_CLIENT_SECRET:
        print("❌ Missing Google Ads credentials in .env file")
        print("   Make sure GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET are set")
        return

    print("📋 Step 1: Authorization URL")
    auth_url = get_authorization_url()
    print(f"   {auth_url}")
    print()

    print("📋 Step 2: Open the URL above in your browser")
    print("   Sign in and authorize access")
    print()

    # Start local server to capture callback
    print("📋 Step 3: Starting local server to capture authorization code...")
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.auth_code = None

    # Open browser automatically
    webbrowser.open(auth_url)

    # Wait for authorization
    print("   Waiting for authorization (timeout: 5 minutes)...")
    timeout = time.time() + 300  # 5 minutes

    while not server.auth_code and time.time() < timeout:
        server.handle_request()
        time.sleep(0.1)

    server.server_close()

    if not server.auth_code:
        print("❌ Authorization timeout or failed")
        return

    print("✅ Authorization code received!")

    # Exchange for tokens
    print("📋 Step 4: Exchanging code for tokens...")
    try:
        tokens = exchange_code_for_tokens(server.auth_code)
        refresh_token = tokens.get('refresh_token')

        if not refresh_token:
            print("❌ No refresh token received")
            print("   You may need to revoke previous authorizations and try again")
            return

        print("✅ Tokens received successfully!")
        print()
        print("🔑 Your Refresh Token:")
        print(f"   {refresh_token}")
        print()
        print("📝 Add this to your .env file:")
        print(f"   GOOGLE_ADS_REFRESH_TOKEN={refresh_token}")
        print()
        print("⚠️  Keep this token secure and never commit it to version control!")

    except Exception as e:
        print(f"❌ Token exchange failed: {e}")

if __name__ == '__main__':
    main()