"""
Technical Performance Analysis Script
Analyze website technical performance metrics

Usage:
    python technical_performance.py [metric_type] [days]

Examples:
    python technical_performance.py load_times 30
    python technical_performance.py errors 7
    python technical_performance.py all 90
"""

import os
#!/usr/bin/env python3
"""
Run with: ddev exec python scripts/technical_performance.py
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

def analyze_load_performance(start_date: str = None, end_date: str = None):
    """Analyze page load times and performance metrics"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("⚡ Analyzing page load performance...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    # Note: GA4 has limited technical performance metrics compared to Universal Analytics
    # We'll focus on what we can measure: engagement rates, session duration, etc.

    response = run_report(
        dimensions=["pagePath", "deviceCategory"],
        metrics=["totalUsers", "sessions", "engagementRate", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=50
    )

    if response.row_count == 0:
        print("❌ No performance data found for the date range.")
        return None

    print(f"✅ Retrieved performance data for {response.row_count} pages")

    # Analyze performance by page and device
    performance_data = {}
    total_sessions = 0

    for row in response.rows:
        page_path = row.dimension_values[0].value
        device = row.dimension_values[1].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        engagement_rate = float(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)

        if page_path not in performance_data:
            performance_data[page_path] = {
                'total_users': 0,
                'total_sessions': 0,
                'avg_engagement': 0,
                'avg_duration': 0,
                'avg_bounce': 0,
                'devices': {}
            }

        performance_data[page_path]['total_users'] += users
        performance_data[page_path]['total_sessions'] += sessions

        # Weighted averages
        weight = sessions / (performance_data[page_path]['total_sessions'] + sessions)
        current_engagement = performance_data[page_path]['avg_engagement']
        current_duration = performance_data[page_path]['avg_duration']
        current_bounce = performance_data[page_path]['avg_bounce']

        performance_data[page_path]['avg_engagement'] = current_engagement * (1 - weight) + engagement_rate * weight
        performance_data[page_path]['avg_duration'] = current_duration * (1 - weight) + avg_duration * weight
        performance_data[page_path]['avg_bounce'] = current_bounce * (1 - weight) + bounce_rate * weight

        # Device-specific data
        if device not in performance_data[page_path]['devices']:
            performance_data[page_path]['devices'][device] = {
                'users': 0, 'sessions': 0, 'engagement': engagement_rate, 'duration': avg_duration, 'bounce': bounce_rate
            }

        performance_data[page_path]['devices'][device]['users'] += users
        performance_data[page_path]['devices'][device]['sessions'] += sessions

        total_sessions += sessions

    # Identify performance issues
    slow_pages = []
    low_engagement_pages = []
    high_bounce_pages = []

    for page, data in performance_data.items():
        if data['avg_duration'] < 30:  # Less than 30 seconds
            slow_pages.append((page, data['avg_duration']))
        if data['avg_engagement'] < 0.3:  # Less than 30% engagement
            low_engagement_pages.append((page, data['avg_engagement']))
        if data['avg_bounce'] > 0.7:  # Over 70% bounce
            high_bounce_pages.append((page, data['avg_bounce']))

    print("\n📊 TECHNICAL PERFORMANCE ANALYSIS:")
    print(f"   Total Pages Analyzed: {len(performance_data)}")
    print(f"   Total Sessions: {total_sessions:,}")
    print()

    print("   🚨 PERFORMANCE ISSUES DETECTED:")
    print(f"   • Pages with very short sessions (<30s): {len(slow_pages)}")
    print(f"   • Pages with low engagement (<30%): {len(low_engagement_pages)}")
    print(f"   • Pages with high bounce rate (>70%): {len(high_bounce_pages)}")
    print()

    if slow_pages:
        print("   ⚠️  PAGES WITH SHORT SESSIONS:")
        for page, duration in sorted(slow_pages, key=lambda x: x[1])[:5]:
            page_display = page[:50] + "..." if len(page) > 50 else page
            print(f"      • {page_display} ({duration:.1f}s)")
        print()

    if low_engagement_pages:
        print("   ⚠️  PAGES WITH LOW ENGAGEMENT:")
        for page, engagement in sorted(low_engagement_pages, key=lambda x: x[1])[:5]:
            page_display = page[:50] + "..." if len(page) > 50 else page
            print(f"      • {page_display} ({engagement:.1%})")
        print()

    if high_bounce_pages:
        print("   ⚠️  PAGES WITH HIGH BOUNCE RATES:")
        for page, bounce in sorted(high_bounce_pages, key=lambda x: x[1], reverse=True)[:5]:
            page_display = page[:50] + "..." if len(page) > 50 else page
            print(f"      • {page_display} ({bounce:.1%})")
        print()

    # Device performance comparison
    print("📱 DEVICE PERFORMANCE COMPARISON:")
    device_totals = {}
    for page_data in performance_data.values():
        for device, device_data in page_data['devices'].items():
            if device not in device_totals:
                device_totals[device] = {'sessions': 0, 'engagement': 0, 'duration': 0, 'bounce': 0, 'count': 0}

            device_totals[device]['sessions'] += device_data['sessions']
            device_totals[device]['engagement'] += device_data['engagement'] * device_data['sessions']
            device_totals[device]['duration'] += device_data['duration'] * device_data['sessions']
            device_totals[device]['bounce'] += device_data['bounce'] * device_data['sessions']
            device_totals[device]['count'] += 1

    print("   Device    | Sessions | Avg Engagement | Avg Duration | Avg Bounce")
    print("   ----------|----------|----------------|--------------|------------")

    for device, data in device_totals.items():
        avg_engagement = data['engagement'] / data['sessions'] if data['sessions'] > 0 else 0
        avg_duration = data['duration'] / data['sessions'] if data['sessions'] > 0 else 0
        avg_bounce = data['bounce'] / data['sessions'] if data['sessions'] > 0 else 0

        print(f"   {device:<10} | {data['sessions']:<8,} | {avg_engagement:.1%}        | {avg_duration:.1f}s        | {avg_bounce:.1%}")
    print()

    # Performance recommendations
    print("💡 TECHNICAL PERFORMANCE RECOMMENDATIONS:")
    print("   1. Page Load Speed:")
    print("      • Aim for <3 second load times on mobile")
    print("      • Optimize images and reduce server response time")
    print("      • Use caching and CDN for static assets")
    print()
    print("   2. User Experience:")
    print("      • Ensure mobile responsiveness across all pages")
    print("      • Test forms and interactive elements")
    print("      • Verify tracking code implementation")
    print()
    print("   3. Content Quality:")
    print("      • Review content relevance for target pages")
    print("      • Add clear calls-to-action")
    print("      • Improve internal linking structure")
    print()

    return performance_data

def analyze_errors_events(start_date: str = None, end_date: str = None):
    """Analyze custom events and potential error indicators"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("🚨 Analyzing custom events and errors...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    # Get custom events data
    response = run_report(
        dimensions=["eventName", "pagePath"],
        metrics=["eventCount", "totalUsers", "eventValue"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventCount"), desc=True)
        ],
        limit=50
    )

    if response.row_count == 0:
        print("❌ No custom events data found for the date range.")
        print("💡 This could mean events aren't properly tracked in GA4")
        return None

    print(f"✅ Retrieved {response.row_count} custom events")

    # Analyze events
    event_data = {}
    total_events = 0

    for row in response.rows:
        event_name = row.dimension_values[0].value
        page_path = row.dimension_values[1].value
        event_count = int(row.metric_values[0].value)
        users = int(row.metric_values[1].value)
        event_value = float(row.metric_values[2].value) if row.metric_values[2].value else 0

        if event_name not in event_data:
            event_data[event_name] = {
                'total_count': 0,
                'total_users': 0,
                'total_value': 0,
                'pages': {}
            }

        event_data[event_name]['total_count'] += event_count
        event_data[event_name]['total_users'] += users
        event_data[event_name]['total_value'] += event_value

        if page_path not in event_data[event_name]['pages']:
            event_data[event_name]['pages'][page_path] = 0
        event_data[event_name]['pages'][page_path] += event_count

        total_events += event_count

    print("\n📊 CUSTOM EVENTS ANALYSIS:")
    print(f"   Total Events: {total_events:,}")
    print(f"   Unique Event Types: {len(event_data)}")
    print()

    print("   TOP CUSTOM EVENTS:")
    print("   Event Name              | Count    | Users    | Avg per User | Top Page")
    print("   -----------------------|----------|----------|--------------|----------")

    for event_name, data in sorted(event_data.items(), key=lambda x: x[1]['total_count'], reverse=True)[:10]:
        event_display = event_name[:22] + "..." if len(event_name) > 22 else event_name
        avg_per_user = data['total_count'] / data['total_users'] if data['total_users'] > 0 else 0
        top_page = max(data['pages'].items(), key=lambda x: x[1])[0] if data['pages'] else 'N/A'
        top_page_display = top_page[:15] + "..." if len(top_page) > 15 else top_page

        print(f"   {event_display:<22} | {data['total_count']:<8,} | {data['total_users']:<8,} | {avg_per_user:.1f}        | {top_page_display}")
    print()

    # Identify potential issues
    error_events = [name for name in event_data.keys() if any(word in name.lower() for word in ['error', 'fail', '404', 'exception'])]
    conversion_events = [name for name in event_data.keys() if any(word in name.lower() for word in ['convert', 'submit', 'purchase', 'signup'])]

    print("🔍 EVENT TYPE ANALYSIS:")
    if error_events:
        print(f"   • Potential error events detected: {', '.join(error_events[:3])}")
    if conversion_events:
        print(f"   • Conversion events detected: {', '.join(conversion_events[:3])}")
    print()

    return event_data

def analyze_technical_performance(metric_type: str = "all", start_date: str = None, end_date: str = None):
    """Main function for technical performance analysis"""

    print("🔧 Technical Performance Analysis Tool")
    print("=" * 45)

    results = {}

    if metric_type in ["load_times", "performance", "all"]:
        results['performance'] = analyze_load_performance(start_date, end_date)

    if metric_type in ["errors", "events", "all"]:
        results['events'] = analyze_errors_events(start_date, end_date)

    # Export combined data
    if results:
        csv_data = []

        # Performance data
        if 'performance' in results and results['performance']:
            for page, data in results['performance'].items():
                csv_data.append({
                    'Analysis_Type': 'Performance',
                    'Page_Path': page,
                    'Users': data['total_users'],
                    'Sessions': data['total_sessions'],
                    'Engagement_Rate': data['avg_engagement'],
                    'Avg_Duration': data['avg_duration'],
                    'Bounce_Rate': data['avg_bounce'],
                    'Issue_Type': 'Short_Session' if data['avg_duration'] < 30 else 'Low_Engagement' if data['avg_engagement'] < 0.3 else 'High_Bounce' if data['avg_bounce'] > 0.7 else 'Normal',
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

        # Events data
        if 'events' in results and results['events']:
            for event_name, data in results['events'].items():
                csv_data.append({
                    'Analysis_Type': 'Events',
                    'Page_Path': event_name,  # Using event name as identifier
                    'Users': data['total_users'],
                    'Sessions': data['total_count'],  # Using count as sessions
                    'Engagement_Rate': None,
                    'Avg_Duration': None,
                    'Bounce_Rate': None,
                    'Issue_Type': 'Error_Event' if any(word in event_name.lower() for word in ['error', 'fail', '404']) else 'Conversion_Event' if any(word in event_name.lower() for word in ['convert', 'submit']) else 'Custom_Event',
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_filename = get_report_filename("technical_performance", f"{metric_type}_{start_date}_to_{end_date}")
            df.to_csv(csv_filename, index=False)
            print(f"📄 Technical analysis data exported to: {csv_filename}")

    return results

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        metric_type = sys.argv[1]
        days = int(sys.argv[2]) if len(sys.argv) >= 3 else 30

        print(f"Analysis type: {metric_type}")
        print(f"Time period: Last {days} days")

        if days == 7:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
            analyze_technical_performance(metric_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        else:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=days-1)
            analyze_technical_performance(metric_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    else:
        print("Analyze technical performance and custom events")
        print()
        print("Metric types:")
        print("  load_times  - Page load and engagement analysis")
        print("  errors      - Custom events and error tracking")
        print("  all         - Complete technical analysis")
        print()
        print("Usage: python technical_performance.py <metric_type> [days]")
        print("Example: python technical_performance.py all 30")
        exit(1)