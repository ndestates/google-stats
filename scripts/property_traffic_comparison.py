#!/usr/bin/env python3
"""
Property Traffic Source Comparison Report
Shows detailed traffic breakdown by source for all properties
"""

import sys
import os
from datetime import datetime, timedelta
import argparse
import mysql.connector
from mysql.connector import Error

# Add parent directory to path for imports
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


def generate_traffic_comparison_html(days=30):
    """Generate HTML report comparing traffic sources across all properties."""
    
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get traffic breakdown by source
        query = """
        SELECT 
            p.reference,
            p.house_name,
            p.price,
            SUM(CASE WHEN ptd.traffic_source = 'facebook' AND ptd.traffic_medium IN ('catalog', 'fb_ads', 'paid') 
                THEN ptd.sessions ELSE 0 END) as facebook_paid,
            SUM(CASE WHEN ptd.traffic_source LIKE '%facebook%' AND ptd.traffic_medium NOT IN ('catalog', 'fb_ads', 'paid')
                THEN ptd.sessions ELSE 0 END) as facebook_social,
            SUM(CASE WHEN ptd.traffic_source = 'google' AND ptd.traffic_medium = 'cpc' 
                THEN ptd.sessions ELSE 0 END) as google_paid,
            SUM(CASE WHEN ptd.traffic_source = 'google' AND ptd.traffic_medium = 'organic' 
                THEN ptd.sessions ELSE 0 END) as google_organic,
            SUM(CASE WHEN ptd.traffic_source = 'google.com' AND ptd.traffic_medium = 'social' 
                THEN ptd.sessions ELSE 0 END) as google_social,
            SUM(CASE WHEN ptd.traffic_source LIKE '%linkedin%' 
                THEN ptd.sessions ELSE 0 END) as linkedin,
            SUM(CASE WHEN ptd.traffic_source = 'places.je' 
                THEN ptd.sessions ELSE 0 END) as places_je,
            SUM(CASE WHEN ptd.traffic_source LIKE '%bailiwick%' 
                THEN ptd.sessions ELSE 0 END) as bailiwick,
            SUM(CASE WHEN ptd.traffic_source LIKE '%mailchimp%' OR ptd.traffic_medium = 'email' 
                THEN ptd.sessions ELSE 0 END) as email,
            SUM(ptd.sessions) as total_sessions,
            SUM(ptd.pageviews) as total_pageviews,
            SUM(ptd.users) as total_users
        FROM properties p
        LEFT JOIN property_traffic_detail ptd ON p.reference = ptd.reference AND ptd.period_days = %s
        WHERE p.is_active = 1
        GROUP BY p.reference, p.house_name, p.price
        HAVING total_sessions > 0
        ORDER BY total_sessions DESC
        """
        
        cursor.execute(query, (days,))
        properties = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        if not properties:
            return None
        
        # Generate HTML
        period_text = "Yesterday" if days == 1 else f"Last {days} Days"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Property Traffic Source Comparison - {period_text}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        h1 {{
            color: #667eea;
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #666;
            font-size: 16px;
            margin-bottom: 20px;
        }}
        
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .summary-card .label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .table-container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        th {{
            padding: 15px 10px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        th.numeric {{
            text-align: right;
        }}
        
        td {{
            padding: 12px 10px;
            border-bottom: 1px solid #f0f0f0;
            font-size: 14px;
        }}
        
        td.numeric {{
            text-align: right;
            font-weight: 500;
        }}
        
        tr:hover {{
            background-color: #f8f9ff;
        }}
        
        .property-name {{
            font-weight: 600;
            color: #667eea;
        }}
        
        .reference {{
            color: #999;
            font-size: 12px;
            display: block;
            margin-top: 2px;
        }}
        
        .price {{
            color: #333;
            font-weight: 600;
        }}
        
        .highlight {{
            background-color: #fff3cd;
            font-weight: 600;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-right: 5px;
        }}
        
        .badge-facebook {{
            background-color: #1877f2;
            color: white;
        }}
        
        .badge-google {{
            background-color: #4285f4;
            color: white;
        }}
        
        .badge-email {{
            background-color: #ffc107;
            color: #333;
        }}
        
        .badge-social {{
            background-color: #17a2b8;
            color: white;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            font-size: 14px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .header, .table-container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Property Traffic Source Comparison</h1>
            <div class="subtitle">
                Period: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')} ({period_text})
            </div>
            
            <div class="summary-cards">
"""
        
        # Calculate totals
        total_properties = len(properties)
        total_sessions = sum(p['total_sessions'] for p in properties)
        total_pageviews = sum(p['total_pageviews'] for p in properties)
        total_users = sum(p['total_users'] for p in properties)
        total_facebook_paid = sum(p['facebook_paid'] for p in properties)
        total_google_organic = sum(p['google_organic'] for p in properties)
        total_email = sum(p['email'] for p in properties)
        
        html += f"""
                <div class="summary-card">
                    <div class="value">{total_properties}</div>
                    <div class="label">Active Properties</div>
                </div>
                <div class="summary-card">
                    <div class="value">{total_sessions:,}</div>
                    <div class="label">Total Sessions</div>
                </div>
                <div class="summary-card">
                    <div class="value">{total_pageviews:,}</div>
                    <div class="label">Total Pageviews</div>
                </div>
                <div class="summary-card">
                    <div class="value">{total_users:,}</div>
                    <div class="label">Total Users</div>
                </div>
            </div>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Property</th>
                        <th>Price</th>
                        <th class="numeric">Facebook<br>Paid</th>
                        <th class="numeric">Facebook<br>Social</th>
                        <th class="numeric">Google<br>Paid</th>
                        <th class="numeric">Google<br>Organic</th>
                        <th class="numeric">Google<br>Social</th>
                        <th class="numeric">LinkedIn</th>
                        <th class="numeric">Places.je</th>
                        <th class="numeric">Bailiwick</th>
                        <th class="numeric">Email</th>
                        <th class="numeric">Total<br>Sessions</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for prop in properties:
            price_formatted = f"£{prop['price']:,.0f}" if prop['price'] else "N/A"
            
            html += f"""
                    <tr>
                        <td>
                            <div class="property-name">{prop['house_name'] or prop['reference']}</div>
                            <span class="reference">{prop['reference']}</span>
                        </td>
                        <td class="price">{price_formatted}</td>
                        <td class="numeric">{prop['facebook_paid']:,}</td>
                        <td class="numeric">{prop['facebook_social']:,}</td>
                        <td class="numeric">{prop['google_paid']:,}</td>
                        <td class="numeric">{prop['google_organic']:,}</td>
                        <td class="numeric">{prop['google_social']:,}</td>
                        <td class="numeric">{prop['linkedin']:,}</td>
                        <td class="numeric">{prop['places_je']:,}</td>
                        <td class="numeric">{prop['bailiwick']:,}</td>
                        <td class="numeric">{prop['email']:,}</td>
                        <td class="numeric highlight">{prop['total_sessions']:,}</td>
                    </tr>
"""
        
        html += f"""
                </tbody>
                <tfoot>
                    <tr style="background-color: #f8f9ff; font-weight: bold;">
                        <td colspan="2">TOTAL</td>
                        <td class="numeric">{total_facebook_paid:,}</td>
                        <td class="numeric">{sum(p['facebook_social'] for p in properties):,}</td>
                        <td class="numeric">{sum(p['google_paid'] for p in properties):,}</td>
                        <td class="numeric">{total_google_organic:,}</td>
                        <td class="numeric">{sum(p['google_social'] for p in properties):,}</td>
                        <td class="numeric">{sum(p['linkedin'] for p in properties):,}</td>
                        <td class="numeric">{sum(p['places_je'] for p in properties):,}</td>
                        <td class="numeric">{sum(p['bailiwick'] for p in properties):,}</td>
                        <td class="numeric">{total_email:,}</td>
                        <td class="numeric highlight">{total_sessions:,}</td>
                    </tr>
                </tfoot>
            </table>
        </div>
        
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')} | ND Estates Analytics
        </div>
    </div>
</body>
</html>
"""
        
        return html
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Generate property traffic source comparison report')
    parser.add_argument('--days', type=int, choices=[1, 7, 14, 30, 60, 90], default=30,
                      help='Number of days to report on (default: 30)')
    
    args = parser.parse_args()
    
    print("="*80)
    print(f"📊 PROPERTY TRAFFIC SOURCE COMPARISON - LAST {args.days} DAYS")
    print("="*80)
    
    print(f"\n📝 Generating HTML report...")
    
    html = generate_traffic_comparison_html(args.days)
    
    if not html:
        print("❌ Failed to generate report - no data available")
        return
    
    # Save to reports directory
    period_label = "yesterday" if args.days == 1 else f"{args.days}days"
    filename = f"traffic_comparison_{period_label}_{datetime.now().strftime('%Y%m%d')}.html"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    with open(filepath, 'w') as f:
        f.write(html)
    
    print(f"✅ Report generated successfully!")
    print(f"   📄 File: {filepath}")
    print(f"\n💡 Open in browser: file://{filepath}")
    print(f"   Or run: xdg-open {filepath}")


if __name__ == "__main__":
    main()
