"""
Page Traffic Analysis Script
Analyze traffic sources and performance for a specific URL/page

Run with: ddev exec python scripts/page_traffic_analysis.py [URL] [days]
          ddev exec python scripts/page_traffic_analysis.py [URL] --start-date YYYY-MM-DD --end-date YYYY-MM-DD

Examples:
    ddev exec python scripts/page_traffic_analysis.py /valuations
    ddev exec python scripts/page_traffic_analysis.py /valuations 30
    ddev exec python scripts/page_traffic_analysis.py /valuations --start-date 2025-11-01 --end-date 2025-11-19
"""

import os
#!/usr/bin/env python3
"""
Run with: ddev exec python scripts/page_traffic_analysis.py
"""

import os
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta.types import OrderBy

from src.config import REPORTS_DIR
from src.ga4_client import run_report, create_date_range, get_report_filename
from src.pdf_generator import create_campaign_report_pdf

def get_last_30_days_range():
    """Get date range for the last 30 days"""
    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=29)  # 30 days back
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def normalize_page_path(url_or_path):
    """Convert URL to page path format for GA4"""
    # Strip surrounding quotes if present
    url_or_path = url_or_path.strip('"').strip("'")

    # Remove protocol and domain if present
    if url_or_path.startswith('http://') or url_or_path.startswith('https://'):
        # Extract path from URL
        from urllib.parse import urlparse
        parsed = urlparse(url_or_path)
        page_path = parsed.path
        if parsed.query:
            page_path += '?' + parsed.query
        if parsed.fragment:
            page_path += '#' + parsed.fragment
    else:
        page_path = url_or_path

    # Ensure it starts with /
    if not page_path.startswith('/'):
        page_path = '/' + page_path

    return page_path

def analyze_page_traffic(target_url: str, start_date: str = None, end_date: str = None, property_name: str = "", property_address: str = ""):
    """Analyze traffic sources for a specific page URL"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    # Normalize the URL to page path
    page_path = normalize_page_path(target_url)

    print(f"🔍 Analyzing traffic for page: {target_url}")
    print(f"   Normalized path: {page_path}")
    print(f"   Date range: {start_date} to {end_date}")
    print("=" * 80)

    # Get traffic data for all pages in date range, then filter for our target page
    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["pagePath", "sessionSourceMedium", "sessionCampaignName"],
        metrics=["totalUsers", "sessions", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=10000,  # Get more data to ensure we capture our page
    )

    if response.row_count == 0:
        print(f"❌ No data found for the date range.")
        return None

    print(f"✅ Retrieved {response.row_count} total page-source combinations")

    # Filter results for our specific page
    page_traffic_data = []
    for row in response.rows:
        actual_page_path = row.dimension_values[0].value
        if actual_page_path == page_path:
            page_traffic_data.append(row)

    if not page_traffic_data:
        print(f"❌ No data found for page: {page_path}")
        print("💡 This could mean:")
        print("   - The page hasn't received traffic in the date range")
        print("   - The URL format might be incorrect")
        print("   - The page path doesn't match GA4 tracking")
        print(f"   Expected path: {page_path}")
        return None

    print(f"✅ Found {len(page_traffic_data)} traffic sources for page: {page_path}")

    # Process data by source/medium
    source_data = {}

    for row in page_traffic_data:
        actual_page_path = row.dimension_values[0].value
        source_medium = row.dimension_values[1].value
        campaign_name = row.dimension_values[2].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_session_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)

        if source_medium not in source_data:
            source_data[source_medium] = {
                'campaigns': {},
                'total_users': 0,
                'total_sessions': 0,
                'total_pageviews': 0,
                'avg_session_duration': 0,
                'bounce_rate': 0
            }

        # Track campaign data
        if campaign_name not in source_data[source_medium]['campaigns']:
            source_data[source_medium]['campaigns'][campaign_name] = {
                'users': 0,
                'sessions': 0,
                'pageviews': 0,
                'avg_session_duration': avg_session_duration,
                'bounce_rate': bounce_rate
            }

        source_data[source_medium]['campaigns'][campaign_name]['users'] += users
        source_data[source_medium]['campaigns'][campaign_name]['sessions'] += sessions
        source_data[source_medium]['campaigns'][campaign_name]['pageviews'] += pageviews

        # Aggregate totals for source
        source_data[source_medium]['total_users'] += users
        source_data[source_medium]['total_sessions'] += sessions
        source_data[source_medium]['total_pageviews'] += pageviews

    # Calculate weighted averages for source
    for source_medium, data in source_data.items():
        if data['total_sessions'] > 0:
            # Weighted average for session duration and bounce rate
            total_weighted_duration = 0
            total_weighted_bounce = 0

            for campaign_data in data['campaigns'].values():
                weight = campaign_data['sessions'] / data['total_sessions']
                total_weighted_duration += campaign_data['avg_session_duration'] * weight
                total_weighted_bounce += campaign_data['bounce_rate'] * weight

            data['avg_session_duration'] = total_weighted_duration
            data['bounce_rate'] = total_weighted_bounce

    # Sort sources by total users
    sorted_sources = sorted(source_data.items(), key=lambda x: x[1]['total_users'], reverse=True)

    # Display results
    print(f"\n📊 TRAFFIC ANALYSIS FOR: {target_url}")
    print(f"   Page Path: {page_path}")
    print(f"   Date Range: {start_date} to {end_date}")
    print("=" * 100)

    total_page_users = 0
    total_page_sessions = 0
    total_page_pageviews = 0

    for i, (source_medium, data) in enumerate(sorted_sources, 1):
        print(f"\n{i}. Source/Medium: {source_medium}")
        print(f"   Total Users: {data['total_users']:,}")
        print(f"   Total Sessions: {data['total_sessions']:,}")
        print(f"   Total Pageviews: {data['total_pageviews']:,}")
        print(f"   Avg Session Duration: {data['avg_session_duration']:.1f} seconds")
        print(f"   Bounce Rate: {data['bounce_rate']:.1%}")

        # Show campaign breakdown if there are multiple campaigns
        campaigns = data['campaigns']
        if len(campaigns) > 1:
            print("   Campaigns (that drove traffic to this page):")
            sorted_campaigns = sorted(campaigns.items(), key=lambda x: x[1]['users'], reverse=True)
            for campaign_name, campaign_data in sorted_campaigns[:5]:  # Show top 5
                campaign_name_display = campaign_name if campaign_name != '(not set)' else 'Direct/None'
                print(f"     • {campaign_name_display}: {campaign_data['users']:,} users")

        total_page_users += data['total_users']
        total_page_sessions += data['total_sessions']
        total_page_pageviews += data['total_pageviews']

        # Limit display to top 25 sources (increased from 10)
        if i >= 25:
            remaining_sources = len(sorted_sources) - 25
            if remaining_sources > 0:
                remaining_users = sum(data['total_users'] for _, data in sorted_sources[25:])
                print(f"\n... and {remaining_sources} more sources with {remaining_users:,} total users")
            break

    print(f"\n{'='*100}")
    print("📈 PAGE SUMMARY:")
    print(f"   Total Users: {total_page_users:,}")
    print(f"   Total Sessions: {total_page_sessions:,}")
    print(f"   Total Pageviews: {total_page_pageviews:,}")
    print(f"   Date Range: {start_date} to {end_date}")

    # Export detailed data to CSV
    csv_data = []
    for source_medium, data in sorted_sources:
        for campaign_name, campaign_data in data['campaigns'].items():
            csv_data.append({
                'Page_URL': target_url,
                'Page_Path': page_path,
                'Date_Range': f"{start_date}_to_{end_date}",
                'Source_Medium': source_medium,
                'Campaign_Name': campaign_name,
                'Users': campaign_data['users'],
                'Sessions': campaign_data['sessions'],
                'Pageviews': campaign_data['pageviews'],
                'Avg_Session_Duration': campaign_data['avg_session_duration'],
                'Bounce_Rate': campaign_data['bounce_rate'],
                'Source_Total_Users': data['total_users']
            })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename("page_traffic_analysis", f"{page_path.replace('/', '_').strip('_')}_{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed data exported to: {csv_filename}")

        # Generate PDF report (reuse campaign PDF generator)
        # Temporarily set property info for PDF generation
        import src.config
        original_property_name = src.config.PROPERTY_NAME
        original_property_address = src.config.PROPERTY_ADDRESS
        
        if property_name:
            src.config.PROPERTY_NAME = property_name
        if property_address:
            src.config.PROPERTY_ADDRESS = property_address
            
        # Restructure data for PDF generator (expects campaign-centric structure)
        pdf_campaign_data = {}
        for source_medium, source_info in source_data.items():
            for campaign_name, campaign_info in source_info['campaigns'].items():
                # Create a unique key combining campaign and source
                campaign_key = f"{campaign_name} ({source_medium})" if campaign_name != '(not set)' else f"Direct ({source_medium})"
                pdf_campaign_data[campaign_key] = {
                    'source_medium': source_medium,
                    'total_users': campaign_info['users'],
                    'total_sessions': campaign_info['sessions'], 
                    'total_pageviews': campaign_info['pageviews'],
                    'pages': {}  # Empty pages dict for compatibility
                }
        
        # Sanitize page_path for filename (replace slashes with underscores)
        safe_page_path = page_path.replace('/', '_').replace('\\', '_')

        pdf_filename = create_campaign_report_pdf(pdf_campaign_data, f"{safe_page_path}_{start_date}_to_{end_date}", total_page_users, len(pdf_campaign_data))
        print(f"📄 PDF report exported to: {pdf_filename}")
        
        # Restore original values
        src.config.PROPERTY_NAME = original_property_name
        src.config.PROPERTY_ADDRESS = original_property_address

    return source_data

if __name__ == "__main__":
    print("🔍 Page Traffic Analysis Tool")
    print("=" * 40)

    # Parse command line arguments
    property_name = ""
    property_address = ""
    start_date = None
    end_date = None
    
    # Check for property arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--property-name' and i + 1 < len(args):
            property_name = args[i + 1]
            args.pop(i)  # Remove the flag
            args.pop(i)  # Remove the value
            continue
        elif args[i] == '--property-address' and i + 1 < len(args):
            property_address = args[i + 1]
            args.pop(i)  # Remove the flag
            args.pop(i)  # Remove the value
            continue
        elif args[i] == '--start-date' and i + 1 < len(args):
            start_date = args[i + 1]
            args.pop(i)  # Remove the flag
            args.pop(i)  # Remove the value
            continue
        elif args[i] == '--end-date' and i + 1 < len(args):
            end_date = args[i + 1]
            args.pop(i)  # Remove the flag
            args.pop(i)  # Remove the value
            continue
        i += 1

    # Check for remaining arguments
    if len(args) >= 1:
        # Command line mode
        target_url = args[0]
        days = int(args[1]) if len(args) >= 2 and not start_date else 30

        print(f"Analyzing URL: {target_url}")
        if start_date and end_date:
            print(f"Date range: {start_date} to {end_date}")
        else:
            print(f"Time period: Last {days} days")
        if property_name:
            print(f"Property Name: {property_name}")
        if property_address:
            print(f"Property Address: {property_address}")

        if start_date and end_date:
            analyze_page_traffic(target_url, start_date, end_date, property_name, property_address)
        elif days == 7:
            # Calculate 7-day range
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
            analyze_page_traffic(target_url, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), property_name, property_address)
        else:
            # Default to 30 days or custom days
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=days-1)
            analyze_page_traffic(target_url, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), property_name, property_address)

    else:
        # Interactive mode
        print("Analyze traffic sources for any specific page URL")
        print()
        print("💡 Tip: You can also run non-interactively:")
        print("   python page_traffic_analysis.py /valuations")
        print("   python page_traffic_analysis.py https://www.ndestates.com/valuations 7")
        print("   python page_traffic_analysis.py /valuations 90")
        print()

        # Check if running in interactive terminal
        if not sys.stdin.isatty():
            print("❌ This script requires command line arguments when run non-interactively.")
            print("   Usage: python page_traffic_analysis.py <url> [days]")
            print("   Example: python page_traffic_analysis.py /valuations 30")
            exit(1)

        # Get URL from user
        target_url = input("Enter the page URL to analyze: ").strip()

        if not target_url:
            print("❌ No URL provided. Exiting.")
            exit(1)

        print("\nChoose time period:")
        print("1. Last 30 days")
        print("2. Last 7 days")
        print("3. Last 90 days")
        print("4. Custom date range")

        choice = input("Enter choice (1, 2, 3, or 4): ").strip()

        if choice == "1":
            analyze_page_traffic(target_url, property_name=property_name, property_address=property_address)
        elif choice == "2":
            # Calculate 7-day range
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
            analyze_page_traffic(target_url, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), property_name, property_address)
        elif choice == "3":
            # Calculate 90-day range
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=89)
            analyze_page_traffic(target_url, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), property_name, property_address)
        elif choice == "4":
            start_date = input("Enter start date (YYYY-MM-DD): ").strip()
            end_date = input("Enter end date (YYYY-MM-DD): ").strip()
            if start_date and end_date:
                analyze_page_traffic(target_url, start_date, end_date, property_name, property_address)
            else:
                print("Invalid dates provided. Using last 30 days.")
                analyze_page_traffic(target_url, property_name=property_name, property_address=property_address)
        else:
            print("Invalid choice. Analyzing last 30 days by default.")
            analyze_page_traffic(target_url, property_name=property_name, property_address=property_address)