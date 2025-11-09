"""
User Behavior Analysis Script
Analyze user navigation patterns and behavior flows

Usage:
    python user_behavior.py [analysis_type] [days]

Examples:
    python user_behavior.py flow 30
    python user_behavior.py paths 7
    python user_behavior.py all 90
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

def analyze_user_flow(start_date: str = None, end_date: str = None):
    """Analyze user navigation flow and page transitions"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("🔄 Analyzing user navigation flow...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    # Get page path data with landing/exit pages
    response = run_report(
        dimensions=["pagePath", "landingPage", "exitPage"],
        metrics=["totalUsers", "sessions", "pageviews", "entrances", "exits"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="pageviews"), desc=True)
        ],
        limit=100
    )

    if response.row_count == 0:
        print("❌ No user flow data found for the date range.")
        return None

    print(f"✅ Retrieved flow data for {response.row_count} page combinations")

    # Analyze flow patterns
    flow_data = {}
    total_pageviews = 0
    total_sessions = 0

    for row in response.rows:
        page_path = row.dimension_values[0].value
        landing_page = row.dimension_values[1].value
        exit_page = row.dimension_values[2].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        entrances = int(row.metric_values[3].value)
        exits = int(row.metric_values[4].value)

        # Track page metrics
        if page_path not in flow_data:
            flow_data[page_path] = {
                'total_users': 0,
                'total_sessions': 0,
                'total_pageviews': 0,
                'total_entrances': 0,
                'total_exits': 0,
                'landing_pages': {},
                'exit_pages': {}
            }

        flow_data[page_path]['total_users'] += users
        flow_data[page_path]['total_sessions'] += sessions
        flow_data[page_path]['total_pageviews'] += pageviews
        flow_data[page_path]['total_entrances'] += entrances
        flow_data[page_path]['total_exits'] += exits

        # Track landing pages
        if landing_page and landing_page != page_path:
            if landing_page not in flow_data[page_path]['landing_pages']:
                flow_data[page_path]['landing_pages'][landing_page] = 0
            flow_data[page_path]['landing_pages'][landing_page] += entrances

        # Track exit pages
        if exit_page and exit_page != page_path:
            if exit_page not in flow_data[page_path]['exit_pages']:
                flow_data[page_path]['exit_pages'][exit_page] = 0
            flow_data[page_path]['exit_pages'][exit_page] += exits

        total_pageviews += pageviews
        total_sessions += sessions

    # Calculate flow metrics
    print("\n📊 USER FLOW ANALYSIS:")
    print(f"   Total Page Views: {total_pageviews:,}")
    print(f"   Total Sessions: {total_sessions:,}")
    print(f"   Unique Pages: {len(flow_data)}")
    print()

    # Identify top landing and exit pages
    landing_pages = {}
    exit_pages = {}

    for page, data in flow_data.items():
        if data['total_entrances'] > 0:
            landing_pages[page] = data['total_entrances']
        if data['total_exits'] > 0:
            exit_pages[page] = data['total_exits']

    print("   🏠 TOP LANDING PAGES:")
    for page, entrances in sorted(landing_pages.items(), key=lambda x: x[1], reverse=True)[:5]:
        page_display = page[:50] + "..." if len(page) > 50 else page
        percentage = (entrances / total_sessions) * 100 if total_sessions > 0 else 0
        print(f"      - {page_display} ({entrances} entrances, {percentage:.1f}%)")
    print()

    print("   🚪 TOP EXIT PAGES:")
    for page, exits in sorted(exit_pages.items(), key=lambda x: x[1], reverse=True)[:5]:
        page_display = page[:50] + "..." if len(page) > 50 else page
        percentage = (exits / total_sessions) * 100 if total_sessions > 0 else 0
        print(f"      - {page_display} ({exits} exits, {percentage:.1f}%)")
    print()

    # Analyze bounce and exit rates
    high_exit_pages = []
    for page, data in flow_data.items():
        if data['total_pageviews'] > 10:  # Minimum threshold
            exit_rate = data['total_exits'] / data['total_pageviews']
            if exit_rate > 0.5:  # High exit rate
                high_exit_pages.append((page, exit_rate, data['total_pageviews']))

    if high_exit_pages:
        print("   ⚠️  PAGES WITH HIGH EXIT RATES (>50%):")
        for page, exit_rate, pageviews in sorted(high_exit_pages, key=lambda x: x[1], reverse=True)[:5]:
            page_display = page[:50] + "..." if len(page) > 50 else page
            print(f"      - {page_display} (Exit Rate: {exit_rate:.1%}, Pageviews: {pageviews})")
        print()

    return flow_data

def analyze_navigation_paths(start_date: str = None, end_date: str = None):
    """Analyze common navigation paths and user journeys"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("🛣️  Analyzing navigation paths...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    # Get page path sequences (simplified approach using pagePath and previousPagePath)
    response = run_report(
        dimensions=["pagePath", "previousPagePath"],
        metrics=["totalUsers", "sessions"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=100
    )

    if response.row_count == 0:
        print("❌ No navigation path data found for the date range.")
        return None

    print(f"✅ Retrieved path data for {response.row_count} page transitions")

    # Build transition matrix
    transitions = {}
    page_totals = {}

    for row in response.rows:
        current_page = row.dimension_values[0].value
        previous_page = row.dimension_values[1].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)

        # Skip if no previous page (entry point)
        if not previous_page or previous_page == current_page:
            continue

        # Track transitions
        if previous_page not in transitions:
            transitions[previous_page] = {}
        if current_page not in transitions[previous_page]:
            transitions[previous_page][current_page] = 0
        transitions[previous_page][current_page] += sessions

        # Track page totals
        if previous_page not in page_totals:
            page_totals[previous_page] = 0
        page_totals[previous_page] += sessions

    # Calculate transition probabilities
    transition_probs = {}
    for from_page, to_pages in transitions.items():
        transition_probs[from_page] = {}
        total_from = page_totals[from_page]
        for to_page, count in to_pages.items():
            transition_probs[from_page][to_page] = count / total_from

    print("📊 NAVIGATION PATH ANALYSIS:")
    print(f"   Unique Transition Pairs: {len(transitions)}")
    print()

    # Show top transitions
    all_transitions = []
    for from_page, to_pages in transitions.items():
        for to_page, count in to_pages.items():
            all_transitions.append((from_page, to_page, count, transition_probs[from_page][to_page]))

    print("   🔄 TOP PAGE TRANSITIONS:")
    print("   From → To                          | Sessions | Probability")
    print("   -----------------------------------|----------|------------")

    for from_page, to_page, sessions, prob in sorted(all_transitions, key=lambda x: x[2], reverse=True)[:10]:
        from_display = from_page[:20] + "..." if len(from_page) > 20 else from_page
        to_display = to_page[:20] + "..." if len(to_page) > 20 else to_page
        transition_display = f"{from_display} → {to_display}"
        print(f"      {transition_display:<35} | {sessions:<8} | {prob:.2%}")
    print()

    # Identify common user journeys
    print("   🗺️  COMMON USER JOURNEYS:")
    # Simple journey patterns (this is a simplified analysis)
    journey_patterns = {
        'Homepage → Property': [],
        'Property → Contact': [],
        'Search → Property': [],
        'Valuation → Contact': []
    }

    for from_page, to_page, sessions, prob in all_transitions:
        if sessions >= 5:  # Minimum threshold
            if from_page in ['/', '/index.html'] and 'property' in to_page.lower():
                journey_patterns['Homepage → Property'].append((to_page, sessions))
            elif 'property' in from_page.lower() and 'contact' in to_page.lower():
                journey_patterns['Property → Contact'].append((to_page, sessions))
            elif 'search' in from_page.lower() and 'property' in to_page.lower():
                journey_patterns['Search → Property'].append((to_page, sessions))
            elif 'valuation' in to_page.lower() and 'contact' in to_page.lower():
                journey_patterns['Valuation → Contact'].append((to_page, sessions))

    for journey_type, paths in journey_patterns.items():
        if paths:
            print(f"   • {journey_type}: {len(paths)} common paths")
            for page, sessions in sorted(paths, key=lambda x: x[1], reverse=True)[:2]:
                page_display = page[:40] + "..." if len(page) > 40 else page
                print(f"      - {page_display} ({sessions} sessions)")
    print()

    return {'transitions': transitions, 'probabilities': transition_probs}

def analyze_behavior_patterns(start_date: str = None, end_date: str = None):
    """Analyze user behavior patterns and engagement"""

    if not start_date or not end_date:
        start_date, end_date = get_last_30_days_range()

    print("👥 Analyzing user behavior patterns...")
    print(f"   Date range: {start_date} to {end_date}")
    print("-" * 80)

    date_range = create_date_range(start_date, end_date)

    # Get behavior metrics
    response = run_report(
        dimensions=["pagePath", "sessionDefaultChannelGrouping"],
        metrics=["totalUsers", "sessions", "pageviews", "averageSessionDuration", "bounceRate", "engagementRate"],
        date_ranges=[date_range],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=50
    )

    if response.row_count == 0:
        print("❌ No behavior data found for the date range.")
        return None

    print(f"✅ Retrieved behavior data for {response.row_count} page/channel combinations")

    # Analyze behavior by channel
    behavior_data = {}
    channel_totals = {}

    for row in response.rows:
        page_path = row.dimension_values[0].value
        channel = row.dimension_values[1].value
        users = int(row.metric_values[0].value)
        sessions = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)
        bounce_rate = float(row.metric_values[4].value)
        engagement_rate = float(row.metric_values[5].value)

        if channel not in behavior_data:
            behavior_data[channel] = {}
            channel_totals[channel] = {'sessions': 0, 'pageviews': 0, 'users': 0}

        if page_path not in behavior_data[channel]:
            behavior_data[channel][page_path] = {
                'users': 0, 'sessions': 0, 'pageviews': 0,
                'avg_duration': 0, 'bounce_rate': 0, 'engagement_rate': 0
            }

        behavior_data[channel][page_path]['users'] += users
        behavior_data[channel][page_path]['sessions'] += sessions
        behavior_data[channel][page_path]['pageviews'] += pageviews

        # Weighted averages
        weight = sessions / (behavior_data[channel][page_path]['sessions'] + sessions)
        current_duration = behavior_data[channel][page_path]['avg_duration']
        current_bounce = behavior_data[channel][page_path]['bounce_rate']
        current_engagement = behavior_data[channel][page_path]['engagement_rate']

        behavior_data[channel][page_path]['avg_duration'] = current_duration * (1 - weight) + avg_duration * weight
        behavior_data[channel][page_path]['bounce_rate'] = current_bounce * (1 - weight) + bounce_rate * weight
        behavior_data[channel][page_path]['engagement_rate'] = current_engagement * (1 - weight) + engagement_rate * weight

        channel_totals[channel]['sessions'] += sessions
        channel_totals[channel]['pageviews'] += pageviews
        channel_totals[channel]['users'] += users

    print("📊 BEHAVIOR PATTERNS BY CHANNEL:")
    print("   Channel          | Sessions | Users | Avg Duration | Bounce Rate | Engagement")
    print("   -----------------|----------|-------|--------------|-------------|-----------")

    for channel, totals in channel_totals.items():
        # Calculate weighted averages for channel
        total_sessions = totals['sessions']
        avg_duration = 0
        avg_bounce = 0
        avg_engagement = 0

        for page_data in behavior_data[channel].values():
            weight = page_data['sessions'] / total_sessions
            avg_duration += page_data['avg_duration'] * weight
            avg_bounce += page_data['bounce_rate'] * weight
            avg_engagement += page_data['engagement_rate'] * weight

        channel_display = channel[:15] + "..." if len(channel) > 15 else channel
        print(f"      {channel_display:<15} | {totals['sessions']:<8,} | {totals['users']:<5,} | {avg_duration:<12.1f} | {avg_bounce:<11.1%} | {avg_engagement:<10.1%}")
    print()

    # Identify channel-specific insights
    print("   💡 CHANNEL INSIGHTS:")
    for channel, totals in channel_totals.items():
        if totals['sessions'] > 10:  # Minimum threshold
            avg_duration = sum(page_data['avg_duration'] * page_data['sessions'] for page_data in behavior_data[channel].values()) / totals['sessions']
            avg_bounce = sum(page_data['bounce_rate'] * page_data['sessions'] for page_data in behavior_data[channel].values()) / totals['sessions']

            if avg_duration < 30:
                print(f"   • {channel}: Short session duration ({avg_duration:.1f}s) - consider improving content engagement")
            if avg_bounce > 0.7:
                print(f"   • {channel}: High bounce rate ({avg_bounce:.1%}) - review landing page relevance")
            if avg_duration > 120:
                print(f"   • {channel}: Long engagement ({avg_duration:.1f}s) - good content resonance")
    print()

    return behavior_data

def analyze_user_behavior(analysis_type: str = "all", start_date: str = None, end_date: str = None):
    """Main function for user behavior analysis"""

    print("👤 User Behavior Analysis Tool")
    print("=" * 32)

    results = {}

    if analysis_type in ["flow", "all"]:
        results['flow'] = analyze_user_flow(start_date, end_date)

    if analysis_type in ["paths", "all"]:
        results['paths'] = analyze_navigation_paths(start_date, end_date)

    if analysis_type in ["patterns", "behavior", "all"]:
        results['behavior'] = analyze_behavior_patterns(start_date, end_date)

    # Export combined data
    if results:
        csv_data = []

        # Flow data
        if 'flow' in results and results['flow']:
            for page, data in results['flow'].items():
                csv_data.append({
                    'Analysis_Type': 'User_Flow',
                    'Page_Path': page,
                    'Users': data['total_users'],
                    'Sessions': data['total_sessions'],
                    'Pageviews': data['total_pageviews'],
                    'Entrances': data['total_entrances'],
                    'Exits': data['total_exits'],
                    'Metric_Type': 'Page_Metrics',
                    'Date_Range': f"{start_date}_to_{end_date}"
                })

        # Paths data
        if 'paths' in results and results['paths']:
            for from_page, to_pages in results['paths']['transitions'].items():
                for to_page, sessions in to_pages.items():
                    prob = results['paths']['probabilities'][from_page][to_page]
                    csv_data.append({
                        'Analysis_Type': 'Navigation_Paths',
                        'Page_Path': f"{from_page} → {to_page}",
                        'Users': None,
                        'Sessions': sessions,
                        'Pageviews': None,
                        'Entrances': None,
                        'Exits': None,
                        'Metric_Type': f"Transition_Prob_{prob:.3f}",
                        'Date_Range': f"{start_date}_to_{end_date}"
                    })

        # Behavior data
        if 'behavior' in results and results['behavior']:
            for channel, pages in results['behavior'].items():
                for page, data in pages.items():
                    csv_data.append({
                        'Analysis_Type': 'Behavior_Patterns',
                        'Page_Path': page,
                        'Users': data['users'],
                        'Sessions': data['sessions'],
                        'Pageviews': data['pageviews'],
                        'Entrances': None,
                        'Exits': None,
                        'Metric_Type': f"Channel_{channel.replace(' ', '_')}",
                        'Date_Range': f"{start_date}_to_{end_date}"
                    })

        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_filename = get_report_filename("user_behavior", f"{analysis_type}_{start_date}_to_{end_date}")
            df.to_csv(csv_filename, index=False)
            print(f"📄 User behavior data exported to: {csv_filename}")

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
            analyze_user_behavior(analysis_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        else:
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=days-1)
            analyze_user_behavior(analysis_type, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    else:
        print("Analyze user navigation patterns and behavior")
        print()
        print("Analysis types:")
        print("  flow      - User flow and page transitions")
        print("  paths     - Navigation paths and journeys")
        print("  patterns  - Behavior patterns by channel")
        print("  all       - Complete user behavior analysis")
        print()
        print("Usage: python user_behavior.py <analysis_type> [days]")
        print("Example: python user_behavior.py all 30")
        exit(1)