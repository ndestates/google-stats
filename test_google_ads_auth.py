#!/usr/bin/env python3
"""
Test Google Ads API Authentication
Verifies that your Google Ads credentials are properly configured.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_environment_variables():
    """Test that all required environment variables are set"""
    print("🔍 Testing Environment Variables")
    print("-" * 30)

    required_vars = [
        'GOOGLE_ADS_CUSTOMER_ID',
        'GOOGLE_ADS_CLIENT_ID',
        'GOOGLE_ADS_CLIENT_SECRET',
        'GOOGLE_ADS_REFRESH_TOKEN',
        'GOOGLE_ADS_DEVELOPER_TOKEN'
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: Not set")
        else:
            # Mask sensitive values
            if 'SECRET' in var or 'TOKEN' in var:
                display_value = value[:10] + "..." + value[-4:] if len(value) > 14 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")

    if missing_vars:
        print(f"\n❌ Missing {len(missing_vars)} required environment variables")
        print("   Please check your .env file")
        return False

    print("✅ All environment variables are set")
    return True

def test_google_ads_client():
    """Test Google Ads client initialization"""
    print("\n🔍 Testing Google Ads Client")
    print("-" * 30)

    try:
        from config import get_google_ads_client
        client = get_google_ads_client()
        print("✅ Google Ads client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Google Ads client initialization failed: {e}")
        return False

def test_api_connection():
    """Test actual API connection"""
    print("\n🔍 Testing API Connection")
    print("-" * 30)

    try:
        from config import get_google_ads_client, GOOGLE_ADS_CUSTOMER_ID
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.v22.services.services.customer_service import CustomerServiceClient

        client = get_google_ads_client()

        # Try to get customer information
        customer_service = client.get_service("CustomerService")
        customer = customer_service.get_customer(
            resource_name=f"customers/{GOOGLE_ADS_CUSTOMER_ID}"
        )

        print(f"✅ API connection successful")
        print(f"   Customer ID: {customer.id}")
        print(f"   Company Name: {customer.descriptive_name}")
        return True

    except Exception as e:
        print(f"❌ API connection failed: {e}")
        print("   This could be due to:")
        print("   - Invalid credentials")
        print("   - Developer token not approved")
        print("   - Customer ID format issues")
        return False

def main():
    print("🧪 Google Ads API Authentication Test")
    print("=" * 40)

    tests_passed = 0
    total_tests = 3

    # Test 1: Environment variables
    if test_environment_variables():
        tests_passed += 1

    # Test 2: Client initialization
    if test_google_ads_client():
        tests_passed += 1

    # Test 3: API connection
    if test_api_connection():
        tests_passed += 1

    print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")

    if tests_passed == total_tests:
        print("🎉 All tests passed! Your Google Ads API setup is working correctly.")
        print("   You can now run scripts/create_ad.py to create ads.")
    else:
        print("⚠️  Some tests failed. Please check the errors above and fix your configuration.")
        print("   Refer to README_Google_Ads_Credentials.md for setup instructions.")

    return tests_passed == total_tests

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)