#!/usr/bin/env python3
"""
Import property data from ND Estates XML feed into the database.

This script fetches the XML feed from https://api.ndestates.com/feeds/ndefeed.xml
and populates the properties database with current property listings.
"""

import sqlite3
import os
import xml.etree.ElementTree as ET
import requests
from datetime import datetime
import time

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'properties.db')
XML_FEED_URL = 'https://api.ndestates.com/feeds/ndefeed.xml'

def fetch_xml_feed():
    """Fetch the XML feed from ND Estates API"""
    try:
        print(f"📡 Fetching XML feed from: {XML_FEED_URL}")
        response = requests.get(XML_FEED_URL, timeout=30)
        response.raise_for_status()
        print("✅ XML feed fetched successfully")
        return response.content
    except requests.RequestException as e:
        print(f"❌ Failed to fetch XML feed: {e}")
        return None

def parse_property_element(property_elem):
    """Parse a single property element from XML"""

    def get_text(elem, tag):
        """Safely get text from XML element"""
        child = elem.find(tag)
        return child.text.strip() if child is not None and child.text else None

    def get_float(elem, tag):
        """Safely get float from XML element"""
        text = get_text(elem, tag)
        try:
            return float(text) if text else None
        except ValueError:
            return None

    def get_int(elem, tag):
        """Safely get int from XML element"""
        text = get_text(elem, tag)
        try:
            return int(text) if text else None
        except ValueError:
            return None

    try:
        property_data = {
            'reference': get_text(property_elem, 'reference'),
            'url': get_text(property_elem, 'url'),
            'property_name': get_text(property_elem, 'propertyname'),
            'house_name': get_text(property_elem, 'housename'),
            'property_type': get_text(property_elem, 'propertytype'),
            'price': get_float(property_elem, 'price'),
            'parish': get_text(property_elem, 'parish'),
            'status': get_text(property_elem, 'status'),
            'type': get_text(property_elem, 'type'),  # buy/rent
            'bedrooms': get_int(property_elem, 'bedrooms'),
            'bathrooms': get_int(property_elem, 'bathrooms'),
            'receptions': get_int(property_elem, 'receptions'),
            'parking': get_int(property_elem, 'parking'),
            'latitude': get_float(property_elem, 'latitude'),
            'longitude': get_float(property_elem, 'longitude'),
            'description': get_text(property_elem, 'description'),
            'image_one': get_text(property_elem, 'image_one'),
            'image_two': get_text(property_elem, 'image_two'),
            'image_three': get_text(property_elem, 'image_three'),
            'image_four': get_text(property_elem, 'image_four'),
            'image_five': get_text(property_elem, 'image_five'),
        }

        # Validate required fields
        if not property_data['reference'] or not property_data['url']:
            print(f"⚠️  Skipping property with missing reference or URL: {property_data.get('reference', 'Unknown')}")
            return None

        return property_data

    except Exception as e:
        print(f"❌ Error parsing property element: {e}")
        return None

def import_properties_to_db(xml_content):
    """Import properties from XML content to database"""

    if not os.path.exists(DB_PATH):
        print("❌ Database does not exist. Run create_property_database.py first.")
        return 0

    try:
        # Parse XML
        root = ET.fromstring(xml_content)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        imported_count = 0
        updated_count = 0
        skipped_count = 0

        for property_elem in root.findall('property'):
            property_data = parse_property_element(property_elem)

            if not property_data:
                skipped_count += 1
                continue

            # Check if property already exists
            cursor.execute('SELECT id FROM properties WHERE reference = ?', (property_data['reference'],))
            existing = cursor.fetchone()

            if existing:
                # Update existing property
                cursor.execute('''
                    UPDATE properties SET
                        url = ?, property_name = ?, house_name = ?, property_type = ?,
                        price = ?, parish = ?, status = ?, type = ?, bedrooms = ?,
                        bathrooms = ?, receptions = ?, parking = ?, latitude = ?,
                        longitude = ?, description = ?, image_one = ?, image_two = ?,
                        image_three = ?, image_four = ?, image_five = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE reference = ?
                ''', (
                    property_data['url'], property_data['property_name'], property_data['house_name'],
                    property_data['property_type'], property_data['price'], property_data['parish'],
                    property_data['status'], property_data['type'], property_data['bedrooms'],
                    property_data['bathrooms'], property_data['receptions'], property_data['parking'],
                    property_data['latitude'], property_data['longitude'], property_data['description'],
                    property_data['image_one'], property_data['image_two'], property_data['image_three'],
                    property_data['image_four'], property_data['image_five'],
                    property_data['reference']
                ))
                updated_count += 1
            else:
                # Insert new property
                cursor.execute('''
                    INSERT INTO properties (
                        reference, url, property_name, house_name, property_type,
                        price, parish, status, type, bedrooms, bathrooms, receptions,
                        parking, latitude, longitude, description, image_one, image_two,
                        image_three, image_four, image_five
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    property_data['reference'], property_data['url'], property_data['property_name'],
                    property_data['house_name'], property_data['property_type'], property_data['price'],
                    property_data['parish'], property_data['status'], property_data['type'],
                    property_data['bedrooms'], property_data['bathrooms'], property_data['receptions'],
                    property_data['parking'], property_data['latitude'], property_data['longitude'],
                    property_data['description'], property_data['image_one'], property_data['image_two'],
                    property_data['image_three'], property_data['image_four'], property_data['image_five']
                ))
                imported_count += 1

        conn.commit()
        conn.close()

        print(f"✅ Import completed:")
        print(f"   📥 New properties imported: {imported_count}")
        print(f"   🔄 Existing properties updated: {updated_count}")
        print(f"   ⏭️  Properties skipped: {skipped_count}")
        print(f"   📊 Total properties processed: {imported_count + updated_count + skipped_count}")

        return imported_count + updated_count

    except ET.ParseError as e:
        print(f"❌ XML parsing error: {e}")
        return 0
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 0

def update_campaigns_after_import():
    """Update campaign assignments after importing new data"""
    from create_property_database import update_property_campaigns
    print("\n🎯 Updating campaign assignments...")
    update_property_campaigns()

def main():
    """Main function to run the import process"""

    print("🏠 ND Estates Property Feed Import")
    print("=" * 50)

    # Fetch XML feed
    xml_content = fetch_xml_feed()
    if not xml_content:
        return

    # Import to database
    imported_count = import_properties_to_db(xml_content)

    if imported_count > 0:
        # Update campaigns
        update_campaigns_after_import()

        print("\n✅ Property feed import completed successfully!")
        print(f"📊 {imported_count} properties processed")
        print("\n💡 The database now contains current property data for better campaign mapping.")
    else:
        print("\n⚠️  No properties were imported. Check the XML feed and database.")

if __name__ == "__main__":
    main()