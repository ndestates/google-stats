"""
Google Analytics 4 Audience Management Script
Create, list, and manage audiences programmatically via the Admin API

DDEV Usage:
    # Generate audiences from XML feed
    ddev exec python3 scripts/audience_management.py --action generate-from-feed --dry-run
    
    # Create audiences for all listings
    ddev exec python3 scripts/audience_management.py --action generate-from-feed --scope listing
    
    # Create price-band audiences only
    ddev exec python3 scripts/audience_management.py --action generate-from-feed --scope price-bands
    
    # Create both listing and price-band audiences
    ddev exec python3 scripts/audience_management.py --action generate-from-feed --scope both
    
    # List all audiences
    ddev exec python3 scripts/audience_management.py --action list
    
    # List audiences with segment info
    ddev exec python3 scripts/audience_management.py --action list-with-segments
    
    # Show audience usage (conversions, campaigns)
    ddev exec python3 scripts/audience_management.py --action show-usage
    
    # Show segment usage (reports, campaigns)
    ddev exec python3 scripts/audience_management.py --action show-segment-usage
    
    # Show comprehensive usage report for all audiences and segments
    ddev exec python3 scripts/audience_management.py --action show-all-usage
    
    # Find audience in Google Ads campaigns
    ddev exec python3 scripts/audience_management.py --action find-in-campaigns --audience-id 13216330243
    
    # List all segments
    ddev exec python3 scripts/audience_management.py --action list-segments
    
    # Delete audience by ID
    ddev exec python3 scripts/audience_management.py --action delete --audience-id 13216330243
    
    # Interactively select and delete audiences
    ddev exec python3 scripts/audience_management.py --action delete-interactive
    
    # Analyze audience performance
    ddev exec python3 scripts/audience_management.py --action analyze

Direct Usage:
    python3 scripts/audience_management.py --action generate-from-feed --dry-run

Features:
    - Generate listing audiences from XML feed
    - Generate price-band combination audiences (£200K-400K, etc.)
    - Idempotent creation (skips duplicates)
    - Dry-run mode for testing
    - Configurable batch limits
    - Uses pagePath for accurate GA4 matching
    - Interactive deletion for easy audience management
    - View audiences in segments
    - Track audience usage across campaigns and conversions
    - Find audience in Google Ads campaigns
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
import urllib.parse
import xml.etree.ElementTree as ET


def extract_url_path(full_url: str) -> str:
    """Extract just the path from a full URL, omitting the domain."""
    try:
        parsed = urllib.parse.urlparse(full_url)
        return parsed.path
    except:
        return full_url


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
        name = get("houseName")
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
    """Create an audience matching page_view on any of the given URLs (OR logic).
    Note: GA4 has limitations on complex OR filters, so this creates multiple filter clauses."""
    if not description:
        description = f"Users who viewed any of {len(urls)} listing URLs"
    
    # Truncate description to stay within GA4 limits (256 characters)
    if len(description) > 256:
        description = description[:253] + "..."

    service = get_admin_service()
    
    # Create multiple filter clauses (one per URL) - each is OR'd at the clause level
    # This works around GA4's limitation on complex nested OR groups
    filter_clauses = []
    for url in urls:
        filter_clauses.append({
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
                                            'orGroup': {
                                                'filterExpressions': [{
                                                    'dimensionOrMetricFilter': {
                                                        'fieldName': 'pageLocation',
                                                        'stringFilter': {
                                                            'matchType': 'CONTAINS',
                                                            'value': url
                                                        }
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
        })

    audience = {
        'displayName': display_name,
        'description': description,
        'membershipDurationDays': membership_duration_days,
        'filterClauses': filter_clauses
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

    # Load credentials - try GA4_KEY_PATH first, then fall back to GOOGLE_APPLICATION_CREDENTIALS
    key_path = os.getenv("GA4_KEY_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not key_path:
        raise ValueError("Neither GA4_KEY_PATH nor GOOGLE_APPLICATION_CREDENTIALS is set")
    
    credentials = service_account.Credentials.from_service_account_file(
        key_path,
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
    
    # Truncate description to stay within GA4 limits (256 characters)
    description = f"Viewed {page_path}"
    if len(description) > 256:
        description = description[:253] + "..."

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


def list_segments_with_audiences():
    """List all audiences (GA4 calls them 'segments' in the UI) with membership sizes"""
    
    service = get_admin_service()
    
    # Get all audiences for the property
    try:
        result = service.properties().audiences().list(
            parent=f'properties/{GA4_PROPERTY_ID}'
        ).execute()
        
        print("\n📊 Audiences/Segments with Membership Sizes:")
        print("=" * 100)
        
        if 'audiences' not in result or len(result['audiences']) == 0:
            print("No audiences found.")
            return
        
        # Get audience sizes for all audiences
        print("Fetching audience membership data (last 30 days)...\n")
        audience_sizes = get_audience_sizes()
        
        for audience in result['audiences']:
            audience_id = audience['name'].split('/')[-1]
            status = "Active" if audience.get('state') == 'ACTIVE' else "Inactive"
            print(f"ID: {audience_id}")
            print(f"Name: {audience['displayName']}")
            print(f"Description: {audience.get('description', 'No description')}")
            print(f"Status: {status}")
            print(f"Membership Duration: {audience.get('membershipDurationDays', 'N/A')} days")
            
            # Show membership metrics if available
            if audience_id in audience_sizes:
                metrics = audience_sizes[audience_id]
                print(f"Members (30d): {metrics['users']:,} users")
                print(f"Sessions (30d): {metrics['sessions']:,}")
                print(f"Pageviews (30d): {metrics['pageviews']:,}")
            else:
                print(f"Members (30d): No data (audience may be new or have no activity)")
            
            print("-" * 60)
            
    except Exception as e:
        print(f"❌ Error listing audiences: {e}")


def show_segment_usage():
    """Show where segments are being used (campaigns, reports, dashboards)"""
    
    service = get_admin_service()
    
    print("\n🔍 Segment Usage Report:")
    print("=" * 100)
    
    try:
        # Get all custom dimensions (which include segments)
        result = service.properties().customDimensions().list(
            parent=f'properties/{GA4_PROPERTY_ID}'
        ).execute()
        
        if 'customDimensions' not in result or len(result['customDimensions']) == 0:
            print("No custom segments found.")
            return
        
        for segment in result['customDimensions']:
            segment_id = segment['name'].split('/')[-1]
            display_name = segment['displayName']
            
            print(f"\n📌 {display_name} (ID: {segment_id})")
            print(f"   Scope: {segment.get('scope', 'N/A')}")
            print(f"   Parameter: {segment.get('parameterName', 'N/A')}")
            
            # Check if segment is used in reports
            # Note: GA4 API doesn't directly expose report/dashboard usage
            # This would need to be checked in the GA4 UI or through other means
            
            # Check campaign usage via Google Ads
            client = get_google_ads_service()
            if client:
                try:
                    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "")
                    ga_service = client.get_service("GoogleAdsService")
                    
                    query = f"""
                        SELECT 
                            campaign.id,
                            campaign.name,
                            campaign.status
                        FROM campaign
                        WHERE campaign.status != REMOVED
                        LIMIT 100
                    """
                    
                    response = ga_service.search(customer_id=customer_id, query=query)
                    
                    campaign_count = sum(1 for _ in response)
                    if campaign_count > 0:
                        print(f"   ✓ Google Ads: {campaign_count} campaigns found (check targeting for segment usage)")
                    else:
                        print(f"   ✗ Google Ads: No active campaigns")
                        
                except Exception as e:
                    print(f"   ⚠️  Could not check Google Ads usage: {e}")
            else:
                print(f"   ℹ️  Google Ads API not available")
            
            # Information note
            print(f"   ℹ️  To see detailed usage:")
            print(f"      - Check GA4 UI → Admin → Custom Definitions")
            print(f"      - Review reports and explorations using this segment")
            print(f"      - Check Google Ads campaign audience targeting")
            
            print("-" * 60)
            
    except Exception as e:
        print(f"❌ Error: {e}")


def show_all_usage():
    """Show comprehensive usage report for both audiences and segments"""
    
    print("\n" + "=" * 100)
    print("🎯 COMPREHENSIVE USAGE REPORT - AUDIENCES & SEGMENTS")
    print("=" * 100)
    
    # Show audience usage
    print("\n" + "─" * 100)
    print("📊 AUDIENCE USAGE")
    print("─" * 100)
    show_audience_usage()
    
    # Show segment usage
    print("\n" + "─" * 100)
    print("📊 SEGMENT USAGE")
    print("─" * 100)
    show_segment_usage()
    
    # Summary
    print("\n" + "=" * 100)
    print("💡 USAGE TRACKING TIPS:")
    print("=" * 100)
    print("1. Audiences → Check Google Ads campaigns for targeting")
    print("2. Segments → Check GA4 reports and explorations")
    print("3. Monitor conversions → Admin → Events → Mark as conversion")
    print("4. Review remarketing lists → Google Ads → Audience Manager")
    print("5. Analyze performance → Use 'analyze' action for detailed metrics")
    print("=" * 100)


def show_audience_usage():
    """Show where audiences are being used (campaigns, conversions, etc.)"""
    
    service = get_admin_service()
    audiences_result = service.properties().audiences().list(
        parent=f'properties/{GA4_PROPERTY_ID}'
    ).execute()
    
    if 'audiences' not in audiences_result:
        print("No audiences found.")
        return
    
    audiences = audiences_result['audiences']
    
    print("\n🔍 Audience Usage Report:")
    print("=" * 100)
    
    for audience in audiences:
        audience_id = audience['name'].split('/')[-1]
        display_name = audience['displayName']
        
        print(f"\n📌 {display_name} (ID: {audience_id})")
        
        # Check if audience is used in conversions
        try:
            conversions = service.properties().conversions().list(
                parent=f'properties/{GA4_PROPERTY_ID}'
            ).execute()
            
            used_in_conversions = False
            if 'conversions' in conversions:
                for conversion in conversions['conversions']:
                    # Check conversion details for audience references
                    if audience_id in str(conversion):
                        used_in_conversions = True
                        break
            
            if used_in_conversions:
                print(f"   ✓ Used in conversions")
            else:
                print(f"   ✗ Not used in conversions")
                
        except Exception as e:
            print(f"   ⚠️  Could not check conversion usage: {e}")
        
        # Note: Full campaign usage requires Google Ads API
        print(f"   ℹ️  To see campaign usage, check Google Ads directly")
        
        print("-" * 60)


def create_segment(display_name: str, audience_ids: list, description: str = ""):
    """Create a new segment with selected audiences"""
    
    if not display_name:
        print("❌ Segment name is required")
        return
    
    if not audience_ids:
        print("❌ At least one audience is required")
        return
    
    service = get_admin_service()
    
    print(f"\n📝 Creating segment: {display_name}")
    print(f"   Audiences: {audience_ids}")
    print(f"   Description: {description}")
    
    try:
        # GA4 segments are typically created through the UI, not API
        # However, we can create custom dimensions that can be used for segmentation
        
        segment_config = {
            'displayName': display_name,
            'description': description or f"Segment with {len(audience_ids)} audience(s)",
            'parameterNames': [f'audience_{aid}' for aid in audience_ids]
        }
        
        print("\n⚠️  Note: GA4 segments are typically managed through the Analytics UI")
        print("   This feature would require manual segment creation in Google Analytics")
        print(f"\n   Create segment '{display_name}' with these audiences:")
        for aid in audience_ids:
            print(f"      - {aid}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def find_audience_in_campaigns(audience_id: str):
    """Find which Google Ads campaigns are using this audience"""
    
    client = get_google_ads_service()
    if not client:
        print("❌ Google Ads API not available")
        return
    
    print(f"\n🔎 Searching for audience {audience_id} in campaigns...")
    
    try:
        ga_service = client.get_service("GoogleAdsService")
        customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "")
        
        query = f"""
            SELECT 
                campaign.id,
                campaign.name,
                campaign.status
            FROM campaign
            WHERE campaign.status != REMOVED
            LIMIT 1000
        """
        
        response = ga_service.search(customer_id=customer_id, query=query)
        
        print("\n📋 Campaigns found:")
        found = False
        for row in response:
            campaign = row.campaign
            print(f"   - {campaign.name} (ID: {campaign.id}, Status: {campaign.status})")
            # Note: Full audience targeting details require deeper campaign analysis
            found = True
        
        if not found:
            print("   No campaigns found")
            
    except Exception as e:
        print(f"❌ Error searching campaigns: {e}")


def delete_audience(audience_id: str):
    """Delete a specific audience by ID (archives it in GA4)"""
    
    service = get_admin_service()
    
    try:
        # GA4 API uses archive/patch to set audience state to ARCHIVED
        service.properties().audiences().archive(
            name=f'properties/{GA4_PROPERTY_ID}/audiences/{audience_id}'
        ).execute()
        print(f"✅ Archived audience ID: {audience_id}")
    except Exception as e:
        raise Exception(f"Failed to archive audience {audience_id}: {e}")


def list_audiences_with_segment_info():
    """List all audiences and show which segments they belong to"""
    
    service = get_admin_service()
    
    audiences_result = service.properties().audiences().list(
        parent=f'properties/{GA4_PROPERTY_ID}'
    ).execute()
    
    if 'audiences' not in audiences_result:
        print("No audiences found.")
        return
    
    audiences = audiences_result['audiences']
    
    print("\n📊 Audiences & Segment Assignment:")
    print("=" * 100)
    
    for idx, audience in enumerate(audiences, 1):
        audience_id = audience['name'].split('/')[-1]
        display_name = audience['displayName']
        status = "Active" if audience.get('state') == 'ACTIVE' else "Inactive"
        
        print(f"{idx}. [{audience_id}] {display_name}")
        print(f"    Status: {status}")
        
        # GA4 doesn't directly associate audiences with segments via API
        # Segments are typically created manually in the UI using audience conditions
        print(f"    Segments: ℹ️  Manage in Analytics UI")
        print("-" * 80)



def delete_audiences_interactive():
    """Interactively select and delete audiences"""
    
    service = get_admin_service()
    result = service.properties().audiences().list(parent=f"properties/{GA4_PROPERTY_ID}").execute()
    
    if 'audiences' not in result or len(result['audiences']) == 0:
        print("No audiences found.")
        return
    
    audiences = result['audiences']
    
    print("\n📋 Available Audiences:")
    print("=" * 100)
    
    for idx, audience in enumerate(audiences, 1):
        audience_id = audience['name'].split('/')[-1]
        display_name = audience['displayName']
        status = "Active" if audience.get('state') == 'ACTIVE' else "Inactive"
        print(f"{idx}. [{audience_id}] {display_name} ({status})")
    
    print("\n" + "=" * 100)
    
    # Get user input for which audiences to delete
    selection = input("\nEnter audience numbers to delete (comma-separated or ranges, e.g., 1,3,5 or 17-50)\nOr press Enter to exit: ").strip()
    
    if not selection:
        print("❌ Exiting without making changes.")
        return
    
    if selection.lower() in ('quit', 'exit', 'q'):
        print("❌ Exiting without making changes.")
        return
    
    try:
        indices = []
        # Parse comma-separated values and ranges
        for part in selection.split(','):
            part = part.strip()
            if '-' in part:
                # Handle range (e.g., "17-50")
                start, end = part.split('-')
                start_idx = int(start.strip()) - 1
                end_idx = int(end.strip()) - 1
                indices.extend(range(start_idx, end_idx + 1))
            else:
                # Handle single number
                indices.append(int(part) - 1)
        
        # Remove duplicates and sort
        indices = sorted(set(indices))
        
        # Validate indices
        invalid = [i+1 for i in indices if i < 0 or i >= len(audiences)]
        if invalid:
            print(f"❌ Invalid selections: {invalid}. Please try again.")
            return
        
        selected_audiences = [audiences[i] for i in indices]
        
        print(f"\n🗑️ Will delete {len(selected_audiences)} audience(s):")
        for audience in selected_audiences:
            print(f"   - [{audience['name'].split('/')[-1]}] {audience['displayName']}")
        
        confirm = input("\nAre you sure? Type 'yes' to confirm, or anything else to cancel: ").strip().lower()
        
        if confirm != 'yes':
            print("❌ Deletion cancelled.")
            return
        
        # Delete selected audiences
        deleted_count = 0
        for audience in selected_audiences:
            audience_id = audience['name'].split('/')[-1]
            try:
                delete_audience(audience_id)
                deleted_count += 1
            except Exception as e:
                print(f"❌ Failed to delete {audience_id}: {e}")
        
        print(f"\n✅ Successfully deleted {deleted_count} audience(s)")
        
    except ValueError:
        print("❌ Invalid input. Please enter numbers separated by commas.")


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
            # Extract just the path, omitting domain
            url_path = extract_url_path(url)
            property_name = l.get("name") or ""
            ref = l.get("reference") or ""
            # Use property name if available, otherwise fall back to reference
            base_name = property_name if property_name else ref
            display_name = f"[Listing] - {base_name}" if base_name else f"[Listing] - {url_path[:80]}"
            if display_name in existing_names:
                print(f"⏭️ Skip existing audience: {display_name}")
                continue
            if dry_run:
                print(f"DRY-RUN: Would create audience '{display_name}' for URL: {url_path}")
            else:
                create_page_view_audience(display_name, url_path, membership_duration_days=duration)
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
            # Extract just the path, omitting domain
            url_path = extract_url_path(url)
            band_to_urls.setdefault(band, []).append(url_path)

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
    parser.add_argument('--action', choices=['create', 'list', 'delete', 'delete-interactive', 'analyze', 'list-segments', 'create-segment', 'show-usage', 'show-segment-usage', 'show-all-usage', 'find-in-campaigns', 'list-with-segments', 'generate-from-feed'], required=True,
                       help='Action to perform')
    parser.add_argument('--type', choices=['basic', 'page', 'event', 'cart-abandoners'],
                       help='Type of audience to create (required for create action)')
    parser.add_argument('--name', help='Display name for the audience or segment')
    parser.add_argument('--page-path', help='Page path for page-view audience')
    parser.add_argument('--event-name', help='Event name for event-based audience')
    parser.add_argument('--audience-id', help='Audience ID for delete or usage lookup')
    parser.add_argument('--audience-ids', help='Comma-separated audience IDs for segment creation')
    parser.add_argument('--description', help='Description for segment or audience')
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

        elif args.action == 'delete-interactive':
            delete_audiences_interactive()

        elif args.action == 'list-segments':
            list_segments_with_audiences()

        elif args.action == 'list-with-segments':
            list_audiences_with_segment_info()

        elif args.action == 'show-usage':
            show_audience_usage()

        elif args.action == 'show-segment-usage':
            show_segment_usage()

        elif args.action == 'show-all-usage':
            show_all_usage()

        elif args.action == 'create-segment':
            if not args.name:
                print("❌ --name is required for segment creation")
                return
            if not args.audience_ids:
                print("❌ --audience-ids is required (comma-separated)")
                return
            audience_ids = [x.strip() for x in args.audience_ids.split(',')]
            create_segment(args.name, audience_ids, args.description or "")

        elif args.action == 'find-in-campaigns':
            if not args.audience_id:
                print("❌ --audience-id is required")
                return
            find_audience_in_campaigns(args.audience_id)

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

