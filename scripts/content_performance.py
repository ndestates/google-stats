"""
Content Performance Analysis Script
Analyze content engagement and effectiveness

Usage:
    python content_performance.py [content_type] [days]

Examples:
    python content_performance.py properties 30
    python content_performance.py pages 7
    python content_performance.py all 90
"""

import os
#!/usr/bin/env python3
"""
Run with: ddev exec python scripts/content_performance.py
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

def analyze_content_engagement(start_date: str = None, end_date: str = None):
    """Analyze content engagement metrics"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("📖 Analyzing content engagement...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["pagePath", "pageTitle"],
        metrics=["totalUsers", "sessions", "screenPageViews", "averageSessionDuration", "bounceRate", "engagementRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)
        ],
        limit=100
    )

    if response.row_count == 0:
        print("❌ No content engagement data found for the date range.")
        return None

    print(f"✅ Retrieved engagement data for {response.row_count} pages")

    # Analyze content performance
    content_data = {}
    total_pageviews = 0

    for row in response.rows:
        page_path = row.dimension_values[0].value
        page_title = row.dimension_values[1].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)
        engagement_rate = float(row.metric_values[5].value)
        screen_views = pageviews  # screenPageViews is already at index 2

        content_data[page_path] = {
            'title': page_title,
            'users': users,
            'sessions': sessions,
            'pageviews': pageviews,
            'avg_duration': avg_duration,
            'bounce_rate': bounce_rate,
            'engagement_rate': engagement_rate,
            'screen_views': screen_views
        }

        total_pageviews += pageviews

    print("📊 CONTENT ENGAGEMENT ANALYSIS:")
    print(f"   Total Page Views: {total_pageviews:,}")
    print(f"   Unique Pages: {len(content_data)}")
    print()

    # Content performance categories
    high_engagement = []
    low_engagement = []
    high_bounce = []
    long_sessions = []

    for page_path, data in content_data.items():
        if data['pageviews'] >= 10:  # Minimum threshold
            if data['engagement_rate'] > 0.7:
                high_engagement.append((page_path, data['engagement_rate'], data['pageviews']))
            elif data['engagement_rate'] < 0.3:
                low_engagement.append((page_path, data['engagement_rate'], data['pageviews']))

            if data['bounce_rate'] > 0.7:
                high_bounce.append((page_path, data['bounce_rate'], data['pageviews']))

            if data['avg_duration'] > 180:  # Over 3 minutes
                long_sessions.append((page_path, data['avg_duration'], data['pageviews']))

    print("   ⭐ HIGH ENGAGEMENT CONTENT (>70%):")
    for page, engagement, views in sorted(high_engagement, key=lambda x: x[1], reverse=True)[:5]:
        page_display = page[:50] + "..." if len(page) > 50 else page
        print(f"      • {page_display} (Engagement: {engagement:.1%}, Views: {views:,})")
    print()

    print("   ⚠️  LOW ENGAGEMENT CONTENT (<30%):")
    for page, engagement, views in sorted(low_engagement, key=lambda x: x[1])[:5]:
        page_display = page[:50] + "..." if len(page) > 50 else page
        print(f"      • {page_display} (Engagement: {engagement:.1%}, Views: {views:,})")
    print()

    print("   🚪 HIGH BOUNCE CONTENT (>70%):")
    for page, bounce, views in sorted(high_bounce, key=lambda x: x[1], reverse=True)[:5]:
        page_display = page[:50] + "..." if len(page) > 50 else page
        print(f"      • {page_display} (Bounce: {bounce:.1%}, Views: {views:,})")
    print()

    print("   ⏰ LONG SESSION CONTENT (>3 min):")
    for page, duration, views in sorted(long_sessions, key=lambda x: x[1], reverse=True)[:5]:
        page_display = page[:50] + "..." if len(page) > 50 else page
        print(f"      • {page_display} (Duration: {duration:.1f}s, Views: {views:,})")
    print()

    return content_data

def analyze_content_types(start_date: str = None, end_date: str = None):
    """Analyze performance by content type/category"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("📂 Analyzing content types...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    # Categorize content by URL patterns
    response = run_report(
        dimensions=["pagePath"],
        metrics=["totalUsers", "sessions", "screenPageViews", "averageSessionDuration", "bounceRate", "engagementRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)
        ],
        limit=200
    )

    if response.row_count == 0:
        print("❌ No content type data found for the date range.")
        return None

    print(f"✅ Retrieved data for {response.row_count} pages")

    # Categorize content
    content_categories = {
        'Properties': {'pattern': lambda p: 'property' in p.lower() or 'apartment' in p.lower() or 'house' in p.lower() or 'cottage' in p.lower()},
        'Valuations': {'pattern': lambda p: 'valuation' in p.lower() or 'value' in p.lower()},
        'About': {'pattern': lambda p: 'about' in p.lower()},
        'Contact': {'pattern': lambda p: 'contact' in p.lower()},
        'Services': {'pattern': lambda p: 'service' in p.lower()},
        'Blog/News': {'pattern': lambda p: 'blog' in p.lower() or 'news' in p.lower()},
        'Homepage': {'pattern': lambda p: p in ['/', '/index.html', '/home']},
        'Other': {'pattern': lambda p: True}  # Catch-all
    }

    category_data = {}
    for category in content_categories.keys():
        category_data[category] = {
            'pages': 0, 'users': 0, 'sessions': 0, 'pageviews': 0,
            'avg_duration': 0, 'bounce_rate': 0, 'engagement_rate': 0
        }

    # Process each page
    for row in response.rows:
        page_path = row.dimension_values[0].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)
        engagement_rate = float(row.metric_values[5].value)

        # Categorize the page
        category_found = False
        for category, config in content_categories.items():
            if category != 'Other' and config['pattern'](page_path):
                cat_data = category_data[category]
                cat_data['pages'] += 1
                cat_data['users'] += users
                cat_data['sessions'] += sessions
                cat_data['pageviews'] += pageviews

                # Weighted averages
                weight = sessions / (cat_data['sessions'] + sessions)
                cat_data['avg_duration'] = cat_data['avg_duration'] * (1 - weight) + avg_duration * weight
                cat_data['bounce_rate'] = cat_data['bounce_rate'] * (1 - weight) + bounce_rate * weight
                cat_data['engagement_rate'] = cat_data['engagement_rate'] * (1 - weight) + engagement_rate * weight

                category_found = True
                break

        # If no category matched, put in Other
        if not category_found:
            cat_data = category_data['Other']
            cat_data['pages'] += 1
            cat_data['users'] += users
            cat_data['sessions'] += sessions
            cat_data['pageviews'] += pageviews

            weight = sessions / (cat_data['sessions'] + sessions)
            cat_data['avg_duration'] = cat_data['avg_duration'] * (1 - weight) + avg_duration * weight
            cat_data['bounce_rate'] = cat_data['bounce_rate'] * (1 - weight) + bounce_rate * weight
            cat_data['engagement_rate'] = cat_data['engagement_rate'] * (1 - weight) + engagement_rate * weight

    print("📊 CONTENT TYPE PERFORMANCE:")
    print("   Category     | Pages | Users | Sessions | Pageviews | Avg Duration | Bounce | Engage")
    print("   --------------|-------|-------|----------|-----------|--------------|--------|--------")

    total_pageviews = sum(cat['pageviews'] for cat in category_data.values())

    for category, data in sorted(category_data.items(), key=lambda x: x[1]['pageviews'], reverse=True):
        if data['pages'] > 0:
            category_display = category[:12] + "..." if len(category) > 12 else category
            percentage = (data['pageviews'] / total_pageviews) * 100 if total_pageviews > 0 else 0
            print(f"   {category_display:<12} | {data['pages']:>5} | {data['users']:>5} | {data['sessions']:>8} | {data['pageviews']:>9} | {data['avg_duration']:>12.1f}s | {data['bounce_rate']:>6.1%} | {data['engagement_rate']:>6.1%}")
    print()

    # Content type insights
    print("   💡 CONTENT TYPE INSIGHTS:")
    for category, data in category_data.items():
        if data['pages'] > 0 and data['sessions'] > 5:
            if data['engagement_rate'] > 0.6:
                print(f"   • {category}: Strong engagement ({data['engagement_rate']:.1%}) - {data['pages']} pages")
            if data['bounce_rate'] > 0.6:
                print(f"   • {category}: High bounce rate ({data['bounce_rate']:.1%}) - review content relevance")
            if data['avg_duration'] > 120:
                print(f"   • {category}: Good time on page ({data['avg_duration']:.1f}s) - engaging content")
    print()

    return category_data

def analyze_content_effectiveness(start_date: str = None, end_date: str = None):
    """Analyze content effectiveness and conversion potential"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("🎯 Analyzing content effectiveness...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    # Get content with goal completions (simplified - using sessions as proxy)
    response = run_report(
        dimensions=["pagePath", "sessionDefaultChannelGrouping"],
        metrics=["totalUsers", "sessions", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)
        ],
        limit=50
    )

    if response.row_count == 0:
        print("❌ No content effectiveness data found for the date range.")
        return None

    print(f"✅ Retrieved effectiveness data for {response.row_count} pages")

    # Analyze effectiveness by channel
    effectiveness_data = {}
    channel_performance = {}

    for row in response.rows:
        page_path = row.dimension_values[0].value
        channel = row.dimension_values[1].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)

        if channel not in channel_performance:
            channel_performance[channel] = {
                'total_users': 0, 'total_sessions': 0, 'total_pageviews': 0,
                'avg_duration': 0, 'avg_bounce': 0, 'pages': 0
            }

        channel_performance[channel]['total_users'] += users
        channel_performance[channel]['total_sessions'] += sessions
        channel_performance[channel]['total_pageviews'] += pageviews
        channel_performance[channel]['pages'] += 1

        # Weighted averages for channel
        weight = sessions / (channel_performance[channel]['total_sessions'] + sessions)
        current_duration = channel_performance[channel]['avg_duration']
        current_bounce = channel_performance[channel]['avg_bounce']

        channel_performance[channel]['avg_duration'] = current_duration * (1 - weight) + avg_duration * weight
        channel_performance[channel]['avg_bounce'] = current_bounce * (1 - weight) + bounce_rate * weight

        # Store page-level data
        effectiveness_data[f"{page_path}_{channel}"] = {
            'page': page_path,
            'channel': channel,
            'users': users,
            'sessions': sessions,
            'pageviews': pageviews,
            'avg_duration': avg_duration,
            'bounce_rate': bounce_rate
        }

    print("📊 CONTENT EFFECTIVENESS BY CHANNEL:")
    print("   Channel          | Users | Sessions | Pageviews | Avg Duration | Bounce Rate")
    print("   -----------------|-------|----------|-----------|--------------|------------")

    for channel, data in sorted(channel_performance.items(), key=lambda x: x[1]['total_sessions'], reverse=True):
        channel_display = channel[:15] + "..." if len(channel) > 15 else channel
        print(f"   {channel_display:<15} | {data['total_users']:>5} | {data['total_sessions']:>8} | {data['total_pageviews']:>9} | {data['avg_duration']:>12.1f}s | {data['avg_bounce']:>10.1%}")
    print()

    # Effectiveness recommendations
    print("   💡 CONTENT EFFECTIVENESS RECOMMENDATIONS:")
    print("   1. Channel Optimization:")
    for channel, data in channel_performance.items():
        if data['total_sessions'] > 10:
            if data['avg_bounce'] > 0.6:
                print(f"      • {channel}: High bounce rate - improve landing page relevance")
            if data['avg_duration'] < 30:
                print(f"      • {channel}: Short sessions - enhance content engagement")
    print()
    print("   2. Content Strategy:")
    print("      • Focus on high-engagement content types")
    print("      • Optimize underperforming pages")
    print("      • Test content variations by channel")
    print()
    print("   3. User Experience:")
    print("      • Ensure mobile-friendly content")
    print("      • Improve page load speeds")
    print("      • Add clear calls-to-action")
    print()

    return effectiveness_data

def analyze_content_performance(content_type: str = "all", start_date: str = None, end_date: str = None):
    """Main function for content performance analysis"""

    print("📄 Content Performance Analysis Tool")
    print("=" * 38)

    results = {}

    if content_type in ["engagement", "all"]:
        results['engagement'] = analyze_content_engagement(start_date, end_date)

    if content_type in ["types", "categories", "all"]:
        results['types'] = analyze_content_types(start_date, end_date)

    if content_type in ["effectiveness", "all"]:
        results['effectiveness'] = analyze_content_effectiveness(start_date, end_date)

    # Export combined data
    if results:
        csv_data = []

        # Engagement data
        if 'engagement' in results and results['engagement']:
            for page_path, data in results['engagement'].items():
                csv_data.append({
                    'Analysis_Type': 'Content_Engagement',
                    'Page_Path': page_path,
                    'Title': data['title'],
                    'Users': data['users'],
                    'Sessions': data['sessions'],
                    'Pageviews': data['pageviews'],
                    'Avg_Duration': data['avg_duration'],
                    'Bounce_Rate': data['bounce_rate'],
                    'Engagement_Rate': data['engagement_rate'],
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

        # Types data
        if 'types' in results and results['types']:
            for category, data in results['types'].items():
                csv_data.append({
                    'Analysis_Type': 'Content_Types',
                    'Page_Path': category,
                    'Title': None,
                    'Users': data['users'],
                    'Sessions': data['sessions'],
                    'Pageviews': data['pageviews'],
                    'Avg_Duration': data['avg_duration'],
                    'Bounce_Rate': data['bounce_rate'],
                    'Engagement_Rate': data['engagement_rate'],
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

        # Effectiveness data
        if 'effectiveness' in results and results['effectiveness']:
            for key, data in results['effectiveness'].items():
                csv_data.append({
                    'Analysis_Type': 'Content_Effectiveness',
                    'Page_Path': data['page'],
                    'Title': data['channel'],
                    'Users': data['users'],
                    'Sessions': data['sessions'],
                    'Pageviews': data['pageviews'],
                    'Avg_Duration': data['avg_duration'],
                    'Bounce_Rate': data['bounce_rate'],
                    'Engagement_Rate': None,
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_filename = get_report_filename("content_performance", f"{content_type}_{start_date}_to_{end_date}")
            df.to_csv(csv_filename, index=False)
            print(f"📄 Content performance data exported to: {csv_filename}")

    return results

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        content_type = sys.argv[1]
        days_or_date = sys.argv[2] if len(sys.argv) >= 3 else "30"

        print(f"Content type: {content_type}")

        # Check if it's a date keyword
        if days_or_date.lower() in ["yesterday", "today"]:
            if days_or_date.lower() == "yesterday":
                end_date = datetime.now() - timedelta(days=1)
                start_date = end_date
                print(f"Time period: Yesterday ({start_date.strftime('%Y-%m-%d')})")
            elif days_or_date.lower() == "today":
                end_date = datetime.now()
                start_date = end_date
                print(f"Time period: Today ({start_date.strftime('%Y-%m-%d')})")
            analyze_content_performance(content_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        else:
            # It's a number of days
            days = int(days_or_date)
            print(f"Time period: Last {days} days")

            if days == 7:
                end_date = datetime.now() - timedelta(days=1)
                start_date = end_date - timedelta(days=6)
                analyze_content_performance(content_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            else:
                end_date = datetime.now() - timedelta(days=1)
                start_date = end_date - timedelta(days=days-1)
                analyze_content_performance(content_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    else:
        print("Analyze content performance and engagement")
        print()
        print("Content types:")
        print("  engagement    - Content engagement metrics")
        print("  types         - Performance by content type")
        print("  effectiveness - Content effectiveness analysis")
        print("  all           - Complete content analysis")
        print()
        print("Usage: python content_performance.py <content_type> [days|yesterday|today]")
        print("Example: python content_performance.py all 30")
        print("Example: python content_performance.py all yesterday")
        exit(1)