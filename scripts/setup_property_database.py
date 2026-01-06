#!/usr/bin/env python3
"""
Setup script for the ND Estates property database.

This script creates the database, imports the XML feed, and sets up campaign mappings.
Run this script to initialize the property database for the first time.
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

    print("🏠 ND Estates Property Database Setup")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Create the database
    if not run_script("create_property_database.py"):
        print("❌ Database creation failed. Aborting setup.")
        sys.exit(1)

    # Step 2: Import property data from XML feed
    if not run_script("import_property_feed.py"):
        print("❌ Property feed import failed. Aborting setup.")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("🎉 Property database setup completed successfully!")
    print("\n📊 Database contains current property listings with campaign mappings")
    print("🔄 Source reports will now use database-driven campaign mapping")
    print("\n💡 To update property data in the future, run:")
    print("   python3 scripts/import_property_feed.py")
    print("\n📈 Your analytics reports will now have more accurate campaign associations!")

if __name__ == "__main__":
    main()