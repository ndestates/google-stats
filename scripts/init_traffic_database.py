#!/usr/bin/env python3
"""
Initialize Property Traffic Database
Creates tables for storing detailed traffic source/medium data per property

DDEV Usage:
    ddev exec python3 scripts/init_traffic_database.py

Creates:
    - property_traffic_detail: Stores source + medium + metrics per property per date range
"""

import os
import sys
import mysql.connector
from mysql.connector import Error

# Add parent directory to path
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


def init_traffic_tables():
    """Create property traffic detail table."""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Drop old tables if requested (careful!)
        print("📋 Creating property_traffic_detail table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_traffic_detail (
                id INT AUTO_INCREMENT PRIMARY KEY,
                reference VARCHAR(50) NOT NULL,
                house_name VARCHAR(255),
                property_url TEXT,
                report_date DATE NOT NULL,
                period_days INT NOT NULL,
                traffic_source VARCHAR(100) NOT NULL,
                traffic_medium VARCHAR(100) NOT NULL,
                sessions INT DEFAULT 0,
                pageviews INT DEFAULT 0,
                users INT DEFAULT 0,
                avg_session_duration DECIMAL(10,2) DEFAULT 0,
                bounce_rate DECIMAL(5,4) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_traffic_record (reference, report_date, period_days, traffic_source, traffic_medium),
                INDEX idx_reference (reference),
                INDEX idx_report_date (report_date),
                INDEX idx_period (period_days),
                INDEX idx_source (traffic_source),
                INDEX idx_medium (traffic_medium),
                INDEX idx_sessions (sessions DESC)
            )
        """)
        
        connection.commit()
        cursor.close()
        
        print("✅ Successfully created property_traffic_detail table")
        print("\n📊 Table Structure:")
        print("   - reference: Property reference (e.g., STH240092)")
        print("   - house_name: Property name (e.g., 'Flat 4 Melrose Apartments')")
        print("   - property_url: Full property URL")
        print("   - report_date: Date of report generation")
        print("   - period_days: Time period analyzed (7, 30, 90, etc.)")
        print("   - traffic_source: GA4 source (e.g., 'google', 'facebook.com', 'mailchimp')")
        print("   - traffic_medium: GA4 medium (e.g., 'organic', 'cpc', 'email', 'social')")
        print("   - sessions: Number of sessions from this source/medium")
        print("   - pageviews: Number of pageviews")
        print("   - users: Number of unique users")
        print("   - avg_session_duration: Average time in seconds")
        print("   - bounce_rate: Percentage (0-1)")
        
        return True
        
    except Error as e:
        print(f"❌ Error creating tables: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()


if __name__ == "__main__":
    print("=" * 80)
    print("🏗️  PROPERTY TRAFFIC DATABASE INITIALIZATION")
    print("=" * 80)
    
    if init_traffic_tables():
        print("\n✅ Database initialized successfully")
        print("\n💡 Next steps:")
        print("   1. Run: ddev exec python3 scripts/populate_traffic_database.py --days 30")
        print("   2. Run: ddev exec python3 scripts/populate_traffic_database.py --days 1  # yesterday")
        print("   3. View: ddev exec python3 scripts/view_traffic_report.py")
    else:
        print("\n❌ Database initialization failed")
        sys.exit(1)
