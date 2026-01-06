#!/usr/bin/env python3
"""
Run with: ddev exec python scripts/yesterday_report.py
"""

import os
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta.types import OrderBy

from src.config import REPORTS_DIR
from src.ga4_client import run_report, create_date_range, get_yesterday_date, get_report_filename
from src.pdf_generator import create_yesterday_report_pdf

def get_yesterday_report():
    """Get comprehensive page-source report for yesterday only"""

    # Get yesterday's date
    yesterday = get_yesterday_date()

    print(f"📊 Generating yesterday's page-source report for {yesterday}")
    print("=" * 80)

    # Get all page + source combinations for yesterday
    date_range = create_date_range(yesterday, yesterday)

    response = run_report(
        dimensions=["pagePath", "sessionSourceMedium", "sessionCampaignName"],
        metrics=["totalUsers", "sessions", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="pagePath"), desc=False),
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=5000,
    )

    if response.row_count == 0:
        print("❌ No data found for yesterday.")
        return

    print(f"✅ Retrieved {response.row_count} page-source combinations for yesterday")

    # Process data into a structured format
    page_data = {}

    for row in response.rows:
        page_path = row.dimension_values[0].value
        source_medium = row.dimension_values[1].value
        campaign_name = row.dimension_values[2].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_session_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)

        # Skip /sold/ pages as they no longer exist
        if page_path.startswith('/sold/'):
            continue

        if page_path not in page_data:
            page_data[page_path] = {
                'total_users': 0,
                'total_sessions': 0,
                'total_pageviews': 0,
                'avg_session_duration': 0,
                'bounce_rate': 0,
                'sources': []
            }

        # Create a combined source_medium + campaign identifier
        if campaign_name and campaign_name != '(not set)':
            source_display = f"{source_medium} | {campaign_name}"
        else:
            source_display = source_medium

        page_data[page_path]['sources'].append({
            'source_medium': source_display,
            'campaign': campaign_name if campaign_name != '(not set)' else '',
            'users': users,
            'sessions': sessions,
            'pageviews': pageviews,
            'avg_session_duration': avg_session_duration,
            'bounce_rate': bounce_rate
        })
        page_data[page_path]['total_users'] += users
        page_data[page_path]['total_sessions'] += sessions
        page_data[page_path]['total_pageviews'] += pageviews

    # Sort pages by total users (descending)
    sorted_pages = sorted(page_data.items(), key=lambda x: x[1]['total_users'], reverse=True)

    # Display results
    print(f"\n📈 YESTERDAY'S PAGE-SOURCE REPORT ({yesterday})")
    print("=" * 100)

    grand_total_users = 0
    page_count = 0

    for i, (page_path, data) in enumerate(sorted_pages, 1):
        if data['total_users'] > 0:  # Only show pages with users
            print(f"\n🏠 PAGE {i}: {page_path}")
            print(f"   Total Users: {data['total_users']:,}")

            # Sort sources by users descending
            sorted_sources = sorted(data['sources'], key=lambda x: x['users'], reverse=True)

            print("   Traffic Sources:")
            for source in sorted_sources:
                if source['users'] > 0:
                    percentage = (source['users'] / data['total_users'] * 100)
                    print(f"     • {source['source_medium']:<35} {source['users']:>3} users ({percentage:5.1f}%)")

            grand_total_users += data['total_users']
            page_count += 1

            # Limit display to top 50 pages to avoid overwhelming output
            if i >= 50:
                remaining_pages = len(sorted_pages) - 50
                remaining_users = sum(data['total_users'] for _, data in sorted_pages[50:])
                if remaining_pages > 0:
                    print(f"\n... and {remaining_pages} more pages with {remaining_users:,} total users")
                break

    print(f"\n{'='*100}")
    print("📊 SUMMARY:")
    print(f"   Date: {yesterday}")
    print(f"   Total Pages: {page_count}")
    print(f"   Total Users Across All Pages: {grand_total_users:,}")
    if page_count > 0:
        print(f"   Average Users Per Page: {grand_total_users / page_count:.1f}")

    # Export detailed data to CSV
    csv_data = []
    for page_path, data in sorted_pages:
        for source in data['sources']:
            if source['users'] > 0:
                csv_data.append({
                    'Date': str(yesterday),
                    'Page_Path': page_path,
                    'Source_Medium': source['source_medium'].split(' | ')[0] if ' | ' in source['source_medium'] else source['source_medium'],
                    'Campaign_Name': source.get('campaign', ''),
                    'Users': source['users'],
                    'Sessions': source['sessions'],
                    'Pageviews': source['pageviews'],
                    'Avg_Session_Duration': source['avg_session_duration'],
                    'Bounce_Rate': source['bounce_rate'],
                    'Page_Total_Users': data['total_users']
                })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename("yesterday_report", yesterday)
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed data exported to: {csv_filename}")

        # Also create a summary CSV with one row per page
        summary_data = []
        for page_path, data in sorted_pages:
            if data['total_users'] > 0:
                # Get top source for summary
                top_source = max(data['sources'], key=lambda x: x['users']) if data['sources'] else {'source_medium': 'None', 'users': 0}
                summary_data.append({
                    'Date': str(yesterday),
                    'Page_Path': page_path,
                    'Total_Users': data['total_users'],
                    'Top_Source': top_source['source_medium'],
                    'Top_Source_Users': top_source['users']
                })

        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_filename = get_report_filename("yesterday_summary", yesterday)
            summary_df.to_csv(summary_filename, index=False)
            print(f"📄 Page summary exported to: {summary_filename}")
        # Export detailed data to CSV
        csv_data = []
        for page_path, data in sorted_pages:
            for source in data['sources']:
                if source['users'] > 0:
                    csv_data.append({
                        'Date': str(yesterday),
                        'Page_Path': page_path,
                        'Source_Medium': source['source_medium'],
                        'Users': source['users'],
                        'Page_Total_Users': data['total_users']
                    })

        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_filename = get_report_filename("yesterday_report", yesterday)
            df.to_csv(csv_filename, index=False)
            print(f"\n📄 Detailed data exported to: {csv_filename}")

            # Also create a summary CSV with one row per page
            summary_data = []
            for page_path, data in sorted_pages:
                if data['total_users'] > 0:
                    # Get top source for summary
                    top_source = max(data['sources'], key=lambda x: x['users']) if data['sources'] else {'source_medium': 'None', 'users': 0}
                    summary_data.append({
                        'Date': str(yesterday),
                        'Page_Path': page_path,
                        'Total_Users': data['total_users'],
                        'Top_Source': top_source['source_medium'],
                        'Top_Source_Users': top_source['users']
                    })

            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_filename = get_report_filename("yesterday_summary", yesterday)
                summary_df.to_csv(summary_filename, index=False)
                print(f"📄 Page summary exported to: {summary_filename}")

            # Generate PDF report
            pdf_filename = create_yesterday_report_pdf(
                page_data,
                yesterday,
                grand_total_users,
                page_count,
                grand_total_users / page_count if page_count > 0 else 0
            )
            print(f"📄 PDF report exported to: {pdf_filename}")

if __name__ == "__main__":
    get_yesterday_report()