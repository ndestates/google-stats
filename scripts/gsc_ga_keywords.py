"""
Google Search Console + Google Analytics 4 Keywords Analysis
Combines GSC keyword data with GA4 page performance metrics
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta.types import OrderBy

from src.config import REPORTS_DIR, GSC_SITE_URL, get_gsc_client
from src.ga4_client import run_report, create_date_range, get_report_filename

def get_last_30_days_range():
    """Get date range for the last 30 days"""
    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=29)  # 30 days back
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def get_gsc_keywords_data(start_date: str, end_date: str, row_limit: int = 1000):
    """Fetch keyword data from Google Search Console"""
    print("🔍 Fetching Google Search Console keyword data...")

    try:
        gsc_client = get_gsc_client()
    except (ValueError, FileNotFoundError) as e:
        if any(keyword in str(e) for keyword in ["GSC_SITE_URL", "GSC_KEY_PATH", "key not found"]):
            print("⚠️  GSC not configured. Skipping GSC data fetch.")
            print("💡 To enable GSC integration, follow the setup instructions above.")
            return []
        raise

    request_body = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['query', 'page'],
        'rowLimit': row_limit
    }

    try:
        response = gsc_client.searchanalytics().query(
            siteUrl=GSC_SITE_URL,
            body=request_body
        ).execute()

        keywords_data = []
        if 'rows' in response:
            for row in response['rows']:
                # Extract page path and remove domain if present
                full_page_url = row['keys'][1]
                page_path = full_page_url.replace('https://www.ndestates.com', '').replace('http://www.ndestates.com', '')
                if not page_path.startswith('/'):
                    page_path = '/' + page_path

                keywords_data.append({
                    'keyword': row['keys'][0],
                    'page': page_path,  # Store cleaned page path
                    'full_url': full_page_url,  # Keep original for display
                    'clicks': row.get('clicks', 0),
                    'impressions': row.get('impressions', 0),
                    'ctr': row.get('ctr', 0),
                    'position': row.get('position', 0)
                })

        print(f"✅ Retrieved {len(keywords_data)} GSC keyword records")
        return keywords_data

    except Exception as e:
        print(f"❌ Error fetching GSC data: {e}")
        return []

def get_ga4_page_data(start_date: str, end_date: str):
    """Fetch page performance data from Google Analytics 4"""
    print("📊 Fetching Google Analytics 4 page data...")

    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=["pagePath"],
        metrics=["totalUsers", "sessions", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)
        ],
        limit=5000,
    )

    if response.row_count == 0:
        print("❌ No GA4 data found for the date range.")
        return []

    pages_data = []
    for row in response.rows:
        pages_data.append({
            'page': row.dimension_values[0].value,
            'ga_users': int(row.metric_values[0].value),
            'ga_sessions': int(row.metric_values[1].value),
            'ga_pageviews': int(row.metric_values[2].value),
            'ga_avg_session_duration': float(row.metric_values[3].value),
            'ga_bounce_rate': float(row.metric_values[4].value)
        })

    print(f"✅ Retrieved {len(pages_data)} GA4 page records")
    return pages_data

def generate_keywords_insights_report(start_date: str = None, end_date: str = None):
    """Generate comprehensive keywords insights report combining GSC and GA4 data"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print(f"🔗 Generating Keywords Insights Report for {start_date} to {end_date}")
    print("=" * 80)

    # Fetch data from both sources
    gsc_data = get_gsc_keywords_data(start_date, end_date)
    ga4_data = get_ga4_page_data(start_date, end_date)

    if not gsc_data and not ga4_data:
        print("❌ No data available from GSC or GA4. Cannot generate report.")
        return

    if not gsc_data:
        print("⚠️  No GSC keyword data available. Showing GA4 page data only.")
        # Create a basic structure for pages without keywords
        df_ga4 = pd.DataFrame(ga4_data)
        df_ga4['keyword'] = 'N/A (Direct/Other traffic)'
        df_ga4['clicks'] = 0
        df_ga4['impressions'] = 0
        df_ga4['ctr'] = 0.0
        df_ga4['position'] = 0.0
        merged_df = df_ga4
    elif not ga4_data:
        print("⚠️  No GA4 page data available. Showing GSC keyword data only.")
        df_gsc = pd.DataFrame(gsc_data)
        df_gsc['ga_users'] = 0
        df_gsc['ga_sessions'] = 0
        df_gsc['ga_pageviews'] = 0
        df_gsc['ga_avg_session_duration'] = 0.0
        df_gsc['ga_bounce_rate'] = 0.0
        merged_df = df_gsc
    else:
        # Convert to DataFrames and merge
        df_gsc = pd.DataFrame(gsc_data)
        df_ga4 = pd.DataFrame(ga4_data)

        # Merge on page path
        merged_df = df_gsc.merge(df_ga4, left_on='page', right_on='page', how='left')

        # Fill NaN values for pages without GA4 data
        merged_df['ga_users'] = merged_df['ga_users'].fillna(0).astype(int)
        merged_df['ga_sessions'] = merged_df['ga_sessions'].fillna(0).astype(int)
        merged_df['ga_pageviews'] = merged_df['ga_pageviews'].fillna(0).astype(int)
        merged_df['ga_avg_session_duration'] = merged_df['ga_avg_session_duration'].fillna(0).astype(float)
        merged_df['ga_bounce_rate'] = merged_df['ga_bounce_rate'].fillna(0).astype(float)

    # Calculate additional metrics
    merged_df['conversion_rate'] = (merged_df['ga_users'] / merged_df['clicks']).fillna(0)
    merged_df['engagement_score'] = (
        (merged_df['ga_users'] * 0.3) +
        (merged_df['ga_sessions'] * 0.2) +
        ((1 - merged_df['ga_bounce_rate']) * 100 * 0.2) +
        (merged_df['ga_avg_session_duration'] * 0.3)
    )

    # Sort by engagement score (descending)
    merged_df = merged_df.sort_values('engagement_score', ascending=False)

    # Display top insights
    print(f"\n🔍 TOP KEYWORD INSIGHTS ({start_date} to {end_date})")
    print("=" * 100)

    top_keywords = merged_df.head(20)
    for i, (_, row) in enumerate(top_keywords.iterrows(), 1):
        # Use full URL for display if available, otherwise use page path
        display_url = row.get('full_url', row['page'])
        print(f"\n{i}. Keyword: '{row['keyword']}'")
        print(f"   Page: {display_url}")
        print(f"   GSC: {row['clicks']:,} clicks, {row['impressions']:,} impressions, CTR: {row['ctr']:.1%}")
        print(f"   GA4: {row['ga_users']:,} users, {row['ga_sessions']:,} sessions")
        print(f"   Conversion: {row['conversion_rate']:.1%} (users/clicks)")
        print(f"   Engagement Score: {row['engagement_score']:.1f}")

    # Export to CSV
    csv_filename = get_report_filename("keywords_insights", f"{start_date}_to_{end_date}")
    merged_df.to_csv(csv_filename, index=False)
    print(f"\n📄 Detailed data exported to: {csv_filename}")

    # Summary statistics
    total_clicks = merged_df['clicks'].sum()
    total_impressions = merged_df['impressions'].sum()
    total_ga_users = merged_df['ga_users'].sum()
    avg_ctr = merged_df['ctr'].mean()
    avg_conversion = merged_df['conversion_rate'].mean()

    print(f"\n{'='*100}")
    print("📊 SUMMARY STATISTICS:")
    print(f"   Date Range: {start_date} to {end_date}")
    print(f"   Total Keywords: {len(merged_df)}")
    print(f"   Total GSC Clicks: {total_clicks:,}")
    print(f"   Total GSC Impressions: {total_impressions:,}")
    print(f"   Average CTR: {avg_ctr:.1%}")
    print(f"   Total GA4 Users: {total_ga_users:,}")
    print(f"   Average Conversion Rate: {avg_conversion:.1%}")

    return merged_df

def get_top_keywords_report(days: int = 30):
    """Get top performing keywords report"""
    start_date, end_date = get_last_30_days_range()
    if days != 30:
        end_date_obj = datetime.now() - timedelta(days=1)
        start_date_obj = end_date_obj - timedelta(days=days-1)
        start_date = start_date_obj.strftime('%Y-%m-%d')
        end_date = end_date_obj.strftime('%Y-%m-%d')

    return generate_keywords_insights_report(start_date, end_date)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Google Search Console + Google Analytics Keywords Insights')
    parser.add_argument('--days', type=int, choices=[1, 7, 30], default=30,
                       help='Number of days for report (1, 7, or 30, default: 30)')
    parser.add_argument('--date', type=str, choices=['yesterday', 'today'],
                       help='Use yesterday or today for single-day reports')
    parser.add_argument('--start-date', type=str,
                       help='Start date in YYYY-MM-DD format (for custom range)')
    parser.add_argument('--end-date', type=str,
                       help='End date in YYYY-MM-DD format (for custom range)')

    args = parser.parse_args()

    print("🔍 Google Search Console + Google Analytics Keywords Insights")
    print("=" * 60)

    # Check if custom date range is provided
    if args.start_date and args.end_date:
        print(f"Running custom date range report: {args.start_date} to {args.end_date}")
        generate_keywords_insights_report(args.start_date, args.end_date)
    elif args.date:
        # Handle yesterday/today
        if args.date == 'yesterday':
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"Running yesterday's keywords insights report: {yesterday}")
            generate_keywords_insights_report(yesterday, yesterday)
        elif args.date == 'today':
            today = datetime.now().strftime('%Y-%m-%d')
            print(f"Running today's keywords insights report: {today}")
            generate_keywords_insights_report(today, today)
    else:
        # Use days parameter for standard reports
        if args.days == 1:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"Running 1-day keywords insights report: {yesterday}")
            generate_keywords_insights_report(yesterday, yesterday)
        elif args.days == 7:
            print("Running 7-day keywords insights report")
            get_top_keywords_report(7)
        else:  # default to 30 days
            print("Running 30-day keywords insights report")
            get_top_keywords_report(30)