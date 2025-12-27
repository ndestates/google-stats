#!/usr/bin/env python3
"""
Run with: ddev exec python scripts/campaign_performance.py
"""

import os
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta.types import OrderBy

from src.config import REPORTS_DIR
from src.ga4_client import run_report, create_date_range, get_yesterday_date, get_last_30_days_range, get_report_filename
from src.pdf_generator import create_campaign_report_pdf

def get_campaign_report_yesterday():
    """Get campaign performance report for yesterday"""

    # Get yesterday's date
    yesterday = get_yesterday_date()

    print(f"📊 Generating campaign performance report for {yesterday}")
    print("=" * 80)

    # Get campaign data for yesterday
    date_range = create_date_range(yesterday, yesterday)

    response = run_report(
        dimensions=["sessionCampaignName", "sessionSourceMedium", "pagePath"],
        metrics=["totalUsers", "sessions", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=5000,
    )

    if response.row_count == 0:
        print("❌ No campaign data found for yesterday.")
        return

    print(f"✅ Retrieved {response.row_count} campaign records for yesterday")

    # Process data into campaign-focused format
    campaign_data = {}

    for row in response.rows:
        campaign_name = row.dimension_values[0].value
        source_medium = row.dimension_values[1].value
        page_path = row.dimension_values[2].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_session_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)

        # Skip entries with no campaign name
        if not campaign_name or campaign_name == '(not set)':
            continue

        # Skip /sold/ pages as they no longer exist
        if page_path.startswith('/sold/'):
            continue

        if campaign_name not in campaign_data:
            campaign_data[campaign_name] = {
                'total_users': 0,
                'total_sessions': 0,
                'total_pageviews': 0,
                'source_medium': source_medium,
                'pages': {}
            }

        campaign_data[campaign_name]['total_users'] += users
        campaign_data[campaign_name]['total_sessions'] += sessions
        campaign_data[campaign_name]['total_pageviews'] += pageviews

        if page_path not in campaign_data[campaign_name]['pages']:
            campaign_data[campaign_name]['pages'][page_path] = {
                'users': 0,
                'sessions': 0,
                'pageviews': 0,
                'avg_session_duration': avg_session_duration,
                'bounce_rate': bounce_rate
            }

        campaign_data[campaign_name]['pages'][page_path]['users'] += users
        campaign_data[campaign_name]['pages'][page_path]['sessions'] += sessions
        campaign_data[campaign_name]['pages'][page_path]['pageviews'] += pageviews

    # Sort campaigns by total users
    sorted_campaigns = sorted(campaign_data.items(), key=lambda x: x[1]['total_users'], reverse=True)

    # Display results
    print(f"\n📈 CAMPAIGN PERFORMANCE REPORT ({yesterday})")
    print("=" * 100)

    grand_total_users = 0
    campaign_count = 0

    for i, (campaign_name, data) in enumerate(sorted_campaigns, 1):
        if data['total_users'] > 0:
            print(f"\n🎯 CAMPAIGN {i}: {campaign_name}")
            print(f"   Source/Medium: {data['source_medium']}")
            print(f"   Total Users: {data['total_users']:,}")
            print(f"   Total Sessions: {data['total_sessions']:,}")
            print(f"   Total Pageviews: {data['total_pageviews']:,}")

            # Show top pages for this campaign
            sorted_pages = sorted(data['pages'].items(), key=lambda x: x[1]['users'], reverse=True)[:5]
            if sorted_pages:
                print("   Top Pages:")
                for page_path, page_data in sorted_pages:
                    percentage = (page_data['users'] / data['total_users'] * 100)
                    print(f"     • {page_path[:50]}{'...' if len(page_path) > 50 else ''} - {page_data['users']:,} users ({percentage:.1f}%)")

            grand_total_users += data['total_users']
            campaign_count += 1

            # Limit display to top 20 campaigns
            if i >= 20:
                remaining_campaigns = len(sorted_campaigns) - 20
                remaining_users = sum(data['total_users'] for _, data in sorted_campaigns[20:])
                if remaining_campaigns > 0:
                    print(f"\n... and {remaining_campaigns} more campaigns with {remaining_users:,} total users")
                break

    print(f"\n{'='*100}")
    print("📊 SUMMARY:")
    print(f"   Date: {yesterday}")
    print(f"   Total Campaigns: {campaign_count}")
    print(f"   Total Users Across All Campaigns: {grand_total_users:,}")

    # Export detailed data to CSV
    csv_data = []
    for campaign_name, data in sorted_campaigns:
        for page_path, page_data in data['pages'].items():
            csv_data.append({
                'Date': str(yesterday),
                'Campaign_Name': campaign_name,
                'Source_Medium': data['source_medium'],
                'Page_Path': page_path,
                'Users': page_data['users'],
                'Sessions': page_data['sessions'],
                'Pageviews': page_data['pageviews'],
                'Avg_Session_Duration': page_data['avg_session_duration'],
                'Bounce_Rate': page_data['bounce_rate'],
                'Campaign_Total_Users': data['total_users']
            })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename("campaign_report_yesterday", yesterday)
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed data exported to: {csv_filename}")

        # Generate PDF report
        pdf_filename = create_campaign_report_pdf(campaign_data, yesterday, grand_total_users, campaign_count)
        print(f"📄 PDF report exported to: {pdf_filename}")

def get_campaign_report_monthly():
    """Get campaign performance report for the past 30 days"""

    # Get date range for last 30 days
    start_date, end_date = get_last_30_days_range()

    print(f"📊 Generating monthly campaign performance report for {start_date} to {end_date}")
    print("=" * 80)

    # Get campaign data for the month
    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["sessionCampaignName", "sessionSourceMedium", "date"],
        metrics=["totalUsers", "sessions", "screenPageViews"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="sessionCampaignName"), desc=False),
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"), desc=False)
        ],
        limit=10000,
    )

    if response.row_count == 0:
        print("❌ No campaign data found for the date range.")
        return

    print(f"✅ Retrieved {response.row_count} campaign records for the month")

    # Process data into campaign-focused format
    campaign_data = {}

    for row in response.rows:
        campaign_name = row.dimension_values[0].value
        source_medium = row.dimension_values[1].value
        date = row.dimension_values[2].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)

        # Skip entries with no campaign name
        if not campaign_name or campaign_name == '(not set)':
            continue

        if campaign_name not in campaign_data:
            campaign_data[campaign_name] = {
                'source_medium': source_medium,
                'daily_data': {},
                'total_users': 0,
                'total_sessions': 0,
                'total_pageviews': 0
            }

        campaign_data[campaign_name]['daily_data'][date] = {
            'users': users,
            'sessions': sessions,
            'pageviews': pageviews
        }
        campaign_data[campaign_name]['total_users'] += users
        campaign_data[campaign_name]['total_sessions'] += sessions
        campaign_data[campaign_name]['total_pageviews'] += pageviews

    # Sort campaigns by total users
    sorted_campaigns = sorted(campaign_data.items(), key=lambda x: x[1]['total_users'], reverse=True)

    # Display results
    print(f"\n📈 MONTHLY CAMPAIGN PERFORMANCE REPORT ({start_date} to {end_date})")
    print("=" * 100)

    grand_total_users = 0
    campaign_count = 0

    for i, (campaign_name, data) in enumerate(sorted_campaigns, 1):
        if data['total_users'] > 0:
            print(f"\n🎯 CAMPAIGN {i}: {campaign_name}")
            print(f"   Source/Medium: {data['source_medium']}")
            print(f"   Total Users: {data['total_users']:,}")
            print(f"   Total Sessions: {data['total_sessions']:,}")
            print(f"   Total Pageviews: {data['total_pageviews']:,}")
            print(f"   Days Active: {len(data['daily_data'])}")

            # Show daily breakdown for top campaigns
            if i <= 5:  # Show daily breakdown for top 5 campaigns
                print("   Daily Performance:")
                sorted_dates = sorted(data['daily_data'].items())
                for date, daily_data in sorted_dates[-7:]:  # Show last 7 days
                    print(f"     • {date}: {daily_data['users']:,} users, {daily_data['sessions']:,} sessions")

            grand_total_users += data['total_users']
            campaign_count += 1

            # Limit display to top 20 campaigns
            if i >= 20:
                remaining_campaigns = len(sorted_campaigns) - 20
                remaining_users = sum(data['total_users'] for _, data in sorted_campaigns[20:])
                if remaining_campaigns > 0:
                    print(f"\n... and {remaining_campaigns} more campaigns with {remaining_users:,} total users")
                break

    print(f"\n{'='*100}")
    print("📊 SUMMARY:")
    print(f"   Date Range: {start_date} to {end_date}")
    print(f"   Total Campaigns: {campaign_count}")
    print(f"   Total Users Across All Campaigns: {grand_total_users:,}")

    # Export detailed data to CSV
    csv_data = []
    for campaign_name, data in sorted_campaigns:
        for date, daily_data in data['daily_data'].items():
            csv_data.append({
                'Date': date,
                'Campaign_Name': campaign_name,
                'Source_Medium': data['source_medium'],
                'Users': daily_data['users'],
                'Sessions': daily_data['sessions'],
                'Pageviews': daily_data['pageviews'],
                'Campaign_Total_Users': data['total_users']
            })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename("campaign_report_monthly", f"{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed data exported to: {csv_filename}")

        # Generate PDF report
        pdf_filename = create_campaign_report_pdf(campaign_data, f"{start_date}_to_{end_date}", grand_total_users, campaign_count)
        print(f"📄 PDF report exported to: {pdf_filename}")

if __name__ == "__main__":
    print("Choose report type:")
    print("1. Yesterday's campaign report")
    print("2. Monthly campaign report")
    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        get_campaign_report_yesterday()
    elif choice == "2":
        get_campaign_report_monthly()
    else:
        print("Invalid choice. Running yesterday's report by default.")
        get_campaign_report_yesterday()