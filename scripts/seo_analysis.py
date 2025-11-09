"""
SEO Analysis Script
Analyze search engine optimization performance

Usage:
    python seo_analysis.py [seo_type] [days]

Examples:
    python seo_analysis.py organic 30
    python seo_analysis.py keywords 7
    python seo_analysis.py all 90
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

def analyze_organic_traffic(start_date: str = None, end_date: str = None):
    """Analyze organic search traffic performance"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("🔍 Analyzing organic search traffic...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["sessionDefaultChannelGrouping", "pagePath"],
        metrics=["totalUsers", "sessions", "pageviews", "averageSessionDuration", "bounceRate", "engagementRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=100
    )

    if response.row_count == 0:
        print("❌ No organic traffic data found for the date range.")
        return None

    print(f"✅ Retrieved organic data for {response.row_count} channel/page combinations")

    # Analyze organic vs other channels
    channel_data = {}
    organic_pages = {}

    for row in response.rows:
        channel = row.dimension_values[0].value
        page_path = row.dimension_values[1].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)
        engagement_rate = float(row.metric_values[5].value)

        if channel not in channel_data:
            channel_data[channel] = {
                'users': 0, 'sessions': 0, 'pageviews': 0,
                'avg_duration': 0, 'bounce_rate': 0, 'engagement_rate': 0
            }

        channel_data[channel]['users'] += users
        channel_data[channel]['sessions'] += sessions
        channel_data[channel]['pageviews'] += pageviews

        # Weighted averages
        weight = sessions / (channel_data[channel]['sessions'] + sessions)
        current_duration = channel_data[channel]['avg_duration']
        current_bounce = channel_data[channel]['bounce_rate']
        current_engagement = channel_data[channel]['engagement_rate']

        channel_data[channel]['avg_duration'] = current_duration * (1 - weight) + avg_duration * weight
        channel_data[channel]['bounce_rate'] = current_bounce * (1 - weight) + bounce_rate * weight
        channel_data[channel]['engagement_rate'] = current_engagement * (1 - weight) + engagement_rate * weight

        # Track organic pages
        if channel == "Organic Search":
            organic_pages[page_path] = {
                'users': users, 'sessions': sessions, 'pageviews': pageviews,
                'avg_duration': avg_duration, 'bounce_rate': bounce_rate, 'engagement_rate': engagement_rate
            }

    print("📊 ORGANIC TRAFFIC ANALYSIS:")
    print("   Channel          | Users | Sessions | Pageviews | Avg Duration | Bounce | Engage")
    print("   -----------------|-------|----------|-----------|--------------|--------|--------")

    total_sessions = sum(data['sessions'] for data in channel_data.values())

    for channel, data in sorted(channel_data.items(), key=lambda x: x[1]['sessions'], reverse=True):
        channel_display = channel[:15] + "..." if len(channel) > 15 else channel
        percentage = (data['sessions'] / total_sessions) * 100 if total_sessions > 0 else 0
        print("15")
    print()

    # Organic search insights
    if "Organic Search" in channel_data:
        organic = channel_data["Organic Search"]
        print("   🔍 ORGANIC SEARCH PERFORMANCE:")
        print(f"   • Organic sessions: {organic['sessions']:,} ({organic['sessions']/total_sessions*100:.1f}%)")
        print(f"   • Organic users: {organic['users']:,}")
        print(f"   • Avg session duration: {organic['avg_duration']:.1f}s")
        print(f"   • Bounce rate: {organic['bounce_rate']:.1%}")
        print(f"   • Engagement rate: {organic['engagement_rate']:.1%}")
        print()

        # Organic landing pages
        print("   🏠 TOP ORGANIC LANDING PAGES:")
        for page, data in sorted(organic_pages.items(), key=lambda x: x[1]['sessions'], reverse=True)[:5]:
            page_display = page[:50] + "..." if len(page) > 50 else page
            print("15")
        print()

    return {'channels': channel_data, 'organic_pages': organic_pages}

def analyze_keyword_performance(start_date: str = None, end_date: str = None):
    """Analyze keyword performance (limited by GA4 capabilities)"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("🔑 Analyzing keyword performance...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    # Note: GA4 doesn't provide individual keywords like Universal Analytics
    # We'll analyze search term categories and landing pages

    response = run_report(
        dimensions=["pagePath", "sessionDefaultChannelGrouping"],
        metrics=["totalUsers", "sessions", "pageviews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        dimension_filter={
            "filter": {
                "field_name": "sessionDefaultChannelGrouping",
                "string_filter": {
                    "value": "Organic Search"
                }
            }
        },
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=50
    )

    if response.row_count == 0:
        print("❌ No keyword performance data found for the date range.")
        print("💡 GA4 has limited keyword data compared to Universal Analytics")
        return None

    print(f"✅ Retrieved keyword data for {response.row_count} organic pages")

    # Analyze organic page performance
    keyword_insights = {}

    for row in response.rows:
        page_path = row.dimension_values[0].value
        channel = row.dimension_values[1].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)

        # Infer keyword themes from page paths
        keyword_themes = infer_keyword_themes(page_path)

        for theme in keyword_themes:
            if theme not in keyword_insights:
                keyword_insights[theme] = {
                    'sessions': 0, 'users': 0, 'pageviews': 0,
                    'avg_duration': 0, 'bounce_rate': 0, 'pages': []
                }

            keyword_insights[theme]['sessions'] += sessions
            keyword_insights[theme]['users'] += users
            keyword_insights[theme]['pageviews'] += pageviews
            keyword_insights[theme]['pages'].append(page_path)

            # Weighted averages
            weight = sessions / (keyword_insights[theme]['sessions'] + sessions)
            current_duration = keyword_insights[theme]['avg_duration']
            current_bounce = keyword_insights[theme]['bounce_rate']

            keyword_insights[theme]['avg_duration'] = current_duration * (1 - weight) + avg_duration * weight
            keyword_insights[theme]['bounce_rate'] = current_bounce * (1 - weight) + bounce_rate * weight

    print("📊 KEYWORD THEME PERFORMANCE:")
    print("   Theme           | Sessions | Users | Pageviews | Avg Duration | Bounce Rate")
    print("   ----------------|----------|-------|-----------|--------------|------------")

    for theme, data in sorted(keyword_insights.items(), key=lambda x: x[1]['sessions'], reverse=True):
        theme_display = theme[:15] + "..." if len(theme) > 15 else theme
        print("15")
    print()

    # Keyword insights
    print("   💡 KEYWORD INSIGHTS:")
    print("   • Focus on high-performing keyword themes")
    print("   • Optimize pages with high bounce rates")
    print("   • Consider long-tail keyword opportunities")
    print("   • GA4 keyword data is limited - consider Search Console integration")
    print()

    return keyword_insights

def infer_keyword_themes(page_path: str):
    """Infer keyword themes from page paths"""
    themes = []
    path_lower = page_path.lower()

    # Property-related keywords
    if any(word in path_lower for word in ['property', 'apartment', 'house', 'home', 'cottage']):
        themes.append('Property Search')

    # Location-based keywords
    if any(word in path_lower for word in ['st-helier', 'st-saviour', 'st-peter', 'jersey']):
        themes.append('Jersey Locations')

    # Service keywords
    if 'valuation' in path_lower or 'value' in path_lower:
        themes.append('Property Valuation')
    if 'letting' in path_lower or 'rent' in path_lower:
        themes.append('Property Letting')
    if 'sale' in path_lower:
        themes.append('Property Sales')

    # If no specific themes, categorize as general
    if not themes:
        themes.append('General Property')

    return themes

def analyze_seo_health(start_date: str = None, end_date: str = None):
    """Analyze overall SEO health indicators"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("🏥 Analyzing SEO health indicators...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    # Get comprehensive SEO metrics
    response = run_report(
        dimensions=["pagePath", "deviceCategory"],
        metrics=["totalUsers", "sessions", "pageviews", "averageSessionDuration", "bounceRate", "engagementRate"],
        date_ranges=[date_range],
        dimension_filter={
            "filter": {
                "field_name": "sessionDefaultChannelGrouping",
                "string_filter": {
                    "value": "Organic Search"
                }
            }
        },
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="pageviews"), desc=True)
        ],
        limit=50
    )

    if response.row_count == 0:
        print("❌ No SEO health data found for the date range.")
        return None

    print(f"✅ Retrieved SEO health data for {response.row_count} pages")

    # Analyze SEO health by device
    seo_health = {
        'mobile': {'sessions': 0, 'bounce_rate': 0, 'engagement_rate': 0, 'avg_duration': 0},
        'desktop': {'sessions': 0, 'bounce_rate': 0, 'engagement_rate': 0, 'avg_duration': 0},
        'tablet': {'sessions': 0, 'bounce_rate': 0, 'engagement_rate': 0, 'avg_duration': 0}
    }

    page_health = {}

    for row in response.rows:
        page_path = row.dimension_values[0].value
        device = row.dimension_values[1].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)
        engagement_rate = float(row.metric_values[5].value)

        if device.lower() in seo_health:
            device_key = device.lower()
            seo_health[device_key]['sessions'] += sessions

            # Weighted averages
            weight = sessions / (seo_health[device_key]['sessions'] + sessions)
            current_bounce = seo_health[device_key]['bounce_rate']
            current_engagement = seo_health[device_key]['engagement_rate']
            current_duration = seo_health[device_key]['avg_duration']

            seo_health[device_key]['bounce_rate'] = current_bounce * (1 - weight) + bounce_rate * weight
            seo_health[device_key]['engagement_rate'] = current_engagement * (1 - weight) + engagement_rate * weight
            seo_health[device_key]['avg_duration'] = current_duration * (1 - weight) + avg_duration * weight

        # Page-level health
        page_health[page_path] = {
            'device': device,
            'sessions': sessions,
            'bounce_rate': bounce_rate,
            'engagement_rate': engagement_rate,
            'avg_duration': avg_duration
        }

    print("📊 SEO HEALTH BY DEVICE:")
    print("   Device   | Sessions | Avg Duration | Bounce Rate | Engagement Rate")
    print("   ---------|----------|--------------|-------------|----------------")

    for device, data in seo_health.items():
        if data['sessions'] > 0:
            print("9")
    print()

    # SEO health assessment
    print("   🏥 SEO HEALTH ASSESSMENT:"    issues = []
    recommendations = []

    for device, data in seo_health.items():
        if data['sessions'] > 10:
            if data['bounce_rate'] > 0.65:
                issues.append(f"High bounce rate on {device} ({data['bounce_rate']:.1%})")
                recommendations.append(f"Improve {device} user experience and content relevance")
            if data['avg_duration'] < 30:
                issues.append(f"Short session duration on {device} ({data['avg_duration']:.1f}s)")
                recommendations.append(f"Enhance content engagement for {device} users")
            if data['engagement_rate'] < 0.4:
                issues.append(f"Low engagement on {device} ({data['engagement_rate']:.1%})")
                recommendations.append(f"Optimize content and calls-to-action for {device}")

    if issues:
        print("   Issues identified:")
        for issue in issues:
            print(f"   • {issue}")
        print()
        print("   Recommendations:")
        for rec in recommendations:
            print(f"   • {rec}")
    else:
        print("   ✅ No major SEO health issues detected")
    print()

    return {'device_health': seo_health, 'page_health': page_health}

def analyze_seo_performance(seo_type: str = "all", start_date: str = None, end_date: str = None):
    """Main function for SEO analysis"""

    print("🔍 SEO Analysis Tool")
    print("=" * 18)

    results = {}

    if seo_type in ["organic", "traffic", "all"]:
        results['organic'] = analyze_organic_traffic(start_date, end_date)

    if seo_type in ["keywords", "all"]:
        results['keywords'] = analyze_keyword_performance(start_date, end_date)

    if seo_type in ["health", "all"]:
        results['health'] = analyze_seo_health(start_date, end_date)

    # Export combined data
    if results:
        csv_data = []

        # Organic traffic data
        if 'organic' in results and results['organic']:
            for channel, data in results['organic']['channels'].items():
                csv_data.append({
                    'Analysis_Type': 'Organic_Traffic',
                    'Channel': channel,
                    'Page_Path': None,
                    'Users': data['users'],
                    'Sessions': data['sessions'],
                    'Pageviews': data['pageviews'],
                    'Avg_Duration': data['avg_duration'],
                    'Bounce_Rate': data['bounce_rate'],
                    'Engagement_Rate': data['engagement_rate'],
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

            # Organic pages
            for page, data in results['organic']['organic_pages'].items():
                csv_data.append({
                    'Analysis_Type': 'Organic_Pages',
                    'Channel': 'Organic Search',
                    'Page_Path': page,
                    'Users': data['users'],
                    'Sessions': data['sessions'],
                    'Pageviews': data['pageviews'],
                    'Avg_Duration': data['avg_duration'],
                    'Bounce_Rate': data['bounce_rate'],
                    'Engagement_Rate': data['engagement_rate'],
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

        # Keyword data
        if 'keywords' in results and results['keywords']:
            for theme, data in results['keywords'].items():
                csv_data.append({
                    'Analysis_Type': 'Keyword_Themes',
                    'Channel': theme,
                    'Page_Path': ', '.join(data['pages'][:3]),  # First 3 pages
                    'Users': data['users'],
                    'Sessions': data['sessions'],
                    'Pageviews': data['pageviews'],
                    'Avg_Duration': data['avg_duration'],
                    'Bounce_Rate': data['bounce_rate'],
                    'Engagement_Rate': None,
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

        # Health data
        if 'health' in results and results['health']:
            for device, data in results['health']['device_health'].items():
                csv_data.append({
                    'Analysis_Type': 'SEO_Health',
                    'Channel': device,
                    'Page_Path': None,
                    'Users': None,
                    'Sessions': data['sessions'],
                    'Pageviews': None,
                    'Avg_Duration': data['avg_duration'],
                    'Bounce_Rate': data['bounce_rate'],
                    'Engagement_Rate': data['engagement_rate'],
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_filename = get_report_filename("seo_analysis", f"{seo_type}_{start_date}_to_{end_date}")
            df.to_csv(csv_filename, index=False)
            print(f"📄 SEO analysis data exported to: {csv_filename}")

    return results

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        seo_type = sys.argv[1]
        days = int(sys.argv[2]) if len(sys.argv) >= 3 else 30

        print(f"SEO type: {seo_type}")
        print(f"Time period: Last {days} days")

        if days == 7:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
            analyze_seo_performance(seo_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        else:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=days-1)
            analyze_seo_performance(seo_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    else:
        print("Analyze search engine optimization performance")
        print()
        print("SEO types:")
        print("  organic    - Organic search traffic analysis")
        print("  keywords   - Keyword performance analysis")
        print("  health     - SEO health indicators")
        print("  all        - Complete SEO analysis")
        print()
        print("Usage: python seo_analysis.py <seo_type> [days]")
        print("Example: python seo_analysis.py all 30")
        exit(1)