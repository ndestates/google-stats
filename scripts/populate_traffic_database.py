#!/usr/bin/env python3
"""
Populate Property Traffic Database
Fetches GA4 data for all properties and stores granular source/medium breakdown

DDEV Usage:
    # Populate with last 30 days data
    ddev exec python3 scripts/populate_traffic_database.py --days 30
    
    # Populate with yesterday only
    ddev exec python3 scripts/populate_traffic_database.py --days 1
    
    # Populate specific properties
    ddev exec python3 scripts/populate_traffic_database.py --days 30 --properties STH240092,STH250039

Features:
    - Fetches source + medium separately from GA4
    - Stores each source/medium combination per property
    - No scoring or categorization - just raw data
    - Updates existing records or inserts new ones
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
import urllib.request
import xml.etree.ElementTree as ET
import mysql.connector
from mysql.connector import Error

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import GA4_PROPERTY_ID, REPORTS_DIR
from src.ga4_client import run_report, create_date_range


def get_db_connection():
    """Get database connection."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'db'),
            database=os.getenv('DB_NAME', 'google-stats'),
            user=os.getenv('DB_USER', 'db'),
            password=os.getenv('DB_PASSWORD', 'db')
        )
        return connection
    except Error as e:
        print(f"❌ Database connection error: {e}")
        return None


def fetch_property_catalog(feed_url=None):
    """Fetch properties from database instead of XML feed."""
    print(f"📥 Fetching property catalog from database...")
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT reference, house_name, url
            FROM properties
            WHERE reference IS NOT NULL AND url IS NOT NULL
        """)
        
        properties = []
        for row in cursor.fetchall():
            url_full = row['url']
            url_path = url_full.replace('https://www.ndestates.com', '') if url_full else ''
            
            properties.append({
                'reference': row['reference'],
                'house_name': row['house_name'] or '',
                'url': url_full,
                'url_path': url_path
            })
        
        cursor.close()
        connection.close()
        
        print(f"✅ Loaded {len(properties)} properties from database")
        return properties
        
    except Error as e:
        print(f"❌ Error fetching from database: {e}")
        return []


def get_analytics_data_with_source_medium(days: int = 30):
    """
    Fetch GA4 analytics data with source AND medium separately.
    Returns data grouped by page path, source, and medium.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    date_range = create_date_range(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    print(f"📊 Fetching analytics data for last {days} days...")
    print(f"   Date range: {start_date.date()} to {end_date.date()}")
    
    # Get page-level metrics WITH source and medium as separate dimensions
    dimensions = ["pagePath", "sessionSource", "sessionMedium"]
    metrics = [
        "screenPageViews",
        "totalUsers",
        "sessions",
        "averageSessionDuration",
        "bounceRate"
    ]
    
    response = run_report(
        dimensions=dimensions,
        metrics=metrics,
        date_ranges=[date_range],
        limit=50000,  # Increased limit for detailed data
    )
    
    # Structure: page_path -> (source, medium) -> metrics
    analytics_data = defaultdict(lambda: defaultdict(lambda: {
        'pageviews': 0,
        'users': 0,
        'sessions': 0,
        'total_session_duration': 0,
        'bounce_rate_sum': 0,
    }))
    
    if response.row_count > 0:
        for row in response.rows:
            page_path = row.dimension_values[0].value
            source = row.dimension_values[1].value
            medium = row.dimension_values[2].value
            
            pageviews = int(row.metric_values[0].value)
            users = int(row.metric_values[1].value)
            sessions = int(row.metric_values[2].value)
            avg_duration = float(row.metric_values[3].value)
            bounce_rate = float(row.metric_values[4].value)
            
            key = (source, medium)
            data = analytics_data[page_path][key]
            data['pageviews'] += pageviews
            data['users'] += users
            data['sessions'] += sessions
            data['total_session_duration'] += avg_duration * sessions
            data['bounce_rate_sum'] += bounce_rate * sessions
        
        # Calculate averages
        for page_path, sources in analytics_data.items():
            for key, data in sources.items():
                if data['sessions'] > 0:
                    data['avg_session_duration'] = data['total_session_duration'] / data['sessions']
                    data['bounce_rate'] = data['bounce_rate_sum'] / data['sessions']
    
    print(f"✅ Retrieved analytics data for {len(analytics_data)} unique pages")
    total_source_medium_combos = sum(len(sources) for sources in analytics_data.values())
    print(f"✅ Found {total_source_medium_combos} unique source/medium combinations")
    
    return dict(analytics_data)


def store_traffic_data(properties, analytics_data, days):
    """Store traffic data in database."""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        report_date = datetime.now().date()
        
        records_inserted = 0
        records_updated = 0
        
        print(f"\n💾 Storing traffic data in database...")
        
        for prop in properties:
            url_path = prop['url_path']
            
            # Find matching analytics data - match the full URL path from GA4
            matching_data = None
            for path, sources in analytics_data.items():
                # GA4 returns paths like /properties/st-helier-one-bedroom-apartment-in-town-3
                # Property url_path should match this exactly or be contained in it
                if path == url_path or url_path in path:
                    matching_data = sources
                    break
            
            if not matching_data:
                continue
            
            # Store each source/medium combination
            for (source, medium), metrics in matching_data.items():
                cursor.execute("""
                    INSERT INTO property_traffic_detail 
                    (reference, house_name, property_url, report_date, period_days, 
                     traffic_source, traffic_medium, sessions, pageviews, users, 
                     avg_session_duration, bounce_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        sessions = VALUES(sessions),
                        pageviews = VALUES(pageviews),
                        users = VALUES(users),
                        avg_session_duration = VALUES(avg_session_duration),
                        bounce_rate = VALUES(bounce_rate),
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    prop['reference'],
                    prop['house_name'],
                    prop['url'],
                    report_date,
                    days,
                    source,
                    medium,
                    metrics['sessions'],
                    metrics['pageviews'],
                    metrics['users'],
                    metrics['avg_session_duration'],
                    metrics['bounce_rate']
                ))
                
                if cursor.rowcount == 1:
                    records_inserted += 1
                elif cursor.rowcount == 2:
                    records_updated += 1
        
        connection.commit()
        cursor.close()
        
        print(f"✅ Database updated successfully")
        print(f"   New records: {records_inserted}")
        print(f"   Updated records: {records_updated}")
        
        return True
        
    except Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()


def main():
    parser = argparse.ArgumentParser(description='Populate Property Traffic Database')
    parser.add_argument('--days', type=int, default=30, choices=[1, 7, 14, 30, 60, 90],
                       help='Time period for analytics (default: 30)')
    parser.add_argument('--properties', type=str,
                       help='Filter by specific property references (comma-separated)')
    parser.add_argument('--feed-url', type=str,
                       help='XML feed URL (default: ND Estates feed)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print(f"📊 POPULATE PROPERTY TRAFFIC DATABASE - LAST {args.days} DAYS")
    print("=" * 80)
    
    # Fetch property catalog
    properties = fetch_property_catalog(args.feed_url)
    if not properties:
        print("❌ No properties found in feed")
        return
    
    # Filter properties if specified
    if args.properties:
        property_refs = [ref.strip() for ref in args.properties.split(',')]
        properties = [p for p in properties if p['reference'] in property_refs]
        print(f"📋 Filtered to {len(properties)} specified properties: {', '.join(property_refs)}")
    
    # Fetch analytics data
    analytics_data = get_analytics_data_with_source_medium(args.days)
    
    # Store in database
    if store_traffic_data(properties, analytics_data, args.days):
        print("\n✅ TRAFFIC DATA POPULATION COMPLETE")
        print(f"\n💡 View the data:")
        print(f"   ddev exec python3 scripts/view_traffic_report.py --days {args.days}")
    else:
        print("\n❌ Failed to populate database")


if __name__ == "__main__":
    main()
