#!/usr/bin/env python3
"""
Create and manage the property database for ND Estates XML feed data.

This script creates a SQLite database to store property information from the XML feed,
enabling better URL-to-campaign mapping for analytics reports.
"""

import sqlite3
import os
from datetime import datetime

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'properties.db')

def create_database():
    """Create the properties database and table"""

    # Ensure data directory exists
    data_dir = os.path.dirname(DB_PATH)
    os.makedirs(data_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create properties table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT UNIQUE NOT NULL,
            url TEXT NOT NULL,
            property_name TEXT,
            house_name TEXT,
            property_type TEXT,
            price REAL,
            parish TEXT,
            status TEXT,
            type TEXT,  -- buy/rent
            bedrooms INTEGER,
            bathrooms INTEGER,
            receptions INTEGER,
            parking INTEGER,
            latitude REAL,
            longitude REAL,
            description TEXT,
            image_one TEXT,
            image_two TEXT,
            image_three TEXT,
            image_four TEXT,
            image_five TEXT,
            campaign TEXT DEFAULT 'Jersey Property Listings',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create index on URL for fast lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_properties_url ON properties(url)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_properties_reference ON properties(reference)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_properties_parish ON properties(parish)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_properties_type ON properties(type)')

    conn.commit()
    conn.close()

    print(f"✅ Database created successfully at: {DB_PATH}")

def get_property_campaign(url_path, parish=None, property_type=None):
    """Determine campaign based on property attributes"""

    # Default campaign
    campaign = "Jersey Property Listings"

    # Special campaigns based on location or type
    if parish:
        if parish.lower() in ['st helier', 'st. helier']:
            campaign = "St Helier Properties"
        elif parish.lower() in ['st clement', 'st. clement']:
            campaign = "St Clement Properties"
        elif parish.lower() in ['st lawrence', 'st. lawrence']:
            campaign = "St Lawrence Properties"
        elif parish.lower() in ['st peter', 'st. peter']:
            campaign = "St Peter Properties"
        elif parish.lower() in ['st martin', 'st. martin']:
            campaign = "St Martin Properties"
        elif parish.lower() in ['st ouen', 'st. ouen']:
            campaign = "St Ouen Properties"
        elif parish.lower() in ['st saviour', 'st. saviour']:
            campaign = "St Saviour Properties"
        elif parish.lower() in ['st john', 'st. john']:
            campaign = "St John Properties"
        elif parish.lower() in ['st brelade', 'st. brelade']:
            campaign = "St Brelade Properties"
        elif parish.lower() in ['trinity']:
            campaign = "Trinity Properties"
        elif parish.lower() in ['grouville']:
            campaign = "Grouville Properties"

    # Special campaigns for property types
    if property_type and property_type.lower() == 'apartment':
        campaign = f"{campaign.replace(' Properties', '')} Apartments"

    return campaign

def update_property_campaigns():
    """Update campaign assignments for existing properties based on their attributes"""

    if not os.path.exists(DB_PATH):
        print("❌ Database does not exist. Run create_database() first.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all properties
    cursor.execute('SELECT id, url, parish, property_type FROM properties')
    properties = cursor.fetchall()

    updated_count = 0
    for prop_id, url, parish, property_type in properties:
        new_campaign = get_property_campaign(url, parish, property_type)

        # Update if campaign changed
        cursor.execute('UPDATE properties SET campaign = ? WHERE id = ?', (new_campaign, prop_id))
        if cursor.rowcount > 0:
            updated_count += 1

    conn.commit()
    conn.close()

    print(f"✅ Updated campaigns for {updated_count} properties")

if __name__ == "__main__":
    create_database()
    print("🏠 Property database created successfully!")
    print("\nNext steps:")
    print("1. Run the XML feed import script to populate the database")
    print("2. Update campaign mappings to use the database")