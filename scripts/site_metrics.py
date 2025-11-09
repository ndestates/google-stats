"""
Site Metrics API
Get total pages viewed, unique visitors, and individual properties viewed
for 24 hours, 30 days, and annual periods
"""

import os
import sys
import json
from datetime import datetime, timedelta
from google.analytics.data_v1beta.types import OrderBy, Filter, FilterExpression

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.config import GA4_PROPERTY_ID
from src.ga4_client import run_report, create_date_range


def get_metrics_for_period(start_date: str, end_date: str):
    """Get site metrics for a specific time period"""
    
    date_range = create_date_range(start_date, end_date)
    
    # Get total pageviews (using gtm.js events as pageviews) and unique visitors
    # First get sessions and users
    response = run_report(
        dimensions=[],
        metrics=["sessions", "totalUsers"],
        date_ranges=[date_range],
        limit=1
    )
    
    total_pageviews = 0
    total_users = 0
    
    if response.row_count > 0:
        total_pageviews = int(response.rows[0].metric_values[0].value)
        total_users = int(response.rows[0].metric_values[1].value)
    
    # Also get gtm.js event count which represents actual pageviews
    gtm_filter = FilterExpression(
        filter=Filter(
            field_name="eventName",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.EXACT,
                value="gtm.js"
            )
        )
    )
    
    gtm_response = run_report(
        dimensions=["eventName"],
        metrics=["eventCount"],
        date_ranges=[date_range],
        dimension_filter=gtm_filter,
        limit=1
    )
    
    # Use gtm.js event count as the actual pageview count
    if gtm_response.row_count > 0:
        total_pageviews = int(gtm_response.rows[0].metric_values[0].value)
    
    # Get unique property pages viewed (pages containing "/properties/")
    property_filter = FilterExpression(
        filter=Filter(
            field_name="pagePath",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.CONTAINS,
                value="/properties/"
            )
        )
    )
    
    property_response = run_report(
        dimensions=["pagePath"],
        metrics=["totalUsers"],
        date_ranges=[date_range],
        dimension_filter=property_filter,
        limit=10000
    )
    
    # Count unique property pages
    unique_properties = property_response.row_count
    
    return {
        "total_pageviews": total_pageviews,
        "total_users": total_users,
        "unique_properties": unique_properties
    }


def get_all_site_metrics():
    """Get site metrics for 24 hours, 30 days, and annual periods"""
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # 24 hours (yesterday)
    metrics_24h = get_metrics_for_period(str(yesterday), str(yesterday))
    
    # 30 days
    date_30_days_ago = today - timedelta(days=30)
    metrics_30d = get_metrics_for_period(str(date_30_days_ago), str(yesterday))
    
    # Annual (365 days)
    date_365_days_ago = today - timedelta(days=365)
    metrics_annual = get_metrics_for_period(str(date_365_days_ago), str(yesterday))
    
    return {
        "24_hours": metrics_24h,
        "30_days": metrics_30d,
        "annual": metrics_annual
    }


def format_number(num):
    """Format large numbers with k/m suffix"""
    if num >= 1000000:
        return f"{num / 1000000:.1f}m"
    elif num >= 1000:
        return f"{num / 1000:.1f}k"
    else:
        return str(num)


if __name__ == "__main__":
    print("📊 Fetching Site Metrics...")
    print("=" * 60)
    
    try:
        metrics = get_all_site_metrics()
        
        # Pretty print for terminal
        print("\n📄 Total Pages Viewed:")
        print(f"   24 Hours: {format_number(metrics['24_hours']['total_pageviews'])}")
        print(f"   30 Days:  {format_number(metrics['30_days']['total_pageviews'])}")
        print(f"   Annual:   {format_number(metrics['annual']['total_pageviews'])}")
        
        print("\n👁️  Individual Properties Viewed:")
        print(f"   24 Hours: {format_number(metrics['24_hours']['unique_properties'])}")
        print(f"   30 Days:  {format_number(metrics['30_days']['unique_properties'])}")
        print(f"   Annual:   {format_number(metrics['annual']['unique_properties'])}")
        
        print("\n👥 Unique Visitors:")
        print(f"   24 Hours: {format_number(metrics['24_hours']['total_users'])}")
        print(f"   30 Days:  {format_number(metrics['30_days']['total_users'])}")
        print(f"   Annual:   {format_number(metrics['annual']['total_users'])}")
        
        # Output JSON for web interface
        if "--json" in sys.argv:
            print("\n" + json.dumps(metrics, indent=2))
            
    except Exception as e:
        print(f"❌ Error fetching metrics: {e}")
        if "--json" in sys.argv:
            print(json.dumps({"error": str(e)}))
        sys.exit(1)
