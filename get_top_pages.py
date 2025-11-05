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
    DimensionFilter,
    DimensionFilterClause,
    FilterExpression,
    Filter,
)

# Hardcoded GA4 Property ID (replace with your actual Property ID)
PROPERTY_ID = "275378361"  # e.g., "123456789" from GA4 Admin > Property Settings

# Hardcoded path to service account key
KEY_PATH = "/var/www/html/.ddev/keys/ga4-page-analytics-cf93eb65ac26.json"

def get_top_pages_with_sources():
    # Set environment variable for authentication
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

    # Verify key file exists
    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError(f"Service account key not found at {KEY_PATH}. Please check the path and permissions.")

    client = BetaAnalyticsDataClient()

    # Calculate date range: last 7 full days (e.g., for Nov 5, 2025: Oct 29 - Nov 4)
    end_date = datetime.now().date() - timedelta(days=1)  # Yesterday as end
    start_date = end_date - timedelta(days=6)  # 7 days total

    # Filter: Exclude "(not set)" sources for cleaner data
    dimension_filter = DimensionFilter(
        filter=Filter(
            field_name="sessionSourceMedium",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.NOT_EQUAL,
                value="(not set)"
            )
        )
    )
    filter_clause = DimensionFilterClause(filters=[dimension_filter])
    filter_expression = FilterExpression(and_group=FilterExpression.OrGroup(clauses=[filter_clause]))

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[
            Dimension(name="pagePath"),
            Dimension(name="sessionSourceMedium")
        ],
        metrics=[Metric(name="views")],
        date_ranges=[DateRange(start_date=str(start_date), end_date=str(end_date))],
        dimension_filter=filter_expression,
        order_bys=[
            OrderBy(
                metric=OrderBy.MetricOrderBy(
                    metric_name="views",
                    order_type=OrderBy.OrderType.DESCENDING
                )
            ),
            OrderBy(
                dimension=OrderBy.DimensionOrderBy(
                    dimension_name="sessionSourceMedium",
                    order_type=OrderBy.OrderType.ASCENDING
                )
            )
        ],
        limit=20,
    )

    try:
        response = client.run_report(request)
        if response.row_count == 0:
            print("No data found for the date range (or all sources are '(not set)').")
            return

        # Process data for output and CSV
        data = [
            [row.dimension_values[0].value, row.dimension_values[1].value, int(row.metric_values[0].value)]
            for row in response.rows
        ]
        df = pd.DataFrame(data, columns=["Page Path", "Source/Medium", "Views"])

        # Print table
        print(f"Top Page-Source Combinations (by Views) from {start_date} to {end_date}:")
        print("=" * 90)
        print(f"{'Page Path':<50} {'Source/Medium':<30} {'Views'}")
        print("=" * 90)
        total_views = 0
        for _, row in df.iterrows():
            print(f"{row['Page Path']:<50} {row['Source/Medium']:<30} {row['Views']:,}")
            total_views += row["Views"]
        print("=" * 90)
        print(f"Total Views Across Top Results: {total_views:,}")

        # Export to CSV
        csv_file = f"top_pages_report_{start_date}_to_{end_date}.csv"
        df.to_csv(csv_file, index=False)
        print(f"Exported to {csv_file}")

    except Exception as error:
        print(f"Error running report: {error}")
        print("Check: API enabled? Service account access? Correct Property ID? Data privacy thresholds?")

if __name__ == "__main__":
    get_top_pages_with_sources()