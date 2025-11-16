"""
Google Ads Creative Performance Analysis Script
Analyze individual Google Ads creative performance to identify best performing creatives
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta.types import OrderBy

from src.config import REPORTS_DIR
from src.ga4_client import run_report, create_date_range, get_report_filename

def get_last_30_days_range():
    """Get date range for the last 30 days"""
    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=29)  # 30 days back
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def analyze_ad_performance(start_date: str = None, end_date: str = None):
    """Analyze individual Google Ads ad performance"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print(f"🎯 Analyzing Google Ads Ad Performance: {start_date} to {end_date}")
    print("=" * 80)

    # Check if Google Ads data is available
    date_range = create_date_range(start_date, end_date)

    test_response = run_report(
        dimensions=["googleAdsCampaignName"],
        metrics=["totalUsers"],
        date_ranges=[date_range],
        limit=1,
    )

    if test_response.row_count == 0:
        print("❌ No Google Ads data found in the date range.")
        print("This could mean:")
        print("  - No Google Ads campaigns ran during this period")
        print("  - Google Ads data is not linked to this GA4 property")
        print("  - Privacy thresholds are hiding the data")
        return None

    print(f"✅ Google Ads data available! Found active campaigns")

    # Get individual ad performance data
    print("\n📢 ANALYZING GOOGLE ADS CREATIVE PERFORMANCE")
    print("-" * 50)

    ad_response = run_report(
        dimensions=[
            "googleAdsCreativeId",
            "googleAdsCampaignName",
            "googleAdsAdGroupName",
            "googleAdsAdNetworkType"
        ],
        metrics=[
            "totalUsers",
            "sessions"
        ],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=1000,  # Get top performing ads
    )

    if ad_response.row_count == 0:
        print("❌ No individual ad data found.")
        return None

    print(f"✅ Retrieved {ad_response.row_count} ads for analysis")

    # Process ad data
    ad_data = []
    campaign_totals = {}

    for row in ad_response.rows:
        creative_id = row.dimension_values[0].value
        campaign_name = row.dimension_values[1].value
        ad_group_name = row.dimension_values[2].value
        network_type = row.dimension_values[3].value

        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)

        ad_data.append({
            'Creative_ID': creative_id,
            'Campaign_Name': campaign_name,
            'Ad_Group_Name': ad_group_name,
            'Network_Type': network_type,
            'Users': users,
            'Sessions': sessions
        })

        # Aggregate by campaign for summary
        if campaign_name not in campaign_totals:
            campaign_totals[campaign_name] = {'users': 0, 'sessions': 0, 'ads': 0}
        campaign_totals[campaign_name]['users'] += users
        campaign_totals[campaign_name]['sessions'] += sessions
        campaign_totals[campaign_name]['ads'] += 1

    # Sort ads by users (primary metric)
    sorted_ads = sorted(ad_data, key=lambda x: x['Users'], reverse=True)

    # Display top performing ads
    print(f"\n🏆 TOP PERFORMING GOOGLE ADS CREATIVES ({start_date} to {end_date})")
    print("=" * 100)

    for i, ad in enumerate(sorted_ads[:20], 1):  # Show top 20 ads
        print(f"\n{i}. Creative ID: '{ad['Creative_ID']}'")
        print(f"   Campaign: {ad['Campaign_Name']}")
        print(f"   Ad Group: {ad['Ad_Group_Name']}")
        print(f"   Network: {ad['Network_Type']}")
        print(f"   Users: {ad['Users']:,}")
        print(f"   Sessions: {ad['Sessions']:,}")

    # Campaign summary
    print(f"\n{'='*100}")
    print("📊 CAMPAIGN SUMMARY:")
    sorted_campaigns = sorted(campaign_totals.items(), key=lambda x: x[1]['users'], reverse=True)

    for campaign_name, totals in sorted_campaigns[:10]:  # Top 10 campaigns
        print(f"• {campaign_name}: {totals['users']:,} users, {totals['ads']} ads")

    # Performance insights
    print(f"\n{'='*100}")
    print("💡 PERFORMANCE INSIGHTS:")

    # Calculate averages for comparison
    avg_users = sum(ad['Users'] for ad in ad_data) / len(ad_data) if ad_data else 0

    top_performers = [ad for ad in sorted_ads[:5]]  # Top 5 ads
    top_avg_users = sum(ad['Users'] for ad in top_performers) / len(top_performers) if top_performers else 0

    print(f"• Average creative performance: {avg_users:.0f} users per creative")
    print(f"• Top 5 creatives average: {top_avg_users:.0f} users per creative")

    if top_avg_users > avg_users * 1.5:
        print("• 📈 Top performers significantly outperform average - focus optimization here!")

    # Identify best performing networks
    network_performance = {}
    for ad in ad_data:
        network = ad['Network_Type']
        if network not in network_performance:
            network_performance[network] = {'users': 0, 'ads': 0}
        network_performance[network]['users'] += ad['Users']
        network_performance[network]['ads'] += 1

    print("• Best performing networks:")
    for network, data in sorted(network_performance.items(), key=lambda x: x[1]['users'], reverse=True):
        avg_users_per_ad = data['users'] / data['ads'] if data['ads'] > 0 else 0
        print(f"  - {network}: {avg_users_per_ad:.1f} users per ad ({data['ads']} ads)")

    # Export detailed data to CSV
    if ad_data:
        df = pd.DataFrame(ad_data)
        csv_filename = get_report_filename("google_ads_ad_performance", f"{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed ad performance data exported to: {csv_filename}")

    return ad_data

def get_top_ads_report(days: int = 30):
    """Get top performing ads report"""
    if days == 7:
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=6)
        return analyze_ad_performance(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    else:
        return analyze_ad_performance()

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Command line mode
        if len(sys.argv) >= 2:
            days = int(sys.argv[1])
            get_top_ads_report(days)
        else:
            print("Usage: python google_ads_ad_performance.py [days]")
            print("Example: python google_ads_ad_performance.py 30")
            analyze_ad_performance()
    else:
        # Interactive mode
        print("🎯 Google Ads Creative Performance Analyzer")
        print("=" * 50)
        print("Identify your best performing individual ad creatives")
        print()

        # Check if running in interactive terminal
        if not sys.stdin.isatty():
            print("❌ This script requires command line arguments when run non-interactively.")
            print("   Usage: python google_ads_ad_performance.py [days]")
            print("   Example: python google_ads_ad_performance.py 30")
            print("   Running with default: Last 30 days")
            analyze_ad_performance()
            exit(0)

        print("Choose time period:")
        print("1. Last 30 days")
        print("2. Last 7 days")
        print("3. Custom date range")

        choice = input("Enter choice (1, 2, or 3): ").strip()

        if choice == "1":
            analyze_ad_performance()
        elif choice == "2":
            get_top_ads_report(7)
        elif choice == "3":
            start_date = input("Enter start date (YYYY-MM-DD): ").strip()
            end_date = input("Enter end date (YYYY-MM-DD): ").strip()
            if start_date and end_date:
                analyze_ad_performance(start_date, end_date)
            else:
                print("Invalid dates provided. Using last 30 days.")
                analyze_ad_performance()
        else:
            print("Invalid choice. Analyzing last 30 days by default.")
            analyze_ad_performance()