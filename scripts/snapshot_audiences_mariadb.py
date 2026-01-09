#!/usr/bin/env python3
"""
Snapshot audience membership counts into MariaDB for historical tracking.
Run via: ddev exec python3 scripts/snapshot_audiences_mariadb.py
"""

import sys
import mysql.connector
from mysql.connector import Error
from datetime import datetime

MARIADB_CONFIG = {
    'host': 'db',
    'user': 'db',
    'password': 'db',
    'database': 'google-stats',
    'port': 3306
}


def snapshot_all():
    try:
        conn = mysql.connector.connect(**MARIADB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO audience_membership_snapshots (audience_id, membership_count, note)
            SELECT id, membership_count, 'scheduled snapshot'
            FROM audiences
            WHERE status IN ('active','archived')
            """
        )
        inserted = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Snapshot completed at {datetime.now().isoformat()} | rows inserted: {inserted}")
        return True
    except Error as e:
        print(f"❌ MariaDB error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = snapshot_all()
    sys.exit(0 if success else 1)
