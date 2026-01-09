#!/usr/bin/env python3
"""
Migrate property data from SQLite database to MariaDB

This script reads all properties from the SQLite database and inserts them
into the MariaDB google-stats database running in DDEV.
"""

import sqlite3
import os
import sys
from datetime import datetime
import mysql.connector
from mysql.connector import Error

# SQLite database path
SQLITE_DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'properties.db')

# MariaDB connection parameters
MARIADB_CONFIG = {
    'host': 'db',  # DDEV db container hostname
    'user': 'db',
    'password': 'db',
    'database': 'google-stats',
    'port': 3306
}

def migrate_properties():
    """Migrate properties from SQLite to MariaDB"""
    
    print("🔄 Starting SQLite to MariaDB migration...")
    print(f"📁 SQLite DB: {SQLITE_DB}")
    print(f"🗄️  MariaDB: {MARIADB_CONFIG['host']}:{MARIADB_CONFIG['port']}/{MARIADB_CONFIG['database']}")
    print("=" * 60)
    
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Fetch all properties from SQLite
        sqlite_cursor.execute('SELECT * FROM properties')
        columns = [description[0] for description in sqlite_cursor.description]
        properties = sqlite_cursor.fetchall()
        
        print(f"📊 Found {len(properties)} properties in SQLite database")
        
        if not properties:
            print("⚠️  No properties to migrate")
            sqlite_conn.close()
            return True
        
        # Connect to MariaDB
        mariadb_conn = mysql.connector.connect(**MARIADB_CONFIG)
        mariadb_cursor = mariadb_conn.cursor()
        
        # Build INSERT statement
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join([f'`{col}`' for col in columns])
        insert_query = f'INSERT INTO properties ({column_names}) VALUES ({placeholders})'
        
        # Insert properties
        inserted = 0
        skipped = 0
        
        for prop in properties:
            try:
                mariadb_cursor.execute(insert_query, prop)
                inserted += 1
            except Error as e:
                if 'Duplicate entry' in str(e):
                    skipped += 1
                else:
                    print(f"❌ Error inserting property: {e}")
                    skipped += 1
        
        mariadb_conn.commit()
        
        print(f"\n✅ Migration completed:")
        print(f"   ✔️  Inserted: {inserted} properties")
        print(f"   ⏭️  Skipped: {skipped} properties (duplicates)")
        print(f"   📊 Total: {len(properties)} properties processed")
        
        # Verify
        mariadb_cursor.execute('SELECT COUNT(*) FROM properties')
        total = mariadb_cursor.fetchone()[0]
        print(f"\n🔍 Verification: MariaDB now contains {total} properties")
        
        mariadb_cursor.close()
        mariadb_conn.close()
        sqlite_conn.close()
        
        return True
        
    except Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = migrate_properties()
    sys.exit(0 if success else 1)
