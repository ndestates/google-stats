"""
Hourly Traffic Analysis Script
Analyze traffic sources and performance by hour of day for a specific URL/page

Usage:
    python hourly_traffic_analysis.py [URL] [days]
    python hourly_traffic_analysis.py [URL] --start-date YYYY-MM-DD --end-date YYYY-MM-DD

Examples:
    python hourly_traffic_analysis.py /valuations
    python hourly_traffic_analysis.py https://www.ndestates.com/valuations 7
    python hourly_traffic_analysis.py /valuations 30
    python hourly_traffic_analysis.py /valuations --start-date 2025-11-01 --end-date 2025-11-19
"""

import os
#!/usr/bin/env python3
"""
Run with: ddev exec python scripts/hourly_traffic_analysis.py
"""

import os
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

def analyze_hourly_traffic(target_url: str, start_date: str = None, end_date: str = None, property_name: str = "", property_address: str = ""):
    """Analyze hourly traffic sources for a specific page URL"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    # Normalize the URL to page path
    page_path = normalize_page_path(target_url)

    print(f"🔍 Analyzing hourly traffic for page: {target_url}")
    print(f"   Normalized path: {page_path}")
    print(f"   Date range: {start_date} to {end_date}")
    print("=" * 80)

    # Get traffic data for all pages in date range, then filter for our target page
    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["pagePath", "hour", "sessionSourceMedium", "sessionCampaignName", "sessionDefaultChannelGrouping"],
        metrics=["totalUsers", "newUsers", "sessions", "engagedSessions", "screenPageViews", "averageSessionDuration", "bounceRate", "engagementRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=50000,  # Need more data for hourly breakdown
    )

    if response.row_count == 0:
        print(f"❌ No data found for the date range.")
        return None

    print(f"✅ Retrieved {response.row_count} total page-hour-source combinations")

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

    print(f"✅ Found {len(page_traffic_data)} hour-source combinations for page: {page_path}")

    # Process data by source/medium and hour
    source_hourly_data = {}
    organic_hourly_data = {}  # Track search organic traffic by hour
    social_organic_data = {
        'facebook': {},
        'instagram': {},
        'twitter': {},
        'linkedin': {},
        'buffer': {}
    }  # Track organic social traffic by platform and hour

    # Define organic source/medium combinations
    organic_sources = {
        'google / organic',
        'bing / organic',
        'yahoo / organic',
        'duckduckgo / organic',
        'yandex / organic'
    }

    # Define organic social source/medium combinations
    social_organic_sources = {
        'facebook': {
            'facebook.com / referral',
            'l.facebook.com / referral',
            'm.facebook.com / referral',
            'facebook / social'
        },
        'instagram': {
            'instagram.com / referral',
            'l.instagram.com / referral',
            'instagram.com / social'
        },
        'twitter': {
            'twitter.com / social',
            't.co / referral',
            'twitter.com / referral'
        },
        'linkedin': {
            'linkedin.com / social',
            'linkedin.com / referral',
            'lnkd.in / referral'
        },
        'buffer': {
            'buffer'
        }
    }

    for row in page_traffic_data:
        actual_page_path = row.dimension_values[0].value
        hour = int(row.dimension_values[1].value)
        source_medium = row.dimension_values[2].value
        campaign_name = row.dimension_values[3].value
        channel_grouping = row.dimension_values[4].value
        users = int(row.metric_values[0].value)
        new_users = int(row.metric_values[1].value)
        sessions = int(row.metric_values[2].value)
        engaged_sessions = int(row.metric_values[3].value)
        pageviews = int(row.metric_values[4].value)
        avg_session_duration = float(row.metric_values[5].value)
        bounce_rate = float(row.metric_values[6].value)
        engagement_rate = float(row.metric_values[7].value)

        # Track organic traffic separately
        if source_medium in organic_sources:
            if hour not in organic_hourly_data:
                organic_hourly_data[hour] = {
                    'users': 0,
                    'new_users': 0,
                    'sessions': 0,
                    'engaged_sessions': 0,
                    'pageviews': 0
                }
            organic_hourly_data[hour]['users'] += users
            organic_hourly_data[hour]['new_users'] += new_users
            organic_hourly_data[hour]['sessions'] += sessions
            organic_hourly_data[hour]['engaged_sessions'] += engaged_sessions
            organic_hourly_data[hour]['pageviews'] += pageviews

        # Track organic social traffic by platform
        for platform, sources in social_organic_sources.items():
            if source_medium in sources:
                if hour not in social_organic_data[platform]:
                    social_organic_data[platform][hour] = {
                        'users': 0,
                        'new_users': 0,
                        'sessions': 0,
                        'engaged_sessions': 0,
                        'pageviews': 0
                    }
                social_organic_data[platform][hour]['users'] += users
                social_organic_data[platform][hour]['new_users'] += new_users
                social_organic_data[platform][hour]['sessions'] += sessions
                social_organic_data[platform][hour]['engaged_sessions'] += engaged_sessions
                social_organic_data[platform][hour]['pageviews'] += pageviews

        if source_medium not in source_hourly_data:
            source_hourly_data[source_medium] = {
                'hourly_data': {},
                'total_users': 0,
                'total_new_users': 0,
                'total_sessions': 0,
                'total_engaged_sessions': 0,
                'total_pageviews': 0,
                'best_hour': None,
                'best_hour_users': 0,
                'channel_groupings': set(),
                'campaigns': set()
            }

        if hour not in source_hourly_data[source_medium]['hourly_data']:
            source_hourly_data[source_medium]['hourly_data'][hour] = {
                'users': 0,
                'new_users': 0,
                'sessions': 0,
                'engaged_sessions': 0,
                'pageviews': 0,
                'avg_session_duration': avg_session_duration,
                'bounce_rate': bounce_rate,
                'engagement_rate': engagement_rate,
                'channel_groupings': set(),
                'campaigns': set()
            }

        source_hourly_data[source_medium]['hourly_data'][hour]['users'] += users
        source_hourly_data[source_medium]['hourly_data'][hour]['new_users'] += new_users
        source_hourly_data[source_medium]['hourly_data'][hour]['sessions'] += sessions
        source_hourly_data[source_medium]['hourly_data'][hour]['engaged_sessions'] += engaged_sessions
        source_hourly_data[source_medium]['hourly_data'][hour]['pageviews'] += pageviews

        # Add channel grouping and campaign to hourly data
        if channel_grouping and channel_grouping != '(not set)':
            source_hourly_data[source_medium]['hourly_data'][hour]['channel_groupings'].add(channel_grouping)
        if campaign_name and campaign_name != '(not set)':
            source_hourly_data[source_medium]['hourly_data'][hour]['campaigns'].add(campaign_name)

        # Aggregate totals for source
        source_hourly_data[source_medium]['total_users'] += users
        source_hourly_data[source_medium]['total_new_users'] += new_users
        source_hourly_data[source_medium]['total_sessions'] += sessions
        source_hourly_data[source_medium]['total_engaged_sessions'] += engaged_sessions
        source_hourly_data[source_medium]['total_pageviews'] += pageviews

        # Add to source-level channel grouping and campaign sets
        if channel_grouping and channel_grouping != '(not set)':
            source_hourly_data[source_medium]['channel_groupings'].add(channel_grouping)
        if campaign_name and campaign_name != '(not set)':
            source_hourly_data[source_medium]['campaigns'].add(campaign_name)

        # Track best hour
        if users > source_hourly_data[source_medium]['best_hour_users']:
            source_hourly_data[source_medium]['best_hour'] = hour
            source_hourly_data[source_medium]['best_hour_users'] = users

    # Calculate weighted averages for each hour
    for source_medium, data in source_hourly_data.items():
        for hour, hour_data in data['hourly_data'].items():
            # For now, keep the metrics as is (they're already aggregated)
            pass

    # Sort sources by total users
    sorted_sources = sorted(source_hourly_data.items(), key=lambda x: x[1]['total_users'], reverse=True)

    # Display results
    print(f"\n📊 HOURLY TRAFFIC ANALYSIS FOR: {target_url}")
    print(f"   Page Path: {page_path}")
    print(f"   Date Range: {start_date} to {end_date}")
    print("=" * 120)

    total_page_users = 0
    total_page_new_users = 0
    total_page_sessions = 0
    total_page_engaged_sessions = 0
    total_page_pageviews = 0

    for i, (source_medium, data) in enumerate(sorted_sources, 1):
        print(f"\n{i}. Source/Medium: {source_medium}")
        print(f"   Total Users: {data['total_users']:,} (New: {data['total_new_users']:,})")
        print(f"   Total Sessions: {data['total_sessions']:,} (Engaged: {data['total_engaged_sessions']:,})")
        print(f"   Total Pageviews: {data['total_pageviews']:,}")
        print(f"   Best Hour: {data['best_hour']:02d}:00 ({data['best_hour_users']:,} users)" if data['best_hour'] is not None else f"   Best Hour: N/A (0 users)")

        # Show channel grouping information
        if data['channel_groupings']:
            top_channels = list(data['channel_groupings'])[:3]  # Show top 3 channels
            print(f"   Channel Groups: {', '.join(top_channels)}")

        # Show campaign information
        if data['campaigns']:
            top_campaigns = list(data['campaigns'])[:5]  # Show top 5 campaigns
            print(f"   Campaigns (that drove traffic to this page): {', '.join(top_campaigns)}")

        # Display hourly breakdown
        print("   Hourly Traffic:")
        print("   Hour | Users | New Users | Sessions | Engaged | Pageviews")
        print("   -----|-------|-----------|----------|----------|-----------")

        for hour in range(24):
            hour_data = data['hourly_data'].get(hour, {'users': 0, 'new_users': 0, 'sessions': 0, 'engaged_sessions': 0, 'pageviews': 0})
            print(f"   {hour:2d}:00 | {hour_data['users']:5,} | {hour_data['new_users']:9,} | {hour_data['sessions']:8,} | {hour_data['engaged_sessions']:8,} | {hour_data['pageviews']:9,}")

        total_page_users += data['total_users']
        total_page_new_users += data['total_new_users']
        total_page_sessions += data['total_sessions']
        total_page_engaged_sessions += data['total_engaged_sessions']
        total_page_pageviews += data['total_pageviews']

        # Limit display to top 25 sources (increased from 5)
        if i >= 25:
            remaining_sources = len(sorted_sources) - 25
            if remaining_sources > 0:
                remaining_users = sum(data['total_users'] for _, data in sorted_sources[25:])
                print(f"\n... and {remaining_sources} more sources with {remaining_users:,} total users")
            break

    print(f"\n{'='*120}")
    print("📈 PAGE SUMMARY:")
    print(f"   Total Users: {total_page_users:,} (New: {total_page_new_users:,})")
    print(f"   Total Sessions: {total_page_sessions:,} (Engaged: {total_page_engaged_sessions:,})")
    print(f"   Total Pageviews: {total_page_pageviews:,}")
    print(f"   Date Range: {start_date} to {end_date}")

    # Calculate and display organic traffic summary
    if organic_hourly_data:
        total_organic_users = sum(hour_data['users'] for hour_data in organic_hourly_data.values())
        total_organic_new_users = sum(hour_data['new_users'] for hour_data in organic_hourly_data.values())
        total_organic_sessions = sum(hour_data['sessions'] for hour_data in organic_hourly_data.values())

        # Find best hour for organic traffic
        best_organic_hour = max(organic_hourly_data.keys(), key=lambda h: organic_hourly_data[h]['users'])
        best_organic_users = organic_hourly_data[best_organic_hour]['users']

        print(f"\n{'='*120}")
        print("🌱 ORGANIC TRAFFIC SUMMARY:")
        print(f"   Total Organic Users: {total_organic_users:,} (New: {total_organic_new_users:,})")
        print(f"   Total Organic Sessions: {total_organic_sessions:,}")
        print(f"   Best Hour for Organic Traffic: {best_organic_hour:02d}:00 ({best_organic_users:,} users)")
        print(f"   Organic Traffic % of Total: {total_organic_users/total_page_users*100:.1f}%" if total_page_users > 0 else "   Organic Traffic % of Total: 0.0%")

    # Calculate and display social organic traffic summaries
    social_platforms = []
    for platform, hourly_data in social_organic_data.items():
        if hourly_data:
            total_users = sum(hour_data['users'] for hour_data in hourly_data.values())
            if total_users > 0:
                best_hour = max(hourly_data.keys(), key=lambda h: hourly_data[h]['users'])
                best_users = hourly_data[best_hour]['users']
                social_platforms.append((platform, total_users, best_hour, best_users))

    # Always print social media section for dashboard parsing
    print(f"\n{'='*120}")
    print("📱 SOCIAL ORGANIC TRAFFIC SUMMARY:")
    if social_platforms:
        print("   Best posting hours for each platform (organic reach):")
        for platform, total_users, best_hour, best_users in sorted(social_platforms, key=lambda x: x[1], reverse=True):
            platform_name = platform.title()
            print(f"   {platform_name}: {best_hour:02d}:00 ({best_users:,} users) - Total: {total_users:,} users")
    else:
        print("   No organic social media traffic detected in the selected time period.")

    # Export detailed data to CSV
    csv_data = []
    for source_medium, data in sorted_sources:
        for hour in range(24):
            hour_data = data['hourly_data'].get(hour, {'users': 0, 'new_users': 0, 'sessions': 0, 'engaged_sessions': 0, 'pageviews': 0, 'avg_session_duration': 0, 'bounce_rate': 0, 'engagement_rate': 0, 'channel_groupings': set(), 'campaigns': set()})
            csv_data.append({
                'Page_URL': target_url,
                'Page_Path': page_path,
                'Date_Range': f"{start_date}_to_{end_date}",
                'Source_Medium': source_medium,
                'Hour': hour,
                'Users': hour_data['users'],
                'New_Users': hour_data['new_users'],
                'Sessions': hour_data['sessions'],
                'Engaged_Sessions': hour_data['engaged_sessions'],
                'Pageviews': hour_data['pageviews'],
                'Avg_Session_Duration': hour_data['avg_session_duration'],
                'Bounce_Rate': hour_data['bounce_rate'],
                'Engagement_Rate': hour_data['engagement_rate'],
                'Channel_Groupings': '; '.join(hour_data['channel_groupings']) if hour_data['channel_groupings'] else '',
                'Campaigns': '; '.join(hour_data['campaigns']) if hour_data['campaigns'] else '',
                'Source_Total_Users': data['total_users'],
                'Source_Total_New_Users': data['total_new_users'],
                'Source_Channel_Groupings': '; '.join(data['channel_groupings']) if data['channel_groupings'] else '',
                'Source_Campaigns': '; '.join(data['campaigns']) if data['campaigns'] else '',
                'Best_Hour': data['best_hour'],
                'Best_Hour_Users': data['best_hour_users']
            })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename("hourly_traffic_analysis", f"{page_path.replace('/', '_').strip('_')}_{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed data exported to: {csv_filename}")

    return source_hourly_data

if __name__ == "__main__":
    print("🔍 Hourly Traffic Analysis Tool")
    print("=" * 40)

    # Check for command line arguments
    if len(sys.argv) >= 2:
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
                analyze_hourly_traffic(target_url, start_date, end_date, property_name, property_address)
            elif days == 7:
                # Calculate 7-day range
                end_date = datetime.now() - timedelta(days=1)
                start_date = end_date - timedelta(days=6)
                analyze_hourly_traffic(target_url, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), property_name, property_address)
            else:
                # Default to 30 days or custom days
                end_date = datetime.now() - timedelta(days=1)
                start_date = end_date - timedelta(days=days-1)
                analyze_hourly_traffic(target_url, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), property_name, property_address)

    else:
        # Interactive mode
        print("Analyze hourly traffic sources for any specific page URL")
        print()
        print("💡 Tip: You can also run non-interactively:")
        print("   python hourly_traffic_analysis.py /valuations")
        print("   python hourly_traffic_analysis.py https://www.ndestates.com/valuations 7")
        print("   python hourly_traffic_analysis.py /valuations 90")
        print()

        # Check if running in interactive terminal
        if not sys.stdin.isatty():
            print("❌ This script requires command line arguments when run non-interactively.")
            print("   Usage: python hourly_traffic_analysis.py <url> [days]")
            print("   Example: python hourly_traffic_analysis.py /valuations 30")
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
            analyze_hourly_traffic(target_url, property_name="", property_address="")
        elif choice == "2":
            # Calculate 7-day range
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
            analyze_hourly_traffic(target_url, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), "", "")
        elif choice == "3":
            # Calculate 90-day range
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=89)
            analyze_hourly_traffic(target_url, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), "", "")
        elif choice == "4":
            start_date = input("Enter start date (YYYY-MM-DD): ").strip()
            end_date = input("Enter end date (YYYY-MM-DD): ").strip()
            if start_date and end_date:
                analyze_hourly_traffic(target_url, start_date, end_date, "", "")
            else:
                print("Invalid dates provided. Using last 30 days.")
                analyze_hourly_traffic(target_url, property_name="", property_address="")
        else:
            print("Invalid choice. Analyzing last 30 days by default.")
            analyze_hourly_traffic(target_url, property_name="", property_address="")