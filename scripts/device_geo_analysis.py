"""
Device & Geographic Analysis Script
Analyze website performance by device type and geographic location

Usage:
    python device_geo_analysis.py [analysis_type] [days]

Examples:
    python device_geo_analysis.py device 30
    python device_geo_analysis.py geo 7
    python device_geo_analysis.py all 90
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

def analyze_device_performance(start_date: str = None, end_date: str = None):
    """Analyze website performance by device type"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("📱 Analyzing device performance...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["deviceCategory", "operatingSystem", "browser"],
        metrics=["totalUsers", "sessions", "screenPageViews", "bounceRate", "averageSessionDuration", "engagementRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=50
    )

    if response.row_count == 0:
        print("❌ No device data found for the date range.")
        return None

    # Organize data by device category
    device_data = {}
    total_users = 0
    total_sessions = 0

    for row in response.rows:
        device_category = row.dimension_values[0].value
        os = row.dimension_values[1].value
        browser = row.dimension_values[2].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        bounce_rate = float(row.metric_values[3].value)
        avg_duration = float(row.metric_values[4].value)
        engagement_rate = float(row.metric_values[5].value)

        if device_category not in device_data:
            device_data[device_category] = {
                'total_users': 0,
                'total_sessions': 0,
                'total_pageviews': 0,
                'avg_bounce_rate': 0,
                'avg_duration': 0,
                'avg_engagement': 0,
                'os_breakdown': {},
                'browser_breakdown': {}
            }

        device_data[device_category]['total_users'] += users
        device_data[device_category]['total_sessions'] += sessions
        device_data[device_category]['total_pageviews'] += pageviews

        # Weighted averages
        weight = sessions / (device_data[device_category]['total_sessions'] + sessions)
        current_bounce = device_data[device_category]['avg_bounce_rate']
        current_duration = device_data[device_category]['avg_duration']
        current_engagement = device_data[device_category]['avg_engagement']

        device_data[device_category]['avg_bounce_rate'] = current_bounce * (1 - weight) + bounce_rate * weight
        device_data[device_category]['avg_duration'] = current_duration * (1 - weight) + avg_duration * weight
        device_data[device_category]['avg_engagement'] = current_engagement * (1 - weight) + engagement_rate * weight

        # OS and browser breakdown
        if os not in device_data[device_category]['os_breakdown']:
            device_data[device_category]['os_breakdown'][os] = 0
        device_data[device_category]['os_breakdown'][os] += users

        if browser not in device_data[device_category]['browser_breakdown']:
            device_data[device_category]['browser_breakdown'][browser] = 0
        device_data[device_category]['browser_breakdown'][browser] += users

        total_users += users
        total_sessions += sessions

    # Display device analysis
    print("📊 DEVICE PERFORMANCE ANALYSIS:"    print(f"   Total Users: {total_users:,}")
    print(f"   Total Sessions: {total_sessions:,}")
    print()

    print("   Device Category    | Users    | Sessions | Pageviews | Bounce Rate | Avg Duration | Engagement")
    print("   -------------------|----------|----------|-----------|-------------|--------------|-----------")

    for device, data in sorted(device_data.items(), key=lambda x: x[1]['total_users'], reverse=True):
        print("19")
    print()

    # Detailed OS and browser breakdown
    for device, data in device_data.items():
        print(f"📱 {device.upper()} DETAILS:"        print("   Operating Systems:")
        for os, users in sorted(data['os_breakdown'].items(), key=lambda x: x[1], reverse=True)[:5]:
            percentage = users / data['total_users'] * 100
            print("25")

        print("   Browsers:")
        for browser, users in sorted(data['browser_breakdown'].items(), key=lambda x: x[1], reverse=True)[:5]:
            percentage = users / data['total_users'] * 100
            print("25")
        print()

    # Device optimization recommendations
    print("💡 DEVICE OPTIMIZATION RECOMMENDATIONS:"    mobile_users = device_data.get('mobile', {}).get('total_users', 0)
    desktop_users = device_data.get('desktop', {}).get('total_users', 0)

    if mobile_users > desktop_users:
        print("   • Mobile is your primary device - ensure mobile-first design")
        print("   • Test touch interactions and mobile form usability")
        print("   • Optimize page load speed for mobile networks")
    else:
        print("   • Desktop is primary - focus on desktop user experience")
        print("   • Ensure large screens are well utilized")
        print("   • Consider progressive web app features")

    # Check for device-specific issues
    for device, data in device_data.items():
        if data['avg_bounce_rate'] > 0.8:
            print(f"   • High bounce rate on {device} devices - investigate UX issues")
        if data['avg_duration'] < 30:  # Less than 30 seconds
            print(f"   • Very short sessions on {device} devices - content may not be engaging")
    print()

    return device_data

def analyze_geographic_performance(start_date: str = None, end_date: str = None):
    """Analyze website performance by geographic location"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("🌍 Analyzing geographic performance...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["country", "region", "city"],
        metrics=["totalUsers", "sessions", "screenPageViews", "bounceRate", "averageSessionDuration"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=100
    )

    if response.row_count == 0:
        print("❌ No geographic data found for the date range.")
        return None

    # Organize data by country and region
    geo_data = {}
    total_users = 0

    for row in response.rows:
        country = row.dimension_values[0].value
        region = row.dimension_values[1].value
        city = row.dimension_values[2].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        bounce_rate = float(row.metric_values[3].value)
        avg_duration = float(row.metric_values[4].value)

        if country not in geo_data:
            geo_data[country] = {
                'total_users': 0,
                'total_sessions': 0,
                'total_pageviews': 0,
                'avg_bounce_rate': 0,
                'avg_duration': 0,
                'regions': {}
            }

        geo_data[country]['total_users'] += users
        geo_data[country]['total_sessions'] += sessions
        geo_data[country]['total_pageviews'] += pageviews

        # Weighted averages for country
        weight = users / (geo_data[country]['total_users'] + users)
        current_bounce = geo_data[country]['avg_bounce_rate']
        current_duration = geo_data[country]['avg_duration']

        geo_data[country]['avg_bounce_rate'] = current_bounce * (1 - weight) + bounce_rate * weight
        geo_data[country]['avg_duration'] = current_duration * (1 - weight) + avg_duration * weight

        # Region data
        if region not in geo_data[country]['regions']:
            geo_data[country]['regions'][region] = {
                'users': 0, 'sessions': 0, 'pageviews': 0, 'cities': {}
            }

        geo_data[country]['regions'][region]['users'] += users
        geo_data[country]['regions'][region]['sessions'] += sessions
        geo_data[country]['regions'][region]['pageviews'] += pageviews

        # City data
        if city not in geo_data[country]['regions'][region]['cities']:
            geo_data[country]['regions'][region]['cities'][city] = {
                'users': users, 'sessions': sessions, 'pageviews': pageviews
            }

        total_users += users

    # Display geographic analysis
    print("🌍 GEOGRAPHIC PERFORMANCE ANALYSIS:"    print(f"   Total Users: {total_users:,}")
    print(f"   Countries: {len(geo_data)}")
    print()

    print("   Country              | Users    | Sessions | Pageviews | Bounce Rate | Avg Duration")
    print("   ---------------------|----------|----------|-----------|-------------|-------------")

    for country, data in sorted(geo_data.items(), key=lambda x: x[1]['total_users'], reverse=True)[:10]:
        country_display = country[:20] + "..." if len(country) > 20 else country
        print("21")
    print()

    # Top regions for top countries
    top_countries = sorted(geo_data.items(), key=lambda x: x[1]['total_users'], reverse=True)[:3]
    for country, data in top_countries:
        print(f"📍 TOP REGIONS IN {country.upper()}:"        regions = sorted(data['regions'].items(), key=lambda x: x[1]['users'], reverse=True)[:5]
        for region, region_data in regions:
            region_display = region[:25] + "..." if len(region) > 25 else region
            print("30")
        print()

    # Geographic insights and recommendations
    print("💡 GEOGRAPHIC OPTIMIZATION RECOMMENDATIONS:"    # Language and localization
    top_country = max(geo_data.items(), key=lambda x: x[1]['total_users'])[0]
    if top_country != "United States":
        print(f"   • Consider localizing content for {top_country} market")
        print("   • Check if language barriers exist")
        print("   • Research local search preferences")

    # Time zone considerations
    international_users = sum(data['total_users'] for country, data in geo_data.items() if country != "United States")
    if international_users / total_users > 0.3:  # Over 30% international
        print("   • Significant international traffic - consider global SEO")
        print("   • Optimize for different time zones")
        print("   • Consider hreflang tags for multi-language sites")

    # Regional targeting
    for country, data in geo_data.items():
        if data['avg_bounce_rate'] > 0.8 and data['total_users'] > 100:
            print(f"   • High bounce rate in {country} - investigate regional preferences")
    print()

    return geo_data

def analyze_device_geo(analysis_type: str = "all", start_date: str = None, end_date: str = None):
    """Main function to analyze device and/or geographic performance"""

    print("📊 Device & Geographic Analysis Tool")
    print("=" * 50)

    results = {}

    if analysis_type in ["device", "all"]:
        results['device'] = analyze_device_performance(start_date, end_date)

    if analysis_type in ["geo", "all"]:
        results['geo'] = analyze_geographic_performance(start_date, end_date)

    # Export combined data
    if results:
        csv_data = []

        # Device data
        if 'device' in results and results['device']:
            for device, data in results['device'].items():
                csv_data.append({
                    'Analysis_Type': 'Device',
                    'Category': device,
                    'Users': data['total_users'],
                    'Sessions': data['total_sessions'],
                    'Pageviews': data['total_pageviews'],
                    'Bounce_Rate': data['avg_bounce_rate'],
                    'Avg_Duration': data['avg_duration'],
                    'Engagement_Rate': data['avg_engagement'],
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

        # Geographic data
        if 'geo' in results and results['geo']:
            for country, data in results['geo'].items():
                csv_data.append({
                    'Analysis_Type': 'Geography',
                    'Category': country,
                    'Users': data['total_users'],
                    'Sessions': data['total_sessions'],
                    'Pageviews': data['total_pageviews'],
                    'Bounce_Rate': data['avg_bounce_rate'],
                    'Avg_Duration': data['avg_duration'],
                    'Engagement_Rate': None,
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_filename = get_report_filename("device_geo_analysis", f"{analysis_type}_{start_date}_to_{end_date}")
            df.to_csv(csv_filename, index=False)
            print(f"📄 Combined analysis data exported to: {csv_filename}")

    return results

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        analysis_type = sys.argv[1]
        days = int(sys.argv[2]) if len(sys.argv) >= 3 else 30

        print(f"Analysis type: {analysis_type}")
        print(f"Time period: Last {days} days")

        if days == 7:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
            analyze_device_geo(analysis_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        else:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=days-1)
            analyze_device_geo(analysis_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    else:
        print("Analyze device and geographic performance")
        print()
        print("Analysis types:")
        print("  device  - Device type analysis only")
        print("  geo     - Geographic analysis only")
        print("  all     - Both device and geographic analysis")
        print()
        print("Usage: python device_geo_analysis.py <analysis_type> [days]")
        print("Example: python device_geo_analysis.py all 30")
        exit(1)