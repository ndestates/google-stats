#!/usr/bin/env python3
"""
Google Ads API Connection Diagnostic Tool
Test and troubleshoot Google Ads API authentication and permissions

Usage:
    ddev exec python3 test_google_ads_connection.py
"""

import os
import sys
import json
from datetime import datetime
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.config import (
    get_google_ads_client,
    GOOGLE_ADS_CUSTOMER_ID,
    GOOGLE_ADS_LOGIN_CUSTOMER_ID,
    GOOGLE_ADS_DEVELOPER_TOKEN,
    GOOGLE_ADS_JSON_KEY_PATH
)

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_section(title):
    """Print a section header"""
    print(f"\n{title}")
    print("-" * 80)

def check_config():
    """Check if all required configuration is set"""
    print_header("CONFIGURATION CHECK")
    
    checks = {
        "GOOGLE_ADS_CUSTOMER_ID": GOOGLE_ADS_CUSTOMER_ID,
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": GOOGLE_ADS_LOGIN_CUSTOMER_ID,
        "GOOGLE_ADS_DEVELOPER_TOKEN": "***" if GOOGLE_ADS_DEVELOPER_TOKEN else None,
        "GOOGLE_ADS_JSON_KEY_PATH": GOOGLE_ADS_JSON_KEY_PATH,
    }
    
    all_set = True
    for key, value in checks.items():
        if value:
            status = "✅ SET"
            display = value if not key.endswith("TOKEN") else value
        else:
            status = "❌ NOT SET"
            all_set = False
            display = "N/A"
        print(f"{key:<35} {status}")
        if value and not key.endswith("TOKEN"):
            print(f"{'  Value':<35} {display}")
    
    # Check if JSON key file exists
    print_section("SERVICE ACCOUNT KEY FILE")
    if GOOGLE_ADS_JSON_KEY_PATH:
        if os.path.exists(GOOGLE_ADS_JSON_KEY_PATH):
            print(f"✅ File exists: {GOOGLE_ADS_JSON_KEY_PATH}")
            
            # Read the key file
            try:
                with open(GOOGLE_ADS_JSON_KEY_PATH, 'r') as f:
                    key_data = json.load(f)
                print(f"\n  Service Account Email: {key_data.get('client_email')}")
                print(f"  Project ID: {key_data.get('project_id')}")
                print(f"  Type: {key_data.get('type')}")
                print(f"  Key ID: {key_data.get('private_key_id')[:20]}...")
            except Exception as e:
                print(f"❌ Error reading key file: {e}")
        else:
            print(f"❌ File NOT found: {GOOGLE_ADS_JSON_KEY_PATH}")
            all_set = False
    
    return all_set

def test_client_initialization():
    """Test if the Google Ads client can be initialized"""
    print_header("CLIENT INITIALIZATION TEST")
    
    try:
        client = get_google_ads_client()
        print(f"✅ Client initialized successfully")
        print(f"\n  Developer Token: {client.developer_token[:20]}...")
        print(f"  Login Customer ID: {client.login_customer_id}")
        print(f"  Linked Customer ID: {client.linked_customer_id}")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize client")
        print(f"  Error: {str(e)[:200]}")
        return None

@pytest.mark.skip(reason="Skipped to avoid customer list access in tests")
def test_customer_list_access(client):
    """Test if we can list customers accessible from the manager account"""
    print_header("CUSTOMER ACCESSIBILITY TEST")
    
    if not client:
        print("⚠️ Skipped: Client not initialized")
        return False
    
    try:
        googleads_service = client.get_service("GoogleAdsService")
        
        # Try to list customers that the manager account can access
        query = """
            SELECT
                customer.descriptive_name,
                customer.id,
                customer_client.hidden,
                customer_client.manager
            FROM customer_client
            WHERE customer_client.hidden = FALSE
            ORDER BY customer_client.manager DESC, customer.descriptive_name
        """
        
        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = GOOGLE_ADS_LOGIN_CUSTOMER_ID
        request.query = query
        
        response = googleads_service.search(request=request)
        
        customers = []
        for row in response:
            customers.append({
                'id': row.customer_client.id,
                'name': row.customer.descriptive_name,
                'is_manager': row.customer_client.manager,
                'hidden': row.customer_client.hidden
            })
        
        if customers:
            print(f"✅ Successfully retrieved {len(customers)} accessible customer(s)")
            print(f"\nAccessible Customers from Manager Account {GOOGLE_ADS_LOGIN_CUSTOMER_ID}:")
            print(f"{'ID':<15} {'Name':<40} {'Manager':<10}")
            print("-" * 80)
            for cust in customers:
                manager_str = "Yes" if cust['is_manager'] else "No"
                print(f"{cust['id']:<15} {cust['name'][:39]:<40} {manager_str:<10}")
            
            # Check if target customer is in the list
            target_found = any(c['id'] == GOOGLE_ADS_CUSTOMER_ID for c in customers)
            if target_found:
                print(f"\n✅ Target customer {GOOGLE_ADS_CUSTOMER_ID} IS accessible")
                return True
            else:
                print(f"\n❌ Target customer {GOOGLE_ADS_CUSTOMER_ID} is NOT in the accessible list")
                print("   This customer may not be linked to your manager account")
                return False
        else:
            print("❌ No accessible customers found")
            return False
            
    except Exception as e:
        error_str = str(e)
        if "developer token is only approved for use with test accounts" in error_str.lower():
            print("❌ DEVELOPER TOKEN TEST-ONLY")
            print("   Your developer token can only access test accounts.")
            print("   Options:")
            print("   - Use test accounts for both login and customer IDs")
            print("   - Apply for Basic or Standard access in API Center")
            return False
        if "USER_PERMISSION_DENIED" in error_str or "permission" in error_str.lower():
            print("❌ PERMISSION DENIED")
            print("   The service account cannot access the manager account")
            print("   This usually means:")
            print("   - The service account is not added to the manager account")
            print("   - The service account doesn't have the right permissions")
        else:
            print(f"❌ Error accessing customer list: {error_str[:200]}")
        return False

@pytest.mark.skip(reason="Skipped to avoid customer access in tests")
def test_target_customer_access(client):
    """Test if we can access the target customer account directly"""
    print_header("TARGET CUSTOMER ACCESS TEST")
    
    if not client:
        print("⚠️ Skipped: Client not initialized")
        return False
    
    print(f"Testing access to customer {GOOGLE_ADS_CUSTOMER_ID}...")
    
    try:
        googleads_service = client.get_service("GoogleAdsService")
        
        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status
            FROM campaign
            WHERE campaign.status = 'ENABLED'
            LIMIT 1
        """
        
        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = GOOGLE_ADS_CUSTOMER_ID
        request.query = query
        
        response = googleads_service.search(request=request)
        
        print(f"✅ Successfully accessed customer {GOOGLE_ADS_CUSTOMER_ID}")
        print(f"   Sample query returned {response.row_count} campaign(s)")
        return True
        
    except Exception as e:
        error_str = str(e)
        if "developer token is only approved for use with test accounts" in error_str.lower():
            print("❌ DEVELOPER TOKEN TEST-ONLY")
            print("   The token is limited to test accounts and cannot access this customer.")
            print("\n   To proceed:")
            print("   - Switch `.env` IDs to test accounts; or")
            print("   - Upgrade token in Google Ads API Center (Basic/Standard)")
            return False
        if "USER_PERMISSION_DENIED" in error_str or "permission" in error_str.lower():
            print(f"❌ PERMISSION DENIED for customer {GOOGLE_ADS_CUSTOMER_ID}")
            print("\n   Possible causes:")
            print("   1. Customer account is not linked to manager account")
            print("   2. Service account is not added to the customer account")
            print("   3. Service account doesn't have proper permissions")
            print("\n   To fix:")
            print(f"   - Add the service account to customer {GOOGLE_ADS_CUSTOMER_ID}")
            print("   - Or add the service account to manager account and ensure")
            print(f"      the customer is linked to the manager account")
            return False
        else:
            print(f"❌ Error accessing customer: {error_str[:200]}")
            return False

def main():
    """Run all diagnostic tests"""
    print("\n" + "="*80)
    print("  GOOGLE ADS API CONNECTION DIAGNOSTIC TOOL")
    print("="*80)
    print(f"  Timestamp: {datetime.now().isoformat()}")
    
    # Step 1: Check configuration
    config_ok = check_config()
    
    if not config_ok:
        print("\n" + "!"*80)
        print("❌ CONFIGURATION INCOMPLETE")
        print("Please set all required environment variables in .env file")
        print("!"*80)
        return
    
    # Step 2: Test client initialization
    client = test_client_initialization()
    
    if not client:
        print("\n" + "!"*80)
        print("❌ CLIENT INITIALIZATION FAILED")
        print("Cannot proceed with other tests")
        print("!"*80)
        return
    
    # Step 3: Test customer list access
    can_list_customers = test_customer_list_access(client)
    
    # Step 4: Test target customer access
    can_access_target = test_target_customer_access(client)
    
    # Summary
    print_header("SUMMARY")
    
    print("Configuration:              ✅" if config_ok else "Configuration:              ❌")
    print("Client Initialization:       ✅" if client else "Client Initialization:       ❌")
    print("List Customers:              ✅" if can_list_customers else "List Customers:              ❌")
    print("Access Target Customer:      ✅" if can_access_target else "Access Target Customer:      ❌")
    
    if can_access_target:
        print("\n✅ All tests passed! You can use the manage_google_ads.py script.")
    else:
        print("\n❌ Some tests failed. Review the errors above.")
        if not can_list_customers:
            print("\nRECOMMENDATION:")
            print("1. Verify the service account is added to your Google Ads manager account")
            print("2. Check the manager account ID matches GOOGLE_ADS_LOGIN_CUSTOMER_ID")
            print("3. Ensure customer {GOOGLE_ADS_CUSTOMER_ID} is linked to the manager account")

if __name__ == "__main__":
    main()
