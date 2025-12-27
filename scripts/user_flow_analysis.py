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
#!/usr/bin/env python3
"""
Run with: ddev exec python scripts/user_flow_analysis.py
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

def analyze_user_flow(start_page: str = "/", max_steps: int = 5, start_date: str = None, end_date: str = None):
    """Analyze user navigation flows starting from a specific page"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print(f"🔍 Analyzing user flows starting from: {start_page}")
    print(f"   Maximum steps: {max_steps}")
    print(f"   Date range: {start_date} to {end_date}")
    print("=" * 120)

    date_range = create_date_range(start_date, end_date)

def analyze_user_behavior(start_date: str = None, end_date: str = None, min_sessions: int = 100):
    """Analyze overall user behavior and page interactions"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print(f"🔍 Analyzing user behavior patterns")
    print(f"   Date range: {start_date} to {end_date}")
    print(f"   Minimum sessions threshold: {min_sessions}")
    print("=" * 120)

    date_range = create_date_range(start_date, end_date)

    # Get page performance data
    page_response = run_report(
        dimensions=["pagePath"],
        metrics=["sessions", "totalUsers", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=50
    )

    if page_response.row_count == 0:
        print("❌ No page data found for the date range.")
        return None

    print(f"✅ Retrieved {page_response.row_count} page performance records")

    # Analyze page performance
    page_data = {}
    total_sessions = 0
    total_users = 0

    for row in page_response.rows:
        page_path = row.dimension_values[0].value
        sessions = int(row.metric_values[0].value)
        users = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)

        if sessions >= min_sessions:  # Filter out low-traffic pages
            page_data[page_path] = {
                'sessions': sessions,
                'users': users,
                'pageviews': pageviews,
                'avg_duration': avg_duration,
                'bounce_rate': bounce_rate,
                'pages_per_session': pageviews / sessions if sessions > 0 else 0
            }

            total_sessions += sessions
            total_users += users

    if not page_data:
        print(f"❌ No pages found with at least {min_sessions} sessions")
        return None

    # Sort pages by session volume
    sorted_pages = sorted(page_data.items(), key=lambda x: x[1]['sessions'], reverse=True)

    print("\n📊 USER BEHAVIOR ANALYSIS:")
    print(f"   Total Sessions: {total_sessions:,}")
    print(f"   Total Users: {total_users:,}")
    print(f"   Pages Analyzed: {len(sorted_pages)}")
    print()

    print("   TOP PAGES BY TRAFFIC:")
    print("   Page Path                              | Sessions | Users | Pageviews | Avg Duration | Bounce Rate | Pages/Session")
    print("   ---------------------------------------|----------|-------|-----------|--------------|-------------|--------------")

    for page_path, data in sorted_pages[:15]:  # Show top 15
        path_display = page_path[:39] + "..." if len(page_path) > 39 else page_path
        print(f"   {path_display:<39} | {data['sessions']:>8,} | {data['users']:>5,} | {data['pageviews']:>9,} | {data['avg_duration']:>12.1f} | {data['bounce_rate']*100:>10.1f}% | {data['pages_per_session']:>12.1f}")

    print()

    # Analyze engagement patterns
    high_engagement_pages = [(p, d) for p, d in sorted_pages if d['bounce_rate'] < 0.3]
    low_engagement_pages = [(p, d) for p, d in sorted_pages if d['bounce_rate'] > 0.7]

    print("🎯 ENGAGEMENT ANALYSIS:")
    print(f"   High Engagement Pages (Bounce < 30%): {len(high_engagement_pages)}")
    print(f"   Low Engagement Pages (Bounce > 70%): {len(low_engagement_pages)}")
    print()

    if high_engagement_pages:
        print("   🟢 HIGH ENGAGEMENT PAGES:")
        for page_path, data in high_engagement_pages[:5]:
            print(f"      {page_path}: {data['bounce_rate']*100:.1f}% bounce, {data['avg_duration']:.1f}s avg duration")
    if low_engagement_pages:
        print("   🔴 LOW ENGAGEMENT PAGES:")
        for page_path, data in low_engagement_pages[:5]:
            print(f"      {page_path}: {data['bounce_rate']*100:.1f}% bounce, {data['avg_duration']:.1f}s avg duration")
    print()

    # Time-based analysis
    hourly_response = run_report(
        dimensions=["hour"],
        metrics=["sessions", "totalUsers"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="hour"))
        ]
    )

    if hourly_response.row_count > 0:
        print("🕐 HOURLY TRAFFIC PATTERNS:")
        print("   Hour | Sessions | Users")
        print("   -----|----------|------")

        for row in hourly_response.rows:
            hour = int(row.dimension_values[0].value)
            sessions = int(row.metric_values[0].value)
            users = int(row.metric_values[1].value)
            print(f"   {hour:>3} | {sessions:>8,} | {users:>5,}")

    print()

    # Export detailed page data
    csv_data = []
    for page_path, data in sorted_pages:
        csv_data.append({
            'Page_Path': page_path,
            'Sessions': data['sessions'],
            'Users': data['users'],
            'Pageviews': data['pageviews'],
            'Avg_Duration': data['avg_duration'],
            'Bounce_Rate': data['bounce_rate'],
            'Pages_Per_Session': data['pages_per_session'],
            'Date_Range': f"{start_date}_to_{end_date}"
        })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename("user_behavior_analysis", f"{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"📄 Detailed behavior data exported to: {csv_filename}")

    return {
        'page_data': page_data,
        'total_sessions': total_sessions,
        'total_users': total_users,
        'high_engagement_pages': len(high_engagement_pages),
        'low_engagement_pages': len(low_engagement_pages)
    }

def analyze_property_pages(start_date: str = None, end_date: str = None, min_sessions: int = 50):
    """Analyze user behavior specifically for property-related pages"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print(f"🏠 Analyzing property page user behavior")
    print(f"   Date range: {start_date} to {end_date}")
    print(f"   Minimum sessions threshold: {min_sessions}")
    print("=" * 120)

    date_range = create_date_range(start_date, end_date)

    # Get all page performance data
    page_response = run_report(
        dimensions=["pagePath"],
        metrics=["sessions", "totalUsers", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=100
    )

    if page_response.row_count == 0:
        print("❌ No page data found for the date range.")
        return None

    print(f"✅ Retrieved {page_response.row_count} page performance records")

    # Separate property pages from other pages
    property_pages = {}
    other_pages = {}
    total_property_sessions = 0
    total_property_users = 0
    total_other_sessions = 0
    total_other_users = 0

    for row in page_response.rows:
        page_path = row.dimension_values[0].value
        sessions = int(row.metric_values[0].value)
        users = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)

        page_data = {
            'sessions': sessions,
            'users': users,
            'pageviews': pageviews,
            'avg_duration': avg_duration,
            'bounce_rate': bounce_rate,
            'pages_per_session': pageviews / sessions if sessions > 0 else 0
        }

        if page_path.startswith('/properties/') and sessions >= min_sessions:
            property_pages[page_path] = page_data
            total_property_sessions += sessions
            total_property_users += users
        elif sessions >= min_sessions:
            other_pages[page_path] = page_data
            total_other_sessions += sessions
            total_other_users += users

    if not property_pages:
        print(f"❌ No property pages found with at least {min_sessions} sessions")
        return None

    # Sort property pages by session volume
    sorted_property_pages = sorted(property_pages.items(), key=lambda x: x[1]['sessions'], reverse=True)

    print(f"\n🏠 PROPERTY PAGES ANALYSIS:")
    print(f"   Property Pages Found: {len(sorted_property_pages)}")
    print(f"   Total Property Sessions: {total_property_sessions:,}")
    print(f"   Total Property Users: {total_property_users:,}")
    print(f"   Other Pages Sessions: {total_other_sessions:,}")
    print(f"   Property Traffic Share: {total_property_sessions / (total_property_sessions + total_other_sessions) * 100:.1f}%")
    print()

    print("   TOP PROPERTY PAGES BY TRAFFIC:")
    print("   Property Page                          | Sessions | Users | Pageviews | Avg Duration | Bounce Rate")
    print("   ---------------------------------------|----------|-------|-----------|--------------|-------------")

    for page_path, data in sorted_property_pages[:10]:  # Show top 10
        # Extract property name from path
        property_name = page_path.replace('/properties/', '').replace('-', ' ').title()
        if len(property_name) > 39:
            property_name = property_name[:36] + "..."

        print(f"   {property_name:<39} | {data['sessions']:>8,} | {data['users']:>5,} | {data['pageviews']:>9,} | {data['avg_duration']:>12.1f} | {data['bounce_rate']*100:>10.1f}%")

    print()

    # Analyze property page engagement
    high_engagement_props = [(p, d) for p, d in sorted_property_pages if d['bounce_rate'] < 0.4]
    low_engagement_props = [(p, d) for p, d in sorted_property_pages if d['bounce_rate'] > 0.7]

    print("🎯 PROPERTY ENGAGEMENT ANALYSIS:")
    print(f"   High Engagement Properties (Bounce < 40%): {len(high_engagement_props)}")
    print(f"   Low Engagement Properties (Bounce > 70%): {len(low_engagement_props)}")
    print(f"   Average Bounce Rate: {sum(d['bounce_rate'] for d in property_pages.values()) / len(property_pages) * 100:.1f}%")
    print(f"   Average Session Duration: {sum(d['avg_duration'] for d in property_pages.values()) / len(property_pages):.1f} seconds")
    print()

    # Property type analysis
    property_types = {}
    for page_path, data in property_pages.items():
        # Extract location/bedroom info from path
        path_parts = page_path.lower().split('/')
        if len(path_parts) > 2:
            property_info = path_parts[2]
            # Categorize by location
            if 'st-helier' in property_info:
                prop_type = 'St Helier'
            elif 'st-saviour' in property_info:
                prop_type = 'St Saviour'
            elif 'st-peter' in property_info:
                prop_type = 'St Peter'
            elif 'st-lawrence' in property_info:
                prop_type = 'St Lawrence'
            elif 'st-john' in property_info:
                prop_type = 'St John'
            else:
                prop_type = 'Other'

            if prop_type not in property_types:
                property_types[prop_type] = {'sessions': 0, 'users': 0, 'pages': 0}
            property_types[prop_type]['sessions'] += data['sessions']
            property_types[prop_type]['users'] += data['users']
            property_types[prop_type]['pages'] += 1

    if property_types:
        print("📍 PROPERTY LOCATION ANALYSIS:")
        print("   Location    | Properties | Sessions | Users | Avg Sessions/Property")
        print("   ------------|------------|----------|-------|---------------------")

        for location, data in sorted(property_types.items(), key=lambda x: x[1]['sessions'], reverse=True):
            avg_sessions = data['sessions'] / data['pages']
            print(f"   {location:<12} | {data['pages']:>10} | {data['sessions']:>8,} | {data['users']:>5,} | {avg_sessions:>19.1f}")

    print()

    # User journey insights
    print("🔄 PROPERTY USER JOURNEY INSIGHTS:")
    print("   💡 Property pages show strong user intent - users are actively looking at specific properties")
    print("   💡 High bounce rates suggest users may be comparing multiple properties")
    print("   💡 Consider adding 'Similar Properties' or 'Contact Agent' CTAs prominently")
    print("   💡 Property detail pages could benefit from virtual tours or 360° views")
    print()

    # Export detailed property data
    csv_data = []
    for page_path, data in sorted_property_pages:
        property_name = page_path.replace('/properties/', '').replace('-', ' ').title()
        csv_data.append({
            'Property_Path': page_path,
            'Property_Name': property_name,
            'Sessions': data['sessions'],
            'Users': data['users'],
            'Pageviews': data['pageviews'],
            'Avg_Duration': data['avg_duration'],
            'Bounce_Rate': data['bounce_rate'],
            'Pages_Per_Session': data['pages_per_session'],
            'Date_Range': f"{start_date}_to_{end_date}"
        })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename("property_pages_analysis", f"{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"📄 Detailed property analysis exported to: {csv_filename}")

    return {
        'property_pages': property_pages,
        'total_property_sessions': total_property_sessions,
        'total_property_users': total_property_users,
        'property_types': property_types,
        'high_engagement_count': len(high_engagement_props),
        'low_engagement_count': len(low_engagement_props)
    }
    """Analyze overall user behavior and page interactions"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print(f"🔍 Analyzing user behavior patterns")
    print(f"   Date range: {start_date} to {end_date}")
    print(f"   Minimum sessions threshold: {min_sessions}")
    print("=" * 120)

    date_range = create_date_range(start_date, end_date)

    # Get page performance data
    page_response = run_report(
        dimensions=["pagePath"],
        metrics=["sessions", "totalUsers", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=50
    )

    if page_response.row_count == 0:
        print("❌ No page data found for the date range.")
        return None

    print(f"✅ Retrieved {page_response.row_count} page performance records")

    # Analyze page performance
    page_data = {}
    total_sessions = 0
    total_users = 0

    for row in page_response.rows:
        page_path = row.dimension_values[0].value
        sessions = int(row.metric_values[0].value)
        users = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)

        if sessions >= min_sessions:  # Filter out low-traffic pages
            page_data[page_path] = {
                'sessions': sessions,
                'users': users,
                'pageviews': pageviews,
                'avg_duration': avg_duration,
                'bounce_rate': bounce_rate,
                'pages_per_session': pageviews / sessions if sessions > 0 else 0
            }

            total_sessions += sessions
            total_users += users

    if not page_data:
        print(f"❌ No pages found with at least {min_sessions} sessions")
        return None

    # Sort pages by session volume
    sorted_pages = sorted(page_data.items(), key=lambda x: x[1]['sessions'], reverse=True)

    print("\n📊 USER BEHAVIOR ANALYSIS:")
    print(f"   Total Sessions: {total_sessions:,}")
    print(f"   Total Users: {total_users:,}")
    print(f"   Pages Analyzed: {len(sorted_pages)}")
    print()

    print("   TOP PAGES BY TRAFFIC:")
    print("   Page Path                              | Sessions | Users | Pageviews | Avg Duration | Bounce Rate | Pages/Session")
    print("   ---------------------------------------|----------|-------|-----------|--------------|-------------|--------------")

    for page_path, data in sorted_pages[:15]:  # Show top 15
        path_display = page_path[:39] + "..." if len(page_path) > 39 else page_path
        print("39")

    print()

    # Analyze engagement patterns
    high_engagement_pages = [(p, d) for p, d in sorted_pages if d['bounce_rate'] < 0.3]
    low_engagement_pages = [(p, d) for p, d in sorted_pages if d['bounce_rate'] > 0.7]

    print("🎯 ENGAGEMENT ANALYSIS:")
    print(f"   High Engagement Pages (Bounce < 30%): {len(high_engagement_pages)}")
    print(f"   Low Engagement Pages (Bounce > 70%): {len(low_engagement_pages)}")
    print()

    if high_engagement_pages:
        print("   🟢 HIGH ENGAGEMENT PAGES:")
        for page_path, data in high_engagement_pages[:5]:
            print(f"      {page_path}: {data['bounce_rate']*100:.1f}% bounce, {data['avg_duration']:.1f}s avg duration")
    if low_engagement_pages:
        print("   🔴 LOW ENGAGEMENT PAGES:")
        for page_path, data in low_engagement_pages[:5]:
            print(f"      {page_path}: {data['bounce_rate']*100:.1f}% bounce, {data['avg_duration']:.1f}s avg duration")
    print()

    # Time-based analysis
    hourly_response = run_report(
        dimensions=["hour"],
        metrics=["sessions", "totalUsers"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="hour"))
        ]
    )

    if hourly_response.row_count > 0:
        print("🕐 HOURLY TRAFFIC PATTERNS:")
        print("   Hour | Sessions | Users")
        print("   -----|----------|------")

        for row in hourly_response.rows:
            hour = int(row.dimension_values[0].value)
            sessions = int(row.metric_values[0].value)
            users = int(row.metric_values[1].value)
            print("2d")

    print()

    # Export detailed page data
    csv_data = []
    for page_path, data in sorted_pages:
        csv_data.append({
            'Page_Path': page_path,
            'Sessions': data['sessions'],
            'Users': data['users'],
            'Pageviews': data['pageviews'],
            'Avg_Duration': data['avg_duration'],
            'Bounce_Rate': data['bounce_rate'],
            'Pages_Per_Session': data['pages_per_session'],
            'Date_Range': f"{start_date}_to_{end_date}"
        })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename("user_behavior_analysis", f"{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"📄 Detailed behavior data exported to: {csv_filename}")

    return {
        'page_data': page_data,
        'total_sessions': total_sessions,
        'total_users': total_users,
        'high_engagement_pages': len(high_engagement_pages),
        'low_engagement_pages': len(low_engagement_pages)
    }

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

    print("   TOP PAGES IN USER FLOW:")
    print("   Page Path                    | Sessions | Users | Pageviews | Avg Duration | Top Channel")
    print("   -----------------------------|----------|-------|-----------|--------------|-------------")

    for page_path, data in sorted_flows[:20]:  # Show top 20
        path_display = page_path[:28] + "..." if len(page_path) > 28 else page_path
        top_channel = max(data['channels'].items(), key=lambda x: x[1])[0] if data['channels'] else 'N/A'

        print("28")
    print()

    # Analyze flow depth and engagement
    single_page_sessions = sum(data['sessions'] for page, data in sorted_flows if page == start_page)
    multi_page_sessions = total_sessions - single_page_sessions

    print("📊 FLOW ENGAGEMENT ANALYSIS:")
    print(f"   Single Page Sessions: {single_page_sessions:,} ({single_page_sessions/total_sessions*100:.1f}%)")
    print(f"   Multi-Page Sessions: {multi_page_sessions:,} ({multi_page_sessions/total_sessions*100:.1f}%)")
    print(f"   Average Pages per Session: {sum(data['pageviews'] for data in flow_data.values()) / total_sessions:.1f}")
    print()

    # Channel distribution in flows
    channel_totals = {}
    for page_data in flow_data.values():
        for channel, sessions in page_data['channels'].items():
            channel_totals[channel] = channel_totals.get(channel, 0) + sessions

    print("📈 CHANNEL DISTRIBUTION IN FLOWS:")
    print("   Channel              | Sessions | Percentage")
    print("   ---------------------|----------|-----------")

    for channel, sessions in sorted(channel_totals.items(), key=lambda x: x[1], reverse=True):
        percentage = sessions / total_sessions * 100
        print("21")
    print()

    # Flow recommendations
    print("💡 FLOW OPTIMIZATION RECOMMENDATIONS:")
    if single_page_sessions / total_sessions > 0.7:  # Over 70% single page
        print("   • High bounce rate detected - users aren't exploring further")
        print("   • Add prominent internal links and related content suggestions")
        print("   • Consider improving page content to encourage deeper navigation")
    elif multi_page_sessions / total_sessions > 0.8:  # Over 80% multi-page
        print("   • Good engagement - users are exploring multiple pages")
        print("   • Focus on conversion optimization for engaged users")
        print("   • Consider adding cross-sell or related content recommendations")

    # Popular transition patterns
    print("\n🔄 POPULAR PAGE TRANSITIONS:")
    # This is a simplified analysis - in a real implementation,
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
    print("🌊 User Flow & Behavior Analysis Tool")
    print("=" * 50)

    if len(sys.argv) >= 2:
        analysis_type = sys.argv[1].lower()

        if analysis_type == "properties" or analysis_type == "property":
            # Analyze property pages
            days = int(sys.argv[2]) if len(sys.argv) >= 3 else 30
            min_sessions = int(sys.argv[3]) if len(sys.argv) >= 4 else 50

            print(f"Analyzing property pages")
            print(f"Time period: Last {days} days")
            print(f"Minimum sessions: {min_sessions}")

            if days == 7:
                end_date = datetime.now() - timedelta(days=1)
                start_date = end_date - timedelta(days=6)
                analyze_property_pages(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), min_sessions)
            else:
                end_date = datetime.now() - timedelta(days=1)
                start_date = end_date - timedelta(days=days-1)
                analyze_property_pages(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), min_sessions)

        elif analysis_type == "behavior":
            # Analyze overall user behavior
            days = int(sys.argv[2]) if len(sys.argv) >= 3 else 30
            min_sessions = int(sys.argv[3]) if len(sys.argv) >= 4 else 100

            print(f"Analyzing user behavior patterns")
            print(f"Time period: Last {days} days")
            print(f"Minimum sessions: {min_sessions}")

            if days == 7:
                end_date = datetime.now() - timedelta(days=1)
                start_date = end_date - timedelta(days=6)
                analyze_user_behavior(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), min_sessions)
            else:
                end_date = datetime.now() - timedelta(days=1)
                start_date = end_date - timedelta(days=days-1)
                analyze_user_behavior(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), min_sessions)

        else:
            # Original flow analysis from specific page
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
        print("Analyze user navigation flows and behavior patterns")
        print()
        print("Analysis Types:")
        print("  properties  - Analyze user behavior on property pages")
        print("  behavior    - Analyze overall user behavior patterns")
        print("  <page_path> - Analyze flows starting from specific page")
        print()
        print("Usage:")
        print("  python user_flow_analysis.py properties [days] [min_sessions]")
        print("  python user_flow_analysis.py behavior [days] [min_sessions]")
        print("  python user_flow_analysis.py <start_page> [max_steps] [days]")
        print()
        print("Examples:")
        print("  python user_flow_analysis.py properties 30 50")
        print("  python user_flow_analysis.py behavior 7 100")
        print("  python user_flow_analysis.py /valuations 5 30")
        exit(1)