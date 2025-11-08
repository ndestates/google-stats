"""
Social Media Timing Analysis Script
Analyze the best times to post on social media platforms based on organic traffic patterns

Usage:
    python social_media_timing.py [days]

Examples:
    python social_media_timing.py 30    # Last 30 days
    python social_media_timing.py 90    # Last 90 days
    python social_media_timing.py       # Default 30 days
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from collections import defaultdict
from google.analytics.data_v1beta.types import OrderBy

from src.config import REPORTS_DIR
from src.ga4_client import run_report, create_date_range, get_report_filename

def get_date_range(days_back: int = 30):
    """Get date range for analysis"""
    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=days_back - 1)  # N days back
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def categorize_social_source(source_medium: str) -> str:
    """Categorize social media sources into platform groups"""
    source_medium = source_medium.lower()

    # Facebook platforms
    if any(term in source_medium for term in ['facebook', 'fb', 'm.facebook', 'l.facebook']):
        return 'Facebook'

    # Google Social
    elif 'google.com / social' in source_medium:
        return 'Google Social'

    # Twitter/X
    elif any(term in source_medium for term in ['twitter', 'x.com', 't.co']):
        return 'Twitter/X'

    # Instagram
    elif 'instagram' in source_medium:
        return 'Instagram'

    # LinkedIn
    elif 'linkedin' in source_medium:
        return 'LinkedIn'

    # Pinterest
    elif 'pinterest' in source_medium:
        return 'Pinterest'

    # TikTok
    elif 'tiktok' in source_medium:
        return 'TikTok'

    # YouTube
    elif any(term in source_medium for term in ['youtube', 'youtu.be']):
        return 'YouTube'

    # Other social
    elif 'social' in source_medium:
        return 'Other Social'

    return 'Non-Social'

def is_social_source(source_medium: str) -> bool:
    """Check if a source is social media"""
    platform = categorize_social_source(source_medium)
    return platform != 'Non-Social'

def analyze_social_timing(days_back: int = 30):
    """Analyze social media traffic timing patterns"""

    start_date, end_date = get_date_range(days_back)

    print("📊 Analyzing Social Media Timing Patterns")
    print(f"   Date range: {start_date} to {end_date} ({days_back} days)")
    print("=" * 80)

    # Get all traffic data with hourly breakdown
    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["hour", "sessionSourceMedium", "sessionDefaultChannelGrouping"],
        metrics=["totalUsers", "newUsers", "sessions", "engagedSessions", "screenPageViews",
                "averageSessionDuration", "bounceRate", "engagementRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="hour"), desc=False)
        ],
        limit=50000,
    )

    if response.row_count == 0:
        print("❌ No data found for the specified date range.")
        return None

    print(f"✅ Retrieved {response.row_count} total hour-source combinations")

    # Process data by platform and hour
    platform_hourly_data = defaultdict(lambda: defaultdict(lambda: {
        'total_users': 0,
        'new_users': 0,
        'sessions': 0,
        'engaged_sessions': 0,
        'pageviews': 0,
        'avg_session_duration': 0,
        'bounce_rate': 0,
        'engagement_rate': 0,
        'data_points': 0
    }))

    for row in response.rows:
        hour = int(row.dimension_values[0].value)
        source_medium = row.dimension_values[1].value
        channel_grouping = row.dimension_values[2].value

        # Only process social media sources
        if not is_social_source(source_medium):
            continue

        platform = categorize_social_source(source_medium)

        # Aggregate metrics
        data = platform_hourly_data[platform][hour]
        data['total_users'] += int(row.metric_values[0].value)
        data['new_users'] += int(row.metric_values[1].value)
        data['sessions'] += int(row.metric_values[2].value)
        data['engaged_sessions'] += int(row.metric_values[3].value)
        data['pageviews'] += int(row.metric_values[4].value)
        data['avg_session_duration'] += float(row.metric_values[5].value)
        data['bounce_rate'] += float(row.metric_values[6].value)
        data['engagement_rate'] += float(row.metric_values[7].value)
        data['data_points'] += 1

    # Calculate averages and prepare final data
    results = []
    for platform, hourly_data in platform_hourly_data.items():
        for hour in range(24):  # Ensure all hours are represented
            data = hourly_data.get(hour, {
                'total_users': 0, 'new_users': 0, 'sessions': 0, 'engaged_sessions': 0,
                'pageviews': 0, 'avg_session_duration': 0, 'bounce_rate': 0,
                'engagement_rate': 0, 'data_points': 0
            })

            if data['data_points'] > 0:
                # Calculate averages for rates
                data['avg_session_duration'] /= data['data_points']
                data['bounce_rate'] /= data['data_points']
                data['engagement_rate'] /= data['data_points']

            results.append({
                'Platform': platform,
                'Hour': hour,
                'Hour_Display': f"{hour:02d}:00",
                'Total_Users': data['total_users'],
                'New_Users': data['new_users'],
                'Sessions': data['sessions'],
                'Engaged_Sessions': data['engaged_sessions'],
                'Pageviews': data['pageviews'],
                'Avg_Session_Duration': round(data['avg_session_duration'], 2),
                'Bounce_Rate': round(data['bounce_rate'], 4),
                'Engagement_Rate': round(data['engagement_rate'], 4),
                'Data_Points': data['data_points']
            })

    if not results:
        print("❌ No social media traffic found in the specified date range.")
        return None

    # Convert to DataFrame and sort
    df = pd.DataFrame(results)

    # Calculate platform totals and best hours
    platform_summary = []
    for platform in df['Platform'].unique():
        platform_df = df[df['Platform'] == platform].copy()

        # Calculate engagement score (weighted combination of metrics)
        platform_df['Engagement_Score'] = (
            platform_df['Engagement_Rate'] * 0.4 +
            (1 - platform_df['Bounce_Rate']) * 0.3 +
            (platform_df['Avg_Session_Duration'] / platform_df['Avg_Session_Duration'].max()) * 0.3
        )

        # Find best hours
        best_hours = platform_df.nlargest(3, 'Engagement_Score')[['Hour', 'Hour_Display', 'Engagement_Score', 'Total_Users', 'Engagement_Rate']]

        platform_summary.append({
            'Platform': platform,
            'Total_Users': platform_df['Total_Users'].sum(),
            'Total_Sessions': platform_df['Sessions'].sum(),
            'Avg_Engagement_Rate': platform_df['Engagement_Rate'].mean(),
            'Best_Hour_1': best_hours.iloc[0]['Hour_Display'] if len(best_hours) > 0 else 'N/A',
            'Best_Hour_2': best_hours.iloc[1]['Hour_Display'] if len(best_hours) > 1 else 'N/A',
            'Best_Hour_3': best_hours.iloc[2]['Hour_Display'] if len(best_hours) > 2 else 'N/A',
            'Best_Hour_1_Score': round(best_hours.iloc[0]['Engagement_Score'], 3) if len(best_hours) > 0 else 0,
            'Best_Hour_2_Score': round(best_hours.iloc[1]['Engagement_Score'], 3) if len(best_hours) > 1 else 0,
            'Best_Hour_3_Score': round(best_hours.iloc[2]['Engagement_Score'], 3) if len(best_hours) > 2 else 0,
        })

    summary_df = pd.DataFrame(platform_summary)

    # Sort platforms by total users
    df = df.sort_values(['Platform', 'Hour'])
    summary_df = summary_df.sort_values('Total_Users', ascending=False)

    # Generate filename and save
    filename = get_report_filename(f"social_media_timing_{start_date}_to_{end_date}")
    df.to_csv(filename, index=False)

    summary_filename = get_report_filename(f"social_media_timing_summary_{start_date}_to_{end_date}")
    summary_df.to_csv(summary_filename, index=False)

    print(f"✅ Analysis complete!")
    print(f"   Detailed report: {filename}")
    print(f"   Summary report: {summary_filename}")
    print()

    # Display summary
    print("📈 Social Media Timing Summary:")
    print("=" * 80)
    for _, row in summary_df.iterrows():
        print(f"🏆 {row['Platform']}")
        print(f"   Total Users: {row['Total_Users']:,}")
        print(f"   Best Posting Times: {row['Best_Hour_1']}, {row['Best_Hour_2']}, {row['Best_Hour_3']}")
        print(f"   Avg Engagement: {row['Avg_Engagement_Rate']:.1%}")
        print()

    return filename, summary_filename

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid number of days. Using default (30).")
            days_back = 30
    else:
        days_back = 30

    analyze_social_timing(days_back)

if __name__ == "__main__":
    main()