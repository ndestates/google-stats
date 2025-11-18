import os
import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta.types import OrderBy, FilterExpression, Filter

from src.pdf_generator import create_campaign_report_pdf, create_24hour_campaign_report_pdf
from src.ga4_client import run_report, create_date_range, get_yesterday_date, get_last_30_days_range, get_report_filename

def get_filtered_email_report_by_date(source_filter="mailchimp", target_date=None, hour_filter=None):
    """Get email campaign performance report for a specific date with optional hour filtering"""

    # Use provided date or default to yesterday
    if target_date is None:
        target_date = get_yesterday_date()

    print(f"📧 Generating {source_filter} performance report for {target_date}")
    if hour_filter is not None:
        print(f"   Filtering by hour: {hour_filter}")
    print("=" * 80)

    # Get email data for the specified date
    date_range = create_date_range(target_date, target_date)

    # Build dimensions - always use the same dimensions
    dimensions = ["sessionCampaignName", "sessionSourceMedium", "pagePath"]

    # Build dimension filter for hour if specified
    dimension_filter = None
    if hour_filter is not None:
        dimension_filter = FilterExpression(
            filter=Filter(
                field_name="hour",
                string_filter=Filter.StringFilter(value=str(hour_filter))
            )
        )

    response = run_report(
        dimensions=dimensions,
        metrics=["totalUsers", "sessions", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        dimension_filter=dimension_filter,
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=5000,
    )

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
        print(f"❌ No data found for {target_date}.")
        return

    # Filter results to only include specified email sources
    filtered_data = []
    for row in response.rows:
        # Dimensions are always: [sessionCampaignName, sessionSourceMedium, pagePath]
        campaign_name = row.dimension_values[0].value
        source_medium = row.dimension_values[1].value
        page_path = row.dimension_values[2].value

        # Check if source contains the filter term (case insensitive)
        # For Mailchimp, also check for common Mailchimp domains and email sources
        # Exclude Places.je and Bailiwick Express sources
        is_mailchimp = False
        if source_filter.lower() == "mailchimp":
            mailchimp_indicators = [
                'campaign-archive.com',  # Main Mailchimp campaign domain
                'mailchi.mp',           # Mailchimp link shortener
                'mailchimp',            # Any mailchimp references
                'email'                 # Email sources (for comprehensive email tracking)
            ]
            source_lower = source_medium.lower()
            # Include if it matches Mailchimp indicators AND is NOT Places.je or Bailiwick Express
            is_mailchimp = (any(indicator in source_lower for indicator in mailchimp_indicators) and
                          'places.je' not in source_lower and
                          'allislandmedia.cmail' not in source_lower)
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
        filter_desc = f" for hour {hour_filter}" if hour_filter is not None else ""
        print(f"❌ No {source_filter} data found for {target_date}{filter_desc} after filtering.")
        return

    print(f"✅ Retrieved {len(filtered_data)} {source_filter} records for {target_date}")

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
    filter_desc = f" (Hour {hour_filter})" if hour_filter is not None else ""
    print(f"\n📧 {source_filter.upper()} CAMPAIGN PERFORMANCE REPORT ({target_date}){filter_desc}")
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
    print(f"   Date: {target_date}")
    if hour_filter is not None:
        print(f"   Hour Filter: {hour_filter}:00")
    print(f"   Total {source_filter} Campaigns: {campaign_count}")
    print(f"   Total Users from {source_filter}: {grand_total_users:,}")

    # Export detailed data to CSV
    csv_data = []
    for campaign_name, data in sorted_campaigns:
        for page_path, page_data in data['pages'].items():
            csv_data.append({
                'Date': str(target_date),
                'Hour': hour_filter if hour_filter is not None else 'All',
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
        hour_suffix = f"_hour_{hour_filter}" if hour_filter is not None else ""
        csv_filename = get_report_filename(f"{source_filter}_report_{target_date}{hour_suffix}", target_date)
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed data exported to: {csv_filename}")

        # Generate PDF report
        pdf_filename = create_campaign_report_pdf(campaign_data, f"{target_date}", grand_total_users, campaign_count)
        print(f"📄 PDF report exported to: {pdf_filename}")

def get_filtered_email_report_yesterday(source_filter="mailchimp"):
    """Get email campaign performance report for yesterday with custom source filter"""
    get_filtered_email_report_by_date(source_filter, None, None)

def get_24_hour_email_report(target_date=None, source_filter="mailchimp"):
    """Get 24-hour breakdown email campaign performance report for a specific date"""

    # Use provided date or default to yesterday
    if target_date is None:
        target_date = get_yesterday_date()

    print(f"📧 Generating 24-hour {source_filter} performance report for {target_date}")
    print("=" * 80)

    # Get email data for the specified date with hour dimension
    date_range = create_date_range(target_date, target_date)

    response = run_report(
        dimensions=["hour", "sessionCampaignName", "sessionSourceMedium", "pagePath"],
        metrics=["totalUsers", "sessions", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="hour"), desc=False),
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=10000,
    )

    if response.row_count == 0:
        print(f"❌ No data found for {target_date}.")
        return

    # Process data into hour-based format
    hourly_data = {}
    campaign_data = {}

    for row in response.rows:
        hour = int(row.dimension_values[0].value)
        campaign_name = row.dimension_values[1].value
        source_medium = row.dimension_values[2].value
        page_path = row.dimension_values[3].value

        # Check if source contains the filter term (case insensitive)
        # For Mailchimp, also check for common Mailchimp domains and email sources
        # Exclude Places.je and Bailiwick Express sources
        is_match = False
        if source_filter.lower() == "mailchimp":
            mailchimp_indicators = [
                'campaign-archive.com',  # Main Mailchimp campaign domain
                'mailchi.mp',           # Mailchimp link shortener
                'mailchimp',            # Any mailchimp references
                'email'                 # Email sources (for comprehensive email tracking)
            ]
            source_lower = source_medium.lower()
            # Include if it matches Mailchimp indicators AND is NOT Places.je or Bailiwick Express
            is_match = (any(indicator in source_lower for indicator in mailchimp_indicators) and
                       'places.je' not in source_lower and
                       'allislandmedia.cmail' not in source_lower)
        else:
            is_match = source_filter.lower() in source_medium.lower()

        if not is_match:
            continue

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

        # Initialize hour data
        if hour not in hourly_data:
            hourly_data[hour] = {
                'total_users': 0,
                'total_sessions': 0,
                'total_pageviews': 0,
                'campaigns': {}
            }

        hourly_data[hour]['total_users'] += users
        hourly_data[hour]['total_sessions'] += sessions
        hourly_data[hour]['total_pageviews'] += pageviews

        # Track campaign data per hour
        if campaign_name not in hourly_data[hour]['campaigns']:
            hourly_data[hour]['campaigns'][campaign_name] = {
                'users': 0,
                'sessions': 0,
                'pageviews': 0,
                'source_medium': source_medium
            }

        hourly_data[hour]['campaigns'][campaign_name]['users'] += users
        hourly_data[hour]['campaigns'][campaign_name]['sessions'] += sessions
        hourly_data[hour]['campaigns'][campaign_name]['pageviews'] += pageviews

        # Also track overall campaign data
        if campaign_name not in campaign_data:
            campaign_data[campaign_name] = {
                'total_users': 0,
                'total_sessions': 0,
                'total_pageviews': 0,
                'source_medium': source_medium,
                'hourly_breakdown': {}
            }

        campaign_data[campaign_name]['total_users'] += users
        campaign_data[campaign_name]['total_sessions'] += sessions
        campaign_data[campaign_name]['total_pageviews'] += pageviews

        if hour not in campaign_data[campaign_name]['hourly_breakdown']:
            campaign_data[campaign_name]['hourly_breakdown'][hour] = {
                'users': 0,
                'sessions': 0,
                'pageviews': 0
            }

        campaign_data[campaign_name]['hourly_breakdown'][hour]['users'] += users
        campaign_data[campaign_name]['hourly_breakdown'][hour]['sessions'] += sessions
        campaign_data[campaign_name]['hourly_breakdown'][hour]['pageviews'] += pageviews

    if not hourly_data:
        print(f"❌ No {source_filter} data found for {target_date} after filtering.")
        return

    print(f"✅ Retrieved data for {len(hourly_data)} hours on {target_date}")

    # Display 24-hour summary
    print(f"\n📧 24-HOUR {source_filter.upper()} PERFORMANCE REPORT ({target_date})")
    print("=" * 100)

    total_users_all_hours = 0
    total_sessions_all_hours = 0
    total_pageviews_all_hours = 0

    # Show hourly breakdown
    for hour in range(24):
        if hour in hourly_data:
            data = hourly_data[hour]
            total_users_all_hours += data['total_users']
            total_sessions_all_hours += data['total_sessions']
            total_pageviews_all_hours += data['total_pageviews']

            print(f"\n🕐 HOUR {hour:02d}:00 - {hour+1:02d}:00")
            print(f"   Users: {data['total_users']:,} | Sessions: {data['total_sessions']:,} | Pageviews: {data['total_pageviews']:,}")

            # Show top campaigns for this hour
            sorted_campaigns = sorted(data['campaigns'].items(), key=lambda x: x[1]['users'], reverse=True)[:3]
            if sorted_campaigns:
                print("   Top Campaigns:")
                for campaign_name, camp_data in sorted_campaigns:
                    print(f"     • {campaign_name[:40]}{'...' if len(campaign_name) > 40 else ''} - {camp_data['users']:,} users")
        else:
            print(f"\n🕐 HOUR {hour:02d}:00 - {hour+1:02d}:00")
            print("   No data")

    print(f"\n{'='*100}")
    print("📊 DAILY SUMMARY:")
    print(f"   Date: {target_date}")
    print(f"   Total Hours with Data: {len(hourly_data)}")
    print(f"   Total Users: {total_users_all_hours:,}")
    print(f"   Total Sessions: {total_sessions_all_hours:,}")
    print(f"   Total Pageviews: {total_pageviews_all_hours:,}")

    # Export detailed data to CSV
    csv_data = []
    for hour in range(24):
        if hour in hourly_data:
            for campaign_name, camp_data in hourly_data[hour]['campaigns'].items():
                csv_data.append({
                    'Date': str(target_date),
                    'Hour': hour,
                    'Campaign_Name': campaign_name,
                    'Source_Medium': camp_data['source_medium'],
                    'Users': camp_data['users'],
                    'Sessions': camp_data['sessions'],
                    'Pageviews': camp_data['pageviews'],
                    'Hourly_Total_Users': hourly_data[hour]['total_users'],
                    'Hourly_Total_Sessions': hourly_data[hour]['total_sessions'],
                    'Hourly_Total_Pageviews': hourly_data[hour]['total_pageviews']
                })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename(f"{source_filter}_24hour_report_{target_date}", target_date)
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed data exported to: {csv_filename}")

        # Generate PDF report with hourly data
        pdf_filename = create_24hour_campaign_report_pdf(hourly_data, campaign_data, target_date, total_users_all_hours)
        print(f"📄 PDF report exported to: {pdf_filename}")

def get_date_range_email_report(start_date, end_date, source_filter="mailchimp"):
    """Get email campaign performance report for a custom date range"""

    print(f"📧 Generating {source_filter} performance report for {start_date} to {end_date}")
    print("=" * 80)

    # Get email data for the specified date range
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
        print(f"❌ No data found for the date range {start_date} to {end_date}.")
        return

    # Filter results to only include specified email sources
    filtered_data = []
    for row in response.rows:
        campaign_name = row.dimension_values[0].value
        source_medium = row.dimension_values[1].value
        page_path = row.dimension_values[2].value

        # Check if source contains the filter term (case insensitive)
        # For Mailchimp, also check for common Mailchimp domains and email sources
        # Exclude Places.je and Bailiwick Express sources
        is_match = False
        if source_filter.lower() == "mailchimp":
            mailchimp_indicators = [
                'campaign-archive.com',  # Main Mailchimp campaign domain
                'mailchi.mp',           # Mailchimp link shortener
                'mailchimp',            # Any mailchimp references
                'email'                 # Email sources (for comprehensive email tracking)
            ]
            source_lower = source_medium.lower()
            # Include if it matches Mailchimp indicators AND is NOT Places.je or Bailiwick Express
            is_match = (any(indicator in source_lower for indicator in mailchimp_indicators) and
                       'places.je' not in source_lower and
                       'allislandmedia.cmail' not in source_lower)
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
        print(f"❌ No {source_filter} data found for the date range {start_date} to {end_date} after filtering.")
        return

    print(f"✅ Retrieved {len(filtered_data)} {source_filter} records for the date range")

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

    print(f"\n📧 {source_filter.upper()} CAMPAIGN PERFORMANCE REPORT ({start_date} to {end_date})")
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
        csv_filename = get_report_filename(f"{source_filter}_report_{start_date}_to_{end_date}", f"{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed data exported to: {csv_filename}")

        # Generate PDF report
        pdf_filename = create_campaign_report_pdf(campaign_data, f"{start_date}_to_{end_date}", grand_total_users, campaign_count)
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
        # For Mailchimp, also check for common Mailchimp domains and email sources
        # Exclude Places.je and Bailiwick Express sources
        is_match = False
        if source_filter.lower() == "mailchimp":
            mailchimp_indicators = [
                'campaign-archive.com',  # Main Mailchimp campaign domain
                'mailchi.mp',           # Mailchimp link shortener
                'mailchimp',            # Any mailchimp references
                'email'                 # Email sources (for comprehensive email tracking)
            ]
            source_lower = source_medium.lower()
            # Include if it matches Mailchimp indicators AND is NOT Places.je or Bailiwick Express
            is_match = (any(indicator in source_lower for indicator in mailchimp_indicators) and
                       'places.je' not in source_lower and
                       'allislandmedia.cmail' not in source_lower)
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
    parser = argparse.ArgumentParser(description='Mailchimp Campaign Performance Analysis')
    parser.add_argument('--report-type', type=str,
                       choices=['yesterday', 'monthly', 'sources', 'custom', 'by-date', '24-hour', 'date-range'],
                       default='yesterday', help='Type of report to generate (default: yesterday)')
    parser.add_argument('--source-filter', type=str, default='mailchimp',
                       help='Source filter term for custom reports (default: mailchimp)')
    parser.add_argument('--date', type=str,
                       help='Specific date for by-date report (format: YYYY-MM-DD, e.g., 2025-11-16)')
    parser.add_argument('--hour', type=int,
                       help='Hour filter for by-date report (0-23, e.g., 14 for 2 PM)')
    parser.add_argument('--start-date', type=str,
                       help='Start date for date-range report (format: YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                       help='End date for date-range report (format: YYYY-MM-DD)')

    args = parser.parse_args()

    print("📧 Email Campaign Performance Analysis")
    print("=" * 50)

    if args.report_type == 'yesterday':
        print("Running yesterday's email report")
        get_filtered_email_report_yesterday(args.source_filter)
    elif args.report_type == 'monthly':
        print("Running monthly email report")
        get_filtered_email_report_monthly(args.source_filter)
    elif args.report_type == 'sources':
        print("Checking available email sources")
        get_email_sources_report()
    elif args.report_type == 'custom':
        print(f"Running custom source filter report for '{args.source_filter}'")
        get_filtered_email_report_yesterday(args.source_filter)
    elif args.report_type == 'by-date':
        if not args.date:
            print("❌ Error: --date is required for by-date report type")
            print("   Example: --report-type by-date --date 2025-11-16")
            exit(1)
        try:
            # Validate date format
            datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"❌ Error: Invalid date format '{args.date}'. Use YYYY-MM-DD format.")
            exit(1)
        if args.hour is not None and (args.hour < 0 or args.hour > 23):
            print(f"❌ Error: Invalid hour '{args.hour}'. Must be between 0-23.")
            exit(1)
        print(f"Running by-date email report for {args.date}")
        if args.hour is not None:
            print(f"   Filtering by hour: {args.hour}:00")
        get_filtered_email_report_by_date(args.source_filter, args.date, args.hour)
    elif args.report_type == '24-hour':
        if not args.date:
            print("❌ Error: --date is required for 24-hour report type")
            print("   Example: --report-type 24-hour --date 2025-11-16")
            exit(1)
        try:
            # Validate date format
            datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"❌ Error: Invalid date format '{args.date}'. Use YYYY-MM-DD format.")
            exit(1)
        get_24_hour_email_report(args.date, args.source_filter)
    elif args.report_type == 'date-range':
        if not args.start_date or not args.end_date:
            print("❌ Error: --start-date and --end-date are required for date-range report type")
            print("   Example: --report-type date-range --start-date 2025-11-10 --end-date 2025-11-16")
            exit(1)
        try:
            # Validate date formats
            start_dt = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(args.end_date, '%Y-%m-%d')
            if start_dt > end_dt:
                print("❌ Error: Start date cannot be after end date.")
                exit(1)
        except ValueError:
            print(f"❌ Error: Invalid date format. Use YYYY-MM-DD format for both dates.")
            exit(1)
        print(f"Running date-range email report from {args.start_date} to {args.end_date}")
        get_date_range_email_report(args.start_date, args.end_date, args.source_filter)