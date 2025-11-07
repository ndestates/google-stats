"""
Bounce Rate Analysis Script
Identify pages with high bounce rates and provide optimization recommendations

Usage:
    python bounce_rate_analysis.py [threshold] [days]

Examples:
    python bounce_rate_analysis.py 0.7 30
    python bounce_rate_analysis.py 0.5 7
    python bounce_rate_analysis.py 0.8 90
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

def analyze_bounce_rates(threshold: float = 0.7, start_date: str = None, end_date: str = None):
    """Analyze bounce rates and identify problematic pages"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print(f"🔍 Analyzing bounce rates (threshold: {threshold*100:.0f}%)")
    print(f"   Date range: {start_date} to {end_date}")
    print("=" * 120)

    date_range = create_date_range(start_date, end_date)

    # Get page-level bounce rate data
    response = run_report(
        dimensions=["pagePath", "pageTitle", "sessionDefaultChannelGrouping"],
        metrics=["screenPageViews", "sessions", "totalUsers", "bounceRate", "averageSessionDuration", "exitRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="bounceRate"), desc=True)
        ],
        limit=100
    )

    if response.row_count == 0:
        print("❌ No page data found for the date range.")
        return None

    print(f"✅ Retrieved {response.row_count} pages with bounce rate data")

    # Categorize pages by bounce rate
    high_bounce_pages = []
    medium_bounce_pages = []
    low_bounce_pages = []

    total_pageviews = 0
    total_sessions = 0

    for row in response.rows:
        page_path = row.dimension_values[0].value
        page_title = row.dimension_values[1].value
        channel = row.dimension_values[2].value
        pageviews = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        users = int(row.metric_values[2].value)
        bounce_rate = float(row.metric_values[3].value)
        avg_duration = float(row.metric_values[4].value)
        exit_rate = float(row.metric_values[5].value)

        total_pageviews += pageviews
        total_sessions += sessions

        page_data = {
            'page_path': page_path,
            'page_title': page_title,
            'channel': channel,
            'pageviews': pageviews,
            'sessions': sessions,
            'users': users,
            'bounce_rate': bounce_rate,
            'avg_duration': avg_duration,
            'exit_rate': exit_rate
        }

        if bounce_rate >= threshold:
            high_bounce_pages.append(page_data)
        elif bounce_rate >= threshold * 0.7:  # Medium threshold
            medium_bounce_pages.append(page_data)
        else:
            low_bounce_pages.append(page_data)

    # Display summary
    print("
📊 BOUNCE RATE SUMMARY:"    print(f"   Total Pages Analyzed: {response.row_count}")
    print(f"   Total Pageviews: {total_pageviews:,}")
    print(f"   Total Sessions: {total_sessions:,}")
    print(f"   High Bounce Pages (≥{threshold*100:.0f}%): {len(high_bounce_pages)}")
    print(f"   Medium Bounce Pages ({threshold*70:.0f}%-{threshold*100:.0f}%): {len(medium_bounce_pages)}")
    print(f"   Low Bounce Pages (<{threshold*70:.0f}%): {len(low_bounce_pages)}")
    print()

    # Display high bounce rate pages
    if high_bounce_pages:
        print(f"🚨 HIGH BOUNCE RATE PAGES (≥{threshold*100:.0f}%):"        print("   Page Path                    | Title                     | Channel    | Views | Sessions | Bounce | Duration | Exit")
        print("   -----------------------------|---------------------------|------------|-------|----------|--------|----------|------")

        for page in high_bounce_pages[:15]:  # Show top 15
            path_display = page['page_path'][:28] + "..." if len(page['page_path']) > 28 else page['page_path']
            title_display = page['page_title'][:25] + "..." if len(page['page_title']) > 25 else page['page_title']
            channel_display = page['channel'][:10]

            print("28")
        print()

        # Provide recommendations for high bounce pages
        print("💡 RECOMMENDATIONS FOR HIGH BOUNCE PAGES:"        print("   1. Content Quality:")
        print("      • Review page content - is it relevant to user search intent?")
        print("      • Check for broken links, images, or formatting issues")
        print("      • Ensure page load speed is optimal (<3 seconds)")
        print()
        print("   2. User Experience:")
        print("      • Improve navigation and internal linking")
        print("      • Add clear calls-to-action (CTAs)")
        print("      • Consider mobile responsiveness issues")
        print()
        print("   3. Technical Issues:")
        print("      • Check for JavaScript errors or console warnings")
        print("      • Verify tracking code implementation")
        print("      • Test forms and interactive elements")
        print()

    # Analyze bounce rates by channel
    channel_bounce_rates = {}
    for row in response.rows:
        channel = row.dimension_values[2].value
        bounce_rate = float(row.metric_values[3].value)
        sessions = int(row.metric_values[1].value)

        if channel not in channel_bounce_rates:
            channel_bounce_rates[channel] = {'total_bounce': 0, 'total_sessions': 0, 'page_count': 0}

        channel_bounce_rates[channel]['total_bounce'] += bounce_rate * sessions
        channel_bounce_rates[channel]['total_sessions'] += sessions
        channel_bounce_rates[channel]['page_count'] += 1

    print("📈 BOUNCE RATES BY TRAFFIC CHANNEL:"    print("   Channel              | Avg Bounce Rate | Total Sessions | Pages")
    print("   ---------------------|-----------------|---------------|-------")

    for channel, data in sorted(channel_bounce_rates.items(), key=lambda x: x[1]['total_sessions'], reverse=True):
        avg_bounce = data['total_bounce'] / data['total_sessions'] if data['total_sessions'] > 0 else 0
        print("21")
    print()

    # Time-based bounce analysis (if we can get hourly data)
    print("⏰ BOUNCE RATE PATTERNS:"    print("   💡 Bounce rates often vary by:")
    print("      • Time of day (business hours vs off-hours)")
    print("      • Day of week (weekdays vs weekends)")
    print("      • Traffic source quality")
    print("      • Device type (mobile vs desktop)")
    print()

    # Export detailed data
    csv_data = []
    for row in response.rows:
        csv_data.append({
            'Page_Path': row.dimension_values[0].value,
            'Page_Title': row.dimension_values[1].value,
            'Channel': row.dimension_values[2].value,
            'Pageviews': int(row.metric_values[0].value),
            'Sessions': int(row.metric_values[1].value),
            'Users': int(row.metric_values[2].value),
            'Bounce_Rate': float(row.metric_values[3].value),
            'Avg_Session_Duration': float(row.metric_values[4].value),
            'Exit_Rate': float(row.metric_values[5].value),
            'Bounce_Category': 'High' if float(row.metric_values[3].value) >= threshold else 'Medium' if float(row.metric_values[3].value) >= threshold * 0.7 else 'Low',
            'Date_Range': f"{start_date}_to_{end_date}"
        })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename("bounce_rate_analysis", f"threshold_{int(threshold*100)}_{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"📄 Detailed data exported to: {csv_filename}")

    return {
        'high_bounce_pages': high_bounce_pages,
        'medium_bounce_pages': medium_bounce_pages,
        'low_bounce_pages': low_bounce_pages,
        'channel_analysis': channel_bounce_rates,
        'total_pages': response.row_count,
        'total_pageviews': total_pageviews
    }

if __name__ == "__main__":
    print("📈 Bounce Rate Analysis Tool")
    print("=" * 40)

    if len(sys.argv) >= 2:
        threshold = float(sys.argv[1])
        days = int(sys.argv[2]) if len(sys.argv) >= 3 else 30

        print(f"Analyzing bounce rates above: {threshold*100:.0f}%")
        print(f"Time period: Last {days} days")

        if days == 7:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
            analyze_bounce_rates(threshold, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        else:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=days-1)
            analyze_bounce_rates(threshold, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    else:
        print("Analyze bounce rates and identify pages needing optimization")
        print()
        print("Bounce rate thresholds:")
        print("  0.5 - 50% (moderate bounce rate)")
        print("  0.7 - 70% (high bounce rate)")
        print("  0.8 - 80% (very high bounce rate)")
        print()
        print("Usage: python bounce_rate_analysis.py <threshold> [days]")
        print("Example: python bounce_rate_analysis.py 0.7 30")
        exit(1)