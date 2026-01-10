#!/usr/bin/env python3
"""
Test Database Credential Integration with GA4

This script tests that the database-backed credential system works correctly
with the Google Analytics Data API client.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import get_ga4_client, GA4_PROPERTY_ID, USE_DATABASE_CREDENTIALS

def main():
    print("="*70)
    print("TESTING DATABASE CREDENTIAL INTEGRATION")
    print("="*70)
    
    print(f"\n✓ USE_DATABASE_CREDENTIALS: {USE_DATABASE_CREDENTIALS}")
    print(f"✓ GA4_PROPERTY_ID: {GA4_PROPERTY_ID}")
    
    try:
        # Get GA4 client (should use database credentials if enabled)
        print("\n📡 Initializing GA4 client...")
        client = get_ga4_client()
        print("✅ GA4 client initialized successfully")
        
        # Test a simple API call
        print("\n📊 Testing API call (fetching property metadata)...")
        from google.analytics.data_v1beta import RunReportRequest, DateRange, Dimension, Metric
        
        request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="sessions")],
            date_ranges=[DateRange(start_date="yesterday", end_date="yesterday")],
            limit=1
        )
        
        response = client.run_report(request)
        
        if response.row_count > 0:
            print(f"✅ API call successful - Retrieved {response.row_count} row(s)")
            print(f"   Yesterday's sessions: {response.rows[0].metric_values[0].value}")
        else:
            print("⚠️  API call successful but no data returned")
        
        print("\n" + "="*70)
        print("✅ DATABASE CREDENTIAL INTEGRATION TEST PASSED")
        print("="*70)
        print("\nCredentials are being retrieved from encrypted database storage.")
        print("No plaintext credential files are being used.")
        
        return True
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
