import os
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    OrderBy,
)
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")
KEY_PATH = os.getenv("GA4_KEY_PATH")

def get_all_pages_with_sources():
    """Get all pages with their traffic sources for the past 30 days"""

    # Set environment variable for authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

    # Verify key file exists
    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError(f"Service account key not found at {KEY_PATH}. Please check the path and permissions.")

    client = BetaAnalyticsDataClient()

    # Calculate date range: last 30 days
    end_date = datetime.now().date() - timedelta(days=1)  # Yesterday as end
    start_date = end_date - timedelta(days=29)  # 30 days total

    print(f"📊 Generating comprehensive page-source report for {start_date} to {end_date}")
    print("=" * 80)

    # Get all page + source combinations
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[
            Dimension(name="pagePath"),
            Dimension(name="sessionSourceMedium")
        ],
        metrics=[Metric(name="totalUsers")],
        date_ranges=[DateRange(start_date=str(start_date), end_date=str(end_date))],
        order_bys=[
            OrderBy(
                dimension=OrderBy.DimensionOrderBy(dimension_name="pagePath"),
                desc=False  # Sort pages alphabetically
            ),
            OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name="totalUsers"),
                desc=True  # Sort sources by users descending within each page
            )
        ],
        limit=10000,  # High limit to get all data
    )

    try:
        response = client.run_report(request)

        if response.row_count == 0:
            print("❌ No data found for the date range.")
            return

        print(f"✅ Retrieved {response.row_count} page-source combinations")

        # Process data into a structured format
        page_data = {}

        for row in response.rows:
            page_path = row.dimension_values[0].value
            source_medium = row.dimension_values[1].value
            users = int(row.metric_values[0].value)

            # Skip /sold/ pages as they no longer exist
            if page_path.startswith('/sold/'):
                continue

            if page_path not in page_data:
                page_data[page_path] = {
                    'total_users': 0,
                    'sources': []
                }

            page_data[page_path]['sources'].append({
                'source_medium': source_medium,
                'users': users
            })
            page_data[page_path]['total_users'] += users

        # Sort pages by total users (descending)
        sorted_pages = sorted(page_data.items(), key=lambda x: x[1]['total_users'], reverse=True)

        # Display results
        print(f"\n📈 COMPREHENSIVE PAGE-SOURCE REPORT ({start_date} to {end_date})")
        print("=" * 100)

        grand_total_users = 0
        page_count = 0

        for page_path, data in sorted_pages:
            page_count += 1
            total_page_users = data['total_users']
            grand_total_users += total_page_users

            print(f"\n🏠 PAGE {page_count}: {page_path}")
            print(f"   Total Users: {total_page_users:,}")
            print("   Traffic Sources:")

            # Sort sources by users within each page
            sorted_sources = sorted(data['sources'], key=lambda x: x['users'], reverse=True)

            for source in sorted_sources:
                percentage = (source['users'] / total_page_users) * 100
                print(f"     • {source['source_medium']:<35} {source['users']:>6,} users ({percentage:>5.1f}%)")

        print(f"\n{'='*100}")
        print(f"📊 SUMMARY:")
        print(f"   Total Pages: {page_count:,}")
        print(f"   Total Users Across All Pages: {grand_total_users:,}")
        print(f"   Average Users Per Page: {grand_total_users/page_count:,.1f}")

        # Export to CSV
        csv_data = []
        for page_path, data in sorted_pages:
            for source in data['sources']:
                csv_data.append({
                    'Page Path': page_path,
                    'Source/Medium': source['source_medium'],
                    'Users': source['users'],
                    'Page Total Users': data['total_users']
                })

        df = pd.DataFrame(csv_data)
        csv_file = f"comprehensive_page_source_report_{start_date}_to_{end_date}.csv"
        df.to_csv(csv_file, index=False)
        print(f"\n📄 Detailed data exported to: {csv_file}")

        # Also create a summary CSV with one row per page
        summary_data = []
        for page_path, data in sorted_pages:
            top_source = max(data['sources'], key=lambda x: x['users'])
            summary_data.append({
                'Page Path': page_path,
                'Total Users': data['total_users'],
                'Top Source': top_source['source_medium'],
                'Top Source Users': top_source['users'],
                'Number of Sources': len(data['sources'])
            })

        summary_df = pd.DataFrame(summary_data)
        summary_csv = f"page_summary_report_{start_date}_to_{end_date}.csv"
        summary_df.to_csv(summary_csv, index=False)
        print(f"📄 Page summary exported to: {summary_csv}")

    except Exception as error:
        print(f"❌ Error running report: {error}")
        print("Check: API enabled? Service account access? Correct Property ID? Data privacy thresholds?")

if __name__ == "__main__":
    get_all_pages_with_sources()