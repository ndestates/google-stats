import os
import sys
import json
import argparse
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    OrderBy,
    Filter,
    FilterExpression,
)

from src.config import REPORTS_DIR, GA4_PROPERTY_ID, GA4_KEY_PATH
from src.pdf_generator import create_channel_report_pdf

def get_top_pages_with_sources():
    # Set environment variable for authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GA4_KEY_PATH

    # Verify key file exists
    if not os.path.exists(GA4_KEY_PATH):
        raise FileNotFoundError(f"Service account key not found at {GA4_KEY_PATH}. Please check the path and permissions.")

    client = BetaAnalyticsDataClient()

    # Test basic connectivity first
    print("🔗 Testing basic API connectivity...")
    test_request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        metrics=[Metric(name="totalUsers")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="yesterday")],
    )

    try:
        test_response = client.run_report(test_request)
        print(f"✅ API connection successful! Total users (7 days): {test_response.rows[0].metric_values[0].value if test_response.rows else 'No data'}")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return

    print("\n🔍 Now trying page-level data approaches...")

    # Try multiple approaches to get page data
    approaches = [
        {
            "name": "Simple page views (7 days)",
            "dimensions": [Dimension(name="pagePath")],
            "metric": "screenPageViews",
            "date_range": ("7daysAgo", "yesterday")
        },
        {
            "name": "Page path + source (7 days, totalUsers)",
            "dimensions": [Dimension(name="pagePath"), Dimension(name="sessionSourceMedium")],
            "metric": "totalUsers",
            "date_range": ("7daysAgo", "yesterday")
        },
        {
            "name": "Page title only (30 days)",
            "dimensions": [Dimension(name="pageTitle")],
            "metric": "screenPageViews",
            "date_range": ("30daysAgo", "yesterday")
        },
        {
            "name": "Landing page + source (7 days)",
            "dimensions": [Dimension(name="landingPage"), Dimension(name="sessionSourceMedium")],
            "metric": "totalUsers",
            "date_range": ("7daysAgo", "yesterday")
        },
        {
            "name": "Page path + default channel (30 days)",
            "dimensions": [Dimension(name="pagePath"), Dimension(name="sessionDefaultChannelGrouping")],
            "metric": "totalUsers",
            "date_range": ("30daysAgo", "yesterday")
        }
    ]

    for approach in approaches:
        print(f"\n🔍 Trying: {approach['name']}")
        print("-" * 50)

        request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=approach["dimensions"],
            metrics=[Metric(name=approach["metric"])],
            date_ranges=[DateRange(start_date=approach["date_range"][0], end_date=approach["date_range"][1])],
            order_bys=[OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name=approach["metric"]),
                desc=True
            )],
            limit=20,
        )

        try:
            response = client.run_report(request)
            print(f"API Response: {response.row_count} rows, {len(response.rows)} actual rows")

            # Debug: Check if there are any rows at all
            if hasattr(response, 'rows') and response.rows:
                print(f"First row sample: {response.rows[0]}")
                if response.rows[0].dimension_values:
                    print(f"Dimension values: {[dv.value for dv in response.rows[0].dimension_values]}")
                if response.rows[0].metric_values:
                    print(f"Metric values: {[mv.value for mv in response.rows[0].metric_values]}")

            if response.row_count > 0:
                print(f"✅ Success! Found {response.row_count} rows")
                process_and_display_data(response, approach)
                return
            else:
                print("❌ No data found (row_count = 0)")
        except Exception as error:
            print(f"❌ Error: {error}")
            # Try to get more details about the error
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")

    # If all approaches fail, show channel data as fallback
    print("\n" + "="*60)
    print("📊 FALLBACK: Showing Channel Performance Data")
    print("="*60)
    show_channel_fallback()

def process_and_display_data(response, approach):
    """Process and display the analytics data"""
    # Determine column names based on dimensions and metric
    dim_names = [dim.name for dim in approach["dimensions"]]
    metric_name = approach["metric"]
    columns = dim_names + [metric_name.replace("screenPageViews", "Page Views").replace("totalUsers", "Users").title()]

    # Process data
    data = []
    for row in response.rows:
        row_data = [val.value for val in row.dimension_values] + [int(row.metric_values[0].value)]
        
        # Skip /sold/ pages as they no longer exist
        if row_data and row_data[0].startswith('/sold/'):
            continue
            
        data.append(row_data)

    df = pd.DataFrame(data, columns=columns)

    # Display results
    print(f"\n📈 Top Results ({len(data)} rows):")
    print("=" * 100)

    # Create header based on dimensions
    if len(dim_names) == 1:
        print(f"{columns[0]:<60} {columns[1]}")
    else:
        print(f"{columns[0]:<40} {columns[1]:<30} {columns[2]}")
    print("=" * 100)

    total_metric = 0
    metric_col = columns[-1]
    for _, row in df.iterrows():
        if len(dim_names) == 1:
            print(f"{row[columns[0]]:<60} {row[metric_col]:,}")
        else:
            print(f"{row[columns[0]]:<40} {row[columns[1]]:<30} {row[metric_col]:,}")
        total_metric += row[metric_col]

    print("=" * 100)
    print(f"Total {metric_col}: {total_metric:,}")

    # Export to CSV
    date_suffix = f"{approach['date_range'][0]}_to_{approach['date_range'][1]}".replace("daysAgo", "days_ago")
    csv_file = f"analytics_report_{date_suffix}_{metric_name}.csv"
    df.to_csv(csv_file, index=False)
    print(f"📄 Exported to {csv_file}")

def show_channel_fallback():
    """Show channel performance as fallback"""
    client = BetaAnalyticsDataClient()

    request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[Dimension(name="sessionDefaultChannelGrouping")],
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="yesterday")],
        order_bys=[OrderBy(
            metric=OrderBy.MetricOrderBy(metric_name="activeUsers"),
            desc=True
        )],
        limit=10,
    )

    try:
        response = client.run_report(request)
        if response.row_count > 0:
            print("Channel Performance (Last 30 Days):")
            print("=" * 60)
            print(f"{'Channel':<40} {'Active Users'}")
            print("=" * 60)
            for row in response.rows:
                print(f"{row.dimension_values[0].value:<40} {int(row.metric_values[0].value):,}")
            print("=" * 60)

            # Export channel data
            channel_data = [
                [row.dimension_values[0].value, int(row.metric_values[0].value)]
                for row in response.rows
            ]
            channel_df = pd.DataFrame(channel_data, columns=["Channel", "Active Users"])
            channel_csv = "channel_report_30daysAgo_to_yesterday.csv"
            channel_df.to_csv(channel_csv, index=False)
            print(f"📄 Exported channel data to {channel_csv}")

            # Prepare data for PDF generation
            pdf_channel_data = {}
            total_users = 0
            total_sessions = 0  # We don't have sessions data in this query, so we'll use users as proxy

            for row in response.rows:
                channel_name = row.dimension_values[0].value
                users = int(row.metric_values[0].value)
                pdf_channel_data[channel_name] = {
                    'users': users,
                    'sessions': users,  # Using users as sessions proxy
                    'bounce_rate': 0.0,  # Not available in this query
                    'avg_session_duration': 0.0  # Not available in this query
                }
                total_users += users
                total_sessions += users

            # Generate PDF report
            pdf_filename = create_channel_report_pdf(
                pdf_channel_data,
                "30daysAgo_to_yesterday",
                total_users,
                total_sessions
            )
            print(f"📄 PDF report exported to {pdf_filename}")
        else:
            print("No data available at all.")
    except Exception as error:
        print(f"Error getting channel data: {error}")

def get_top_pages_json():
    """Get top pages and output as JSON for web interface"""
    try:
        # Set environment variable for authentication
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GA4_KEY_PATH

        # Verify key file exists
        if not os.path.exists(GA4_KEY_PATH):
            print(json.dumps({'error': f'Service account key not found at {GA4_KEY_PATH}'}))
            return

        client = BetaAnalyticsDataClient()

        # Get top pages from last 30 days
        request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="totalUsers")],
            date_ranges=[DateRange(start_date="30daysAgo", end_date="yesterday")],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="totalUsers"), desc=True)],
            limit=50,  # Get top 50 pages
        )

        response = client.run_report(request)

        pages = []
        for row in response.rows:
            page_path = row.dimension_values[0].value
            users = int(row.metric_values[0].value)

            # Skip very low traffic pages and non-page paths
            if users >= 1 and not page_path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.woff2', '.ttf', '.eot')):
                pages.append({
                    'path': page_path,
                    'users': users
                })

        print(json.dumps({'pages': pages}))

    except Exception as e:
        print(json.dumps({'error': str(e)}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get top performing pages report')
    parser.add_argument('--json', action='store_true', help='Output results as JSON for web interface')
    args = parser.parse_args()

    if args.json:
        get_top_pages_json()
    else:
        get_top_pages_with_sources()