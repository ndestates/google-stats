#!/usr/bin/env python3
"""
Setup script for the ND Estates MariaDB database.

This script creates the database schema and imports property data into MariaDB.
Run this script to initialize the property database in DDEV.
"""

import os
import sys
from datetime import datetime

def run_script(script_name):
    """Run a Python script and return success status"""
    script_path = os.path.join(os.path.dirname(__file__), script_name)

    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return False

    print(f"\n🔧 Running {script_name}...")
    result = os.system(f"cd {os.path.dirname(__file__)} && python3 {script_name}")

    if result == 0:
        print(f"✅ {script_name} completed successfully")
        return True
    else:
        print(f"❌ {script_name} failed with exit code {result}")
        return False

def main():
    """Main setup function"""

    print("🏠 ND Estates MariaDB Setup")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Database: google-stats (MariaDB in DDEV)")

    # Step 1: Create the database schema
    if not run_script("create_mariadb_database.py"):
        print("❌ Database creation failed. Aborting setup.")
        sys.exit(1)

    # Step 2: Import property data from XML feed
    if not run_script("import_property_feed_mariadb.py"):
        print("❌ Property feed import failed. Aborting setup.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🎉 MariaDB setup completed successfully!")
    print("\n📊 Database contains current property listings with campaign mappings")
    print("🔄 Reports will now use MariaDB-driven data storage")
    print("\n💡 To update property data in the future, run:")
    print("   ddev exec python3 scripts/import_property_feed_mariadb.py")
    print("\n📈 Your analytics reports will now have accurate database-backed campaign associations!")

if __name__ == "__main__":
    main()
