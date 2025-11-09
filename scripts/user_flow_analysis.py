"""
User Flow Analysis Script
Analyze user navigation patterns and site flow

Usage:
    python user_flow_analysis.py [start_page] [max_steps] [days]

Examples:
    python user_flow_analysis.py / 5 30
    python user_flow_analysis.py /valuations 3 7
    python user_flow_analysis.py /properties 4 90
"""

import os
import sys
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

def analyze_user_flow(start_page: str = "/", max_steps: int = 5, start_date: str = None, end_date: str = None):
    """Analyze user navigation flows starting from a specific page"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print(f"🔍 Analyzing user flows starting from: {start_page}")
    print(f"   Maximum steps: {max_steps}")
    print(f"   Date range: {start_date} to {end_date}")
    print("=" * 120)

    date_range = create_date_range(start_date, end_date)

    # Get page path sequences (user journeys)
    # Note: GA4 has limitations on path analysis, so we'll use landing/exit page analysis
    # and pageview sequences where available

    # Get top user flow sequences (simplified approach)
    flow_response = run_report(
        dimensions=["landingPage", "pagePath", "sessionDefaultChannelGrouping"],
        metrics=["sessions", "totalUsers", "screenPageViews", "averageSessionDuration"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=100
    )

    if flow_response.row_count == 0:
        print("❌ No user flow data found for the date range.")
        return None

    print(f"✅ Retrieved {flow_response.row_count} page flow combinations")

    # Analyze flows starting from the specified page
    flow_data = {}
    total_sessions = 0
    total_users = 0

    for row in flow_response.rows:
        landing_page = row.dimension_values[0].value
        current_page = row.dimension_values[1].value
        channel = row.dimension_values[2].value
        sessions = int(row.metric_values[0].value)
        users = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)

        # Only include flows that start with our target page
        if landing_page == start_page:
            if current_page not in flow_data:
                flow_data[current_page] = {
                    'sessions': 0,
                    'users': 0,
                    'pageviews': 0,
                    'avg_duration': 0,
                    'channels': {}
                }

            flow_data[current_page]['sessions'] += sessions
            flow_data[current_page]['users'] += users
            flow_data[current_page]['pageviews'] += pageviews
            flow_data[current_page]['avg_duration'] = avg_duration

            if channel not in flow_data[current_page]['channels']:
                flow_data[current_page]['channels'][channel] = 0
            flow_data[current_page]['channels'][channel] += sessions

            total_sessions += sessions
            total_users += users

    if not flow_data:
        print(f"❌ No user flows found starting from page: {start_page}")
        print("💡 This could mean:")
        print("   - The page doesn't receive traffic as a landing page")
        print("   - The page path format might be incorrect")
        print(f"   Expected path: {start_page}")
        return None

    # Sort flows by session volume
    sorted_flows = sorted(flow_data.items(), key=lambda x: x[1]['sessions'], reverse=True)

    print("\n🌊 USER FLOW ANALYSIS:")
    print(f"   Starting Page: {start_page}")
    print(f"   Total Sessions: {total_sessions:,}")
    print(f"   Total Users: {total_users:,}")
    print(f"   Unique Pages in Flow: {len(sorted_flows)}")
    print()

    print("   TOP PAGES IN USER FLOW:"    print("   Page Path                    | Sessions | Users | Pageviews | Avg Duration | Top Channel")
    print("   -----------------------------|----------|-------|-----------|--------------|-------------")

    for page_path, data in sorted_flows[:20]:  # Show top 20
        path_display = page_path[:28] + "..." if len(page_path) > 28 else page_path
        top_channel = max(data['channels'].items(), key=lambda x: x[1])[0] if data['channels'] else 'N/A'

        print("28")
    print()

    # Analyze flow depth and engagement
    single_page_sessions = sum(data['sessions'] for page, data in sorted_flows if page == start_page)
    multi_page_sessions = total_sessions - single_page_sessions

    print("📊 FLOW ENGAGEMENT ANALYSIS:"    print(f"   Single Page Sessions: {single_page_sessions:,} ({single_page_sessions/total_sessions*100:.1f}%)")
    print(f"   Multi-Page Sessions: {multi_page_sessions:,} ({multi_page_sessions/total_sessions*100:.1f}%)")
    print(f"   Average Pages per Session: {sum(data['pageviews'] for data in flow_data.values()) / total_sessions:.1f}")
    print()

    # Channel distribution in flows
    channel_totals = {}
    for page_data in flow_data.values():
        for channel, sessions in page_data['channels'].items():
            channel_totals[channel] = channel_totals.get(channel, 0) + sessions

    print("📈 CHANNEL DISTRIBUTION IN FLOWS:"    print("   Channel              | Sessions | Percentage")
    print("   ---------------------|----------|-----------")

    for channel, sessions in sorted(channel_totals.items(), key=lambda x: x[1], reverse=True):
        percentage = sessions / total_sessions * 100
        print("21")
    print()

    # Flow recommendations
    print("💡 FLOW OPTIMIZATION RECOMMENDATIONS:"    if single_page_sessions / total_sessions > 0.7:  # Over 70% single page
        print("   • High bounce rate detected - users aren't exploring further")
        print("   • Add prominent internal links and related content suggestions")
        print("   • Consider improving page content to encourage deeper navigation")
    elif multi_page_sessions / total_sessions > 0.8:  # Over 80% multi-page
        print("   • Good engagement - users are exploring multiple pages")
        print("   • Focus on conversion optimization for engaged users")
        print("   • Consider adding cross-sell or related content recommendations")

    # Popular transition patterns
    print("
🔄 POPULAR PAGE TRANSITIONS:"    # This is a simplified analysis - in a real implementation,
    # you'd want to use GA4's path exploration or custom event tracking
    print("   💡 For detailed path analysis, consider:")
    print("      • Setting up custom events for page transitions")
    print("      • Using GA4's path exploration features")
    print("      • Implementing journey tracking with UTM parameters")
    print()

    # Export detailed flow data
    csv_data = []
    for page_path, data in sorted_flows:
        for channel, channel_sessions in data['channels'].items():
            csv_data.append({
                'Start_Page': start_page,
                'Flow_Page': page_path,
                'Channel': channel,
                'Sessions': channel_sessions,
                'Users': data['users'],
                'Pageviews': data['pageviews'],
                'Avg_Duration': data['avg_duration'],
                'Session_Percentage': channel_sessions / total_sessions * 100,
                'Date_Range': f"{start_date}_to_{end_date}"
            })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename("user_flow_analysis", f"{start_page.replace('/', '_').strip('_')}_{max_steps}steps_{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"📄 Detailed flow data exported to: {csv_filename}")

    return {
        'start_page': start_page,
        'total_sessions': total_sessions,
        'total_users': total_users,
        'flow_data': flow_data,
        'single_page_rate': single_page_sessions / total_sessions if total_sessions > 0 else 0,
        'channel_distribution': channel_totals
    }

if __name__ == "__main__":
    print("🌊 User Flow Analysis Tool")
    print("=" * 40)

    if len(sys.argv) >= 2:
        start_page = sys.argv[1]
        max_steps = int(sys.argv[2]) if len(sys.argv) >= 3 else 5
        days = int(sys.argv[3]) if len(sys.argv) >= 4 else 30

        print(f"Analyzing flows from page: {start_page}")
        print(f"Maximum steps: {max_steps}")
        print(f"Time period: Last {days} days")

        if days == 7:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
            analyze_user_flow(start_page, max_steps, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        else:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=days-1)
            analyze_user_flow(start_page, max_steps, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    else:
        print("Analyze user navigation flows and site engagement patterns")
        print()
        print("Parameters:")
        print("  start_page  - Page to start flow analysis from (e.g., /)")
        print("  max_steps   - Maximum steps to analyze (default: 5)")
        print("  days        - Number of days to analyze (default: 30)")
        print()
        print("Usage: python user_flow_analysis.py <start_page> [max_steps] [days]")
        print("Example: python user_flow_analysis.py / 5 30")
        exit(1)