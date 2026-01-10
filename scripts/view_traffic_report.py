#!/usr/bin/env python3
"""
View Property Traffic Report
Query and display traffic data from database

DDEV Usage:
    # View all properties with traffic breakdown
    ddev exec python3 scripts/view_traffic_report.py
    
    # View specific period
    ddev exec python3 scripts/view_traffic_report.py --days 30
    
    # View specific property
    ddev exec python3 scripts/view_traffic_report.py --property STH240092
    
    # Compare sources across all properties
    ddev exec python3 scripts/view_traffic_report.py --compare-sources
    
    # Export to CSV
    ddev exec python3 scripts/view_traffic_report.py --export-csv

Features:
    - Shows raw traffic data without scoring
    - Groups by source/medium so you can see Mailchimp vs Facebook etc.
    - Sortable by sessions, pageviews, or users
    - Export to CSV for analysis
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import REPORTS_DIR


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


def view_property_traffic(property_ref=None, days=30, sort_by='sessions'):
    """View traffic data for properties."""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Build query
        query = """
            SELECT 
                reference,
                house_name,
                traffic_source,
                traffic_medium,
                SUM(sessions) as total_sessions,
                SUM(pageviews) as total_pageviews,
                SUM(users) as total_users,
                AVG(avg_session_duration) as avg_duration,
                AVG(bounce_rate) as avg_bounce_rate,
                MAX(report_date) as last_updated
            FROM property_traffic_detail
            WHERE period_days = %s
        """
        
        params = [days]
        
        if property_ref:
            query += " AND reference = %s"
            params.append(property_ref)
        
        query += """
            GROUP BY reference, house_name, traffic_source, traffic_medium
            ORDER BY total_sessions DESC
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        
        return results
        
    except Error as e:
        print(f"❌ Database error: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()


def compare_traffic_sources(days=30):
    """Compare traffic sources across all properties."""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                traffic_source,
                traffic_medium,
                COUNT(DISTINCT reference) as properties_count,
                SUM(sessions) as total_sessions,
                SUM(pageviews) as total_pageviews,
                SUM(users) as total_users,
                AVG(avg_session_duration) as avg_duration,
                AVG(bounce_rate) as avg_bounce_rate
            FROM property_traffic_detail
            WHERE period_days = %s
            GROUP BY traffic_source, traffic_medium
            ORDER BY total_sessions DESC
        """, (days,))
        
        results = cursor.fetchall()
        cursor.close()
        
        return results
        
    except Error as e:
        print(f"❌ Database error: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()


def display_property_report(data, days):
    """Display property traffic report."""
    if not data:
        print(f"\n⚠️  No traffic data found for last {days} days")
        print("\n💡 To populate data, run:")
        print(f"   ddev exec python3 scripts/populate_traffic_database.py --days {days}")
        return
    
    print("\n" + "=" * 120)
    print(f"📊 PROPERTY TRAFFIC REPORT - LAST {days} DAYS")
    print("=" * 120)
    
    # Group by property
    current_property = None
    property_total_sessions = 0
    property_sources = []
    
    for row in data:
        if current_property != row['reference']:
            # Print previous property summary
            if current_property:
                print(f"\n   {'TOTAL':<50} {property_total_sessions:>8} sessions")
                print("   " + "-" * 100)
            
            # New property header
            current_property = row['reference']
            property_total_sessions = 0
            property_sources = []
            
            print(f"\n🏠 {row['house_name'] or row['reference']}")
            print(f"   Reference: {row['reference']}")
            print(f"   Last Updated: {row['last_updated']}")
            print(f"\n   {'Source / Medium':<50} {'Sessions':>8} {'Pageviews':>10} {'Users':>8} {'Avg Duration':>12} {'Bounce Rate':>12}")
            print(f"   {'-'*50} {'-'*8} {'-'*10} {'-'*8} {'-'*12} {'-'*12}")
        
        # Display source/medium row
        source_medium = f"{row['traffic_source']} / {row['traffic_medium']}"
        sessions = row['total_sessions']
        pageviews = row['total_pageviews']
        users = row['total_users']
        duration = int(row['avg_duration'])
        bounce_rate = row['avg_bounce_rate'] * 100
        
        print(f"   {source_medium:<50} {sessions:>8} {pageviews:>10} {users:>8} {duration:>10}s {bounce_rate:>10.1f}%")
        
        property_total_sessions += sessions
    
    # Print last property summary
    if current_property:
        print(f"\n   {'TOTAL':<50} {property_total_sessions:>8} sessions")
        print("   " + "-" * 100)
    
    print("\n" + "=" * 120)


def display_source_comparison(data, days):
    """Display traffic source comparison."""
    if not data:
        print(f"\n⚠️  No traffic data found for last {days} days")
        return
    
    print("\n" + "=" * 120)
    print(f"📊 TRAFFIC SOURCE COMPARISON - LAST {days} DAYS")
    print("=" * 120)
    print("\nThis shows ALL traffic sources across ALL properties - letting YOU decide what's working\n")
    
    print(f"{'Source / Medium':<50} {'Properties':>10} {'Sessions':>10} {'Pageviews':>12} {'Users':>10} {'Avg Duration':>12} {'Bounce Rate':>12}")
    print(f"{'-'*50} {'-'*10} {'-'*10} {'-'*12} {'-'*10} {'-'*12} {'-'*12}")
    
    for row in data:
        source_medium = f"{row['traffic_source']} / {row['traffic_medium']}"
        properties = row['properties_count']
        sessions = row['total_sessions']
        pageviews = row['total_pageviews']
        users = row['total_users']
        duration = int(row['avg_duration'])
        bounce_rate = row['avg_bounce_rate'] * 100
        
        print(f"{source_medium:<50} {properties:>10} {sessions:>10} {pageviews:>12} {users:>10} {duration:>10}s {bounce_rate:>10.1f}%")
    
    print("\n" + "=" * 120)
    print("\n💡 Example insights YOU can derive:")
    print("   - Which source/medium brings the most traffic?")
    print("   - Are Mailchimp emails outperforming Facebook ads?")
    print("   - Which sources have better engagement (duration, bounce rate)?")
    print("   - Which sources reach the most properties?")


def export_to_csv(data, days, filename=None):
    """Export traffic data to CSV."""
    if not data:
        print("⚠️  No data to export")
        return
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(REPORTS_DIR, f"traffic_report_{days}days_{timestamp}.csv")
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    
    print(f"\n✅ Exported to: {filename}")


def main():
    parser = argparse.ArgumentParser(description='View Property Traffic Report')
    parser.add_argument('--property', type=str,
                       help='View specific property (reference)')
    parser.add_argument('--days', type=int, default=30, choices=[1, 7, 14, 30, 60, 90],
                       help='Time period (default: 30)')
    parser.add_argument('--compare-sources', action='store_true',
                       help='Compare traffic sources across all properties')
    parser.add_argument('--export-csv', action='store_true',
                       help='Export to CSV file')
    parser.add_argument('--sort-by', choices=['sessions', 'pageviews', 'users'], default='sessions',
                       help='Sort by metric (default: sessions)')
    
    args = parser.parse_args()
    
    if args.compare_sources:
        data = compare_traffic_sources(args.days)
        display_source_comparison(data, args.days)
        if args.export_csv:
            export_to_csv(data, args.days)
    else:
        data = view_property_traffic(args.property, args.days, args.sort_by)
        display_property_report(data, args.days)
        if args.export_csv:
            export_to_csv(data, args.days)


if __name__ == "__main__":
    main()
