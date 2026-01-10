"""
Marketing Campaign Manager
Track and analyze advertising campaigns and correlate with property performance

DDEV Usage:
    # Add a new campaign
    ddev exec python3 scripts/campaign_manager.py --add \
        --name "Summer Property Showcase" \
        --platform "Facebook Ads" \
        --type "carousel_ads" \
        --start-date 2026-01-10 \
        --budget 500 \
        --properties "REF123,REF456,REF789"
    
    # Log campaign activity
    ddev exec python3 scripts/campaign_manager.py --log-activity \
        --campaign-id 5 \
        --type "budget_adjusted" \
        --description "Increased budget due to good performance" \
        --budget-change 200
    
    # End a campaign
    ddev exec python3 scripts/campaign_manager.py --end-campaign 5 --end-date 2026-02-10
    
    # View all active campaigns
    ddev exec python3 scripts/campaign_manager.py --list-active
    
    # Analyze campaign effectiveness
    ddev exec python3 scripts/campaign_manager.py --analyze --campaign-id 5
    
    # Correlate campaigns with viewing requests
    ddev exec python3 scripts/campaign_manager.py --correlate-viewings --days 30
    
    # Timeline of all campaign activity
    ddev exec python3 scripts/campaign_manager.py --timeline --days 90

Features:
    - Track marketing campaigns across all platforms
    - Log campaign activities (launch, pause, budget changes, etc.)
    - Correlate campaigns with property performance
    - Link viewing requests to active campaigns
    - Analyze campaign ROI and effectiveness
    - Generate timeline of marketing activities
    - Identify which campaigns drove actual viewings
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
            database=os.getenv('DB_NAME', 'google-stats'),
            user=os.getenv('DB_USER', 'db'),
            password=os.getenv('DB_PASSWORD', 'db')
        )
        return connection
    except Error as e:
        print(f"❌ Database connection error: {e}")
        return None


def add_campaign(name, platform, campaign_type, start_date, budget, properties, notes=""):
    """Add a new marketing campaign."""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO marketing_campaigns 
            (campaign_name, platform, campaign_type, start_date, budget_spent, target_references, notes, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
        """, (name, platform, campaign_type, start_date, budget, properties, notes))
        
        campaign_id = cursor.lastrowid
        
        # Log the launch activity
        cursor.execute("""
            INSERT INTO campaign_activity_log 
            (campaign_id, activity_date, activity_type, description, budget_change)
            VALUES (%s, %s, 'launched', %s, %s)
        """, (campaign_id, start_date, f"Campaign launched: {name}", budget))
        
        connection.commit()
        cursor.close()
        
        print(f"✅ Created campaign #{campaign_id}: {name}")
        print(f"   Platform: {platform}")
        print(f"   Type: {campaign_type}")
        print(f"   Start Date: {start_date}")
        print(f"   Budget: £{budget}")
        print(f"   Target Properties: {properties}")
        
        return campaign_id
        
    except Error as e:
        print(f"❌ Error creating campaign: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()


def log_campaign_activity(campaign_id, activity_type, activity_date=None, description="", budget_change=0, created_by=""):
    """Log an activity for a campaign."""
    if activity_date is None:
        activity_date = datetime.now().date()
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO campaign_activity_log 
            (campaign_id, activity_date, activity_type, description, budget_change, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (campaign_id, activity_date, activity_type, description, budget_change, created_by))
        
        # Update campaign budget if changed
        if budget_change != 0:
            cursor.execute("""
                UPDATE marketing_campaigns 
                SET budget_spent = budget_spent + %s
                WHERE id = %s
            """, (budget_change, campaign_id))
        
        connection.commit()
        cursor.close()
        
        print(f"✅ Logged activity for campaign #{campaign_id}")
        print(f"   Type: {activity_type}")
        print(f"   Date: {activity_date}")
        if description:
            print(f"   Description: {description}")
        if budget_change != 0:
            print(f"   Budget Change: £{budget_change}")
        
        return True
        
    except Error as e:
        print(f"❌ Error logging activity: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()


def end_campaign(campaign_id, end_date=None):
    """End a campaign."""
    if end_date is None:
        end_date = datetime.now().date()
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE marketing_campaigns 
            SET end_date = %s, status = 'ended'
            WHERE id = %s
        """, (end_date, campaign_id))
        
        cursor.execute("""
            INSERT INTO campaign_activity_log 
            (campaign_id, activity_date, activity_type, description)
            VALUES (%s, %s, 'ended', 'Campaign ended')
        """, (campaign_id, end_date))
        
        connection.commit()
        cursor.close()
        
        print(f"✅ Ended campaign #{campaign_id} on {end_date}")
        return True
        
    except Error as e:
        print(f"❌ Error ending campaign: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()


def list_active_campaigns():
    """List all active campaigns."""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                id, campaign_name, platform, campaign_type, 
                start_date, budget_spent, target_references, status
            FROM marketing_campaigns
            WHERE status = 'active'
            ORDER BY start_date DESC
        """)
        
        campaigns = cursor.fetchall()
        cursor.close()
        
        if not campaigns:
            print("\n📋 No active campaigns found")
            return
        
        print(f"\n📋 ACTIVE MARKETING CAMPAIGNS ({len(campaigns)})")
        print("=" * 120)
        
        for campaign in campaigns:
            days_running = (datetime.now().date() - campaign['start_date']).days
            print(f"\n#{campaign['id']} - {campaign['campaign_name']}")
            print(f"   Platform: {campaign['platform']} | Type: {campaign['campaign_type']}")
            print(f"   Started: {campaign['start_date']} ({days_running} days ago)")
            print(f"   Budget Spent: £{campaign['budget_spent']}")
            print(f"   Target Properties: {campaign['target_references']}")
        
        print("\n" + "=" * 120)
        
    except Error as e:
        print(f"❌ Error listing campaigns: {e}")
    finally:
        if connection.is_connected():
            connection.close()


def analyze_campaign(campaign_id):
    """Analyze campaign performance and ROI."""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get campaign details
        cursor.execute("""
            SELECT * FROM marketing_campaigns WHERE id = %s
        """, (campaign_id,))
        
        campaign = cursor.fetchone()
        if not campaign:
            print(f"❌ Campaign #{campaign_id} not found")
            return
        
        print(f"\n📊 CAMPAIGN ANALYSIS: {campaign['campaign_name']}")
        print("=" * 120)
        print(f"\nCampaign Details:")
        print(f"   Platform: {campaign['platform']}")
        print(f"   Type: {campaign['campaign_type']}")
        print(f"   Status: {campaign['status'].upper()}")
        print(f"   Started: {campaign['start_date']}")
        if campaign['end_date']:
            print(f"   Ended: {campaign['end_date']}")
            duration = (campaign['end_date'] - campaign['start_date']).days
        else:
            print(f"   Still Running: {(datetime.now().date() - campaign['start_date']).days} days")
            duration = (datetime.now().date() - campaign['start_date']).days
        print(f"   Budget Spent: £{campaign['budget_spent']}")
        
        # Get target properties
        target_refs = campaign['target_references'].split(',') if campaign['target_references'] else []
        print(f"   Target Properties: {len(target_refs)}")
        
        # Get analytics data for campaign period
        cursor.execute("""
            SELECT 
                pa.reference,
                pa.property_name,
                SUM(pa.pageviews) as total_pageviews,
                SUM(pa.users) as total_users,
                SUM(pa.sessions) as total_sessions,
                AVG(pa.performance_score) as avg_score
            FROM property_analytics pa
            WHERE pa.reference IN (%s)
                AND pa.report_date >= %s
                AND pa.report_date <= IFNULL(%s, CURDATE())
            GROUP BY pa.reference, pa.property_name
        """ % (','.join(['%s'] * len(target_refs)), '%s', '%s'), 
        tuple(target_refs) + (campaign['start_date'], campaign['end_date']))
        
        analytics = cursor.fetchall()
        
        # Get viewing requests during campaign
        cursor.execute("""
            SELECT 
                vr.reference,
                COUNT(DISTINCT vr.request_date) as viewing_days,
                SUM(vr.request_count) as total_viewings
            FROM property_viewing_requests vr
            WHERE vr.reference IN (%s)
                AND vr.request_date >= %s
                AND vr.request_date <= IFNULL(%s, CURDATE())
            GROUP BY vr.reference
        """ % (','.join(['%s'] * len(target_refs)), '%s', '%s'),
        tuple(target_refs) + (campaign['start_date'], campaign['end_date']))
        
        viewings = {v['reference']: v for v in cursor.fetchall()}
        
        # Calculate totals
        total_pageviews = sum(a['total_pageviews'] or 0 for a in analytics)
        total_users = sum(a['total_users'] or 0 for a in analytics)
        total_sessions = sum(a['total_sessions'] or 0 for a in analytics)
        total_viewings = sum(v['total_viewings'] for v in viewings.values())
        
        print(f"\n📈 Campaign Performance:")
        print(f"   Duration: {duration} days")
        print(f"   Total Pageviews: {total_pageviews:,}")
        print(f"   Total Users: {total_users:,}")
        print(f"   Total Sessions: {total_sessions:,}")
        print(f"   Total Viewing Requests: {total_viewings}")
        
        if campaign['budget_spent'] and campaign['budget_spent'] > 0:
            print(f"\n💰 ROI Metrics:")
            print(f"   Cost per Session: £{campaign['budget_spent'] / total_sessions:.2f}" if total_sessions > 0 else "   Cost per Session: N/A")
            print(f"   Cost per User: £{campaign['budget_spent'] / total_users:.2f}" if total_users > 0 else "   Cost per User: N/A")
            print(f"   Cost per Viewing: £{campaign['budget_spent'] / total_viewings:.2f}" if total_viewings > 0 else "   Cost per Viewing: N/A")
            print(f"   Viewing Conversion Rate: {(total_viewings / total_sessions * 100):.2f}%" if total_sessions > 0 else "   Viewing Conversion Rate: N/A")
        
        # Property breakdown
        print(f"\n🏠 Performance by Property:")
        for prop in analytics:
            ref = prop['reference']
            viewing_data = viewings.get(ref, {})
            print(f"\n   {prop['property_name'] or ref}")
            print(f"      Pageviews: {prop['total_pageviews']:,}")
            print(f"      Users: {prop['total_users']:,}")
            print(f"      Sessions: {prop['total_sessions']:,}")
            print(f"      Viewing Requests: {viewing_data.get('total_viewings', 0)}")
            print(f"      Avg Performance Score: {prop['avg_score']:.1f}/100")
        
        # Get activity log
        cursor.execute("""
            SELECT activity_date, activity_type, description, budget_change
            FROM campaign_activity_log
            WHERE campaign_id = %s
            ORDER BY activity_date DESC
        """, (campaign_id,))
        
        activities = cursor.fetchall()
        
        if activities:
            print(f"\n📅 Campaign Activity Timeline:")
            for activity in activities:
                print(f"   {activity['activity_date']} - {activity['activity_type'].upper()}")
                if activity['description']:
                    print(f"      {activity['description']}")
                if activity['budget_change']:
                    print(f"      Budget change: £{activity['budget_change']}")
        
        print("\n" + "=" * 120)
        
        cursor.close()
        
    except Error as e:
        print(f"❌ Error analyzing campaign: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if connection.is_connected():
            connection.close()


def correlate_viewings_with_campaigns(days=30):
    """Correlate viewing requests with active campaigns during the period."""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        print(f"\n🔗 CORRELATING VIEWING REQUESTS WITH CAMPAIGNS - LAST {days} DAYS")
        print("=" * 120)
        
        # Get campaigns active during period
        cursor.execute("""
            SELECT 
                mc.id,
                mc.campaign_name,
                mc.platform,
                mc.start_date,
                mc.end_date,
                mc.target_references,
                mc.budget_spent,
                COUNT(DISTINCT vr.request_date) as viewing_days,
                SUM(vr.request_count) as total_viewings
            FROM marketing_campaigns mc
            LEFT JOIN property_viewing_requests vr 
                ON FIND_IN_SET(vr.reference, mc.target_references) > 0
                AND vr.request_date BETWEEN mc.start_date AND IFNULL(mc.end_date, CURDATE())
                AND vr.request_date BETWEEN %s AND %s
            WHERE mc.start_date <= %s
                AND (mc.end_date IS NULL OR mc.end_date >= %s)
            GROUP BY mc.id, mc.campaign_name, mc.platform, mc.start_date, mc.end_date, 
                     mc.target_references, mc.budget_spent
            ORDER BY total_viewings DESC, mc.start_date DESC
        """, (start_date, end_date, end_date, start_date))
        
        campaigns = cursor.fetchall()
        
        if not campaigns:
            print("\n⚠️ No campaigns were active during this period")
            return
        
        print(f"\n📊 Found {len(campaigns)} campaign(s) active during this period:")
        
        total_budget = sum(c['budget_spent'] or 0 for c in campaigns)
        total_viewings = sum(c['total_viewings'] or 0 for c in campaigns)
        
        print(f"\nAggregate Metrics:")
        print(f"   Total Budget Spent: £{total_budget:,.2f}")
        print(f"   Total Viewing Requests: {total_viewings}")
        if total_budget > 0 and total_viewings > 0:
            print(f"   Average Cost per Viewing: £{total_budget / total_viewings:.2f}")
        
        for campaign in campaigns:
            print(f"\n{'─' * 100}")
            print(f"📢 {campaign['campaign_name']}")
            print(f"   Platform: {campaign['platform']}")
            print(f"   Period: {campaign['start_date']} to {campaign['end_date'] or 'ongoing'}")
            print(f"   Budget: £{campaign['budget_spent'] or 0}")
            
            target_refs = campaign['target_references'].split(',') if campaign['target_references'] else []
            print(f"   Target Properties: {len(target_refs)}")
            
            if campaign['total_viewings']:
                print(f"   ✅ Viewing Requests During Campaign: {campaign['total_viewings']}")
                if campaign['budget_spent'] and campaign['budget_spent'] > 0:
                    print(f"   💰 Cost per Viewing: £{campaign['budget_spent'] / campaign['total_viewings']:.2f}")
            else:
                print(f"   ⚠️ No viewing requests recorded during campaign period")
            
            # Get specific viewing dates
            if campaign['total_viewings'] and campaign['total_viewings'] > 0:
                cursor.execute("""
                    SELECT 
                        vr.reference,
                        vr.request_date,
                        SUM(vr.request_count) as requests
                    FROM property_viewing_requests vr
                    WHERE FIND_IN_SET(vr.reference, %s) > 0
                        AND vr.request_date BETWEEN %s AND IFNULL(%s, CURDATE())
                        AND vr.request_date BETWEEN %s AND %s
                    GROUP BY vr.reference, vr.request_date
                    ORDER BY vr.request_date DESC
                    LIMIT 5
                """, (campaign['target_references'], campaign['start_date'], 
                      campaign['end_date'], start_date, end_date))
                
                recent_viewings = cursor.fetchall()
                if recent_viewings:
                    print(f"   Recent Viewing Requests:")
                    for viewing in recent_viewings:
                        print(f"      • {viewing['request_date']}: {viewing['reference']} ({viewing['requests']} request(s))")
        
        print("\n" + "=" * 120)
        
        cursor.close()
        
    except Error as e:
        print(f"❌ Error correlating viewings: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if connection.is_connected():
            connection.close()


def show_campaign_timeline(days=90):
    """Show timeline of all campaign activities."""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        cursor.execute("""
            SELECT 
                cal.activity_date,
                cal.activity_type,
                cal.description,
                cal.budget_change,
                mc.campaign_name,
                mc.platform
            FROM campaign_activity_log cal
            JOIN marketing_campaigns mc ON cal.campaign_id = mc.id
            WHERE cal.activity_date BETWEEN %s AND %s
            ORDER BY cal.activity_date DESC, cal.created_at DESC
        """, (start_date, end_date))
        
        activities = cursor.fetchall()
        cursor.close()
        
        if not activities:
            print(f"\n⚠️ No campaign activities found in last {days} days")
            return
        
        print(f"\n📅 CAMPAIGN ACTIVITY TIMELINE - LAST {days} DAYS")
        print("=" * 120)
        print(f"\nTotal Activities: {len(activities)}\n")
        
        current_date = None
        for activity in activities:
            if current_date != activity['activity_date']:
                current_date = activity['activity_date']
                print(f"\n📆 {current_date}")
                print("─" * 100)
            
            activity_icon = {
                'launched': '🚀',
                'paused': '⏸️',
                'resumed': '▶️',
                'budget_adjusted': '💰',
                'ended': '🏁'
            }.get(activity['activity_type'], '📝')
            
            print(f"\n   {activity_icon} {activity['activity_type'].upper()} - {activity['campaign_name']}")
            print(f"      Platform: {activity['platform']}")
            if activity['description']:
                print(f"      {activity['description']}")
            if activity['budget_change'] and activity['budget_change'] != 0:
                sign = '+' if activity['budget_change'] > 0 else ''
                print(f"      Budget change: {sign}£{activity['budget_change']}")
        
        print("\n" + "=" * 120)
        
    except Error as e:
        print(f"❌ Error showing timeline: {e}")
    finally:
        if connection.is_connected():
            connection.close()


def main():
    parser = argparse.ArgumentParser(description='Marketing Campaign Manager')
    
    # Campaign creation
    parser.add_argument('--add', action='store_true',
                       help='Add a new campaign')
    parser.add_argument('--name',
                       help='Campaign name')
    parser.add_argument('--platform',
                       help='Marketing platform (Facebook Ads, Google Ads, Email, Instagram, LinkedIn, Buffer)')
    parser.add_argument('--type',
                       help='Campaign type (carousel_ads, video_ads, email_campaign, etc.)')
    parser.add_argument('--start-date',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--budget', type=float,
                       help='Budget amount')
    parser.add_argument('--properties',
                       help='Comma-separated property references')
    parser.add_argument('--notes', default='',
                       help='Campaign notes')
    
    # Campaign activity logging
    parser.add_argument('--log-activity', action='store_true',
                       help='Log campaign activity')
    parser.add_argument('--campaign-id', type=int,
                       help='Campaign ID')
    parser.add_argument('--activity-type',
                       help='Activity type (launched, paused, resumed, budget_adjusted, ended)')
    parser.add_argument('--description', default='',
                       help='Activity description')
    parser.add_argument('--budget-change', type=float, default=0,
                       help='Budget change amount')
    parser.add_argument('--activity-date',
                       help='Activity date (YYYY-MM-DD, default: today)')
    
    # Campaign management
    parser.add_argument('--end-campaign', type=int,
                       help='End campaign by ID')
    parser.add_argument('--end-date',
                       help='End date (YYYY-MM-DD, default: today)')
    
    # Reporting
    parser.add_argument('--list-active', action='store_true',
                       help='List all active campaigns')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze campaign performance')
    parser.add_argument('--correlate-viewings', action='store_true',
                       help='Correlate viewing requests with campaigns')
    parser.add_argument('--timeline', action='store_true',
                       help='Show campaign activity timeline')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days to analyze (default: 30)')
    
    args = parser.parse_args()
    
    if args.add:
        if not all([args.name, args.platform, args.start_date, args.budget, args.properties]):
            print("❌ Missing required fields for campaign creation")
            print("   Required: --name, --platform, --start-date, --budget, --properties")
            return
        add_campaign(args.name, args.platform, args.type or 'general', 
                    args.start_date, args.budget, args.properties, args.notes)
    
    elif args.log_activity:
        if not args.campaign_id or not args.activity_type:
            print("❌ Missing required fields: --campaign-id and --activity-type")
            return
        activity_date = datetime.strptime(args.activity_date, '%Y-%m-%d').date() if args.activity_date else None
        log_campaign_activity(args.campaign_id, args.activity_type, activity_date,
                            args.description, args.budget_change)
    
    elif args.end_campaign:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date() if args.end_date else None
        end_campaign(args.end_campaign, end_date)
    
    elif args.list_active:
        list_active_campaigns()
    
    elif args.analyze:
        if not args.campaign_id:
            print("❌ Missing required field: --campaign-id")
            return
        analyze_campaign(args.campaign_id)
    
    elif args.correlate_viewings:
        correlate_viewings_with_campaigns(args.days)
    
    elif args.timeline:
        show_campaign_timeline(args.days)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
