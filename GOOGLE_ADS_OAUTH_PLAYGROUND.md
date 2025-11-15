# Google Ads OAuth Playground Setup Guide

## Overview
This guide walks you through using Google's OAuth Playground to generate refresh tokens for Google Ads API authentication.

## Prerequisites
- Google Cloud Console project with Google Ads API enabled
- OAuth 2.0 Client ID and Secret
- Authorized redirect URI configured

## Step 1: Access OAuth Playground
1. Go to: https://developers.google.com/oauthplayground/
2. Click the gear icon (settings) in the top right

## Step 2: Configure OAuth Settings
1. In the OAuth 2.0 configuration dialog:
   - **OAuth flow**: Server-side
   - **OAuth endpoints**: Google
   - **Access type**: Offline (this ensures you get a refresh token)
2. Enter your **Client ID** and **Client Secret** from Google Cloud Console
3. Click "Close"

## Step 3: Select Google Ads API Scopes
1. In the "Select & authorize APIs" section, enter these scopes:
   ```
   https://www.googleapis.com/auth/adwords
   ```
2. Click "Authorize APIs"

## Step 4: Authorize Access
1. A Google authorization page will open
2. Sign in with your Google account that has access to the Google Ads account
3. Review and accept the permissions
4. You'll be redirected back to OAuth Playground

## Step 5: Exchange for Tokens
1. Click "Exchange authorization code for tokens"
2. You'll receive:
   - **Access Token** (short-lived)
   - **Refresh Token** (long-lived - this is what you need!)

## Step 6: Save Your Refresh Token
1. Copy the **refresh_token** value
2. Add it to your `.env` file:
   ```
   GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token_here
   ```

## Troubleshooting

### "redirect_uri_mismatch" Error
- Ensure your OAuth client has the correct redirect URI: `https://developers.google.com/oauthplayground`
- For Desktop applications, you may need to create a Web application client instead

### "invalid_client" Error
- Double-check your Client ID and Client Secret
- Ensure the OAuth client is from the same Google Cloud project

### "access_denied" Error
- Make sure you're signed in with an account that has access to the Google Ads account
- The account needs to be either the MCC account owner or have appropriate permissions

## Security Notes
- Keep your refresh token secure - it provides ongoing access to your Google Ads account
- Never commit tokens to version control
- Rotate tokens periodically for security