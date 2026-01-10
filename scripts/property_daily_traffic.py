#!/usr/bin/env python3
"""
Property Daily Traffic Breakdown
Shows day-by-day traffic for a specific property over the last 30 days
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


def get_property_list():
    """Get list of all active properties."""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT reference, house_name, price 
            FROM properties 
            WHERE is_active = 1 
            ORDER BY house_name
        """)
        properties = cursor.fetchall()
        cursor.close()
        connection.close()
        return properties
    except Error as e:
        print(f"❌ Database error: {e}")
        return []


def generate_daily_traffic_html(property_ref):
    """Generate HTML report showing daily traffic breakdown for a property."""
    
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get property details
        cursor.execute("""
            SELECT reference, house_name, url, price 
            FROM properties 
            WHERE reference = %s AND is_active = 1
        """, (property_ref,))
        
        property_info = cursor.fetchone()
        if not property_info:
            cursor.close()
            connection.close()
            return None
        
        # Get daily traffic data for last 30 days
        query = """
        SELECT 
            ptd.report_date,
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
        FROM property_traffic_detail ptd
        WHERE ptd.reference = %s 
          AND ptd.period_days = 1
          AND ptd.report_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY ptd.report_date
        ORDER BY ptd.report_date DESC
        """
        
        cursor.execute(query, (property_ref,))
        daily_data = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        if not daily_data:
            return None
        
        # Generate HTML
        property_name = property_info['house_name'] or property_ref
        price_formatted = f"£{property_info['price']:,.0f}" if property_info['price'] else "N/A"
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Traffic - {property_name}</title>
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
        
        .property-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
            padding: 20px;
            background: #f8f9ff;
            border-radius: 8px;
        }}
        
        .info-item {{
            text-align: center;
        }}
        
        .info-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        
        .info-value {{
            font-size: 20px;
            font-weight: 600;
            color: #667eea;
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
        
        .date-cell {{
            font-weight: 600;
            color: #667eea;
        }}
        
        .highlight {{
            background-color: #fff3cd;
            font-weight: 600;
        }}
        
        .chart-container {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
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
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 Daily Traffic Breakdown</h1>
            <h2 style="color: #764ba2; margin-top: 10px;">{property_name}</h2>
            
            <div class="property-info">
                <div class="info-item">
                    <div class="info-label">Reference</div>
                    <div class="info-value">{property_ref}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Price</div>
                    <div class="info-value">{price_formatted}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Total Days</div>
                    <div class="info-value">{len(daily_data)}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Total Sessions</div>
                    <div class="info-value">{sum(d['total_sessions'] for d in daily_data):,}</div>
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="trafficChart" height="80"></canvas>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
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
        
        # Chart data
        chart_labels = []
        chart_facebook_paid = []
        chart_google_organic = []
        chart_email = []
        
        for day in daily_data:
            date_str = day['report_date'].strftime('%B %d, %Y')
            date_short = day['report_date'].strftime('%b %d')
            
            chart_labels.insert(0, date_short)
            chart_facebook_paid.insert(0, day['facebook_paid'])
            chart_google_organic.insert(0, day['google_organic'])
            chart_email.insert(0, day['email'])
            
            html += f"""
                    <tr>
                        <td class="date-cell">{date_str}</td>
                        <td class="numeric">{day['facebook_paid']:,}</td>
                        <td class="numeric">{day['facebook_social']:,}</td>
                        <td class="numeric">{day['google_paid']:,}</td>
                        <td class="numeric">{day['google_organic']:,}</td>
                        <td class="numeric">{day['google_social']:,}</td>
                        <td class="numeric">{day['linkedin']:,}</td>
                        <td class="numeric">{day['places_je']:,}</td>
                        <td class="numeric">{day['bailiwick']:,}</td>
                        <td class="numeric">{day['email']:,}</td>
                        <td class="numeric highlight">{day['total_sessions']:,}</td>
                    </tr>
"""
        
        # Calculate totals
        total_facebook_paid = sum(d['facebook_paid'] for d in daily_data)
        total_facebook_social = sum(d['facebook_social'] for d in daily_data)
        total_google_paid = sum(d['google_paid'] for d in daily_data)
        total_google_organic = sum(d['google_organic'] for d in daily_data)
        total_google_social = sum(d['google_social'] for d in daily_data)
        total_linkedin = sum(d['linkedin'] for d in daily_data)
        total_places_je = sum(d['places_je'] for d in daily_data)
        total_bailiwick = sum(d['bailiwick'] for d in daily_data)
        total_email = sum(d['email'] for d in daily_data)
        total_sessions = sum(d['total_sessions'] for d in daily_data)
        
        html += f"""
                </tbody>
                <tfoot>
                    <tr style="background-color: #f8f9ff; font-weight: bold;">
                        <td>TOTAL</td>
                        <td class="numeric">{total_facebook_paid:,}</td>
                        <td class="numeric">{total_facebook_social:,}</td>
                        <td class="numeric">{total_google_paid:,}</td>
                        <td class="numeric">{total_google_organic:,}</td>
                        <td class="numeric">{total_google_social:,}</td>
                        <td class="numeric">{total_linkedin:,}</td>
                        <td class="numeric">{total_places_je:,}</td>
                        <td class="numeric">{total_bailiwick:,}</td>
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
    
    <script>
        const ctx = document.getElementById('trafficChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {chart_labels},
                datasets: [
                    {{
                        label: 'Facebook Paid',
                        data: {chart_facebook_paid},
                        borderColor: '#1877f2',
                        backgroundColor: 'rgba(24, 119, 242, 0.1)',
                        tension: 0.4
                    }},
                    {{
                        label: 'Google Organic',
                        data: {chart_google_organic},
                        borderColor: '#4285f4',
                        backgroundColor: 'rgba(66, 133, 244, 0.1)',
                        tension: 0.4
                    }},
                    {{
                        label: 'Email',
                        data: {chart_email},
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Daily Traffic Trends - Last 30 Days',
                        font: {{
                            size: 16,
                            weight: 'bold'
                        }}
                    }},
                    legend: {{
                        position: 'top',
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Sessions'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        
        return html
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Generate daily traffic breakdown for a property')
    parser.add_argument('--property', type=str, help='Property reference (e.g., STH250129)')
    parser.add_argument('--list', action='store_true', help='List all available properties')
    
    args = parser.parse_args()
    
    if args.list:
        print("="*80)
        print("📋 AVAILABLE PROPERTIES")
        print("="*80)
        properties = get_property_list()
        for prop in properties:
            name = prop['house_name'] or prop['reference']
            price = f"£{prop['price']:,.0f}" if prop['price'] else "N/A"
            print(f"  {prop['reference']:<15} {name:<40} {price}")
        print(f"\n✅ Total: {len(properties)} active properties")
        return
    
    if not args.property:
        print("❌ Error: Please specify a property reference with --property")
        print("   Use --list to see available properties")
        return
    
    print("="*80)
    print(f"📊 DAILY TRAFFIC BREAKDOWN - {args.property}")
    print("="*80)
    
    print(f"\n📝 Generating HTML report...")
    
    html = generate_daily_traffic_html(args.property)
    
    if not html:
        print(f"❌ No data found for property {args.property}")
        print("   Make sure the property exists and has traffic data")
        print("   Run: ddev exec python3 scripts/populate_traffic_database.py --days 1")
        return
    
    # Save to reports directory
    filename = f"daily_traffic_{args.property}_{datetime.now().strftime('%Y%m%d')}.html"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    with open(filepath, 'w') as f:
        f.write(html)
    
    print(f"✅ Report generated successfully!")
    print(f"   📄 File: {filepath}")
    print(f"\n💡 Open in browser: file://{filepath}")
    print(f"   Or run: xdg-open {filepath}")


if __name__ == "__main__":
    main()
