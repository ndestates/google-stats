"""
Google Analytics 4 Audience Management Script
Create, list, and manage audiences programmatically via the Admin API
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta

from src.config import GA4_PROPERTY_ID, REPORTS_DIR
from googleapiclient.discovery import build
from google.oauth2 import service_account


def get_admin_service():
    """Get authenticated Google Analytics Admin API service"""

    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv("GA4_KEY_PATH"),
        scopes=['https://www.googleapis.com/auth/analytics.edit']
    )

    # Build the service
    service = build('analyticsadmin', 'v1beta', credentials=credentials)
    return service


def create_basic_audience(display_name: str, description: str = "", membership_duration_days: int = 30):
    """Create a basic audience with all users"""

    service = get_admin_service()

    audience = {
        'displayName': display_name,
        'description': description,
        'membershipDurationDays': membership_duration_days,
        # All users audience - no filters needed for basic audience
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
                'filterType': 'DIMENSION_OR_METRIC',
                'dimensionOrMetricFilter': {
                    'fieldName': 'pagePath',
                    'stringFilter': {
                        'matchType': 'CONTAINS',
                        'value': page_path
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
                'filterType': 'DIMENSION_OR_METRIC',
                'dimensionOrMetricFilter': {
                    'fieldName': 'eventName',
                    'stringFilter': {
                        'matchType': 'EXACT',
                        'value': event_name
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
                    'filterType': 'DIMENSION_OR_METRIC',
                    'dimensionOrMetricFilter': {
                        'fieldName': 'eventName',
                        'stringFilter': {
                            'matchType': 'EXACT',
                            'value': 'add_to_cart'
                        }
                    }
                }
            },
            {
                'clauseType': 'EXCLUDE',
                'simpleFilter': {
                    'filterType': 'DIMENSION_OR_METRIC',
                    'dimensionOrMetricFilter': {
                        'fieldName': 'eventName',
                        'stringFilter': {
                            'matchType': 'EXACT',
                            'value': 'purchase'
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


def list_audiences():
    """List all audiences for the property"""

    service = get_admin_service()

    audiences = service.properties().audiences().list(
        parent=f'properties/{GA4_PROPERTY_ID}'
    ).execute()

    print(f"\n📋 Audiences for property {GA4_PROPERTY_ID}:")
    print("=" * 80)

    if 'audiences' in audiences:
        for audience in audiences['audiences']:
            audience_id = audience['name'].split('/')[-1]
            status = "Active" if audience.get('state') == 'ACTIVE' else "Inactive"
            print(f"ID: {audience_id}")
            print(f"Name: {audience['displayName']}")
            print(f"Description: {audience.get('description', 'N/A')}")
            print(f"Status: {status}")
            print(f"Membership Duration: {audience.get('membershipDurationDays', 'N/A')} days")
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


def main():
    parser = argparse.ArgumentParser(description='Google Analytics 4 Audience Management')
    parser.add_argument('--action', choices=['create', 'list', 'delete'], required=True,
                       help='Action to perform')
    parser.add_argument('--type', choices=['basic', 'page', 'event', 'cart-abandoners'],
                       help='Type of audience to create (required for create action)')
    parser.add_argument('--name', help='Display name for the audience')
    parser.add_argument('--page-path', help='Page path for page-view audience')
    parser.add_argument('--event-name', help='Event name for event-based audience')
    parser.add_argument('--audience-id', help='Audience ID for delete action')
    parser.add_argument('--duration', type=int, default=30,
                       help='Membership duration in days (default: 30)')

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
            list_audiences()

        elif args.action == 'delete':
            if not args.audience_id:
                print("❌ --audience-id is required for delete action")
                return
            delete_audience(args.audience_id)

    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()

