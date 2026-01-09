"""
Catalog Analytics Comparison Script
Compare property catalog listings against GA4 analytics data

DDEV Usage:
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
    - Identify low-performing listings
    - Generate marketing recommendations by platform
    - Export results to CSV
    - Filter by property type and status
    - Compare performance across time periods
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
            data['traffic_sources'][traffic_source] += sessions
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
    
    # Analyze traffic sources
    organic_sessions = listing['traffic_sources'].get('Organic Search', 0)
    paid_sessions = listing['traffic_sources'].get('Paid Search', 0)
    social_sessions = listing['traffic_sources'].get('Organic Social', 0)
    direct_sessions = listing['traffic_sources'].get('Direct', 0)
    
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
        
        recommendations.append({
            'priority': 'HIGH',
            'platform': 'Facebook/Instagram',
            'action': 'Create property showcase ads',
            'reason': 'Need broader audience reach with visual content',
            'suggested_budget': '£100-200/month',
            'expected_impact': 'MEDIUM'
        })
    
    # Low organic traffic
    if organic_sessions < total_sessions * 0.3:
        recommendations.append({
            'priority': 'MEDIUM',
            'platform': 'SEO',
            'action': 'Optimize listing content and metadata',
            'reason': f'Low organic traffic ({organic_sessions} sessions, {organic_sessions/total_sessions*100:.1f}% of total)',
            'suggested_budget': 'Internal effort or £300-500 one-time',
            'expected_impact': 'MEDIUM (long-term)'
        })
    
    # No paid traffic on valuable property
    if paid_sessions == 0 and listing.get('price', 0) > 400000:
        recommendations.append({
            'priority': 'MEDIUM',
            'platform': 'Google Ads',
            'action': 'Consider PPC for high-value property',
            'reason': f'Premium property (£{listing["price"]:,}) with no paid advertising',
            'suggested_budget': '£200-400/month',
            'expected_impact': 'MEDIUM'
        })
    
    # Low social presence
    if social_sessions < 5:
        recommendations.append({
            'priority': 'LOW',
            'platform': 'Social Media',
            'action': 'Increase social media posting frequency',
            'reason': f'Minimal social traffic ({social_sessions} sessions)',
            'suggested_budget': 'Internal effort',
            'expected_impact': 'LOW-MEDIUM'
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
    listings_with_traffic = sum(1 for l in listings if l['pageviews'] > 0)
    total_pageviews = sum(l['pageviews'] for l in listings)
    total_users = sum(l['users'] for l in listings)
    avg_score = sum(l['performance_score'] for l in listings) / len(listings) if listings else 0
    
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
                print(f"     Traffic Sources:")
                for source, count in sorted(listing['traffic_sources'].items(), key=lambda x: x[1], reverse=True):
                    print(f"        - {source}: {count} sessions")
            
            if include_recommendations:
                recommendations = generate_marketing_recommendations(listing)
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
        })
    
    df = pd.DataFrame(export_data)
    df.to_csv(filename, index=False)
    
    print(f"\n✅ Report exported to: {filename}")
    return filename


def main():
    parser = argparse.ArgumentParser(description='Catalog Analytics Comparison Report')
    parser.add_argument('--days', type=int, default=30, choices=[30, 60, 90],
                       help='Time period for analytics (default: 30)')
    parser.add_argument('--recommendations', action='store_true',
                       help='Include marketing recommendations')
    parser.add_argument('--export-csv', action='store_true',
                       help='Export results to CSV file')
    parser.add_argument('--type', choices=['buy', 'rent'],
                       help='Filter by property type')
    parser.add_argument('--status', choices=['available', 'sold', 'let'],
                       help='Filter by property status')
    parser.add_argument('--low-performers', action='store_true',
                       help='Show only low-performing listings (score < 40)')
    parser.add_argument('--feed-url', default='https://api.ndestates.com/feeds/ndefeed.xml',
                       help='XML feed URL (default: ND Estates feed)')
    
    args = parser.parse_args()
    
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
        
        # Get analytics data
        analytics_data = get_analytics_data(days=args.days)
        
        # Match listings to analytics
        listings = match_listings_to_analytics(listings, analytics_data)
        
        # Generate report
        listings = generate_report(
            listings,
            args.days,
            include_recommendations=args.recommendations,
            low_performers_only=args.low_performers
        )
        
        # Export if requested
        if args.export_csv:
            export_to_csv(listings, args.days)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
