"""
Conversion Funnel Analysis Script
Analyze user conversion paths and funnel performance

Usage:
    python conversion_funnel_analysis.py [goal_type] [days]

Examples:
    python conversion_funnel_analysis.py contact_form 30
    python conversion_funnel_analysis.py property_inquiry 7
    python conversion_funnel_analysis.py all_goals 90
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta.types import OrderBy, FilterExpression, Filter

from src.config import REPORTS_DIR
from src.ga4_client import run_report, create_date_range, get_report_filename

def get_last_30_days_range():
    """Get date range for the last 30 days"""
    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=29)  # 30 days back
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def analyze_conversion_funnel(goal_type: str = "all", start_date: str = None, end_date: str = None):
    """Analyze conversion funnels and user paths to goals"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print(f"🔍 Analyzing conversion funnels for: {goal_type}")
    print(f"   Date range: {start_date} to {end_date}")
    print("=" * 100)

    # Define goal events based on type
    goal_events = {
        "contact_form": ["form_submit", "contact_submit"],
        "property_inquiry": ["property_inquiry", "inquiry_submit"],
        "phone_call": ["phone_click", "call_click"],
        "email_click": ["email_click"],
        "social_share": ["social_share"],
        "all_goals": ["form_submit", "contact_submit", "property_inquiry", "phone_click", "email_click"]
    }

    if goal_type not in goal_events and goal_type != "all":
        print(f"❌ Unknown goal type: {goal_type}")
        print(f"   Available types: {', '.join(goal_events.keys())}")
        return None

    target_events = goal_events.get(goal_type, goal_events["all_goals"])

    # Get overall traffic data
    date_range = create_date_range(start_date, end_date)

    # First, get total sessions and users
    total_response = run_report(
        dimensions=[],
        metrics=["totalUsers", "sessions", "conversions", "totalRevenue"],
        date_ranges=[date_range],
        limit=1
    )

    if not total_response.row_count:
        print("❌ No data found for the date range.")
        return None

    total_users = int(total_response.rows[0].metric_values[0].value)
    total_sessions = int(total_response.rows[0].metric_values[1].value)
    total_conversions = int(total_response.rows[0].metric_values[2].value)
    total_revenue = float(total_response.rows[0].metric_values[3].value)

    print("📊 OVERALL SITE PERFORMANCE:")
    print(f"   Total Users: {total_users:,}")
    print(f"   Total Sessions: {total_sessions:,}")
    print(f"   Total Conversions: {total_conversions:,}")
    print(f"   Total Revenue: ${total_revenue:,.2f}")
    print(f"   Conversion Rate: {total_conversions/total_sessions*100:.2f}%" if total_sessions > 0 else "   Conversion Rate: N/A")
    print()

    # Get conversion data by event
    conversion_data = {}
    for event_name in target_events:
        try:
            event_response = run_report(
                dimensions=["eventName"],
                metrics=["eventCount", "totalUsers"],
                date_ranges=[date_range],
                dimension_filter=FilterExpression(
                    filter=Filter(
                        field_name="eventName",
                        string_filter=Filter.StringFilter(value=event_name)
                    )
                ),
                limit=10
            )

            if event_response.row_count > 0:
                count = int(event_response.rows[0].metric_values[0].value)
                users = int(event_response.rows[0].metric_values[1].value)
                conversion_data[event_name] = {"count": count, "users": users}
        except:
            continue

    # Get top landing pages and their conversion rates
    landing_page_response = run_report(
        dimensions=["landingPage", "sessionDefaultChannelGrouping"],
        metrics=["sessions", "totalUsers", "conversions", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=20
    )

    # Get top pages by pageviews (using screenPageViews which is the GA4 equivalent)
    top_pages_response = run_report(
        dimensions=["pagePath", "sessionDefaultChannelGrouping"],
        metrics=["screenPageViews", "sessions", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)
        ],
        limit=20
    )

    # Display conversion analysis
    print("🎯 CONVERSION ANALYSIS:")
    print(f"   Goal Type: {goal_type}")
    print(f"   Target Events: {', '.join(target_events)}")
    print()

    if conversion_data:
        print("   Event Performance:")
        print("   Event Name          | Count    | Users    | Rate")
        print("   --------------------|----------|----------|-------")

        for event_name, data in conversion_data.items():
            rate = data['users'] / total_users * 100 if total_users > 0 else 0
            print("12")
    else:
        print("   ⚠️  No conversion events found for the specified goals")
        print("   💡 This could mean:")
        print("      - Events are not properly tracked in GA4")
        print("      - Event names don't match the expected names")
        print("      - No conversions occurred in the date range")
    print()

    # Landing page analysis
    print("🚪 TOP LANDING PAGES:")
    print("   Page Path              | Channel      | Sessions | Users | Conversions | Bounce Rate")
    print("   -----------------------|--------------|----------|-------|-------------|------------")

    for row in landing_page_response.rows[:10]:
        page_path = row.dimension_values[0].value[:23]  # Truncate long paths
        channel = row.dimension_values[1].value[:12]
        sessions = int(row.metric_values[0].value)
        users = int(row.metric_values[1].value)
        conversions = int(row.metric_values[2].value)
        bounce_rate = float(row.metric_values[3].value) * 100

        print("23")
    print()

    # Top pages analysis (instead of exit pages since exits metric isn't available)
    print("� TOP PAGES BY VIEWS:")
    print("   Page Path              | Channel      | Pageviews | Sessions | Bounce Rate")
    print("   -----------------------|--------------|-----------|----------|------------")

    for row in top_pages_response.rows[:10]:
        page_path = row.dimension_values[0].value[:23]
        channel = row.dimension_values[1].value[:12]
        pageviews = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        bounce_rate = float(row.metric_values[2].value) * 100

        print("23")
    print()

    # Funnel analysis - if we have e-commerce or defined funnel steps
    print("🔄 FUNNEL ANALYSIS:")
    print("   💡 For detailed funnel analysis, consider setting up:")
    print("      - E-commerce tracking (if applicable)")
    print("      - Custom funnel events in GA4")
    print("      - Goal completions for specific user journeys")
    print()

    # Recommendations
    print("💡 OPTIMIZATION RECOMMENDATIONS:")
    if conversion_data:
        total_goal_completions = sum(data['count'] for data in conversion_data.values())
        if total_goal_completions / total_sessions < 0.01:  # Less than 1%
            print("   • Low conversion rate detected - consider A/B testing landing pages")
        if total_conversions > 0 and total_conversions / total_sessions > 0.05:  # Over 5%
            print("   • Good conversion rate - focus on increasing traffic volume")
    else:
        print("   • Set up conversion tracking to measure goal completions")
        print("   • Define key user actions as conversion events in GA4")

    # High bounce rate pages
    high_bounce_pages = []
    for row in landing_page_response.rows:
        bounce_rate = float(row.metric_values[3].value)
        if bounce_rate > 0.7:  # Over 70% bounce rate
            high_bounce_pages.append(row.dimension_values[0].value)

    if high_bounce_pages:
        print(f"   • {len(high_bounce_pages)} pages have high bounce rates (>70%)")
        print("   • Review content and user experience on these pages")

    print()

    # Export detailed data
    csv_data = []

    # Landing page data
    for row in landing_page_response.rows:
        csv_data.append({
            'Analysis_Type': 'Landing_Page',
            'Page_Path': row.dimension_values[0].value,
            'Channel': row.dimension_values[1].value,
            'Sessions': int(row.metric_values[0].value),
            'Users': int(row.metric_values[1].value),
            'Conversions': int(row.metric_values[2].value),
            'Bounce_Rate': float(row.metric_values[3].value),
            'Date_Range': f"{start_date}_to_{end_date}"
        })

    # Top pages data
    for row in top_pages_response.rows:
        csv_data.append({
            'Analysis_Type': 'Top_Page',
            'Page_Path': row.dimension_values[0].value,
            'Channel': row.dimension_values[1].value,
            'Pageviews': int(row.metric_values[0].value),
            'Sessions': int(row.metric_values[1].value),
            'Bounce_Rate': float(row.metric_values[2].value),
            'Date_Range': f"{start_date}_to_{end_date}"
        })

    # Conversion data
    for event_name, data in conversion_data.items():
        csv_data.append({
            'Analysis_Type': 'Conversion_Event',
            'Event_Name': event_name,
            'Count': data['count'],
            'Users': data['users'],
            'Conversion_Rate': data['users'] / total_users if total_users > 0 else 0,
            'Date_Range': f"{start_date}_to_{end_date}"
        })

    if csv_data:
        df = pd.DataFrame(csv_data)
        csv_filename = get_report_filename("conversion_funnel_analysis", f"{goal_type}_{start_date}_to_{end_date}")
        df.to_csv(csv_filename, index=False)
        print(f"📄 Detailed data exported to: {csv_filename}")

    return {
        'total_users': total_users,
        'total_sessions': total_sessions,
        'total_conversions': total_conversions,
        'conversion_data': conversion_data,
        'landing_pages': landing_page_response.rows,
        'top_pages': top_pages_response.rows
    }

if __name__ == "__main__":
    print("🎯 Conversion Funnel Analysis Tool")
    print("=" * 40)

    if len(sys.argv) >= 2:
        goal_type = sys.argv[1]
        days = int(sys.argv[2]) if len(sys.argv) >= 3 else 30

        print(f"Analyzing goal type: {goal_type}")
        print(f"Time period: Last {days} days")

        if days == 7:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
            analyze_conversion_funnel(goal_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        else:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=days-1)
            analyze_conversion_funnel(goal_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    else:
        print("Analyze conversion funnels and user goal completion")
        print()
        print("Available goal types:")
        print("  contact_form    - Contact form submissions")
        print("  property_inquiry - Property inquiry forms")
        print("  phone_call      - Phone call clicks")
        print("  email_click     - Email link clicks")
        print("  all_goals       - All conversion events")
        print()
        print("Usage: python conversion_funnel_analysis.py <goal_type> [days]")
        print("Example: python conversion_funnel_analysis.py contact_form 30")
        exit(1)