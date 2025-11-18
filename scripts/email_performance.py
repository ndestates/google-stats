import os
import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta.types import OrderBy

from src.pdf_generator import create_campaign_report_pdf
from src.ga4_client import run_report, create_date_range, get_yesterday_date, get_last_30_days_range, get_report_filename

def categorize_email_source(source_medium: str) -> str:
    """Categorize email sources into different providers/campaigns"""
    source_lower = source_medium.lower()

    # Bailiwick Express campaigns
    if 'allislandmedia.cmail' in source_lower:
        return 'Bailiwick Express'

    # Places.je campaigns
    if 'places.je' in source_lower:
        return 'Places.je'

    # Other email sources (excluding actual Mailchimp)
    if 'email' in source_lower:
        return 'Email'

    # Don't categorize actual Mailchimp sources
    return 'Other'

def generate_comprehensive_email_reports():
    """Generate separate reports for different email marketing sources"""

    print("📧 Generating Comprehensive Email Reports")
    print("=" * 80)

    # Get yesterday's date
    yesterday = get_yesterday_date()
    date_range = create_date_range(yesterday, yesterday)

    # Get all email-related data
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
        print("❌ No email data found for yesterday.")
        return

    # Categorize data by email source type
    categorized_data = {
        'Bailiwick Express': [],
        'Places.je': []
    }

    for row in response.rows:
        campaign_name = row.dimension_values[0].value
        source_medium = row.dimension_values[1].value
        page_path = row.dimension_values[2].value

        category = categorize_email_source(source_medium)

        # Only include if it's Places.je or Bailiwick Express
        if category in ['Bailiwick Express', 'Places.je']:
            users = int(row.metric_values[0].value)
            sessions = int(row.metric_values[1].value)
            pageviews = int(row.metric_values[2].value)
            avg_session_duration = float(row.metric_values[3].value)
            bounce_rate = float(row.metric_values[4].value)

            categorized_data[category].append({
                'campaign_name': campaign_name,
                'source_medium': source_medium,
                'page_path': page_path,
                'users': users,
                'sessions': sessions,
                'pageviews': pageviews,
                'avg_session_duration': avg_session_duration,
                'bounce_rate': bounce_rate
            })

    # Generate separate reports for each category with data
    for category, data in categorized_data.items():
        if not data:
            continue

        print(f"\n📧 Processing {category} ({len(data)} records)")
        print("-" * 50)

        # Process data for this category
        campaign_data = {}
        total_users = 0
        campaign_count = 0

        for row in data:
            campaign_name = row['campaign_name']
            page_path = row['page_path']
            users = row['users']
            sessions = row['sessions']
            pageviews = row['pageviews']
            avg_session_duration = row['avg_session_duration']
            bounce_rate = row['bounce_rate']

            total_users += users

            # Skip entries with no campaign name
            if not campaign_name or campaign_name == '(not set)':
                continue

            # Skip /sold/ pages
            if page_path.startswith('/sold/'):
                continue

            if campaign_name not in campaign_data:
                campaign_data[campaign_name] = {
                    'total_users': 0,
                    'total_sessions': 0,
                    'total_pageviews': 0,
                    'source_medium': row['source_medium'],  # Add source_medium for PDF generator
                    'pages': {}
                }
                campaign_count += 1

            campaign_data[campaign_name]['total_users'] += users
            campaign_data[campaign_name]['total_sessions'] += sessions
            campaign_data[campaign_name]['total_pageviews'] += pageviews

            if page_path not in campaign_data[campaign_name]['pages']:
                campaign_data[campaign_name]['pages'][page_path] = {
                    'users': 0,
                    'sessions': 0,
                    'pageviews': 0,
                    'avg_session_duration': 0,
                    'bounce_rate': 0
                }

            campaign_data[campaign_name]['pages'][page_path]['users'] += users
            campaign_data[campaign_name]['pages'][page_path]['sessions'] += sessions
            campaign_data[campaign_name]['pages'][page_path]['pageviews'] += pageviews
            campaign_data[campaign_name]['pages'][page_path]['avg_session_duration'] = avg_session_duration
            campaign_data[campaign_name]['pages'][page_path]['bounce_rate'] = bounce_rate

        if campaign_count > 0:
            # Collect top pages for this category
            all_pages = {}
            for campaign_name, campaign_info in campaign_data.items():
                for page_path, page_data in campaign_info['pages'].items():
                    if page_path not in all_pages:
                        all_pages[page_path] = {'users': 0, 'sessions': 0, 'pageviews': 0}
                    all_pages[page_path]['users'] += page_data['users']
                    all_pages[page_path]['sessions'] += page_data['sessions']
                    all_pages[page_path]['pageviews'] += page_data['pageviews']

            # Display top 10 pages for this category
            if all_pages:
                print(f"\n📄 Top pages visited from {category}:")
                sorted_pages = sorted(all_pages.items(), key=lambda x: x[1]['users'], reverse=True)
                for i, (page_path, page_stats) in enumerate(sorted_pages[:10], 1):
                    print(f"   {i}. {page_path}")
                    print(f"      Users: {page_stats['users']:,}, Sessions: {page_stats['sessions']:,}, Pageviews: {page_stats['pageviews']:,}")

            # Generate PDF report for this category
            pdf_filename = create_campaign_report_pdf(campaign_data, f"{yesterday}", total_users, campaign_count)
            print(f"✅ {category} report generated: {pdf_filename}")
            print(f"   {campaign_count} campaigns, {total_users:,} total users")
        else:
            print(f"⚠️  No valid campaigns found for {category}")

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Comprehensive Email Campaign Performance Analysis')
    parser.add_argument('--report-type', type=str,
                       choices=['comprehensive', 'sources'],
                       default='comprehensive', help='Type of report to generate')

    args = parser.parse_args()

    print("📧 Comprehensive Email Campaign Performance Analysis")
    print("=" * 60)

    if args.report_type == 'comprehensive':
        print("Running comprehensive email reports (separate reports for each email source)")
        generate_comprehensive_email_reports()
    elif args.report_type == 'sources':
        print("Checking available email sources")
        get_email_sources_report()