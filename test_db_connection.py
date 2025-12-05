#!/usr/bin/env python3
"""
Test script to verify database connection for the LMS
"""

import mysql.connector as mysql_connector
from config import Config

def test_database_connection():
    print("Testing database connection...")
    print(f"Host: {Config.MYSQL_HOST}")
    print(f"User: {Config.MYSQL_USER}")
    print(f"Database: {Config.MYSQL_DB}")
    
    try:
        # Test connection without specifying database first
        print("\n1. Testing connection to MySQL server...")
        conn = mysql_connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        print("MySQL server connection successful!")
        conn.close()
        
        # Test connection with database
        print("\n2. Testing connection to specific database...")
        conn = mysql_connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset='utf8mb4'
        )
        print("Database connection successful!")
        
        
        # Test if tables exist
        print("\n3. Checking if required tables exist...")
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        cursor.close()
        conn.close()
        
        print("\nAll tests passed! Database is ready for use.")
        return True
        
    except mysql_connector.Error as e:
        print(f"Database connection failed: {e}")
        if e.errno == 1045:
            print("   This usually means the username or password is incorrect.")
        elif e.errno == 1049:
            print("   This usually means the database doesn't exist.")
        elif e.errno == 2003:
            print("   This usually means MySQL server is not running.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()