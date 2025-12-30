"""
Google Analytics 4 Audience Management Script
Create, list, and manage audiences programmatically via the Admin API
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta

# Add the parent directory to sys.path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import GA4_PROPERTY_ID, REPORTS_DIR
from src.ga4_client import run_report, create_date_range, get_last_30_days_range
from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd
import urllib.request
import xml.etree.ElementTree as ET


def fetch_feed(feed_url: str) -> str:
    """Fetch XML feed content (standard library only)."""
    with urllib.request.urlopen(feed_url) as resp:
        return resp.read().decode("utf-8")


def parse_feed(xml_text: str):
    """Parse XML feed into a list of listings with key fields."""
    root = ET.fromstring(xml_text)
    listings = []
    # Expected structure: <xml><property>...</property></xml>
    for prop in root.findall(".//property"):
        get = lambda tag: (prop.find(tag).text.strip() if prop.find(tag) is not None and prop.find(tag).text else "")
        url = get("url")
        price_raw = get("price")
        type_ = get("type")  # 'buy' or 'rent'
        status = get("status")
        reference = get("reference")
        name = get("HouseName")
        try:
            price = int(price_raw) if price_raw else None
        except ValueError:
            price = None
        listings.append({
            "url": url,
            "price": price,
            "type": type_.lower() if type_ else "",
            "status": status.lower() if status else "",
            "reference": reference,
            "name": name
        })
    return listings


def list_existing_audience_names():
    """Return a set of existing audience display names for dedupe."""
    service = get_admin_service()
    result = service.properties().audiences().list(parent=f"properties/{GA4_PROPERTY_ID}").execute()
    names = set()
    for a in result.get("audiences", []):
        dn = a.get("displayName")
        if dn:
            names.add(dn)
    return names


def create_page_view_audience_for_urls(display_name: str, urls: list, membership_duration_days: int = 30, description: str = ""):
    """Create an audience matching page_view on any of the given URLs (OR logic)."""
    if not description:
        description = f"Users who viewed any of {len(urls)} listing URLs"

    service = get_admin_service()
    url_filters = [{
        'dimensionOrMetricFilter': {
            'fieldName': 'pageLocation',
            'stringFilter': {
                'matchType': 'CONTAINS',
                'value': u
            }
        }
    } for u in urls]

    audience = {
        'displayName': display_name,
        'description': description,
        'membershipDurationDays': membership_duration_days,
        'filterClauses': [{
            'clauseType': 'INCLUDE',
            'simpleFilter': {
                'scope': 'AUDIENCE_FILTER_SCOPE_ACROSS_ALL_SESSIONS',
                'filterExpression': {
                    'andGroup': {
                        'filterExpressions': [{
                            'orGroup': {
                                'filterExpressions': [{
                                    'eventFilter': {
                                        'eventName': 'page_view',
                                        'eventParameterFilterExpression': {
                                            'andGroup': {
                                                'filterExpressions': [{
                                                    'orGroup': {
                                                        'filterExpressions': url_filters
                                                    }
                                                }]
                                            }
                                        }
                                    }
                                }]
                            }
                        }]
                    }
                }
            }
        }]
    }

    request = service.properties().audiences().create(
        parent=f'properties/{GA4_PROPERTY_ID}',
        body=audience
    ).execute()

    print(f"✅ Created audience: {request['displayName']} (ID: {request['name'].split('/')[-1]})")
    return request


def assign_price_band(price: int):
    """Return a canonical price band label for buy listings."""
    if price is None:
        return None
    bands = [
        (200_000, 400_000, "[Combination] - £200K-400K"),
        (400_000, 600_000, "[Combination] - £400K-600K"),
        (600_000, 800_000, "[Combination] - £600K-800K"),
        (800_000, 1_000_000, "[Combination] - £800K-1M"),
    ]
    for lo, hi, label in bands:
        if lo <= price < hi:
            return label
    if price >= 1_000_000:
        return "[Combination] - £1M+"
    return None


def get_admin_service():
    """Get authenticated Google Analytics Admin API service"""

    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv("GA4_KEY_PATH"),
        scopes=['https://www.googleapis.com/auth/analytics.edit']
    )

    # Build the service
    service = build('analyticsadmin', 'v1alpha', credentials=credentials)
    return service


def get_google_ads_service():
    """Get authenticated Google Ads API service"""
    try:
        from google.ads.googleads.client import GoogleAdsClient
        from src.config import load_google_ads_config

        # Load Google Ads configuration
        ads_config = load_google_ads_config()
        if not ads_config:
            return None

        client = GoogleAdsClient.load_from_dict(ads_config)
        return client
    except ImportError:
        print("⚠️ Google Ads API not available. Install with: pip install google-ads")
        return None
    except Exception as e:
        print(f"⚠️ Could not initialize Google Ads client: {e}")
        return None


def check_audience_campaign_usage(audience_ids):
    """Check if audiences are used in active Google Ads campaigns"""

    client = get_google_ads_service()
    if not client:
        return {}

    usage_data = {}
    try:
        # This is a simplified check - in reality you'd need to query campaigns
        # and check their audience targeting settings
        ga_service = client.get_service("GoogleAdsService")

        # For each audience, check if it's used in campaigns
        for audience_id in audience_ids:
            usage_data[audience_id] = {
                'used_in_campaigns': False,
                'campaign_count': 0,
                'campaign_names': []
            }

        # Note: Full implementation would require querying campaign audience targeting
        # This is a placeholder for the concept

    except Exception as e:
        print(f"⚠️ Error checking campaign usage: {e}")

    return usage_data


def get_audience_sizes(audience_ids=None):
    """Get user counts for audiences over the last 30 days"""

    # Get date range for last 30 days
    start_date, end_date = get_last_30_days_range()

    # Build dimensions for audience analysis
    dimensions = ["audienceId", "audienceName"]
    metrics = ["totalUsers", "sessions", "screenPageViews"]

    date_range = create_date_range(start_date, end_date)

    response = run_report(
        dimensions=dimensions,
        metrics=metrics,
        date_ranges=[date_range],
        limit=1000,
    )

    audience_data = {}
    if response.row_count > 0:
        for row in response.rows:
            audience_id = row.dimension_values[0].value
            audience_name = row.dimension_values[1].value
            users = int(row.metric_values[0].value)
            sessions = int(row.metric_values[1].value)
            pageviews = int(row.metric_values[2].value)

            audience_data[audience_id] = {
                'name': audience_name,
                'users': users,
                'sessions': sessions,
                'pageviews': pageviews,
                'avg_session_duration': 0,  # Will be added if needed
                'bounce_rate': 0
            }

    return audience_data


def create_basic_audience(display_name: str, description: str = "", membership_duration_days: int = 30):
    """Create a basic audience with all users"""

    if not description:
        description = f"All users audience: {display_name}"

    service = get_admin_service()

    audience = {
        'displayName': display_name,
        'description': description,
        'membershipDurationDays': membership_duration_days
    }

    request = service.properties().audiences().create(
        parent=f'properties/{GA4_PROPERTY_ID}',
        body=audience
    ).execute()

    print(f"✅ Created audience: {request['displayName']} (ID: {request['name'].split('/')[-1]})")
    return request


def create_page_view_audience(display_name: str, page_path: str, membership_duration_days: int = 30):
    """Create an audience based on page views"""

    service = get_admin_service()

    audience = {
        'displayName': display_name,
        'description': f"Users who viewed {page_path}",
        'membershipDurationDays': membership_duration_days,
        'filterClauses': [{
            'clauseType': 'INCLUDE',
            'simpleFilter': {
                'scope': 'AUDIENCE_FILTER_SCOPE_ACROSS_ALL_SESSIONS',
                'filterExpression': {
                    'andGroup': {
                        'filterExpressions': [{
                            'orGroup': {
                                'filterExpressions': [{
                                    'eventFilter': {
                                        'eventName': 'page_view',
                                        'eventParameterFilterExpression': {
                                            'andGroup': {
                                                'filterExpressions': [{
                                                    'orGroup': {
                                                        'filterExpressions': [{
                                                            'dimensionOrMetricFilter': {
                                                                'fieldName': 'pageLocation',
                                                                'stringFilter': {
                                                                    'matchType': 'CONTAINS',
                                                                    'value': page_path
                                                                }
                                                            }
                                                        }]
                                                    }
                                                }]
                                            }
                                        }
                                    }
                                }]
                            }
                        }]
                    }
                }
            }
        }]
    }

    request = service.properties().audiences().create(
        parent=f'properties/{GA4_PROPERTY_ID}',
        body=audience
    ).execute()

    print(f"✅ Created page view audience: {request['displayName']} (ID: {request['name'].split('/')[-1]})")
    return request


def create_event_audience(display_name: str, event_name: str, membership_duration_days: int = 30):
    """Create an audience based on event completion"""

    service = get_admin_service()

    audience = {
        'displayName': display_name,
        'description': f"Users who completed {event_name} event",
        'membershipDurationDays': membership_duration_days,
        'filterClauses': [{
            'clauseType': 'INCLUDE',
            'simpleFilter': {
                'scope': 'AUDIENCE_FILTER_SCOPE_ACROSS_ALL_SESSIONS',
                'filterExpression': {
                    'andGroup': {
                        'filterExpressions': [{
                            'orGroup': {
                                'filterExpressions': [{
                                    'eventFilter': {
                                        'eventName': event_name
                                    }
                                }]
                            }
                        }]
                    }
                }
            }
        }]
    }

    request = service.properties().audiences().create(
        parent=f'properties/{GA4_PROPERTY_ID}',
        body=audience
    ).execute()

    print(f"✅ Created event audience: {request['displayName']} (ID: {request['name'].split('/')[-1]})")
    return request


def create_cart_abandoner_audience(display_name: str = "Cart Abandoners", membership_duration_days: int = 7):
    """Create an audience for users who added to cart but didn't purchase"""

    service = get_admin_service()

    audience = {
        'displayName': display_name,
        'description': "Users who added items to cart but didn't complete purchase",
        'membershipDurationDays': membership_duration_days,
        'filterClauses': [
            {
                'clauseType': 'INCLUDE',
                'simpleFilter': {
                    'scope': 'AUDIENCE_FILTER_SCOPE_ACROSS_ALL_SESSIONS',
                    'filterExpression': {
                        'andGroup': {
                            'filterExpressions': [{
                                'orGroup': {
                                    'filterExpressions': [{
                                        'eventFilter': {
                                            'eventName': 'add_to_cart'
                                        }
                                    }]
                                }
                            }]
                        }
                    }
                }
            },
            {
                'clauseType': 'EXCLUDE',
                'simpleFilter': {
                    'scope': 'AUDIENCE_FILTER_SCOPE_ACROSS_ALL_SESSIONS',
                    'filterExpression': {
                        'andGroup': {
                            'filterExpressions': [{
                                'orGroup': {
                                    'filterExpressions': [{
                                        'eventFilter': {
                                            'eventName': 'purchase'
                                        }
                                    }]
                                }
                            }]
                        }
                    }
                }
            }
        ]
    }

    request = service.properties().audiences().create(
        parent=f'properties/{GA4_PROPERTY_ID}',
        body=audience
    ).execute()

    print(f"✅ Created cart abandoner audience: {request['displayName']} (ID: {request['name'].split('/')[-1]})")
    return request


def list_audiences(include_metrics=False, analyze_performance=False):
    """List all audiences for the property with optional metrics and analysis"""

    service = get_admin_service()

    audiences = service.properties().audiences().list(
        parent=f'properties/{GA4_PROPERTY_ID}'
    ).execute()

    print(f"\n📋 Audiences for property {GA4_PROPERTY_ID}:")
    print("=" * 100)

    if 'audiences' in audiences:
        # Get audience sizes if requested
        audience_sizes = {}
        campaign_usage = {}

        if include_metrics or analyze_performance:
            audience_sizes = get_audience_sizes()

        if analyze_performance:
            audience_ids = [audience['name'].split('/')[-1] for audience in audiences['audiences']]
            campaign_usage = check_audience_campaign_usage(audience_ids)

        low_threshold_audiences = []

        for audience in audiences['audiences']:
            audience_id = audience['name'].split('/')[-1]
            status = "Active" if audience.get('state') == 'ACTIVE' else "Inactive"

            print(f"ID: {audience_id}")
            print(f"Name: {audience['displayName']}")
            print(f"Description: {audience.get('description', 'N/A')}")
            print(f"Status: {status}")
            print(f"Membership Duration: {audience.get('membershipDurationDays', 'N/A')} days")

            # Show metrics if available
            if include_metrics and audience_id in audience_sizes:
                metrics = audience_sizes[audience_id]
                print(f"Users (30d): {metrics['users']:,}")
                print(f"Sessions (30d): {metrics['sessions']:,}")
                print(f"Pageviews (30d): {metrics['pageviews']:,}")

                # Check for low user threshold
                if metrics['users'] < 100:  # Threshold for "low"
                    low_threshold_audiences.append({
                        'id': audience_id,
                        'name': audience['displayName'],
                        'users': metrics['users'],
                        'audience': audience
                    })

            # Show campaign usage if available
            if analyze_performance and audience_id in campaign_usage:
                usage = campaign_usage[audience_id]
                if usage['used_in_campaigns']:
                    print(f"Campaign Usage: Used in {usage['campaign_count']} campaigns")
                else:
                    print("Campaign Usage: Not used in active campaigns")

            print("-" * 60)

        # Provide analysis and recommendations for low-performing audiences
        if analyze_performance and low_threshold_audiences:
            print(f"\n🔍 ANALYSIS: {len(low_threshold_audiences)} audiences with low user counts (< 100 users in 30 days)")
            print("=" * 100)

            for item in low_threshold_audiences:
                audience = item['audience']
                audience_id = item['id']
                audience_name = item['name']
                user_count = item['users']

                print(f"\n🎯 Audience: {audience_name} (ID: {audience_id})")
                print(f"   Users in last 30 days: {user_count}")

                # Check campaign usage
                if audience_id in campaign_usage and not campaign_usage[audience_id]['used_in_campaigns']:
                    print("   ❌ Not used in any active campaigns")
                    print("   💡 RECOMMENDATION: Consider deleting this unused audience")
                else:
                    print("   ⚠️ Used in campaigns but low engagement")

                # Analyze audience filters to suggest improvements
                if 'filterClauses' in audience:
                    filters = audience['filterClauses']
                    print("   📊 Current filters:")
                    for i, filter_clause in enumerate(filters, 1):
                        if 'simpleFilter' in filter_clause:
                            filter_info = filter_clause['simpleFilter']
                            if 'dimensionOrMetricFilter' in filter_info:
                                field = filter_info['dimensionOrMetricFilter']['fieldName']
                                print(f"      {i}. {field}")

                    # Provide improvement suggestions
                    print("   💡 IMPROVEMENT SUGGESTIONS:")
                    if user_count < 10:
                        print("      - Audience is extremely small, consider broadening criteria")
                        print("      - Check if the page/event still exists")
                        print("      - Consider combining with similar audiences")
                    elif user_count < 50:
                        print("      - Try reducing membership duration for more recent users")
                        print("      - Consider adding additional qualifying criteria")
                        print("      - Check if targeting is too narrow")
                    else:
                        print("      - Monitor performance over next 30 days")
                        print("      - Consider A/B testing with slightly broader criteria")
                else:
                    print("   📊 Audience type: All users (no specific filters)")
                    print("   💡 This is a basic audience - consider adding specific targeting")

                print("-" * 40)

    else:
        print("No audiences found.")

    return audiences.get('audiences', [])


def delete_audience(audience_id: str):
    """Delete an audience by ID"""

    service = get_admin_service()

    audience_name = f'properties/{GA4_PROPERTY_ID}/audiences/{audience_id}'

    service.properties().audiences().delete(
        name=audience_name
    ).execute()

    print(f"🗑️ Deleted audience: {audience_id}")


def generate_audiences_from_feed(
    feed_url: str,
    scope: str = "both",
    include_rent: bool = False,
    limit: int = 0,
    duration: int = 30,
    dry_run: bool = True,
):
    """Generate audiences from external XML feed per listing and price bands."""
    xml_text = fetch_feed(feed_url)
    listings = parse_feed(xml_text)

    # Filter available listings and, optionally, type
    available = [
        l for l in listings
        if (l.get("status") == "available") and (include_rent or l.get("type") == "buy")
    ]

    existing_names = list_existing_audience_names()
    created_count = 0

    def can_create_more():
        return (limit <= 0) or (created_count < limit)

    # Per-listing audiences
    if scope in ("listing", "both"):
        for l in available:
            if not can_create_more():
                break
            url = l.get("url") or ""
            if not url:
                continue
            property_name = l.get("name") or ""
            ref = l.get("reference") or ""
            # Use property name if available, otherwise fall back to reference
            base_name = property_name if property_name else ref
            display_name = f"[Listing] - {base_name}" if base_name else f"[Listing] - {url[:80]}"
            if display_name in existing_names:
                print(f"⏭️ Skip existing audience: {display_name}")
                continue
            if dry_run:
                print(f"DRY-RUN: Would create audience '{display_name}' for URL: {url}")
            else:
                create_page_view_audience(display_name, url, membership_duration_days=duration)
            created_count += 1

    # Price band audiences (buy only)
    if scope in ("price-bands", "both"):
        band_to_urls = {}
        for l in available:
            if l.get("type") != "buy":
                continue
            band = assign_price_band(l.get("price"))
            if not band:
                continue
            url = l.get("url") or ""
            if not url:
                continue
            band_to_urls.setdefault(band, []).append(url)

        for band_label, urls in band_to_urls.items():
            if not can_create_more():
                break
            display_name = band_label
            if display_name in existing_names:
                print(f"⏭️ Skip existing audience: {display_name}")
                continue
            # Cap to reasonable number of URLs per audience to avoid overly large filters
            capped_urls = urls[:200]
            if dry_run:
                print(f"DRY-RUN: Would create audience '{display_name}' for {len(capped_urls)} URLs (band total: {len(urls)})")
            else:
                create_page_view_audience_for_urls(display_name, capped_urls, membership_duration_days=duration,
                                                   description=f"Buy listings in {band_label}")
            created_count += 1

    print(f"✅ Generation complete. Audiences processed: {created_count}")


def main():
    parser = argparse.ArgumentParser(description='Google Analytics 4 Audience Management')
    parser.add_argument('--action', choices=['create', 'list', 'delete', 'analyze', 'generate-from-feed'], required=True,
                       help='Action to perform')
    parser.add_argument('--type', choices=['basic', 'page', 'event', 'cart-abandoners'],
                       help='Type of audience to create (required for create action)')
    parser.add_argument('--name', help='Display name for the audience')
    parser.add_argument('--page-path', help='Page path for page-view audience')
    parser.add_argument('--event-name', help='Event name for event-based audience')
    parser.add_argument('--audience-id', help='Audience ID for delete action')
    parser.add_argument('--duration', type=int, default=30,
                       help='Membership duration in days (default: 30)')
    parser.add_argument('--include-metrics', action='store_true',
                       help='Include user count metrics when listing audiences')
    parser.add_argument('--analyze-performance', action='store_true',
                       help='Analyze audience performance and provide recommendations')
    # Feed generation flags
    parser.add_argument('--feed-url', default='https://api.ndestates.com/feeds/ndefeed.xml',
                        help='XML feed URL for listings (default: ND Estates feed)')
    parser.add_argument('--scope', choices=['listing', 'price-bands', 'both'], default='both',
                        help='Which audiences to generate from feed')
    parser.add_argument('--include-rent', action='store_true',
                        help='Include rent listings (default: only buy)')
    parser.add_argument('--limit', type=int, default=0,
                        help='Maximum audiences to create in this run (0 = no limit)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print actions without creating audiences')

    args = parser.parse_args()

    if not GA4_PROPERTY_ID:
        print("❌ GA4_PROPERTY_ID not found. Please check your .env file.")
        return

    try:
        if args.action == 'create':
            if not args.type:
                print("❌ --type is required for create action")
                return

            if not args.name:
                print("❌ --name is required for create action")
                return

            if args.type == 'basic':
                create_basic_audience(args.name, membership_duration_days=args.duration)

            elif args.type == 'page':
                if not args.page_path:
                    print("❌ --page-path is required for page audience")
                    return
                create_page_view_audience(args.name, args.page_path, args.duration)

            elif args.type == 'event':
                if not args.event_name:
                    print("❌ --event-name is required for event audience")
                    return
                create_event_audience(args.name, args.event_name, args.duration)

            elif args.type == 'cart-abandoners':
                create_cart_abandoner_audience(args.name or "Cart Abandoners", args.duration)

        elif args.action == 'list':
            list_audiences(include_metrics=args.include_metrics, analyze_performance=args.analyze_performance)

        elif args.action == 'analyze':
            # Analyze is just list with performance analysis
            list_audiences(include_metrics=True, analyze_performance=True)

        elif args.action == 'delete':
            if not args.audience_id:
                print("❌ --audience-id is required for delete action")
                return
            delete_audience(args.audience_id)

        elif args.action == 'generate-from-feed':
            generate_audiences_from_feed(
                feed_url=args.feed_url,
                scope=args.scope,
                include_rent=args.include_rent,
                limit=args.limit,
                duration=args.duration,
                dry_run=args.dry_run or False,
            )

    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()

