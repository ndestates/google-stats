#!/usr/bin/env python3
"""
Sync Property Feed with Database
Compares feed with database, marks inactive properties, adds new ones

DDEV Usage:
    ddev exec python3 scripts/sync_property_feed.py
    
    # Dry run (show what would change without modifying database)
    ddev exec python3 scripts/sync_property_feed.py --dry-run

Features:
    - Fetches from https://api.ndestates.com/feeds/ndefeed.xml
    - Marks properties not in feed as inactive
    - Adds new properties from feed
    - Updates existing property details
    - Shows summary of changes
"""

import os
import sys
import argparse
import urllib.request
import xml.etree.ElementTree as ET
import mysql.connector
from mysql.connector import Error
from datetime import datetime

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


def fetch_feed_properties():
    """Fetch properties from XML feed."""
    feed_url = "https://api.ndestates.com/feeds/ndefeed.xml"
    
    print(f"📥 Fetching property feed from {feed_url}...")
    
    try:
        with urllib.request.urlopen(feed_url, timeout=30) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        properties = []
        
        # Parse XML structure - adjust based on actual feed structure
        for listing in root.findall('.//property'):
            reference = listing.find('reference')
            name = listing.find('houseName')  # Feed uses 'houseName' field
            url = listing.find('url')
            price = listing.find('price')
            status = listing.find('status')
            bedrooms = listing.find('bedrooms')
            property_type = listing.find('type')
            
            if reference is not None:
                properties.append({
                    'reference': reference.text.strip() if reference.text else None,
                    'house_name': name.text.strip() if name is not None and name.text else '',
                    'url': url.text.strip() if url is not None and url.text else '',
                    'price': int(price.text) if price is not None and price.text and price.text.isdigit() else None,
                    'status': status.text.strip() if status is not None and status.text else 'available',
                    'bedrooms': int(bedrooms.text) if bedrooms is not None and bedrooms.text and bedrooms.text.isdigit() else None,
                    'property_type': property_type.text.strip() if property_type is not None and property_type.text else None
                })
        
        print(f"✅ Found {len(properties)} properties in feed")
        return properties
        
    except urllib.error.URLError as e:
        print(f"❌ Error fetching feed: {e}")
        print(f"   URL: {feed_url}")
        return None
    except ET.ParseError as e:
        print(f"❌ Error parsing XML feed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def get_database_properties():
    """Get all properties from database."""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT reference, house_name, url, price, bedrooms, property_type, is_active
            FROM properties
        """)
        
        properties = {}
        for row in cursor.fetchall():
            properties[row['reference']] = row
        
        cursor.close()
        connection.close()
        
        print(f"📊 Found {len(properties)} properties in database")
        return properties
        
    except Error as e:
        print(f"❌ Database error: {e}")
        if connection.is_connected():
            connection.close()
        return None


def sync_properties(feed_properties, db_properties, dry_run=False):
    """Sync feed properties with database."""
    
    if feed_properties is None or db_properties is None:
        print("❌ Cannot sync - missing data")
        return False
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Track changes
        added = []
        updated = []
        marked_inactive = []
        reactivated = []
        
        # Get feed references
        feed_refs = {prop['reference'] for prop in feed_properties if prop['reference']}
        db_refs = set(db_properties.keys())
        
        # Mark properties not in feed as inactive
        inactive_refs = db_refs - feed_refs
        for ref in inactive_refs:
            if db_properties[ref]['is_active']:
                marked_inactive.append(ref)
                if not dry_run:
                    cursor.execute("""
                        UPDATE properties 
                        SET is_active = 0, last_updated = CURRENT_TIMESTAMP
                        WHERE reference = %s
                    """, (ref,))
        
        # Add or update properties from feed
        for prop in feed_properties:
            ref = prop['reference']
            if not ref:
                continue
            
            if ref in db_properties:
                # Check if needs reactivation or update
                db_prop = db_properties[ref]
                
                needs_update = False
                if not db_prop['is_active']:
                    reactivated.append(ref)
                    needs_update = True
                elif (db_prop['house_name'] != prop['house_name'] or
                      db_prop['url'] != prop['url'] or
                      db_prop['price'] != prop['price']):
                    updated.append(ref)
                    needs_update = True
                
                if needs_update and not dry_run:
                    cursor.execute("""
                        UPDATE properties
                        SET house_name = %s, url = %s, price = %s, 
                            bedrooms = %s, property_type = %s, is_active = 1,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE reference = %s
                    """, (prop['house_name'], prop['url'], prop['price'],
                          prop['bedrooms'], prop['property_type'], ref))
            else:
                # New property
                added.append(ref)
                if not dry_run:
                    cursor.execute("""
                        INSERT INTO properties 
                        (reference, house_name, url, price, bedrooms, property_type, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, 1)
                    """, (ref, prop['house_name'], prop['url'], prop['price'],
                          prop['bedrooms'], prop['property_type']))
        
        if not dry_run:
            connection.commit()
        
        cursor.close()
        connection.close()
        
        # Print summary
        print("\n" + "="*80)
        print("📋 SYNC SUMMARY")
        print("="*80)
        
        if added:
            print(f"\n✅ Added {len(added)} new properties:")
            for ref in added[:10]:
                print(f"   + {ref}")
            if len(added) > 10:
                print(f"   ... and {len(added) - 10} more")
        
        if updated:
            print(f"\n🔄 Updated {len(updated)} properties:")
            for ref in updated[:10]:
                print(f"   ~ {ref}")
            if len(updated) > 10:
                print(f"   ... and {len(updated) - 10} more")
        
        if reactivated:
            print(f"\n🔓 Reactivated {len(reactivated)} properties:")
            for ref in reactivated[:10]:
                print(f"   ✓ {ref}")
            if len(reactivated) > 10:
                print(f"   ... and {len(reactivated) - 10} more")
        
        if marked_inactive:
            print(f"\n🔒 Marked {len(marked_inactive)} properties as inactive:")
            for ref in marked_inactive[:10]:
                print(f"   - {ref}")
            if len(marked_inactive) > 10:
                print(f"   ... and {len(marked_inactive) - 10} more")
        
        if not any([added, updated, reactivated, marked_inactive]):
            print("\n✅ No changes needed - database is in sync with feed")
        
        print("\n" + "="*80)
        
        if dry_run:
            print("\n💡 This was a DRY RUN - no changes were made to the database")
            print("   Run without --dry-run to apply these changes")
        
        return True
        
    except Error as e:
        print(f"❌ Database error during sync: {e}")
        if connection.is_connected():
            connection.rollback()
            connection.close()
        return False


def main():
    parser = argparse.ArgumentParser(description='Sync Property Feed with Database')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would change without modifying database')
    
    args = parser.parse_args()
    
    print("="*80)
    print("🔄 PROPERTY FEED SYNC")
    print("="*80)
    
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")
    
    # Fetch feed
    feed_properties = fetch_feed_properties()
    if feed_properties is None:
        print("\n❌ Failed to fetch feed - aborting sync")
        return 1
    
    # Get database properties
    db_properties = get_database_properties()
    if db_properties is None:
        print("\n❌ Failed to fetch database properties - aborting sync")
        return 1
    
    # Sync
    if sync_properties(feed_properties, db_properties, args.dry_run):
        print("\n✅ Sync completed successfully")
        return 0
    else:
        print("\n❌ Sync failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
