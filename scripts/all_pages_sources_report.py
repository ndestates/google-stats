#!/usr/bin/env python3
"""
Run with: ddev exec python scripts/all_pages_sources_report.py
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta.types import OrderBy

from src.config import REPORTS_DIR
from src.ga4_client import run_report, create_date_range, get_last_30_days_range, get_report_filename
from src.pdf_generator import create_comprehensive_report_pdf

def load_campaign_mappings():
    """Load URL-to-campaign mappings from database and source unifications from config file"""

    # Load source unifications from JSON config
    mapping_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'url_campaign_mapping.json')
    source_unifications = {}

    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r') as f:
                data = json.load(f)
                source_unifications = data.get('source_unifications', {})
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️  Warning: Could not load source unifications: {e}")

    # Load campaign mappings from database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'properties.db')
    campaign_mappings = {}

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get all URL-to-campaign mappings from database
            cursor.execute('SELECT url, campaign FROM properties WHERE campaign IS NOT NULL')
            rows = cursor.fetchall()

            for url, campaign in rows:
                if url and campaign:
                    campaign_mappings[url] = campaign

            conn.close()
            print(f"📋 Loaded {len(campaign_mappings)} URL-to-campaign mappings from database")

        except sqlite3.Error as e:
            print(f"⚠️  Warning: Could not load campaign mappings from database: {e}")
            # Fall back to basic mapping
            campaign_mappings = {"/properties/": "Jersey Property Listings"}
    else:
        print("ℹ️  Property database not found. Using basic property mapping.")
        campaign_mappings = {"/properties/": "Jersey Property Listings"}

    return campaign_mappings, source_unifications

def unify_source_name(source_medium, source_unifications):
    """Unify source names based on mapping rules"""
    # Check for exact matches first
    if source_medium in source_unifications:
        return source_unifications[source_medium]

    # Handle common patterns
    if source_medium.startswith('google.com'):
        return source_medium.replace('google.com', 'google')

    return source_medium

def get_campaign_for_url(url_path, campaign_mappings):
    """Get campaign name for a URL path"""
    # Check for exact match first (from database)
    if url_path in campaign_mappings:
        return campaign_mappings[url_path]

    # Check for prefix matches (fallback for URLs not in database)
    for mapped_url, campaign in campaign_mappings.items():
        if url_path.startswith(mapped_url):
            return campaign

    # Default fallback for property URLs
    if url_path.startswith('/properties/'):
        return "Jersey Property Listings"

    return "Unmapped"

def get_all_pages_with_sources():
    """Get all pages with their traffic sources for the past 30 days"""

    # Load campaign mappings and source unifications
    campaign_mappings, source_unifications = load_campaign_mappings()

    # Get date range for last 30 days
    start_date, end_date = get_last_30_days_range()

    print(f"📊 Generating comprehensive page-source report for {start_date} to {end_date}")
    print("=" * 80)
    print(f"📋 Loaded {len(campaign_mappings)} URL-to-campaign mappings")
    print(f"🔄 Loaded {len(source_unifications)} source unification rules")

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

        # Unify source names
        unified_source = unify_source_name(source_medium, source_unifications)

        # Get campaign for this URL
        campaign_name = get_campaign_for_url(page_path, campaign_mappings)

        if page_path not in page_data:
            page_data[page_path] = {
                'total_users': 0,
                'campaign': campaign_name,
                'sources': []
            }

        page_data[page_path]['sources'].append({
            'source_medium': unified_source,
            'original_source': source_medium,  # Keep original for reference
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
        campaign_name = data.get('campaign', 'Unmapped')
        grand_total_users += total_page_users

        print(f"\n🏠 PAGE {page_count}: {page_path}")
        print(f"   Campaign: {campaign_name}")
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
        campaign_name = data.get('campaign', 'Unmapped')
        for source in data['sources']:
            csv_data.append({
                'Date_Range': f"{start_date}_to_{end_date}",
                'Page_Path': page_path,
                'Campaign': campaign_name,
                'Source_Medium': source['source_medium'],
                'Original_Source': source.get('original_source', source['source_medium']),
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
            campaign_name = data.get('campaign', 'Unmapped')
            # Get top source for summary
            top_source = max(data['sources'], key=lambda x: x['users']) if data['sources'] else {'source_medium': 'None', 'users': 0}
            summary_data.append({
                'Date_Range': f"{start_date}_to_{end_date}",
                'Page_Path': page_path,
                'Campaign': campaign_name,
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