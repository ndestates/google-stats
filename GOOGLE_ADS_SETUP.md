# Google Ads API Setup Guide

## Current Status

Your Google Ads API configuration is **partially complete**, but the service account needs proper permissions in Google Ads to function.

### What's Working ✅
- Environment variables are configured correctly
- Service account JSON key file is present and valid
- Python Google Ads SDK is installed
- Client can be initialized with developer token

### What's Not Working ❌
- Service account cannot access Google Ads accounts (permission denied)
- Cannot list campaigns or manage ads

---

## Fixing the Permission Issue

The error message indicates:
```
User doesn't have permission to access customer. Note: If you're accessing a client customer, 
the manager's customer id must be set in the 'login-customer-id' header.
```

### Solution Steps

#### 1. Identify Your Account Structure

Your configuration shows:
- **Manager Account ID**: `2445831419`
- **Target Customer Account ID**: `5933984170`
- **Service Account Email**: `google-ads-sa@ndestates-websit-1764495112771.iam.gserviceaccount.com`

#### 2. Add Service Account to Google Ads Manager Account

**Option A: If 2445831419 is YOUR manager account:**

1. Go to [Google Ads Manager Account](https://ads.google.com/home/)
2. Click **Tools & Settings** (top right) → **Account access**
3. Click the **"Invite" button** (blue button on the right)
4. Enter the service account email: `google-ads-sa@ndestates-websit-1764495112771.iam.gserviceaccount.com`
5. Select role: **Admin** (or appropriate role)
6. Click **Send invitation**
7. Wait 1-5 minutes for the invitation to be processed

**Option B: If you need to access a different account structure:**

1. Verify that customer account `5933984170` is:
   - A child of manager account `2445831419`
   - Has the service account added with appropriate permissions
2. Update `.env` if the customer IDs are incorrect

#### 3. Verify Setup

After adding the service account, run the diagnostic tool:

```bash
ddev exec python3 test_google_ads_connection.py
```

Expected output after successful setup:
```
Configuration:              ✅
Client Initialization:       ✅
List Customers:             ✅
Access Target Customer:     ✅
```

---

## Testing After Setup

Once permissions are configured:

### Test 1: Run Diagnostic Tool
```bash
ddev exec python3 test_google_ads_connection.py
```

### Test 2: Run Management Script
```bash
ddev exec python3 scripts/manage_google_ads.py
```

### Test 3: Run Tests
```bash
python run_tests.py --script manage_google_ads
```

---

## Troubleshooting

### Still getting permission denied?

1. **Wait for propagation**: Google Ads sometimes takes 5-10 minutes to fully process service account additions
2. **Check the service account email**: Verify you added the exact email from the JSON key file
3. **Verify account IDs**: Make sure the customer and manager account IDs don't have hyphens
4. **Check the account structure**: In Google Ads settings, verify the target customer account is visible
5. **Confirm role permissions**: The service account role needs "Admin" access

### Need to change account IDs?

Edit `.env`:
```env
# Change the target account you want to manage
GOOGLE_ADS_CUSTOMER_ID=5933984170

# Manager account (where the service account is added)
GOOGLE_ADS_LOGIN_CUSTOMER_ID=2445831419
```

Then run:
```bash
ddev exec python3 test_google_ads_connection.py
```

### Account access issues?

1. Go to Google Ads Manager Account Settings
2. Click **Account access** → **User access** tab
3. Look for your service account email
4. Verify the status is "Active" or "Accepted"
5. Check the role has appropriate permissions

---

## Google Ads Account Structure

### Standard Setup (Most Common)
```
Manager Account (MCC) - Where service account is added
  └── Child Account 1 - Your ads account
  └── Child Account 2 - Another account
```

### For This Project
```
Manager Account: 2445831419
  └── Target Account: 5933984170
```

The service account needs to be added to the **Manager Account (2445831419)** with Admin or appropriate permissions.

---

## Configuration Files

### Environment Variables (.env)
```env
GOOGLE_ADS_CUSTOMER_ID=5933984170              # Target account to manage
GOOGLE_ADS_JSON_KEY_PATH=...                   # Path to service account key
GOOGLE_ADS_LOGIN_CUSTOMER_ID=2445831419        # Manager account
GOOGLE_ADS_DEVELOPER_TOKEN=...                 # Developer token
```

### Service Account Key (.env path)
Location: `.ddev/keys/ndestates-websit-1764495112771-73cdb6c929b4.json`
- Generated from Google Cloud Console
- Contains credentials for: `google-ads-sa@ndestates-websit-1764495112771.iam.gserviceaccount.com`

---

## Useful Resources

- [Google Ads API Setup Guide](https://developers.google.com/google-ads/api/docs/start)
- [Service Account Setup](https://developers.google.com/google-ads/api/docs/oauth/service-accounts)
- [Account Structure Documentation](https://developers.google.com/google-ads/api/docs/concepts/call-structure)
- [API Quotas & Limits](https://developers.google.com/google-ads/api/docs/concepts/quotas)

---

## Next Steps

1. Run diagnostic tool: `ddev exec python3 test_google_ads_connection.py`
2. Add service account to Google Ads if needed
3. Wait 5-10 minutes for propagation
4. Run diagnostic tool again to verify
5. Use management script: `ddev exec python3 scripts/manage_google_ads.py`

---

## Support

If you continue having issues:

1. **Run diagnostics**: `ddev exec python3 test_google_ads_connection.py`
2. **Check logs**: `tail logs/manage_google_ads.log`
3. **Verify credentials**: Ensure service account JSON is valid and matches `.env`
4. **Check Google Cloud**: Verify service account exists in Google Cloud Console
5. **Review Google Ads settings**: Confirm service account in Account Access section
