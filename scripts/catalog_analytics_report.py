"""
Catalog Analytics Comparison Script
Compare property catalog listings against GA4 analytics data

DDEV Usage:
    # Generate 7-day catalog analytics report
    ddev exec python3 scripts/catalog_analytics_report.py --days 7
    
    # Generate 14-day report
    ddev exec python3 scripts/catalog_analytics_report.py --days 14
    
    # Generate 30-day catalog analytics report
    ddev exec python3 scripts/catalog_analytics_report.py --days 30
    
    # Generate 60-day report
    ddev exec python3 scripts/catalog_analytics_report.py --days 60
    
    # Generate 90-day report with marketing recommendations
    ddev exec python3 scripts/catalog_analytics_report.py --days 90 --recommendations
    
    # Export to CSV
    ddev exec python3 scripts/catalog_analytics_report.py --days 30 --export-csv
    
    # Filter by property type (buy/rent)
    ddev exec python3 scripts/catalog_analytics_report.py --days 30 --type buy
    
    # Filter by status (available/sold/let)
    ddev exec python3 scripts/catalog_analytics_report.py --days 30 --status available
    
    # Show only low-performing listings
    ddev exec python3 scripts/catalog_analytics_report.py --days 30 --low-performers

Direct Usage:
    python3 scripts/catalog_analytics_report.py --days 30 --recommendations

Features:
    - Fetch property catalog from XML feed
    - Match listings to GA4 pageview data
    - Calculate pageviews, traffic sources, and average time on page
    - Expanded traffic source tracking (Email, Social, Paid, Organic, Direct)
    - Identify low-performing listings
    - Platform-specific marketing recommendations (Email, Facebook, Google Ads, LinkedIn, Instagram)
    - Store analytics data in MariaDB database
    - Track viewing requests with dates
    - Correlate viewing requests with marketing channels
    - Export results to CSV
    - Filter by property type and status
    - Compare performance across time periods (7, 14, 30, 60, 90 days)
    - Trend analysis over multiple time periods
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Add the parent directory to sys.path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import GA4_PROPERTY_ID, REPORTS_DIR
from src.ga4_client import run_report, create_date_range
import pandas as pd
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import mysql.connector
from mysql.connector import Error


def map_traffic_source(ga4_channel):
    """
    Map GA4 channel groups to specific marketing platforms.
    """
    channel_mapping = {
        'Organic Search': 'Google Organic',
        'Organic Social': 'Social',
        'Paid Search': 'Google Ads',
        'Paid Social': 'Social',
        'Email': 'Email',
        'Direct': 'Direct',
        'Referral': 'Referral',
        'Display': 'Display Ads',
        'Organic Shopping': 'Shopping',
        'Paid Shopping': 'Shopping Ads',
    }
    
    # Check for specific sources
    ga4_lower = ga4_channel.lower()
    if 'facebook' in ga4_lower or 'fb' in ga4_lower:
        return 'Facebook'
    elif 'instagram' in ga4_lower or 'ig' in ga4_lower:
        return 'Instagram'
    elif 'linkedin' in ga4_lower:
        return 'LinkedIn'
    elif 'mailchimp' in ga4_lower or 'email' in ga4_lower:
        return 'Email'
    elif 'buffer' in ga4_lower:
        return 'Buffer'
    elif 'google' in ga4_lower and 'organic' in ga4_lower:
        return 'Google Organic'
    elif 'google' in ga4_lower and ('ads' in ga4_lower or 'cpc' in ga4_lower or 'paid' in ga4_lower):
        return 'Google Ads'
    
    return channel_mapping.get(ga4_channel, ga4_channel)


def get_db_connection():
    """Get database connection using environment variables."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'db'),
            database=os.getenv('DB_NAME', 'google-stats'),
            user=os.getenv('DB_USER', 'db'),
            password=os.getenv('DB_PASSWORD', 'db')
        )
        return connection
    except Error as e:
        print(f"⚠️ Database connection error: {e}")
        return None


def init_database_tables():
    """Create database tables if they don't exist."""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Property analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_analytics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                reference VARCHAR(50) NOT NULL,
                property_name VARCHAR(255),
                property_url TEXT,
                property_type VARCHAR(10),
                property_status VARCHAR(20),
                price INT,
                report_date DATE NOT NULL,
                period_days INT NOT NULL,
                pageviews INT DEFAULT 0,
                users INT DEFAULT 0,
                sessions INT DEFAULT 0,
                avg_session_duration DECIMAL(10,2) DEFAULT 0,
                bounce_rate DECIMAL(5,4) DEFAULT 0,
                performance_score INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_property_report (reference, report_date, period_days),
                INDEX idx_reference (reference),
                INDEX idx_report_date (report_date),
                INDEX idx_performance (performance_score)
            )
        """)
        
        # Traffic sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_traffic_sources (
                id INT AUTO_INCREMENT PRIMARY KEY,
                analytics_id INT NOT NULL,
                source VARCHAR(50) NOT NULL,
                sessions INT DEFAULT 0,
                FOREIGN KEY (analytics_id) REFERENCES property_analytics(id) ON DELETE CASCADE,
                INDEX idx_analytics_id (analytics_id),
                INDEX idx_source (source)
            )
        """)
        
        # Viewing requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_viewing_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                reference VARCHAR(50) NOT NULL,
                request_date DATE NOT NULL,
                request_count INT DEFAULT 1,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_reference_date (reference, request_date),
                INDEX idx_reference (reference),
                INDEX idx_request_date (request_date)
            )
        """)
        
        # Marketing recommendations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_marketing_recommendations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                analytics_id INT NOT NULL,
                priority VARCHAR(20) NOT NULL,
                platform VARCHAR(50) NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                suggested_budget VARCHAR(100),
                expected_impact VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analytics_id) REFERENCES property_analytics(id) ON DELETE CASCADE,
                INDEX idx_analytics_id (analytics_id),
                INDEX idx_priority (priority)
            )
        """)
        
        # Marketing campaigns table - track actual campaigns launched
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS marketing_campaigns (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campaign_name VARCHAR(255) NOT NULL,
                platform VARCHAR(50) NOT NULL,
                campaign_type VARCHAR(50),
                start_date DATE NOT NULL,
                end_date DATE,
                budget_spent DECIMAL(10,2),
                target_references TEXT COMMENT 'Comma-separated property references',
                status VARCHAR(20) DEFAULT 'active',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_platform (platform),
                INDEX idx_start_date (start_date),
                INDEX idx_status (status)
            )
        """)
        
        # Campaign performance metrics - correlate campaigns with results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_performance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campaign_id INT NOT NULL,
                reference VARCHAR(50) NOT NULL,
                metric_date DATE NOT NULL,
                impressions INT DEFAULT 0,
                clicks INT DEFAULT 0,
                sessions INT DEFAULT 0,
                pageviews INT DEFAULT 0,
                viewing_requests INT DEFAULT 0,
                conversions INT DEFAULT 0,
                cost DECIMAL(10,2) DEFAULT 0,
                FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(id) ON DELETE CASCADE,
                UNIQUE KEY unique_campaign_property_date (campaign_id, reference, metric_date),
                INDEX idx_campaign_id (campaign_id),
                INDEX idx_reference (reference),
                INDEX idx_metric_date (metric_date)
            )
        """)
        
        # Campaign timeline - track when activity was done on campaigns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_activity_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campaign_id INT NOT NULL,
                activity_date DATE NOT NULL,
                activity_type VARCHAR(50) NOT NULL COMMENT 'launched, paused, resumed, budget_adjusted, ended',
                description TEXT,
                budget_change DECIMAL(10,2) DEFAULT 0,
                created_by VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(id) ON DELETE CASCADE,
                INDEX idx_campaign_id (campaign_id),
                INDEX idx_activity_date (activity_date),
                INDEX idx_activity_type (activity_type)
            )
        """)
        
        connection.commit()
        cursor.close()
        return True
        
    except Error as e:
        print(f"⚠️ Error creating tables: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()


def store_analytics_in_database(listings, days):
    """Store analytics data and recommendations in database."""
    connection = get_db_connection()
    if not connection:
        print("⚠️ Skipping database storage - no connection")
        return False
    
    try:
        cursor = connection.cursor()
        report_date = datetime.now().date()
        stored_count = 0
        
        for listing in listings:
            # Insert or update property analytics
            cursor.execute("""
                INSERT INTO property_analytics (
                    reference, property_name, property_url, property_type, property_status,
                    price, report_date, period_days, pageviews, users, sessions,
                    avg_session_duration, bounce_rate, performance_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    property_name = VALUES(property_name),
                    property_url = VALUES(property_url),
                    property_type = VALUES(property_type),
                    property_status = VALUES(property_status),
                    price = VALUES(price),
                    pageviews = VALUES(pageviews),
                    users = VALUES(users),
                    sessions = VALUES(sessions),
                    avg_session_duration = VALUES(avg_session_duration),
                    bounce_rate = VALUES(bounce_rate),
                    performance_score = VALUES(performance_score),
                    updated_at = CURRENT_TIMESTAMP
            """, (
                listing['reference'],
                listing['name'],
                listing['url'],
                listing['type'],
                listing['status'],
                listing['price'],
                report_date,
                days,
                listing['pageviews'],
                listing['users'],
                listing['sessions'],
                listing['avg_session_duration'],
                listing['bounce_rate'],
                listing['performance_score']
            ))
            
            analytics_id = cursor.lastrowid or cursor.execute(
                "SELECT id FROM property_analytics WHERE reference = %s AND report_date = %s AND period_days = %s",
                (listing['reference'], report_date, days)
            ) or cursor.fetchone()[0]
            
            # Delete old traffic sources for this record
            cursor.execute("""
                DELETE FROM property_traffic_sources WHERE analytics_id = %s
            """, (analytics_id,))
            
            # Insert traffic sources
            for source, sessions in listing.get('traffic_sources', {}).items():
                cursor.execute("""
                    INSERT INTO property_traffic_sources (analytics_id, source, sessions)
                    VALUES (%s, %s, %s)
                """, (analytics_id, source, sessions))
            
            # Store marketing recommendations if available
            if 'recommendations' in listing:
                # Delete old recommendations
                cursor.execute("""
                    DELETE FROM property_marketing_recommendations WHERE analytics_id = %s
                """, (analytics_id,))
                
                for rec in listing['recommendations']:
                    cursor.execute("""
                        INSERT INTO property_marketing_recommendations (
                            analytics_id, priority, platform, action, reason,
                            suggested_budget, expected_impact
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        analytics_id,
                        rec['priority'],
                        rec['platform'],
                        rec['action'],
                        rec['reason'],
                        rec['suggested_budget'],
                        rec['expected_impact']
                    ))
            
            stored_count += 1
        
        connection.commit()
        cursor.close()
        print(f"✅ Stored {stored_count} property analytics records in database")
        return True
        
    except Error as e:
        print(f"⚠️ Error storing data in database: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            connection.close()


def add_viewing_request(reference, request_date=None, notes=""):
    """Add a viewing request for a property."""
    if request_date is None:
        request_date = datetime.now().date()
    
    connection = get_db_connection()
    if not connection:
        print("❌ Cannot add viewing request - no database connection")
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
        return True
        
    except Error as e:
        print(f"❌ Error adding viewing request: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()


def get_viewing_requests_for_period(reference, days=30):
    """Get viewing requests for a property over a period."""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        cursor.execute("""
            SELECT request_date, SUM(request_count) as total_requests, GROUP_CONCAT(notes SEPARATOR '; ') as all_notes
            FROM property_viewing_requests
            WHERE reference = %s AND request_date BETWEEN %s AND %s
            GROUP BY request_date
            ORDER BY request_date DESC
        """, (reference, start_date, end_date))
        
        results = cursor.fetchall()
        cursor.close()
        return results
        
    except Error as e:
        print(f"⚠️ Error fetching viewing requests: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()


def correlate_viewings_with_marketing(listings, days):
    """Add viewing request data to listings and correlate with traffic sources."""
    for listing in listings:
        viewing_requests = get_viewing_requests_for_period(listing['reference'], days)
        listing['viewing_requests'] = viewing_requests
        listing['total_viewing_requests'] = sum(vr['total_requests'] for vr in viewing_requests)
        
        # Calculate correlation score (simple metric)
        if listing['total_viewing_requests'] > 0 and listing['sessions'] > 0:
            listing['viewing_conversion_rate'] = (listing['total_viewing_requests'] / listing['sessions']) * 100
        else:
            listing['viewing_conversion_rate'] = 0
    
    return listings


def fetch_feed(feed_url: str = "https://api.ndestates.com/feeds/ndefeed.xml") -> str:
    """Fetch XML feed content from catalog."""
    with urllib.request.urlopen(feed_url) as resp:
        return resp.read().decode("utf-8")


def parse_feed(xml_text: str):
    """Parse XML feed into a list of property listings."""
    root = ET.fromstring(xml_text)
    listings = []
    
    for prop in root.findall(".//property"):
        get = lambda tag: (prop.find(tag).text.strip() if prop.find(tag) is not None and prop.find(tag).text else "")
        
        url = get("url")
        price_raw = get("price")
        type_ = get("type")  # 'buy' or 'rent'
        status = get("status")  # 'available', 'sold', 'let'
        reference = get("reference")
        name = get("houseName")
        address = get("address")
        
        try:
            price = int(price_raw) if price_raw else None
        except ValueError:
            price = None
        
        # Extract URL path for matching with GA4 data
        try:
            parsed_url = urllib.parse.urlparse(url)
            url_path = parsed_url.path
        except:
            url_path = url
        
        listings.append({
            "url": url,
            "url_path": url_path,
            "price": price,
            "type": type_.lower() if type_ else "",
            "status": status.lower() if status else "",
            "reference": reference,
            "name": name,
            "address": address,
            # Analytics data (will be populated later)
            "pageviews": 0,
            "users": 0,
            "sessions": 0,
            "avg_session_duration": 0,
            "bounce_rate": 0,
            "traffic_sources": {},
        })
    
    return listings


def get_analytics_data(days: int = 30):
    """
    Fetch GA4 analytics data for the specified time period.
    Returns pageviews, users, sessions, and traffic source by page path.
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    date_range = create_date_range(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    # Get page-level metrics
    print(f"📊 Fetching analytics data for last {days} days...")
    
    dimensions = ["pagePath", "sessionDefaultChannelGroup"]
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
        limit=10000,
    )
    
    # Aggregate data by page path
    analytics_data = defaultdict(lambda: {
        'pageviews': 0,
        'users': 0,
        'sessions': 0,
        'total_session_duration': 0,
        'bounce_rate_sum': 0,
        'traffic_sources': defaultdict(int),
        'session_count': 0
    })
    
    if response.row_count > 0:
        for row in response.rows:
            page_path = row.dimension_values[0].value
            traffic_source = row.dimension_values[1].value
            
            # Map GA4 channel groups to our specific channels
            mapped_source = map_traffic_source(traffic_source)
            
            pageviews = int(row.metric_values[0].value)
            users = int(row.metric_values[1].value)
            sessions = int(row.metric_values[2].value)
            avg_duration = float(row.metric_values[3].value)
            bounce_rate = float(row.metric_values[4].value)
            
            data = analytics_data[page_path]
            data['pageviews'] += pageviews
            data['users'] += users
            data['sessions'] += sessions
            data['total_session_duration'] += avg_duration * sessions
            data['bounce_rate_sum'] += bounce_rate * sessions
            data['traffic_sources'][mapped_source] += sessions
            data['session_count'] += sessions
    
    # Calculate averages
    for path, data in analytics_data.items():
        if data['session_count'] > 0:
            data['avg_session_duration'] = data['total_session_duration'] / data['session_count']
            data['bounce_rate'] = data['bounce_rate_sum'] / data['session_count']
    
    print(f"✅ Found analytics data for {len(analytics_data)} unique pages")
    
    return dict(analytics_data)


def match_listings_to_analytics(listings, analytics_data):
    """
    Match property listings to GA4 analytics data based on URL paths.
    Updates listings with analytics metrics.
    """
    matched_count = 0
    
    for listing in listings:
        url_path = listing['url_path']
        
        # Try exact match first
        if url_path in analytics_data:
            data = analytics_data[url_path]
            listing['pageviews'] = data['pageviews']
            listing['users'] = data['users']
            listing['sessions'] = data['sessions']
            listing['avg_session_duration'] = data['avg_session_duration']
            listing['bounce_rate'] = data['bounce_rate']
            listing['traffic_sources'] = dict(data['traffic_sources'])
            matched_count += 1
        else:
            # Try partial match (URL path might have variations)
            for path, data in analytics_data.items():
                if url_path in path or path in url_path:
                    listing['pageviews'] = data['pageviews']
                    listing['users'] = data['users']
                    listing['sessions'] = data['sessions']
                    listing['avg_session_duration'] = data['avg_session_duration']
                    listing['bounce_rate'] = data['bounce_rate']
                    listing['traffic_sources'] = dict(data['traffic_sources'])
                    matched_count += 1
                    break
    
    print(f"✅ Matched {matched_count} of {len(listings)} listings to analytics data")
    
    return listings


def calculate_performance_score(listing):
    """
    Calculate a performance score for a listing based on multiple factors.
    Score ranges from 0-100.
    """
    score = 0
    
    # Pageviews (max 40 points)
    if listing['pageviews'] > 100:
        score += 40
    elif listing['pageviews'] > 50:
        score += 30
    elif listing['pageviews'] > 20:
        score += 20
    elif listing['pageviews'] > 10:
        score += 10
    
    # Users (max 30 points)
    if listing['users'] > 50:
        score += 30
    elif listing['users'] > 25:
        score += 20
    elif listing['users'] > 10:
        score += 10
    
    # Engagement quality (max 30 points)
    if listing['avg_session_duration'] > 120:  # 2+ minutes
        score += 15
    elif listing['avg_session_duration'] > 60:  # 1+ minute
        score += 10
    elif listing['avg_session_duration'] > 30:  # 30+ seconds
        score += 5
    
    # Bounce rate (lower is better)
    if listing['bounce_rate'] < 0.3:
        score += 15
    elif listing['bounce_rate'] < 0.5:
        score += 10
    elif listing['bounce_rate'] < 0.7:
        score += 5
    
    return score


def generate_marketing_recommendations(listing):
    """
    Generate platform-specific marketing recommendations for a listing.
    """
    recommendations = []
    score = calculate_performance_score(listing)
    
    # Traffic source analysis
    total_sessions = sum(listing['traffic_sources'].values()) if listing['traffic_sources'] else 0
    
    if total_sessions == 0:
        return [{
            'priority': 'CRITICAL',
            'platform': 'All Channels',
            'action': 'Start marketing campaign',
            'reason': 'No traffic detected - listing has zero visibility',
            'suggested_budget': '£200-500/month',
            'expected_impact': 'HIGH'
        }]
    
    # Analyze traffic sources with expanded channels
    email_sessions = listing['traffic_sources'].get('Email', 0)
    facebook_sessions = listing['traffic_sources'].get('Facebook', 0)
    instagram_sessions = listing['traffic_sources'].get('Instagram', 0)
    linkedin_sessions = listing['traffic_sources'].get('LinkedIn', 0)
    google_organic = listing['traffic_sources'].get('Google Organic', 0)
    google_paid = listing['traffic_sources'].get('Google Ads', 0)
    organic_search = listing['traffic_sources'].get('Organic Search', 0)
    paid_search = listing['traffic_sources'].get('Paid Search', 0)
    social_sessions = listing['traffic_sources'].get('Social', 0)
    direct_sessions = listing['traffic_sources'].get('Direct', 0)
    
    # Calculate totals
    total_organic = google_organic + organic_search
    total_paid = google_paid + paid_search
    total_social = facebook_sessions + instagram_sessions + linkedin_sessions + social_sessions
    
    # No email traffic - critical missed opportunity
    if email_sessions == 0:
        recommendations.append({
            'priority': 'HIGH',
            'platform': 'Mailchimp Email',
            'action': 'Launch email marketing campaign',
            'reason': 'No email traffic detected - leverage existing database',
            'suggested_budget': 'Internal effort + Mailchimp subscription',
            'expected_impact': 'HIGH'
        })
    
    # Low overall performance
    if score < 30:
        recommendations.append({
            'priority': 'HIGH',
            'platform': 'Google Ads',
            'action': 'Launch targeted PPC campaign',
            'reason': f'Low performance score ({score}/100) - needs immediate visibility boost',
            'suggested_budget': '£150-300/month',
            'expected_impact': 'HIGH'
        })
        
        # Separate Facebook and Instagram recommendations
        if facebook_sessions < 5:
            recommendations.append({
                'priority': 'HIGH',
                'platform': 'Facebook Ads',
                'action': 'Create property showcase ads',
                'reason': f'Low Facebook traffic ({facebook_sessions} sessions) - visual platform ideal for properties',
                'suggested_budget': '£100-200/month',
                'expected_impact': 'HIGH'
            })
        
        if instagram_sessions < 5:
            recommendations.append({
                'priority': 'HIGH',
                'platform': 'Instagram Ads',
                'action': 'Create Instagram Stories and Feed ads',
                'reason': f'Low Instagram traffic ({instagram_sessions} sessions) - high engagement platform',
                'suggested_budget': '£75-150/month',
                'expected_impact': 'MEDIUM'
            })
    
    # Low organic traffic
    if total_organic < total_sessions * 0.3 and total_sessions > 0:
        recommendations.append({
            'priority': 'MEDIUM',
            'platform': 'SEO / Google Organic',
            'action': 'Optimize listing content and metadata',
            'reason': f'Low organic traffic ({total_organic} sessions, {total_organic/total_sessions*100:.1f}% of total)',
            'suggested_budget': 'Internal effort or £300-500 one-time',
            'expected_impact': 'MEDIUM (long-term)'
        })
    
    # No paid traffic on valuable property
    if total_paid == 0 and listing.get('price', 0) > 400000:
        recommendations.append({
            'priority': 'MEDIUM',
            'platform': 'Google Ads',
            'action': 'Consider PPC for high-value property',
            'reason': f'Premium property (£{listing["price"]:,}) with no paid advertising',
            'suggested_budget': '£200-400/month',
            'expected_impact': 'MEDIUM'
        })
    
    # LinkedIn for high-value properties
    if linkedin_sessions < 3 and listing.get('price', 0) > 500000:
        recommendations.append({
            'priority': 'MEDIUM',
            'platform': 'LinkedIn Ads',
            'action': 'Target professional audience',
            'reason': f'Premium property (£{listing["price"]:,}) with minimal LinkedIn presence ({linkedin_sessions} sessions)',
            'suggested_budget': '£100-200/month',
            'expected_impact': 'MEDIUM'
        })
    
    # Low overall social presence
    if total_social < 10:
        recommendations.append({
            'priority': 'MEDIUM',
            'platform': 'Social Media',
            'action': 'Increase social media posting frequency',
            'reason': f'Minimal social traffic ({total_social} sessions across all platforms)',
            'suggested_budget': 'Internal effort',
            'expected_impact': 'MEDIUM'
        })
    
    # High bounce rate
    if listing['bounce_rate'] > 0.7 and listing['pageviews'] > 20:
        recommendations.append({
            'priority': 'MEDIUM',
            'platform': 'Website/Content',
            'action': 'Improve listing content and images',
            'reason': f'High bounce rate ({listing["bounce_rate"]*100:.1f}%) - visitors leaving quickly',
            'suggested_budget': 'Internal effort',
            'expected_impact': 'MEDIUM'
        })
    
    # Good performance - maintain momentum
    if score > 70:
        recommendations.append({
            'priority': 'LOW',
            'platform': 'All Channels',
            'action': 'Maintain current marketing efforts',
            'reason': f'Strong performance ({score}/100) - continue successful strategy',
            'suggested_budget': 'Current spend',
            'expected_impact': 'Maintain current results'
        })
    
    return recommendations if recommendations else [{
        'priority': 'LOW',
        'platform': 'All Channels',
        'action': 'Monitor and optimize',
        'reason': 'Moderate performance - watch for trends',
        'suggested_budget': 'Current spend',
        'expected_impact': 'MEDIUM'
    }]


def generate_report(listings, days, include_recommendations=False, low_performers_only=False):
    """
    Generate formatted report of catalog analytics.
    """
    # Calculate scores and sort
    for listing in listings:
        listing['performance_score'] = calculate_performance_score(listing)
    
    # Filter if needed
    if low_performers_only:
        listings = [l for l in listings if l['performance_score'] < 40]
    
    # Sort by performance score (lowest first for action items)
    listings.sort(key=lambda x: x['performance_score'])
    
    print("\n" + "=" * 120)
    print(f"📊 CATALOG ANALYTICS REPORT - LAST {days} DAYS")
    print("=" * 120)
    
    # Summary statistics
    total_listings = len(listings)
    
    if total_listings == 0:
        print("\n⚠️  WARNING: No properties found matching your criteria!")
        print("\nPossible issues:")
        print("  - Property references don't exist in the feed")
        print("  - Check spelling of property references")
        print("  - Run without --properties filter to see all available properties")
        return listings
    
    listings_with_traffic = sum(1 for l in listings if l['pageviews'] > 0)
    total_pageviews = sum(l['pageviews'] for l in listings)
    total_users = sum(l['users'] for l in listings)
    avg_score = sum(l['performance_score'] for l in listings) / total_listings
    
    print(f"\n📈 Summary:")
    print(f"   Total Listings: {total_listings}")
    print(f"   Listings with Traffic: {listings_with_traffic} ({listings_with_traffic/total_listings*100:.1f}%)")
    print(f"   Total Pageviews: {total_pageviews:,}")
    print(f"   Total Users: {total_users:,}")
    print(f"   Average Performance Score: {avg_score:.1f}/100")
    
    # Top performers
    print(f"\n🏆 Top 5 Performing Listings:")
    top_performers = sorted(listings, key=lambda x: x['performance_score'], reverse=True)[:5]
    for idx, listing in enumerate(top_performers, 1):
        print(f"   {idx}. {listing['name'] or listing['reference']} - Score: {listing['performance_score']}/100")
        print(f"      Pageviews: {listing['pageviews']:,} | Users: {listing['users']:,} | Avg Time: {listing['avg_session_duration']:.0f}s")
        if listing['traffic_sources']:
            top_sources = sorted(listing['traffic_sources'].items(), key=lambda x: x[1], reverse=True)[:3]
            sources_str = ", ".join([f"{src}: {cnt}" for src, cnt in top_sources])
            print(f"      Top Sources: {sources_str}")
    
    # Low performers needing attention
    print(f"\n⚠️ Listings Needing Attention (Score < 40):")
    low_performers = [l for l in listings if l['performance_score'] < 40]
    
    if not low_performers:
        print("   None - all listings performing well!")
    else:
        for listing in low_performers[:10]:  # Show top 10 worst
            print(f"\n   • {listing['name'] or listing['reference']} ({listing['type'].upper()})")
            print(f"     Reference: {listing['reference']}")
            print(f"     Status: {listing['status'].title()}")
            print(f"     Price: £{listing['price']:,}" if listing['price'] else "     Price: N/A")
            print(f"     URL: {listing['url']}")
            print(f"     Performance Score: {listing['performance_score']}/100")
            print(f"     Pageviews: {listing['pageviews']:,} | Users: {listing['users']:,}")
            print(f"     Avg Session Duration: {listing['avg_session_duration']:.0f}s | Bounce Rate: {listing['bounce_rate']*100:.1f}%")
            
            if listing['traffic_sources']:
                print(f"\n     📍 TRAFFIC SOURCES & MEDIUM:")
                print(f"     {'Source/Medium':<30} {'Sessions':<12} {'% of Total'}")
                print(f"     {'-'*30} {'-'*12} {'-'*10}")
                total_sessions = sum(listing['traffic_sources'].values())
                for source, count in sorted(listing['traffic_sources'].items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_sessions * 100) if total_sessions > 0 else 0
                    print(f"     {source:<30} {count:<12} {percentage:>6.1f}%")
            else:
                print(f"\n     📍 TRAFFIC SOURCES: No traffic data available (0 sessions)")
            
            # Show viewing requests if available
            if listing.get('total_viewing_requests', 0) > 0:
                print(f"     👁️ Viewing Requests: {listing['total_viewing_requests']} in last {days} days")
                if listing.get('viewing_conversion_rate', 0) > 0:
                    print(f"        Viewing Conversion Rate: {listing['viewing_conversion_rate']:.2f}%")
                if listing.get('viewing_requests'):
                    for vr in listing['viewing_requests'][:3]:  # Show last 3
                        print(f"        - {vr['request_date']}: {vr['total_requests']} request(s)")
            
            if include_recommendations:
                recommendations = generate_marketing_recommendations(listing)
                listing['recommendations'] = recommendations  # Store for database
                print(f"     🎯 Marketing Recommendations:")
                for rec in recommendations[:3]:  # Show top 3 recommendations
                    print(f"        [{rec['priority']}] {rec['platform']}: {rec['action']}")
                    print(f"           Reason: {rec['reason']}")
                    print(f"           Budget: {rec['suggested_budget']} | Impact: {rec['expected_impact']}")
    
    print("\n" + "=" * 120)
    
    return listings


def export_to_csv(listings, days, filename=None):
    """
    Export catalog analytics report to CSV.
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(REPORTS_DIR, f"catalog_analytics_{days}days_{timestamp}.csv")
    
    # Flatten data for CSV export
    export_data = []
    for listing in listings:
        # Get top 3 traffic sources
        traffic_sources_str = ", ".join([
            f"{source}: {count}" 
            for source, count in sorted(listing['traffic_sources'].items(), key=lambda x: x[1], reverse=True)[:3]
        ]) if listing['traffic_sources'] else "None"
        
        export_data.append({
            'Reference': listing['reference'],
            'Name': listing['name'],
            'Type': listing['type'],
            'Status': listing['status'],
            'Price': listing['price'],
            'URL': listing['url'],
            'Performance Score': listing['performance_score'],
            'Pageviews': listing['pageviews'],
            'Users': listing['users'],
            'Sessions': listing['sessions'],
            'Avg Session Duration (s)': round(listing['avg_session_duration'], 2),
            'Bounce Rate (%)': round(listing['bounce_rate'] * 100, 2),
            'Top Traffic Sources': traffic_sources_str,
            'Viewing Requests': listing.get('total_viewing_requests', 0),
            'Viewing Conversion Rate (%)': round(listing.get('viewing_conversion_rate', 0), 2),
        })
    
    df = pd.DataFrame(export_data)
    df.to_csv(filename, index=False)
    
    print(f"\n✅ Report exported to: {filename}")
    return filename


def main():
    parser = argparse.ArgumentParser(description='Catalog Analytics Comparison Report')
    parser.add_argument('--days', type=int, default=30, choices=[7, 14, 30, 60, 90],
                       help='Time period for analytics (default: 30)')
    parser.add_argument('--recommendations', action='store_true',
                       help='Include marketing recommendations')
    parser.add_argument('--export-csv', action='store_true',
                       help='Export results to CSV file')
    parser.add_argument('--type', choices=['buy', 'rent'],
                       help='Filter by property type')
    parser.add_argument('--status', choices=['available', 'sold', 'let'],
                       help='Filter by property status')
    parser.add_argument('--properties', type=str,
                       help='Filter by specific property references (comma-separated, e.g., STH250039,STH240092)')
    parser.add_argument('--low-performers', action='store_true',
                       help='Show only low-performing listings (score < 40)')
    parser.add_argument('--feed-url', default='https://api.ndestates.com/feeds/ndefeed.xml',
                       help='XML feed URL (default: ND Estates feed)')
    parser.add_argument('--store-db', action='store_true',
                       help='Store results in database for trend analysis')
    parser.add_argument('--add-viewing', nargs=2, metavar=('REFERENCE', 'DATE'),
                       help='Add viewing request: REFERENCE YYYY-MM-DD (or "today")')
    parser.add_argument('--viewing-notes', default='',
                       help='Notes for viewing request')
    parser.add_argument('--init-db', action='store_true',
                       help='Initialize database tables')
    
    args = parser.parse_args()
    
    # Handle database initialization
    if args.init_db:
        print("🔧 Initializing database tables...")
        if init_database_tables():
            print("✅ Database tables initialized successfully")
        else:
            print("❌ Failed to initialize database tables")
        return
    
    # Handle adding viewing request
    if args.add_viewing:
        reference, date_str = args.add_viewing
        viewing_date = datetime.now().date() if date_str.lower() == 'today' else datetime.strptime(date_str, '%Y-%m-%d').date()
        add_viewing_request(reference, viewing_date, args.viewing_notes)
        return
    
    if not GA4_PROPERTY_ID:
        print("❌ GA4_PROPERTY_ID not found. Please check your .env file.")
        return
    
    try:
        # Fetch property catalog
        print("📥 Fetching property catalog from feed...")
        xml_text = fetch_feed(args.feed_url)
        listings = parse_feed(xml_text)
        print(f"✅ Loaded {len(listings)} properties from catalog")
        
        # Apply filters
        if args.type:
            listings = [l for l in listings if l['type'] == args.type]
            print(f"📋 Filtered to {len(listings)} {args.type} properties")
        
        if args.status:
            listings = [l for l in listings if l['status'] == args.status]
            print(f"📋 Filtered to {len(listings)} {args.status} properties")
        
        if args.properties:
            # Filter by specific property references
            # Handle both comma-separated and space-separated references
            property_refs = [ref.strip() for ref in args.properties.replace(',', ' ').split() if ref.strip()]
            if property_refs:
                # Get available references before filtering
                available_refs = [l['reference'] for l in listings]
                listings = [l for l in listings if l['reference'] in property_refs]
                print(f"📋 Filtered to {len(listings)} specified properties: {', '.join(property_refs)}")
                if len(listings) == 0:
                    print(f"\n⚠️  ERROR: No properties matched the provided references!")
                    print(f"   Requested: {', '.join(property_refs)}")
                    print(f"   Available: {', '.join(available_refs[:10])}{'...' if len(available_refs) > 10 else ''}")
                    print(f"\nTip: Run without --properties to see all {len(available_refs)} properties")
                    return
            else:
                print(f"⚠️  WARNING: --properties specified but no valid references found")
        
        # Get analytics data
        analytics_data = get_analytics_data(days=args.days)
        
        # Match listings to analytics
        listings = match_listings_to_analytics(listings, analytics_data)
        
        # Correlate with viewing requests
        listings = correlate_viewings_with_marketing(listings, args.days)
        
        # Generate report
        listings = generate_report(
            listings,
            args.days,
            include_recommendations=args.recommendations,
            low_performers_only=args.low_performers
        )
        
        # Store in database if requested
        if args.store_db:
            print("\n💾 Storing analytics data in database...")
            store_analytics_in_database(listings, args.days)
        
        # Export if requested
        if args.export_csv:
            export_to_csv(listings, args.days)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
