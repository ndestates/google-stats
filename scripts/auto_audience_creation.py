"""
Automated GA4 Audience Creation Script
Creates recommended audiences based on user behavior analysis and performance data
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

# Add the parent directory to sys.path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import REPORTS_DIR, GA4_PROPERTY_ID
from src.ga4_client import run_report, create_date_range
from scripts.audience_management import (
    create_page_view_audience,
    create_basic_audience,
    create_event_audience,
    get_admin_service
)
import pandas as pd


def analyze_user_behavior_for_audiences(days: int = 30):
    """Analyze user behavior to identify high-potential audience segments"""

    print("🔍 Analyzing user behavior patterns for audience creation...")
    print("=" * 80)

    # Calculate date range
    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=days-1)  # Period back

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    date_range = create_date_range(start_str, end_str)

    # Get top pages by sessions
    response = run_report(
        dimensions=["pagePath"],
        metrics=["sessions", "totalUsers", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        limit=50
    )

    audience_candidates = []

    if response.row_count > 0:
        print("📊 Top performing pages for audience creation:")
        print("-" * 80)

        for row in response.rows:
            page_path = row.dimension_values[0].value
            sessions = int(row.metric_values[0].value)
            users = int(row.metric_values[1].value)
            pageviews = int(row.metric_values[2].value)
            avg_duration = float(row.metric_values[3].value)
            bounce_rate = float(row.metric_values[4].value)

            # Skip very low traffic pages
            if users < 50:
                continue

            print(f"Page: {page_path}")
            print(f"  Users: {users}, Sessions: {sessions}, Avg Duration: {avg_duration:.1f}s, Bounce: {bounce_rate:.1%}")
            print()

            # Identify audience opportunities
            if page_path == "/valuations" and users > 100:
                audience_candidates.append({
                    'type': 'page_view',
                    'name': 'Valuation Seekers',
                    'page_path': '/valuations',
                    'description': f'Users interested in property valuations ({users} users)',
                    'priority': 'high',
                    'users': users
                })

            elif 'properties' in page_path and users > 100:
                # Extract location/property type from path
                path_parts = page_path.split('/')
                if len(path_parts) >= 3:
                    location = path_parts[2].replace('-', ' ').title()

                    # Check for specific property types and create focused audiences
                    if 'three-bedroom' in page_path.lower() and 'st-saviour' in page_path.lower():
                        audience_candidates.append({
                            'type': 'page_view',
                            'name': 'St Saviour Three Bedroom Interest',
                            'page_path': page_path,
                            'description': f'Users viewing three bedroom properties in St Saviour ({users} users)',
                            'priority': 'high',
                            'users': users
                        })
                    elif 'three-bedroom' in page_path.lower() and 'st-helier' in page_path.lower():
                        audience_candidates.append({
                            'type': 'page_view',
                            'name': 'St Helier Three Bedroom Interest',
                            'page_path': page_path,
                            'description': f'Users viewing three bedroom properties in St Helier ({users} users)',
                            'priority': 'high',
                            'users': users
                        })
                    elif 'st-saviour' in page_path.lower() and users > 500:
                        audience_candidates.append({
                            'type': 'page_view',
                            'name': 'St Saviour Property Interest',
                            'page_path': page_path,
                            'description': f'Users viewing properties in St Saviour ({users} users)',
                            'priority': 'high',
                            'users': users
                        })
                    elif 'st-helier' in page_path.lower() and users > 500:
                        audience_candidates.append({
                            'type': 'page_view',
                            'name': 'St Helier Property Interest',
                            'page_path': page_path,
                            'description': f'Users viewing properties in St Helier ({users} users)',
                            'priority': 'high',
                            'users': users
                        })
                    elif 'st-peter' in page_path.lower() and 'over-60s' in page_path.lower():
                        audience_candidates.append({
                            'type': 'page_view',
                            'name': 'Senior Housing Interest',
                            'page_path': page_path,
                            'description': f'Users viewing senior housing properties ({users} users)',
                            'priority': 'medium',
                            'users': users
                        })

            # High engagement pages (low bounce, high duration)
            if bounce_rate < 0.3 and avg_duration > 60 and users > 50:
                audience_candidates.append({
                    'type': 'page_view',
                    'name': f'High Engagement - {page_path.replace("/", "").replace("-", " ").title()}',
                    'page_path': page_path,
                    'description': f'Highly engaged users on {page_path} (low bounce, high duration)',
                    'priority': 'medium',
                    'users': users
                })

    # Remove duplicates based on name
    seen_names = set()
    unique_candidates = []
    for candidate in audience_candidates:
        if candidate['name'] not in seen_names:
            seen_names.add(candidate['name'])
            unique_candidates.append(candidate)

    return unique_candidates


def analyze_combination_audiences(days: int = 30):
    """Analyze user behavior to identify combination audiences for similar properties"""

    print("🔍 Analyzing combination audiences for similar properties...")
    print("=" * 80)

    # Calculate date range
    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=days-1)  # Period back

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    date_range = create_date_range(start_str, end_str)

    # Get all property pages
    response = run_report(
        dimensions=["pagePath"],
        metrics=["sessions", "totalUsers", "screenPageViews", "averageSessionDuration", "bounceRate"],
        date_ranges=[date_range],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        limit=100
    )

    combination_candidates = []

    if response.row_count > 0:
        # Group pages by categories
        three_bedroom_pages = []
        st_helier_pages = []
        senior_housing_pages = []
        high_engagement_pages = []

        total_three_bedroom_users = 0
        total_st_helier_users = 0
        total_senior_users = 0
        total_high_engagement_users = 0

        for row in response.rows:
            page_path = row.dimension_values[0].value
            sessions = int(row.metric_values[0].value)
            users = int(row.metric_values[1].value)
            pageviews = int(row.metric_values[2].value)
            avg_duration = float(row.metric_values[3].value)
            bounce_rate = float(row.metric_values[4].value)

            # Skip non-property pages and low traffic
            if 'properties' not in page_path or users < 20:
                continue

            # Three bedroom properties
            if 'three-bedroom' in page_path.lower():
                three_bedroom_pages.append({
                    'page_path': page_path,
                    'users': users,
                    'sessions': sessions,
                    'avg_duration': avg_duration,
                    'bounce_rate': bounce_rate
                })
                total_three_bedroom_users += users

            # St Helier properties
            if 'st-helier' in page_path.lower():
                st_helier_pages.append({
                    'page_path': page_path,
                    'users': users,
                    'sessions': sessions,
                    'avg_duration': avg_duration,
                    'bounce_rate': bounce_rate
                })
                total_st_helier_users += users

            # Senior housing
            if 'over-60s' in page_path.lower() or 'senior' in page_path.lower():
                senior_housing_pages.append({
                    'page_path': page_path,
                    'users': users,
                    'sessions': sessions,
                    'avg_duration': avg_duration,
                    'bounce_rate': bounce_rate
                })
                total_senior_users += users

            # High engagement pages
            if bounce_rate < 0.5 and avg_duration > 30 and users > 50:
                high_engagement_pages.append({
                    'page_path': page_path,
                    'users': users,
                    'sessions': sessions,
                    'avg_duration': avg_duration,
                    'bounce_rate': bounce_rate
                })
                total_high_engagement_users += users

        # Create combination audience recommendations with wildcard patterns
        if total_three_bedroom_users > 500:
            combination_candidates.append({
                'type': 'combination',
                'name': 'Three Bedroom Property Seekers',
                'description': f'Users viewing any three bedroom properties ({total_three_bedroom_users} users across {len(three_bedroom_pages)} properties)',
                'priority': 'high',
                'total_users': total_three_bedroom_users,
                'page_count': len(three_bedroom_pages),
                'category': 'three_bedroom',
                'wildcard_filter': {
                    'type': 'contains',
                    'value': 'three-bedroom'
                },
                'pages': three_bedroom_pages[:3]  # Top 3 for reference
            })

        if total_st_helier_users > 1000:
            combination_candidates.append({
                'type': 'combination',
                'name': 'St Helier Property Seekers',
                'description': f'Users viewing any properties in St Helier ({total_st_helier_users} users across {len(st_helier_pages)} properties)',
                'priority': 'high',
                'total_users': total_st_helier_users,
                'page_count': len(st_helier_pages),
                'category': 'st_helier',
                'wildcard_filter': {
                    'type': 'starts_with',
                    'value': '/properties/st-helier/'
                },
                'pages': st_helier_pages[:3]  # Top 3 for reference
            })

        if total_senior_users > 100:
            combination_candidates.append({
                'type': 'combination',
                'name': 'Senior Housing Seekers',
                'description': f'Users viewing senior housing properties ({total_senior_users} users across {len(senior_housing_pages)} properties)',
                'priority': 'medium',
                'total_users': total_senior_users,
                'page_count': len(senior_housing_pages),
                'category': 'senior_housing',
                'wildcard_filter': {
                    'type': 'contains',
                    'value': 'over-60s'
                },
                'pages': senior_housing_pages[:3]  # Top 3 for reference
            })

        if total_high_engagement_users > 200:
            combination_candidates.append({
                'type': 'combination',
                'name': 'High Engagement Property Seekers',
                'description': f'Users showing high engagement on property pages ({total_high_engagement_users} users across {len(high_engagement_pages)} properties)',
                'priority': 'medium',
                'total_users': total_high_engagement_users,
                'page_count': len(high_engagement_pages),
                'category': 'high_engagement',
                'wildcard_filter': {
                    'type': 'starts_with',
                    'value': '/properties/'
                },
                'pages': high_engagement_pages[:3]  # Top 3 for reference
            })

    return combination_candidates


def create_recommended_audiences(audience_candidates, create_all=False, priority_filter=None):
    """Create audiences based on the analysis"""

    print("🎯 Creating Recommended Audiences")
    print("=" * 80)

    created_audiences = []
    skipped_audiences = []

    # Filter by priority if specified
    if priority_filter:
        audience_candidates = [a for a in audience_candidates if a['priority'] == priority_filter]

    # Sort by priority and user count
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    audience_candidates.sort(key=lambda x: (priority_order.get(x['priority'], 3), -x.get('users', 0)))

    for candidate in audience_candidates:
        audience_type = candidate['type']
        name = candidate['name']
        priority = candidate['priority']
        users = candidate.get('users', 0)

        print(f"\n📋 Considering: {name}")
        print(f"   Type: {audience_type}, Priority: {priority}, Users: {users}")

        # Skip if not creating all and this is low priority
        if not create_all and priority == 'low':
            print("   ⏭️ Skipping low priority audience (use --create-all to include)")
            skipped_audiences.append(candidate)
            continue

        try:
            if audience_type == 'page_view':
                page_path = candidate['page_path']
                result = create_page_view_audience(
                    display_name=name,
                    page_path=page_path,
                    membership_duration_days=30
                )
                created_audiences.append(result)

            elif audience_type == 'basic':
                result = create_basic_audience(
                    display_name=name,
                    description=candidate['description'],
                    membership_duration_days=30
                )
                created_audiences.append(result)

            elif audience_type == 'event':
                event_name = candidate.get('event_name')
                if event_name:
                    result = create_event_audience(
                        display_name=name,
                        event_name=event_name,
                        membership_duration_days=30
                    )
                    created_audiences.append(result)

            print(f"   ✅ Created successfully!")

        except Exception as e:
            error_msg = str(e)
            if "SERVICE_DISABLED" in error_msg or "Admin API" in error_msg:
                print(f"   ⚠️ Admin API not enabled. Here's how to create manually:")
                print(f"      GA4 Web Interface > Admin > Audiences > Create Audience")
                print(f"      Name: {name}")
                print(f"      Description: {candidate['description']}")
                if audience_type == 'page_view':
                    print(f"      Filter: Page path contains '{candidate['page_path']}'")
                print(f"      Membership duration: 30 days")
                print()
                skipped_audiences.append(candidate)
            else:
                print(f"   ❌ Failed to create: {error_msg}")
                skipped_audiences.append(candidate)

    return created_audiences, skipped_audiences


def main():
    parser = argparse.ArgumentParser(description='Automated GA4 Audience Creation')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only analyze and show recommendations, do not create audiences')
    parser.add_argument('--create-all', action='store_true',
                       help='Create all recommended audiences including low priority ones')
    parser.add_argument('--priority', choices=['high', 'medium', 'low'],
                       help='Only create audiences of specified priority level')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days to analyze for audience recommendations (default: 30)')
    parser.add_argument('--generate-manual', action='store_true',
                       help='Generate a manual audience creation guide instead of trying to create automatically')
    parser.add_argument('--analyze-combinations', action='store_true',
                       help='Analyze and show combination audiences for similar properties')

    args = parser.parse_args()

    if not GA4_PROPERTY_ID:
        print("❌ GA4_PROPERTY_ID not found. Please check your .env file.")
        return

    # Handle combination audience analysis
    if args.analyze_combinations:
        try:
            combination_candidates = analyze_combination_audiences(args.days)

            if not combination_candidates:
                print("❌ No suitable combination audience candidates found from the analysis.")
                return

            print(f"\n🎯 Found {len(combination_candidates)} combination audiences to create")
            print("=" * 80)

            # Show combination recommendations
            for candidate in combination_candidates:
                print(f"• {candidate['name']} ({candidate['priority']} priority)")
                print(f"  {candidate['description']}")
                print(f"  📊 {candidate['page_count']} properties, {candidate['total_users']} total users")
                print("  📄 Top properties:")
                for page in candidate['pages'][:3]:  # Show top 3
                    print(f"     • {page['page_path']} ({page['users']} users)")
                print()

            print("📋 MANUAL COMBINATION AUDIENCE CREATION GUIDE")
            print("=" * 80)
            print("To create these combination audiences manually in GA4:")
            print()
            print("Steps:")
            print("1. Go to GA4 Property > Admin > Audiences")
            print("2. Click 'Create Audience' > 'Create a custom audience'")
            print("3. Use the efficient wildcard filters below (much better than listing individual pages!)")
            print()

            for candidate in combination_candidates:
                print(f"🎯 {candidate['name']} ({candidate['priority']} priority)")
                print(f"   Description: {candidate['description']}")
                wildcard = candidate.get('wildcard_filter', {})
                if wildcard:
                    filter_type = wildcard.get('type', 'contains')
                    filter_value = wildcard.get('value', '')
                    if filter_type == 'starts_with':
                        print(f"   Filter: Page path starts with '{filter_value}'")
                    elif filter_type == 'contains':
                        print(f"   Filter: Page path contains '{filter_value}'")
                    else:
                        print(f"   Filter: {filter_type} '{filter_value}'")
                else:
                    print("   Filter Type: Page path contains (OR conditions):")
                    for page in candidate['pages']:
                        print(f"     • {page['page_path']}")
                    if candidate['page_count'] > len(candidate['pages']):
                        print(f"     ... and {candidate['page_count'] - len(candidate['pages'])} more properties")
                print("   Membership duration: 30 days")
                print("   Status: Active")
                print()

            return

        except Exception as e:
            print(f"❌ Error analyzing combinations: {str(e)}")
            return

    try:
        # Analyze user behavior for audience recommendations
        audience_candidates = analyze_user_behavior_for_audiences(args.days)

        if not audience_candidates:
            print("❌ No suitable audience candidates found from the analysis.")
            return

        print(f"\n🎯 Found {len(audience_candidates)} potential audiences to create")
        print("=" * 80)

        # Show recommendations
        for candidate in audience_candidates:
            print(f"• {candidate['name']} ({candidate['priority']} priority)")
            print(f"  {candidate['description']}")
            print()

        if args.generate_manual:
            print("📋 MANUAL AUDIENCE CREATION GUIDE")
            print("=" * 80)
            print("Since the Google Analytics Admin API is not enabled, here are the audiences")
            print("you can create manually in the GA4 web interface:")
            print()
            print("Steps:")
            print("1. Go to GA4 Property > Admin > Audiences")
            print("2. Click 'Create Audience'")
            print("3. Use the settings below for each audience")
            print()

            for candidate in audience_candidates:
                if args.priority and candidate['priority'] != args.priority:
                    continue

                print(f"🎯 {candidate['name']} ({candidate['priority']} priority)")
                print(f"   Description: {candidate['description']}")
                if candidate['type'] == 'page_view':
                    print(f"   Filter: Page path contains '{candidate['page_path']}'")
                print("   Membership duration: 30 days")
                print("   Status: Active")
                print()

            return

        if args.analyze_only:
            print("📊 Analysis complete. Use without --analyze-only to create audiences.")
            return
        created, skipped = create_recommended_audiences(
            audience_candidates,
            create_all=args.create_all,
            priority_filter=args.priority
        )

        print("\n📊 SUMMARY:")
        print(f"   ✅ Created: {len(created)} audiences")
        print(f"   ⏭️ Skipped: {len(skipped)} audiences")

        if created:
            print("\n🎉 Successfully created audiences:")
            for audience in created:
                audience_id = audience['name'].split('/')[-1]
                print(f"   • {audience['displayName']} (ID: {audience_id})")

        if skipped:
            print("\n📋 Skipped audiences (use --create-all to include):")
            for audience in skipped:
                print(f"   • {audience['name']} ({audience['priority']} priority)")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()