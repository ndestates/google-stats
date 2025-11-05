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

def get_yesterday_report():
    """Get comprehensive page-source report for yesterday only"""

    # Set environment variable for authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

    # Verify key file exists
    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError(f"Service account key not found at {KEY_PATH}. Please check the path and permissions.")

    client = BetaAnalyticsDataClient()

    # Calculate date range: yesterday only
    yesterday = datetime.now().date() - timedelta(days=1)

    print(f"📊 Generating yesterday's page-source report for {yesterday}")
    print("=" * 80)

    # Get all page + source combinations for yesterday
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[
            Dimension(name="pagePath"),
            Dimension(name="sessionSourceMedium")
        ],
        metrics=[Metric(name="totalUsers")],
        date_ranges=[DateRange(start_date=str(yesterday), end_date=str(yesterday))],
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
        limit=5000,  # High limit to get all data
    )

    try:
        response = client.run_report(request)

        if response.row_count == 0:
            print("❌ No data found for yesterday.")
            return

        print(f"✅ Retrieved {response.row_count} page-source combinations for yesterday")

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
        print(f"\n📈 YESTERDAY'S PAGE-SOURCE REPORT ({yesterday})")
        print("=" * 100)

        grand_total_users = 0
        page_count = 0

        for i, (page_path, data) in enumerate(sorted_pages, 1):
            if data['total_users'] > 0:  # Only show pages with users
                print(f"\n🏠 PAGE {i}: {page_path}")
                print(f"   Total Users: {data['total_users']:,}")

                # Sort sources by users descending
                sorted_sources = sorted(data['sources'], key=lambda x: x['users'], reverse=True)

                print("   Traffic Sources:")
                for source in sorted_sources:
                    if source['users'] > 0:
                        percentage = (source['users'] / data['total_users'] * 100)
                        print(f"     • {source['source_medium']:<35} {source['users']:>3} users ({percentage:5.1f}%)")

                grand_total_users += data['total_users']
                page_count += 1

                # Limit display to top 50 pages to avoid overwhelming output
                if i >= 50:
                    remaining_pages = len(sorted_pages) - 50
                    remaining_users = sum(data['total_users'] for _, data in sorted_pages[50:])
                    if remaining_pages > 0:
                        print(f"\n... and {remaining_pages} more pages with {remaining_users:,} total users")
                    break

        print(f"\n{'='*100}")
        print("📊 SUMMARY:")
        print(f"   Date: {yesterday}")
        print(f"   Total Pages: {page_count}")
        print(f"   Total Users Across All Pages: {grand_total_users:,}")
        if page_count > 0:
            print(f"   Average Users Per Page: {grand_total_users / page_count:.1f}")
        # Export detailed data to CSV
        csv_data = []
        for page_path, data in sorted_pages:
            for source in data['sources']:
                if source['users'] > 0:
                    csv_data.append({
                        'Date': str(yesterday),
                        'Page_Path': page_path,
                        'Source_Medium': source['source_medium'],
                        'Users': source['users'],
                        'Page_Total_Users': data['total_users']
                    })

        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_filename = f"yesterday_report_{yesterday}.csv"
            df.to_csv(csv_filename, index=False)
            print(f"\n📄 Detailed data exported to: {csv_filename}")

            # Also create a summary CSV with one row per page
            summary_data = []
            for page_path, data in sorted_pages:
                if data['total_users'] > 0:
                    # Get top source for summary
                    top_source = max(data['sources'], key=lambda x: x['users']) if data['sources'] else {'source_medium': 'None', 'users': 0}
                    summary_data.append({
                        'Date': str(yesterday),
                        'Page_Path': page_path,
                        'Total_Users': data['total_users'],
                        'Top_Source': top_source['source_medium'],
                        'Top_Source_Users': top_source['users']
                    })

            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_filename = f"yesterday_summary_{yesterday}.csv"
                summary_df.to_csv(summary_filename, index=False)
                print(f"📄 Page summary exported to: {summary_filename}")

    except Exception as e:
        print(f"❌ Error generating yesterday's report: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    get_yesterday_report()