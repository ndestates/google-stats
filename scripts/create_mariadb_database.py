#!/usr/bin/env python3
"""
Create and manage the property database in MariaDB for ND Estates.

This script creates tables in the MariaDB google-stats database to store 
property information, user access, and campaign data.
"""

import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

# MariaDB connection parameters
MARIADB_CONFIG = {
    'host': 'db',  # DDEV db container hostname
    'user': 'db',
    'password': 'db',
    'database': 'google-stats',
    'port': 3306
}

def create_database():
    """Create the MariaDB database schema"""

    try:
        conn = mysql.connector.connect(**MARIADB_CONFIG)
        cursor = conn.cursor()

        # Create properties table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id INT PRIMARY KEY AUTO_INCREMENT,
                reference VARCHAR(50) UNIQUE NOT NULL,
                url TEXT NOT NULL,
                property_name VARCHAR(255),
                house_name VARCHAR(255),
                property_type VARCHAR(50),
                price DECIMAL(15,2),
                parish VARCHAR(100),
                status VARCHAR(50),
                type VARCHAR(20),
                bedrooms INT,
                bathrooms INT,
                receptions INT,
                parking INT,
                latitude DECIMAL(10,8),
                longitude DECIMAL(11,8),
                description LONGTEXT,
                image_one TEXT,
                image_two TEXT,
                image_three TEXT,
                image_four TEXT,
                image_five TEXT,
                campaign VARCHAR(255) DEFAULT 'Jersey Property Listings',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_url (url(255)),
                INDEX idx_reference (reference),
                INDEX idx_parish (parish)
            )
        ''')

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin', 'manager', 'analyst', 'viewer') DEFAULT 'viewer',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')

        # Create user_access table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_access (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                resource_type VARCHAR(50),
                resource_id INT,
                permission VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_resource (resource_type, resource_id)
            )
        ''')

        # Create campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                status ENUM('active', 'inactive', 'archived') DEFAULT 'active',
                created_by INT,
                parish VARCHAR(100),
                property_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_status (status)
            )
        ''')

        # Cache table for external feeds (avoids unnecessary API calls)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feed_cache (
                id INT PRIMARY KEY AUTO_INCREMENT,
                feed_url VARCHAR(512) NOT NULL,
                etag VARCHAR(255),
                last_modified_header VARCHAR(255),
                payload MEDIUMTEXT,
                content_hash CHAR(64),
                content_length INT,
                status_code INT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_feed_url (feed_url(255)),
                INDEX idx_fetched_at (fetched_at)
            )
        ''')

        # Create audiences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audiences (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                source VARCHAR(50) DEFAULT 'GA4',
                external_id VARCHAR(100) UNIQUE,
                status ENUM('active', 'archived', 'deleted') DEFAULT 'active',
                membership_count INT DEFAULT 0,
                last_synced TIMESTAMP NULL DEFAULT NULL,
                archived_at TIMESTAMP NULL DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_status (status)
            )
        ''')

        # Create audience membership snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audience_membership_snapshots (
                id INT PRIMARY KEY AUTO_INCREMENT,
                audience_id INT NOT NULL,
                membership_count INT NOT NULL,
                snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                note VARCHAR(255),
                FOREIGN KEY (audience_id) REFERENCES audiences(id) ON DELETE CASCADE,
                INDEX idx_audience_id (audience_id),
                INDEX idx_snapshot_at (snapshot_at)
            )
        ''')

        conn.commit()
        print("✅ MariaDB database schema created successfully")
        print(f"📊 Database: {MARIADB_CONFIG['database']}")
        print("📋 Tables created: properties, users, user_access, campaigns, audiences, audience_membership_snapshots, feed_cache")
        
        cursor.close()
        conn.close()
        return True

    except Error as e:
        print(f"❌ MariaDB error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = create_database()
    sys.exit(0 if success else 1)
