"""
Viewing Requests Manager
Track and analyze property viewing requests and correlate with marketing efforts

DDEV Usage:
    # Add a viewing request for today
    ddev exec python3 scripts/viewing_requests_manager.py --add REF123 --notes "Called after seeing Facebook ad"
    
    # Add viewing request for specific date
    ddev exec python3 scripts/viewing_requests_manager.py --add REF123 --date 2026-01-08 --notes "Email campaign lead"
    
    # View all viewing requests for a property
    ddev exec python3 scripts/viewing_requests_manager.py --property REF123 --days 30
    
    # Analyze viewing requests vs traffic sources
    ddev exec python3 scripts/viewing_requests_manager.py --analyze --days 30
    
    # Show properties with high viewing conversion rates
    ddev exec python3 scripts/viewing_requests_manager.py --top-converters --days 30

Features:
    - Track viewing requests with dates and notes
    - Correlate viewing requests with marketing channels
    - Analyze viewing conversion rates
    - Identify most effective marketing platforms
    - Generate viewing trends report
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error

# Add the parent directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def get_db_connection():
    """Get database connection."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'db'),
            database=os.getenv('DB_NAME', 'google_stats'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'root')
        )
        return connection
    except Error as e:
        print(f"❌ Database connection error: {e}")
        return None


def add_viewing_request(reference, request_date=None, notes=""):
    """Add a viewing request."""
    if request_date is None:
        request_date = datetime.now().date()
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO property_viewing_requests (reference, request_date, request_count, notes)
            VALUES (%s, %s, 1, %s)
            ON DUPLICATE KEY UPDATE
                request_count = request_count + 1,
                notes = CONCAT(IFNULL(notes, ''), IF(notes IS NULL OR notes = '', '', '; '), %s)
        """, (reference, request_date, notes, notes))
        
        connection.commit()
        cursor.close()
        
        print(f"✅ Added viewing request for {reference} on {request_date}")
        if notes:
            print(f"   Notes: {notes}")
        return True
        
    except Error as e:
        print(f"❌ Error adding viewing request: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()


def get_property_viewing_history(reference, days=30):
    """Get viewing request history for a property."""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        cursor.execute("""
            SELECT request_date, request_count, notes, created_at
            FROM property_viewing_requests
            WHERE reference = %s AND request_date BETWEEN %s AND %s
            ORDER BY request_date DESC
        """, (reference, start_date, end_date))
        
        results = cursor.fetchall()
        cursor.close()
        
        if not results:
            print(f"\n📋 No viewing requests found for {reference} in last {days} days")
            return
        
        total_requests = sum(r['request_count'] for r in results)
        
        print(f"\n📋 Viewing Requests for {reference} (Last {days} days)")
        print("=" * 100)
        print(f"Total Requests: {total_requests}")
        print("\nDetailed History:")
        
        for req in results:
            print(f"\n  Date: {req['request_date']}")
            print(f"  Count: {req['request_count']}")
            if req['notes']:
                print(f"  Notes: {req['notes']}")
            print(f"  Recorded: {req['created_at']}")
        
        print("=" * 100)
        
    except Error as e:
        print(f"❌ Error fetching viewing history: {e}")
    finally:
        if connection.is_connected():
            connection.close()


def analyze_viewing_correlations(days=30):
    """Analyze viewing requests against traffic sources."""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get viewing requests with analytics data
        cursor.execute("""
            SELECT 
                pa.reference,
                pa.property_name,
                SUM(vr.request_count) as total_viewings,
                pa.pageviews,
                pa.users,
                pa.sessions,
                pa.performance_score,
                (SUM(vr.request_count) / NULLIF(pa.sessions, 0)) * 100 as viewing_conversion_rate
            FROM property_viewing_requests vr
            JOIN property_analytics pa ON vr.reference = pa.reference
            WHERE vr.request_date BETWEEN %s AND %s
                AND pa.report_date >= %s
                AND pa.period_days = %s
            GROUP BY pa.reference, pa.property_name, pa.pageviews, pa.users, pa.sessions, pa.performance_score
            HAVING total_viewings > 0
            ORDER BY viewing_conversion_rate DESC
        """, (start_date, end_date, start_date, days))
        
        results = cursor.fetchall()
        
        if not results:
            print(f"\n⚠️ No viewing request data found for last {days} days")
            return
        
        print(f"\n📊 VIEWING REQUEST ANALYSIS - LAST {days} DAYS")
        print("=" * 120)
        
        total_viewings = sum(r['total_viewings'] for r in results)
        total_sessions = sum(r['sessions'] or 0 for r in results)
        avg_conversion = (total_viewings / total_sessions * 100) if total_sessions > 0 else 0
        
        print(f"\n📈 Summary:")
        print(f"   Properties with Viewing Requests: {len(results)}")
        print(f"   Total Viewing Requests: {total_viewings}")
        print(f"   Total Sessions: {total_sessions:,}")
        print(f"   Average Viewing Conversion Rate: {avg_conversion:.2f}%")
        
        print(f"\n🏆 Top Performers by Viewing Conversion Rate:")
        for idx, prop in enumerate(results[:10], 1):
            print(f"\n   {idx}. {prop['property_name'] or prop['reference']}")
            print(f"      Viewing Requests: {prop['total_viewings']}")
            print(f"      Sessions: {prop['sessions']:,}")
            print(f"      Conversion Rate: {prop['viewing_conversion_rate']:.2f}%")
            print(f"      Performance Score: {prop['performance_score']}/100")
        
        # Get traffic source analysis for properties with viewings
        print(f"\n📊 Traffic Source Analysis for Properties with Viewings:")
        
        cursor.execute("""
            SELECT 
                pts.source,
                SUM(pts.sessions) as total_sessions,
                COUNT(DISTINCT pa.reference) as property_count,
                SUM(vr_agg.total_viewings) as associated_viewings
            FROM property_traffic_sources pts
            JOIN property_analytics pa ON pts.analytics_id = pa.id
            JOIN (
                SELECT reference, SUM(request_count) as total_viewings
                FROM property_viewing_requests
                WHERE request_date BETWEEN %s AND %s
                GROUP BY reference
            ) vr_agg ON pa.reference = vr_agg.reference
            WHERE pa.report_date >= %s AND pa.period_days = %s
            GROUP BY pts.source
            ORDER BY associated_viewings DESC, total_sessions DESC
        """, (start_date, end_date, start_date, days))
        
        sources = cursor.fetchall()
        
        for source in sources:
            efficiency = (source['associated_viewings'] / source['total_sessions'] * 100) if source['total_sessions'] > 0 else 0
            print(f"\n   {source['source']}")
            print(f"      Sessions: {source['total_sessions']:,}")
            print(f"      Properties: {source['property_count']}")
            print(f"      Associated Viewings: {source['associated_viewings']}")
            print(f"      Efficiency: {efficiency:.2f}% (viewings per 100 sessions)")
        
        print("\n" + "=" * 120)
        
        cursor.close()
        
    except Error as e:
        print(f"❌ Error analyzing correlations: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if connection.is_connected():
            connection.close()


def show_top_converters(days=30, limit=10):
    """Show properties with highest viewing conversion rates."""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        cursor.execute("""
            SELECT 
                pa.reference,
                pa.property_name,
                pa.property_type,
                pa.property_status,
                pa.price,
                SUM(vr.request_count) as total_viewings,
                pa.sessions,
                pa.pageviews,
                pa.users,
                pa.performance_score,
                (SUM(vr.request_count) / NULLIF(pa.sessions, 0)) * 100 as conversion_rate
            FROM property_analytics pa
            JOIN property_viewing_requests vr ON pa.reference = vr.reference
            WHERE pa.report_date >= %s
                AND vr.request_date BETWEEN %s AND %s
                AND pa.period_days = %s
                AND pa.sessions > 0
            GROUP BY pa.reference, pa.property_name, pa.property_type, pa.property_status, 
                     pa.price, pa.sessions, pa.pageviews, pa.users, pa.performance_score
            ORDER BY conversion_rate DESC
            LIMIT %s
        """, (start_date, start_date, end_date, days, limit))
        
        results = cursor.fetchall()
        cursor.close()
        
        if not results:
            print(f"\n⚠️ No conversion data available for last {days} days")
            return
        
        print(f"\n🏆 TOP {limit} PROPERTIES BY VIEWING CONVERSION RATE - LAST {days} DAYS")
        print("=" * 120)
        
        for idx, prop in enumerate(results, 1):
            print(f"\n{idx}. {prop['property_name'] or prop['reference']}")
            print(f"   Reference: {prop['reference']}")
            print(f"   Type: {prop['property_type'].upper() if prop['property_type'] else 'N/A'}")
            print(f"   Status: {prop['property_status'].title() if prop['property_status'] else 'N/A'}")
            print(f"   Price: £{prop['price']:,}" if prop['price'] else "   Price: N/A")
            print(f"   📊 Metrics:")
            print(f"      Viewing Requests: {prop['total_viewings']}")
            print(f"      Sessions: {prop['sessions']:,}")
            print(f"      Pageviews: {prop['pageviews']:,}")
            print(f"      Users: {prop['users']:,}")
            print(f"   ✨ Performance:")
            print(f"      Conversion Rate: {prop['conversion_rate']:.2f}%")
            print(f"      Performance Score: {prop['performance_score']}/100")
        
        print("\n" + "=" * 120)
        
    except Error as e:
        print(f"❌ Error fetching top converters: {e}")
    finally:
        if connection.is_connected():
            connection.close()


def main():
    parser = argparse.ArgumentParser(description='Viewing Requests Manager')
    parser.add_argument('--add', metavar='REFERENCE',
                       help='Add viewing request for property reference')
    parser.add_argument('--date',
                       help='Date for viewing request (YYYY-MM-DD, default: today)')
    parser.add_argument('--notes', default='',
                       help='Notes about the viewing request')
    parser.add_argument('--property', metavar='REFERENCE',
                       help='Show viewing history for property')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze viewing requests vs traffic sources')
    parser.add_argument('--top-converters', action='store_true',
                       help='Show properties with highest viewing conversion rates')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days to analyze (default: 30)')
    parser.add_argument('--limit', type=int, default=10,
                       help='Number of results to show (default: 10)')
    
    args = parser.parse_args()
    
    if args.add:
        viewing_date = datetime.now().date()
        if args.date:
            viewing_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        add_viewing_request(args.add, viewing_date, args.notes)
    
    elif args.property:
        get_property_viewing_history(args.property, args.days)
    
    elif args.analyze:
        analyze_viewing_correlations(args.days)
    
    elif args.top_converters:
        show_top_converters(args.days, args.limit)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
