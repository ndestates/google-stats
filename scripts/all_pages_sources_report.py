#!/usr/bin/env python3
"""
Run with: ddev exec python scripts/all_pages_sources_report.py
"""

import os
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta.types import OrderBy

from src.config import REPORTS_DIR
from src.ga4_client import run_report, create_date_range, get_last_30_days_range, get_report_filename
from src.pdf_generator import create_comprehensive_report_pdf

def get_all_pages_with_sources():
    """Get all pages with their traffic sources for the past 30 days"""

    # Get date range for last 30 days
    start_date, end_date = get_last_30_days_range()

    print(f"📊 Generating comprehensive page-source report for {start_date} to {end_date}")
    print("=" * 80)

    # Get all page + source combinations
    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["pagePath", "sessionSourceMedium"],
        metrics=["totalUsers"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="pagePath"), desc=False),
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=10000,
    )

    if response.row_count == 0:
        print("❌ No data found for the date range.")
        return

    print(f"✅ Retrieved {response.row_count} page-source combinations")

    # Process data into a structured format
    page_data = {}

    for row in response.rows:
        page_path = row.dimension_values[0].value
        source_medium = row.dimension_values[1].value
        users = int(row.metric_values[0].value)

        # Skip /sold/ pages as they no longer exist
        if page_path.startswith('/sold/'):
            continue

        if page_path not in page_data:
            page_data[page_path] = {
                'total_users': 0,
                'sources': []
            }

        page_data[page_path]['sources'].append({
            'source_medium': source_medium,
            'users': users
        })
        page_data[page_path]['total_users'] += users

    # Sort pages by total users (descending)
    sorted_pages = sorted(page_data.items(), key=lambda x: x[1]['total_users'], reverse=True)

    # Display results
    print(f"\n📈 COMPREHENSIVE PAGE-SOURCE REPORT ({start_date} to {end_date})")
    print("=" * 100)

    grand_total_users = 0
    page_count = 0

    for page_path, data in sorted_pages:
        page_count += 1
        total_page_users = data['total_users']
        grand_total_users += total_page_users

        print(f"\n🏠 PAGE {page_count}: {page_path}")
        print(f"   Total Users: {total_page_users:,}")
        print("   Traffic Sources:")

        # Sort sources by users within each page
        sorted_sources = sorted(data['sources'], key=lambda x: x['users'], reverse=True)

        for source in sorted_sources:
            percentage = (source['users'] / total_page_users) * 100
            print(f"     • {source['source_medium']:<35} {source['users']:>6,} users ({percentage:>5.1f}%)")

    print(f"\n{'='*100}")
    print(f"📊 SUMMARY:")
    print(f"   Total Pages: {page_count:,}")
    print(f"   Total Users Across All Pages: {grand_total_users:,}")
    print(f"   Average Users Per Page: {grand_total_users/page_count:,.1f}")

    # Export detailed data to CSV
    csv_data = []
    for page_path, data in sorted_pages:
        for source in data['sources']:
            csv_data.append({
                'Date_Range': f"{start_date}_to_{end_date}",
                'Page_Path': page_path,
                'Source_Medium': source['source_medium'],
                'Users': source['users'],
                'Page_Total_Users': data['total_users']
            })

    df = pd.DataFrame(csv_data)
    csv_filename = get_report_filename("comprehensive_page_source_report", f"{start_date}_to_{end_date}")
    df.to_csv(csv_filename, index=False)
    print(f"\n📄 Detailed data exported to: {csv_filename}")

    # Also create a summary CSV with one row per page
    summary_data = []
    for page_path, data in sorted_pages:
        if data['total_users'] > 0:
            # Get top source for summary
            top_source = max(data['sources'], key=lambda x: x['users']) if data['sources'] else {'source_medium': 'None', 'users': 0}
            summary_data.append({
                'Date_Range': f"{start_date}_to_{end_date}",
                'Page_Path': page_path,
                'Total_Users': data['total_users'],
                'Top_Source': top_source['source_medium'],
                'Top_Source_Users': top_source['users']
            })

    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_filename = get_report_filename("page_summary_report", f"{start_date}_to_{end_date}")
        summary_df.to_csv(summary_filename, index=False)
        print(f"📄 Page summary exported to: {summary_filename}")

    # Generate PDF report
    pdf_filename = create_comprehensive_report_pdf(
        page_data,
        start_date,
        end_date,
        grand_total_users,
        page_count,
        grand_total_users / page_count if page_count > 0 else 0
    )
    print(f"📄 PDF report exported to: {pdf_filename}")

if __name__ == "__main__":
    get_all_pages_with_sources()