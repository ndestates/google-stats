import os
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    OrderBy,
)

from src.config import REPORTS_DIR, GA4_PROPERTY_ID, GA4_KEY_PATH
from src.pdf_generator import create_google_ads_report_pdf

def get_google_ads_performance():
    """Analyze Google Ads performance by campaign, ad, and time of day"""

    # Set environment variable for authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GA4_KEY_PATH

    # Verify key file exists
    if not os.path.exists(GA4_KEY_PATH):
        raise FileNotFoundError(f"GA4 service account key not found at {GA4_KEY_PATH}. Please check the path and permissions.")

    client = BetaAnalyticsDataClient()

    # Calculate date range: last 30 days
    end_date = datetime.now().date() - timedelta(days=1)  # Yesterday as end
    start_date = end_date - timedelta(days=29)  # 30 days total

    print(f"🎯 Analyzing Google Ads Performance: {start_date} to {end_date}")
    print("=" * 80)

    # Test Google Ads data availability
    print("🔍 Checking Google Ads data availability...")
    test_request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[Dimension(name="googleAdsCampaignName")],
        metrics=[Metric(name="totalUsers")],
        date_ranges=[DateRange(start_date=str(start_date), end_date=str(end_date))],
        limit=5,
    )

    try:
        test_response = client.run_report(test_request)
        if test_response.row_count == 0:
            print("❌ No Google Ads data found in the date range.")
            print("This could mean:")
            print("  - No Google Ads campaigns ran during this period")
            print("  - Google Ads data is not linked to this GA4 property")
            print("  - Privacy thresholds are hiding the data")
            return
        else:
            print(f"✅ Google Ads data available! Found {test_response.row_count} campaigns")
    except Exception as e:
        print(f"❌ Error accessing Google Ads data: {e}")
        return

    # 1. Campaign Performance Analysis
    print("\n📊 CAMPAIGN PERFORMANCE ANALYSIS")
    print("-" * 50)

    campaign_request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[
            Dimension(name="googleAdsCampaignName"),
            Dimension(name="googleAdsCampaignId"),
            Dimension(name="googleAdsAdGroupName")
        ],
        metrics=[
            Metric(name="totalUsers"),
            Metric(name="sessions"),
            Metric(name="engagedSessions")
        ],
        date_ranges=[DateRange(start_date=str(start_date), end_date=str(end_date))],
        order_bys=[OrderBy(
            metric=OrderBy.MetricOrderBy(metric_name="totalUsers"),
            desc=True
        )],
        limit=50,
    )

    try:
        campaign_response = client.run_report(campaign_request)

        if campaign_response.row_count > 0:
            # Process campaign data
            campaign_data = []
            campaign_totals = {}

            for row in campaign_response.rows:
                campaign_name = row.dimension_values[0].value
                campaign_id = row.dimension_values[1].value
                ad_group = row.dimension_values[2].value
                users = int(row.metric_values[0].value)
                sessions = int(row.metric_values[1].value)
                engaged_sessions = int(row.metric_values[2].value)

                campaign_data.append({
                    'Campaign Name': campaign_name,
                    'Campaign ID': campaign_id,
                    'Ad Group': ad_group,
                    'Users': users,
                    'Sessions': sessions,
                    'Engaged Sessions': engaged_sessions,
                    'Engagement Rate': (engaged_sessions / sessions * 100) if sessions > 0 else 0
                })

                # Aggregate by campaign
                key = f"{campaign_name} ({campaign_id})"
                if key not in campaign_totals:
                    campaign_totals[key] = {'users': 0, 'sessions': 0, 'engaged': 0}
                campaign_totals[key]['users'] += users
                campaign_totals[key]['sessions'] += sessions
                campaign_totals[key]['engaged'] += engaged_sessions

            # Display top campaigns
            print("🏆 TOP CAMPAIGNS BY USERS:")
            sorted_campaigns = sorted(campaign_totals.items(), key=lambda x: x[1]['users'], reverse=True)

            for i, (campaign_key, totals) in enumerate(sorted_campaigns[:10], 1):
                engagement_rate = (totals['engaged'] / totals['sessions'] * 100) if totals['sessions'] > 0 else 0
                print(f"{i}. {campaign_key}")
                print(f"   Users: {totals['users']:,} | Sessions: {totals['sessions']:,}")
                print(f"   Engagement Rate: {engagement_rate:.1f}%")
            # Export detailed campaign data
            campaign_df = pd.DataFrame(campaign_data)
            campaign_csv = f"google_ads_campaign_performance_{start_date}_to_{end_date}.csv"
            campaign_df.to_csv(campaign_csv, index=False)
            print(f"\n📄 Detailed campaign data exported to: {campaign_csv}")

            # Prepare campaign data for PDF
            pdf_campaign_data = {}
            for campaign_key, totals in campaign_totals.items():
                pdf_campaign_data[campaign_key] = {
                    'users': totals['users'],
                    'sessions': totals['sessions'],
                    'conversions': totals['engaged']  # Using engaged sessions as proxy for conversions
                }

    except Exception as e:
        print(f"❌ Error getting campaign data: {e}")

    # 2. Time of Day Performance Analysis
    print("\n⏰ TIME OF DAY PERFORMANCE ANALYSIS")
    print("-" * 50)

    time_request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[
            Dimension(name="hour"),
            Dimension(name="googleAdsCampaignName")
        ],
        metrics=[
            Metric(name="totalUsers"),
            Metric(name="sessions")
        ],
        date_ranges=[DateRange(start_date=str(start_date), end_date=str(end_date))],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="hour"), desc=False),
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=100,
    )

    try:
        time_response = client.run_report(time_request)

        if time_response.row_count > 0:
            # Process time data
            time_data = {}
            hourly_totals = {}

            for row in time_response.rows:
                hour = int(row.dimension_values[0].value)
                campaign = row.dimension_values[1].value
                users = int(row.metric_values[0].value)
                sessions = int(row.metric_values[1].value)

                # Aggregate by hour
                if hour not in hourly_totals:
                    hourly_totals[hour] = {'users': 0, 'sessions': 0, 'campaigns': {}}
                hourly_totals[hour]['users'] += users
                hourly_totals[hour]['sessions'] += sessions

                if campaign not in hourly_totals[hour]['campaigns']:
                    hourly_totals[hour]['campaigns'][campaign] = 0
                hourly_totals[hour]['campaigns'][campaign] += users

            # Display hourly performance
            print("📈 HOURLY PERFORMANCE (Top 5 hours):")
            sorted_hours = sorted(hourly_totals.items(), key=lambda x: x[1]['users'], reverse=True)

            for i, (hour, data) in enumerate(sorted_hours[:5], 1):
                hour_12 = f"{hour % 12 or 12}{' AM' if hour < 12 else ' PM'}"
                top_campaign = max(data['campaigns'].items(), key=lambda x: x[1]) if data['campaigns'] else ('None', 0)
                print(f"{i}. {hour_12} (Hour {hour:02d})")
                print(f"   Users: {data['users']:,} | Sessions: {data['sessions']:,}")
                print(f"   Top Campaign: {top_campaign[0]} ({top_campaign[1]:,} users)")

            # Export time data
            time_csv_data = []
            for hour, data in hourly_totals.items():
                for campaign, users in data['campaigns'].items():
                    time_csv_data.append({
                        'Hour': hour,
                        'Hour_12h': f"{hour % 12 or 12}{' AM' if hour < 12 else ' PM'}",
                        'Campaign': campaign,
                        'Users': users,
                        'Sessions': data['sessions']
                    })

            time_df = pd.DataFrame(time_csv_data)
            time_csv = f"google_ads_hourly_performance_{start_date}_to_{end_date}.csv"
            time_df.to_csv(time_csv, index=False)
            print(f"\n📄 Hourly performance data exported to: {time_csv}")

            # Prepare hourly data for PDF
            pdf_hourly_data = {}
            for hour, data in hourly_totals.items():
                pdf_hourly_data[hour] = {
                    'users': data['users'],
                    'sessions': data['sessions']
                }

            # Generate PDF report
            date_range = f"{start_date}_to_{end_date}"
            pdf_filename = create_google_ads_report_pdf(
                pdf_campaign_data,
                pdf_hourly_data,
                date_range
            )
            print(f"📄 PDF report exported to: {pdf_filename}")

    except Exception as e:
        print(f"❌ Error getting time data: {e}")

    # 3. Ad Network Type Analysis
    print("\n🌐 AD NETWORK PERFORMANCE")
    print("-" * 50)

    network_request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[
            Dimension(name="googleAdsAdNetworkType"),
            Dimension(name="googleAdsCampaignName")
        ],
        metrics=[
            Metric(name="totalUsers"),
            Metric(name="sessions")
        ],
        date_ranges=[DateRange(start_date=str(start_date), end_date=str(end_date))],
        order_bys=[OrderBy(
            metric=OrderBy.MetricOrderBy(metric_name="totalUsers"),
            desc=True
        )],
        limit=30,
    )

    try:
        network_response = client.run_report(network_request)

        if network_response.row_count > 0:
            network_totals = {}

            for row in network_response.rows:
                network = row.dimension_values[0].value
                campaign = row.dimension_values[1].value
                users = int(row.metric_values[0].value)
                sessions = int(row.metric_values[1].value)

                if network not in network_totals:
                    network_totals[network] = {'users': 0, 'sessions': 0}
                network_totals[network]['users'] += users
                network_totals[network]['sessions'] += sessions

            print("📊 PERFORMANCE BY AD NETWORK:")
            for network, data in sorted(network_totals.items(), key=lambda x: x[1]['users'], reverse=True):
                print(f"• {network}: {data['users']:,} users, {data['sessions']:,} sessions")

    except Exception as e:
        print(f"❌ Error getting network data: {e}")

    print(f"\n{'='*80}")
    print("🎯 GOOGLE ADS PERFORMANCE ANALYSIS COMPLETE")
    print(f"Date Range: {start_date} to {end_date}")
    print("Check the CSV files for detailed data and insights!")

if __name__ == "__main__":
    get_google_ads_performance()