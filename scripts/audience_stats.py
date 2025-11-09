"""
Google Analytics 4 Audience Statistics Script
Get user counts and performance metrics for GA4 audiences using the Data API
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

# Add the parent directory to sys.path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import REPORTS_DIR
from src.ga4_client import run_report, create_date_range, get_report_filename
from google.analytics.data_v1beta.types import OrderBy
import pandas as pd


def get_audience_performance_stats(days: int = 30):
    """Get performance statistics for all audiences over the specified period"""

    # Calculate date range
    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=days-1)  # Period back

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print(f"📊 Analyzing GA4 Audience Performance: {start_str} to {end_str}")
    print("=" * 80)

    # Get audience performance data
    date_range = create_date_range(start_str, end_str)

    response = run_report(
        dimensions=["audienceId", "audienceName"],
        metrics=[
            "totalUsers",
            "sessions",
            "screenPageViews",
            "averageSessionDuration",
            "bounceRate",
            "newUsers",
            "engagedSessions"
        ],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=1000,
    )

    if response.row_count == 0:
        print("❌ No audience data found for the specified period.")
        print("This could mean:")
        print("  - No audiences have been created yet")
        print("  - Audiences exist but have no users in this time period")
        print("  - Audience data is not available due to privacy thresholds")
        return None

    print(f"✅ Found {response.row_count} audience entries")

    # Process the data
    audience_stats = []

    for row in response.rows:
        audience_id = row.dimension_values[0].value
        audience_name = row.dimension_values[1].value

        # Handle potential missing metrics
        def safe_int(value, default=0):
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return default

        def safe_float(value, default=0.0):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        stats = {
            'audience_id': audience_id,
            'audience_name': audience_name,
            'total_users': safe_int(row.metric_values[0].value),
            'sessions': safe_int(row.metric_values[1].value),
            'pageviews': safe_int(row.metric_values[2].value),
            'avg_session_duration': safe_float(row.metric_values[3].value),
            'bounce_rate': safe_float(row.metric_values[4].value),
            'new_users': safe_int(row.metric_values[5].value),
            'engaged_sessions': safe_int(row.metric_values[6].value),
            'period_days': days,
            'start_date': start_str,
            'end_date': end_str
        }

        # Calculate derived metrics
        if stats['sessions'] > 0:
            stats['pages_per_session'] = round(stats['pageviews'] / stats['sessions'], 2)
            stats['engagement_rate'] = round((stats['engaged_sessions'] / stats['sessions']) * 100, 2)
        else:
            stats['pages_per_session'] = 0
            stats['engagement_rate'] = 0

        if stats['total_users'] > 0:
            stats['new_user_percentage'] = round((stats['new_users'] / stats['total_users']) * 100, 2)
        else:
            stats['new_user_percentage'] = 0

        audience_stats.append(stats)

    # Display results
    print(f"\n🏆 GA4 AUDIENCE PERFORMANCE REPORT ({start_str} to {end_str})")
    print("=" * 120)

    for i, audience in enumerate(audience_stats[:20], 1):  # Show top 20 audiences
        print(f"\n{i}. {audience['audience_name']} (ID: {audience['audience_id']})")
        print(f"   Users: {audience['total_users']:,}")
        print(f"   Sessions: {audience['sessions']:,}")
        print(f"   Pageviews: {audience['pageviews']:,}")
        print(f"   New Users: {audience['new_users']:,} ({audience['new_user_percentage']}%)")
        print(f"   Avg Session Duration: {audience['avg_session_duration']:.1f}s")
        print(f"   Bounce Rate: {audience['bounce_rate']:.1%}")
        print(f"   Pages/Session: {audience['pages_per_session']}")
        print(f"   Engagement Rate: {audience['engagement_rate']}%")

    # Summary statistics
    print(f"\n{'='*120}")
    print("📈 AUDIENCE PORTFOLIO SUMMARY:")

    total_users = sum(a['total_users'] for a in audience_stats)
    total_sessions = sum(a['sessions'] for a in audience_stats)
    total_pageviews = sum(a['pageviews'] for a in audience_stats)

    print(f"• Total Audiences: {len(audience_stats)}")
    print(f"• Total Users Across All Audiences: {total_users:,}")
    print(f"• Total Sessions: {total_sessions:,}")
    print(f"• Total Pageviews: {total_pageviews:,}")

    if total_sessions > 0:
        avg_bounce_rate = sum(a['bounce_rate'] for a in audience_stats) / len(audience_stats)
        avg_pages_per_session = total_pageviews / total_sessions
        print(f"• Average Bounce Rate: {avg_bounce_rate:.1%}")
        print(f"• Average Pages per Session: {avg_pages_per_session:.2f}")

    # Performance insights
    print(f"\n💡 PERFORMANCE INSIGHTS:")

    # Find best performing audiences
    if audience_stats:
        best_users = max(audience_stats, key=lambda x: x['total_users'])
        best_engagement = max(audience_stats, key=lambda x: x['engagement_rate'])
        lowest_bounce = min(audience_stats, key=lambda x: x['bounce_rate'])

        print(f"• Largest Audience: '{best_users['audience_name']}' with {best_users['total_users']:,} users")
        print(f"• Most Engaged: '{best_engagement['audience_name']}' with {best_engagement['engagement_rate']}% engagement")
        print(f"• Lowest Bounce: '{lowest_bounce['audience_name']}' with {lowest_bounce['bounce_rate']:.1%} bounce rate")

    # Export to CSV
    if audience_stats:
        df = pd.DataFrame(audience_stats)
        csv_filename = get_report_filename("audience_stats", f"{start_str}_to_{end_str}")
        df.to_csv(csv_filename, index=False)
        print(f"\n📄 Detailed audience stats exported to: {csv_filename}")

    return audience_stats


def main():
    parser = argparse.ArgumentParser(description='GA4 Audience Statistics Analysis')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days to analyze (default: 30)')
    parser.add_argument('--output', choices=['console', 'csv', 'both'], default='both',
                       help='Output format (default: both)')

    args = parser.parse_args()

    try:
        stats = get_audience_performance_stats(args.days)

        if not stats:
            print("\n❌ No audience data available.")
            return

        print(f"\n✅ Successfully analyzed {len(stats)} audiences!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return


if __name__ == "__main__":
    main()
