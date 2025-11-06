import os
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta.types import OrderBy

from src.config import REPORTS_DIR
from src.ga4_client import run_report, create_date_range, get_yesterday_date, get_last_30_days_range, get_report_filename
from src.pdf_generator import create_campaign_report_pdf

def get_filtered_email_report_yesterday(source_filter="mailchimp"):
    """Get email campaign performance report for yesterday with custom source filter"""

    # Get yesterday's date
    yesterday = get_yesterday_date()

    print(f"📧 Generating {source_filter} performance report for {yesterday}")
    print("=" * 80)

    # Get email data for yesterday
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
        print(f"❌ No data found for yesterday.")
        return

    # Filter results to only include specified email sources
    filtered_data = []
    for row in response.rows:
        campaign_name = row.dimension_values[0].value
        source_medium = row.dimension_values[1].value
        page_path = row.dimension_values[2].value

        # Check if source contains the filter term (case insensitive)
        # For Mailchimp, also check for common Mailchimp domains
        is_mailchimp = False
        if source_filter.lower() == "mailchimp":
            mailchimp_domains = ['campaign-archive.com', 'mailchi.mp', 'mailchimp']
            is_mailchimp = any(domain in source_medium.lower() for domain in mailchimp_domains)
        else:
            is_mailchimp = source_filter.lower() in source_medium.lower()

        if is_mailchimp:
            users = int(row.metric_values[0].value)
            sessions = int(row.metric_values[1].value)
            pageviews = int(row.metric_values[2].value)
            avg_session_duration = float(row.metric_values[3].value)
            bounce_rate = float(row.metric_values[4].value)

            filtered_data.append({
                'campaign_name': campaign_name,
                'source_medium': source_medium,
                'page_path': page_path,
                'users': users,
                'sessions': sessions,
                'pageviews': pageviews,
                'avg_session_duration': avg_session_duration,
                'bounce_rate': bounce_rate
            })

    if not filtered_data:
        print(f"❌ No {source_filter} data found for yesterday after filtering.")
        return

    print(f"✅ Retrieved {len(filtered_data)} {source_filter} records for yesterday")

    # Process data into campaign-focused format
    campaign_data = {}

    for row in filtered_data:
        campaign_name = row['campaign_name']
        source_medium = row['source_medium']
        page_path = row['page_path']
        users = row['users']
        sessions = row['sessions']
        pageviews = row['pageviews']
        avg_session_duration = row['avg_session_duration']
        bounce_rate = row['bounce_rate']

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
    print(f"\n📧 {source_filter.upper()} CAMPAIGN PERFORMANCE REPORT ({yesterday})")
    print("=" * 100)

    grand_total_users = 0
    campaign_count = 0

    for i, (campaign_name, data) in enumerate(sorted_campaigns, 1):
        if data['total_users'] > 0:
            print(f"\n📧 CAMPAIGN {i}: {campaign_name}")
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
    print(f"   Total {source_filter} Campaigns: {campaign_count}")
    print(f"   Total Users from {source_filter}: {grand_total_users:,}")

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
        csv_filename = get_report_filename(f"{source_filter}_report_yesterday", yesterday)
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed data exported to: {csv_filename}")

        # Generate PDF report
        pdf_filename = create_campaign_report_pdf(campaign_data, yesterday, grand_total_users, campaign_count)
        print(f"📄 PDF report exported to: {pdf_filename}")

def get_email_sources_report():
    """Get a report of all email-related sources to see what's available"""

    # Get date range for last 30 days
    start_date, end_date = get_last_30_days_range()

    print(f"📧 Analyzing email sources for {start_date} to {end_date}")
    print("=" * 80)

    # Get all source/medium combinations
    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["sessionSourceMedium"],
        metrics=["totalUsers", "sessions"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=1000,
    )

    if response.row_count == 0:
        print("❌ No data found for the date range.")
        return

    print("📧 EMAIL-RELATED SOURCES FOUND:")
    print("=" * 80)

    email_sources = []
    for row in response.rows:
        source_medium = row.dimension_values[0].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)

        # Check for email-related sources
        email_keywords = ['mailchimp', 'email', 'newsletter', 'mail', 'campaign']
        if any(keyword in source_medium.lower() for keyword in email_keywords):
            email_sources.append({
                'source_medium': source_medium,
                'users': users,
                'sessions': sessions
            })

    if not email_sources:
        print("❌ No email-related sources found.")
        print("\n💡 Common email source patterns to look for:")
        print("   - mailchimp / email")
        print("   - email / newsletter")
        print("   - newsletter / email")
        print("   - campaign / email")
        return

    # Display email sources
    for i, source in enumerate(email_sources, 1):
        print(f"{i}. {source['source_medium']} - {source['users']:,} users, {source['sessions']:,} sessions")

    return email_sources
    """Get Mailchimp campaign performance report for the past 30 days"""

    # Get date range for last 30 days
    start_date, end_date = get_last_30_days_range()

    print(f"📧 Generating monthly Mailchimp performance report for {start_date} to {end_date}")
    print("=" * 80)

    # Get Mailchimp data for the month
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
        print("❌ No Mailchimp data found for the date range.")
        return

    # Filter results to only include Mailchimp sources
    mailchimp_data = []
    for row in response.rows:
        campaign_name = row.dimension_values[0].value
        source_medium = row.dimension_values[1].value
        date = row.dimension_values[2].value

        # Check if source contains the filter term (case insensitive)
        # For Mailchimp, also check for common Mailchimp domains
        is_mailchimp = False
        if source_filter.lower() == "mailchimp":
            mailchimp_domains = ['campaign-archive.com', 'mailchi.mp', 'mailchimp']
            is_mailchimp = any(domain in source_medium.lower() for domain in mailchimp_domains)
        else:
            is_mailchimp = source_filter.lower() in source_medium.lower()

        if is_mailchimp:
            users = int(row.metric_values[0].value)
            sessions = int(row.metric_values[1].value)
            pageviews = int(row.metric_values[2].value)

            mailchimp_data.append({
                'campaign_name': campaign_name,
                'source_medium': source_medium,
                'date': date,
                'users': users,
                'sessions': sessions,
                'pageviews': pageviews
            })

    if not mailchimp_data:
        print("❌ No Mailchimp data found for the date range after filtering.")
        return

    print(f"✅ Retrieved {len(mailchimp_data)} Mailchimp records for the month")

    # Process data into campaign-focused format
    campaign_data = {}

    for row in filtered_data:
        campaign_name = row['campaign_name']
        source_medium = row['source_medium']
        page_path = row['page_path']
        users = row['users']
        sessions = row['sessions']
        pageviews = row['pageviews']
        avg_session_duration = row['avg_session_duration']
        bounce_rate = row['bounce_rate']

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
    print(f"\n📧 MONTHLY MAILCHIMP CAMPAIGN PERFORMANCE REPORT ({start_date} to {end_date})")
    print("=" * 100)

    grand_total_users = 0
    campaign_count = 0

    for i, (campaign_name, data) in enumerate(sorted_campaigns, 1):
        if data['total_users'] > 0:
            print(f"\n📧 CAMPAIGN {i}: {campaign_name}")
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
    print(f"   Total Mailchimp Campaigns: {campaign_count}")
    print(f"   Total Users from Mailchimp: {grand_total_users:,}")

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
        csv_filename = get_report_filename("mailchimp_report_monthly", f"{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed data exported to: {csv_filename}")

        # Generate PDF report
        pdf_filename = create_campaign_report_pdf(campaign_data, f"{start_date}_to_{end_date}", grand_total_users, campaign_count)
        print(f"📄 PDF report exported to: {pdf_filename}")

def get_filtered_email_report_monthly(source_filter="mailchimp"):
    """Get email campaign performance report for the past 30 days with custom source filter"""

    # Get date range for last 30 days
    start_date, end_date = get_last_30_days_range()

    print(f"📧 Generating monthly {source_filter} performance report for {start_date} to {end_date}")
    print("=" * 80)

    # Get email data for the month
    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["sessionCampaignName", "sessionSourceMedium", "pagePath"],
        metrics=["totalUsers", "sessions", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="sessionCampaignName"), desc=False),
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=10000,
    )

    if response.row_count == 0:
        print(f"❌ No data found for the date range.")
        return

    # Filter results to only include specified email sources
    filtered_data = []
    for row in response.rows:
        campaign_name = row.dimension_values[0].value
        source_medium = row.dimension_values[1].value
        page_path = row.dimension_values[2].value

        # Check if source contains the filter term (case insensitive)
        # For Mailchimp, also check for common Mailchimp domains
        is_match = False
        if source_filter.lower() == "mailchimp":
            mailchimp_domains = ['campaign-archive.com', 'mailchi.mp', 'mailchimp']
            is_match = any(domain in source_medium.lower() for domain in mailchimp_domains)
        else:
            is_match = source_filter.lower() in source_medium.lower()

        if is_match:
            users = int(row.metric_values[0].value)
            sessions = int(row.metric_values[1].value)
            pageviews = int(row.metric_values[2].value)
            avg_session_duration = float(row.metric_values[3].value)
            bounce_rate = float(row.metric_values[4].value)

            filtered_data.append({
                'campaign_name': campaign_name,
                'source_medium': source_medium,
                'page_path': page_path,
                'users': users,
                'sessions': sessions,
                'pageviews': pageviews,
                'avg_session_duration': avg_session_duration,
                'bounce_rate': bounce_rate
            })

    if not filtered_data:
        print(f"❌ No {source_filter} data found for the date range after filtering.")
        return

    print(f"✅ Retrieved {len(filtered_data)} {source_filter} records for the month")

    # Process data into campaign-focused format
    campaign_data = {}

    for row in filtered_data:
        campaign_name = row['campaign_name']
        source_medium = row['source_medium']
        page_path = row['page_path']
        users = row['users']
        sessions = row['sessions']
        pageviews = row['pageviews']
        avg_session_duration = row['avg_session_duration']
        bounce_rate = row['bounce_rate']

        # Skip entries with no campaign name
        if not campaign_name or campaign_name == '(not set)':
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

    print(f"\n📧 MONTHLY {source_filter.upper()} CAMPAIGN PERFORMANCE REPORT ({start_date} to {end_date})")
    print("=" * 100)

    grand_total_users = 0
    campaign_count = 0

    for i, (campaign_name, data) in enumerate(sorted_campaigns, 1):
        if data['total_users'] > 0:
            print(f"\n📧 CAMPAIGN {i}: {campaign_name}")
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
    print(f"   Date Range: {start_date} to {end_date}")
    print(f"   Total {source_filter} Campaigns: {campaign_count}")
    print(f"   Total Users from {source_filter}: {grand_total_users:,}")

    # Export detailed data to CSV
    csv_data = []
    for campaign_name, data in sorted_campaigns:
        for page_path, page_data in data['pages'].items():
            csv_data.append({
                'Date_Range': f"{start_date}_to_{end_date}",
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
        csv_filename = get_report_filename(f"{source_filter}_report_monthly", f"{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed data exported to: {csv_filename}")

        # Generate PDF report
        pdf_filename = create_campaign_report_pdf(campaign_data, f"{start_date}_to_{end_date}", grand_total_users, campaign_count)
        print(f"📄 PDF report exported to: {pdf_filename}")

if __name__ == "__main__":
    print("Choose email source report type:")
    print("1. Yesterday's Mailchimp report")
    print("2. Monthly Mailchimp report")
    print("3. Check available email sources")
    print("4. Custom source filter (yesterday)")
    choice = input("Enter choice (1, 2, 3, or 4): ").strip()

    if choice == "1":
        get_filtered_email_report_yesterday("mailchimp")
    elif choice == "2":
        get_filtered_email_report_monthly("mailchimp")
    elif choice == "3":
        get_email_sources_report()
    elif choice == "4":
        source_filter = input("Enter source filter term (e.g., 'mailchimp', 'email', 'newsletter'): ").strip()
        if source_filter:
            get_filtered_email_report_yesterday(source_filter)
        else:
            print("No filter provided. Using 'mailchimp' by default.")
            get_filtered_email_report_yesterday("mailchimp")
    else:
        print("Invalid choice. Running yesterday's Mailchimp report by default.")
        get_filtered_email_report_yesterday("mailchimp")