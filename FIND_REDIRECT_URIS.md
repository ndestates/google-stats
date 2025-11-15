# Finding Authorized Redirect URIs - Troubleshooting Guide

## Your OAuth Client Details
- **Client ID**: `[YOUR_CLIENT_ID_FROM_GOOGLE_CLOUD_CONSOLE]`
- **Client Secret**: `[YOUR_CLIENT_SECRET_FROM_GOOGLE_CLOUD_CONSOLE]`
- **Application Type**: Desktop application

## Step-by-Step: Finding Authorized Redirect URIs

### Method 1: Direct URL Approach
1. Go directly to: https://console.cloud.google.com/apis/credentials
2. Find your OAuth client (it will end with `.apps.googleusercontent.com`)
3. Click on it to open the details

### Method 2: If You Don't See the Section
If "Authorized redirect URIs" is missing, you might need to:

1. **Check if you're editing the right client**
   - Make sure you're editing the Desktop application client
   - The name should show your Client ID ending in `.apps.googleusercontent.com`

2. **Try creating a new OAuth client**
   - Go to Credentials → Create Credentials → OAuth 2.0 Client IDs
   - Select "Web application" instead of "Desktop application"
   - Then you can add redirect URIs

### Method 3: Alternative - Use Web Application Type (EASIEST)
Since Desktop applications don't always show redirect URIs clearly:

1. **Create a new OAuth client** as "Web application"
2. **Add these redirect URIs**:
   ```
   https://developers.google.com/oauthplayground
   urn:ietf:wg:oauth:2.0:oob
   http://localhost
   ```
3. **Update your .env file** with the new Client ID and Secret
4. **Use the new credentials** in OAuth Playground

## Quick Test
Once you add the redirect URI, test it:
1. Go to https://developers.google.com/oauthplayground/
2. Use your Client ID and Secret
3. It should work without redirect URI errors

## If Still Having Issues
The Google Cloud Console UI can be tricky. Try:
- Using an incognito/private browser window
- Clearing browser cache
- Using a different browser
- Making sure you're the project owner/editor