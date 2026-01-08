#!/usr/bin/env python3
"""
Import property data from ND Estates XML feed into MariaDB

This script fetches current property data from the ND Estates XML feed
and populates the MariaDB google-stats database with campaign assignments.
"""

import mysql.connector
from mysql.connector import Error
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import hashlib
import sys

# MariaDB connection parameters
MARIADB_CONFIG = {
    'host': 'db',
    'user': 'db',
    'password': 'db',
    'database': 'google-stats',
    'port': 3306
}

# ND Estates XML feed URL
XML_FEED_URL = 'https://api.ndestates.com/feeds/ndefeed.xml'
MIN_FETCH_INTERVAL_MINUTES = 30

def get_campaign_name(parish, property_type):
    """Determine campaign name based on parish and property type"""
    property_category = 'Apartments' if property_type and 'apartment' in property_type.lower() else 'Properties'
    return f"{parish} {property_category}"


def get_cached_feed(conn):
    """Fetch the most recent cached feed entry"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, etag, last_modified_header, payload, fetched_at
        FROM feed_cache
        WHERE feed_url = %s
        ORDER BY fetched_at DESC
        LIMIT 1
        """,
        (XML_FEED_URL,)
    )
    row = cursor.fetchone()
    cursor.close()
    return row


def cache_feed_response(conn, status_code, payload, etag, last_modified_header):
    """Persist feed response to cache"""
    cursor = conn.cursor()
    content_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    content_length = len(payload.encode('utf-8'))
    cursor.execute(
        """
        INSERT INTO feed_cache (feed_url, etag, last_modified_header, payload, content_hash, content_length, status_code)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (XML_FEED_URL, etag, last_modified_header, payload, content_hash, content_length, status_code)
    )
    conn.commit()
    cursor.close()


def fetch_feed_with_cache(conn, force_refresh=False):
    """Fetch feed using cache and conditional requests to avoid unnecessary API calls"""
    cached = get_cached_feed(conn)

    # Use cached payload if fetched recently and not forcing refresh
    if not force_refresh and cached and cached.get('fetched_at'):
        fetched_at = cached['fetched_at']
        if cached.get('payload') and fetched_at >= datetime.now() - timedelta(minutes=MIN_FETCH_INTERVAL_MINUTES):
            return cached['payload'], 'cache-recent'

    headers = {}
    if not force_refresh and cached and cached.get('etag'):
        headers['If-None-Match'] = cached['etag']
    if not force_refresh and cached and cached.get('last_modified_header'):
        headers['If-Modified-Since'] = cached['last_modified_header']

    response = requests.get(XML_FEED_URL, headers=headers, timeout=30)

    if not force_refresh and response.status_code == 304:
        # Not modified; use cached payload
        if not cached or not cached.get('payload'):
            raise ValueError("Received 304 but no cached payload available")
        return cached['payload'], 'cache-304'

    response.raise_for_status()
    payload = response.text
    etag = response.headers.get('ETag')
    last_modified_header = response.headers.get('Last-Modified')

    cache_feed_response(conn, response.status_code, payload, etag, last_modified_header)
    return payload, 'network'

def import_property_feed():
    """Import properties from XML feed into MariaDB"""

    print("🏠 ND Estates Property Feed Import (MariaDB)")
    print("=" * 60)
    
    try:
        # Connect to MariaDB first (needed for cache)
        conn = mysql.connector.connect(**MARIADB_CONFIG)
        cursor = conn.cursor()

        # Check if properties table is empty
        cursor.execute('SELECT COUNT(*) FROM properties')
        property_count = cursor.fetchone()[0]
        force_refresh = property_count == 0
        
        if force_refresh:
            print("ℹ️ Properties table is empty. Forcing a fresh feed download.")

        # Fetch XML feed with cache support
        print(f"📡 Fetching XML feed from: {XML_FEED_URL}")
        payload, source = fetch_feed_with_cache(conn, force_refresh=force_refresh)
        print(f"✅ Feed ready via: {source}")

        # Parse XML
        root = ET.fromstring(payload)

        # The root element is <xml>, and properties are direct children
        properties_found = root.findall('property')
        print(f"🔍 Found {len(properties_found)} properties in the XML feed.")

        properties_imported = 0
        properties_updated = 0
        properties_skipped = 0

        # Process each property
        for prop_elem in properties_found:
            try:
                # Extract data
                reference = prop_elem.find('reference').text if prop_elem.find('reference') is not None else ''
                url = prop_elem.find('url').text if prop_elem.find('url') is not None else ''
                property_name = prop_elem.find('propertyname').text if prop_elem.find('propertyname') is not None else ''
                house_name = prop_elem.find('houseName').text if prop_elem.find('houseName') is not None else ''
                property_type = prop_elem.find('propertytype').text if prop_elem.find('propertytype') is not None else ''
                
                price_elem = prop_elem.find('price')
                price = float(price_elem.text) if price_elem is not None and price_elem.text else 0
                
                parish = prop_elem.find('parish').text if prop_elem.find('parish') is not None else 'Jersey'
                status = prop_elem.find('status').text if prop_elem.find('status') is not None else 'Available'
                type_sale = prop_elem.find('type').text if prop_elem.find('type') is not None else 'buy'
                
                bedrooms = int(prop_elem.find('bedrooms').text or 0) if prop_elem.find('bedrooms') is not None else 0
                bathrooms = int(prop_elem.find('bathrooms').text or 0) if prop_elem.find('bathrooms') is not None else 0
                receptions = int(prop_elem.find('receptions').text or 0) if prop_elem.find('receptions') is not None else 0
                parking = int(prop_elem.find('parking').text or 0) if prop_elem.find('parking') is not None else 0
                
                latitude = float(prop_elem.find('latitude').text or 0) if prop_elem.find('latitude') is not None else 0
                longitude = float(prop_elem.find('longitude').text or 0) if prop_elem.find('longitude') is not None else 0
                
                description = prop_elem.find('description').text if prop_elem.find('description') is not None else ''
                
                image_one = prop_elem.find('image_one').text if prop_elem.find('image_one') is not None else ''
                image_two = prop_elem.find('image_two').text if prop_elem.find('image_two') is not None else ''
                image_three = prop_elem.find('image_three').text if prop_elem.find('image_three') is not None else ''
                image_four = prop_elem.find('image_four').text if prop_elem.find('image_four') is not None else ''
                image_five = prop_elem.find('image_five').text if prop_elem.find('image_five') is not None else ''
                
                campaign = get_campaign_name(parish, property_type)

                # Insert or update property
                cursor.execute('''
                    INSERT INTO properties 
                    (reference, url, property_name, house_name, property_type, price, parish, 
                     status, type, bedrooms, bathrooms, receptions, parking, latitude, longitude, 
                     description, image_one, image_two, image_three, image_four, image_five, campaign)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    url = VALUES(url), property_name = VALUES(property_name), house_name = VALUES(house_name),
                    property_type = VALUES(property_type), price = VALUES(price), status = VALUES(status),
                    bedrooms = VALUES(bedrooms), bathrooms = VALUES(bathrooms), receptions = VALUES(receptions),
                    parking = VALUES(parking), latitude = VALUES(latitude), longitude = VALUES(longitude),
                    description = VALUES(description), image_one = VALUES(image_one), image_two = VALUES(image_two),
                    image_three = VALUES(image_three), image_four = VALUES(image_four), image_five = VALUES(image_five),
                    campaign = VALUES(campaign), last_updated = CURRENT_TIMESTAMP
                ''', (reference, url, property_name, house_name, property_type, price, parish,
                      status, type_sale, bedrooms, bathrooms, receptions, parking, latitude, longitude,
                      description, image_one, image_two, image_three, image_four, image_five, campaign))
                
                if cursor.rowcount == 1:
                    properties_imported += 1
                elif cursor.rowcount == 2:
                    properties_updated += 1
                else:
                    # This can happen if the data is identical and no update occurs
                    pass

            except Exception as e:
                properties_skipped += 1
                print(f"⚠️  Skipping property due to error: {e}")
                continue

        conn.commit()

        print(f"\n✅ Import completed:")
        print(f"   📥 New properties: {properties_imported}")
        print(f"   🔄 Updated properties: {properties_updated}")
        print(f"   ⏭️  Skipped: {properties_skipped}")
        print(f"   📊 Total processed: {properties_imported + properties_updated}")

        # Verify total
        cursor.execute('SELECT COUNT(*) FROM properties')
        total = cursor.fetchone()[0]
        print(f"\n🔍 MariaDB now contains {total} properties")

    except Error as e:
        print(f"❌ MariaDB Error: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch XML feed: {e}")
        sys.exit(1)
    except ET.ParseError as e:
        print(f"❌ Failed to parse XML: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    import_property_feed()
