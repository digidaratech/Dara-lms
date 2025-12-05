#!/usr/bin/env python3
"""
Test script to verify session flow between login and dashboard
"""
import sys
import os
import requests
from werkzeug.security import generate_password_hash

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import mysql.connector as mysql_connector
from config import Config

def test_database_connection():
    """Test database connection"""
    try:
        connection = mysql_connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset='utf8mb4'
        )
        print("✅ Database connection successful")
        return connection
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def create_test_user():
    """Create a test user"""
    try:
        connection = test_database_connection()
        if not connection:
            return False
            
        cur = connection.cursor()
        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE email = %s", ("sessiontest@example.com",))
        if cur.fetchone():
            print("✅ Test user already exists, deleting...")
            cur.execute("DELETE FROM user_sessions WHERE user_id IN (SELECT id FROM users WHERE email = %s)", ("sessiontest@example.com",))
            cur.execute("DELETE FROM users WHERE email = %s", ("sessiontest@example.com",))
            connection.commit()
            
        # Create test user
        password_hash = generate_password_hash("sessiontest123")
        cur.execute(
            "INSERT INTO users (name, email, mobile, password_hash) VALUES (%s, %s, %s, %s)",
            ("Session Test User", "sessiontest@example.com", "1234567891", password_hash)
        )
        connection.commit()
        user_id = cur.lastrowid
        cur.close()
        connection.close()
        
        print(f"✅ Test user created with ID: {user_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False

def test_login_flow():
    """Test the complete login flow"""
    print("Testing login flow...")
    
    # First, create a test user
    if not create_test_user():
        return False
    
    print("✅ Test user created successfully")
    return True

if __name__ == "__main__":
    print("=== Session Flow Test Script ===")
    
    success = test_login_flow()
    
    if success:
        print("\n🎉 Session flow test setup completed!")
        print("   To test the full login flow, you would need to:")
        print("   1. Start the Flask application")
        print("   2. Navigate to http://localhost:5000/login")
        print("   3. Login with email: sessiontest@example.com and password: sessiontest123")
        print("   4. Check if you're redirected to the dashboard")
    else:
        print("\n💥 Session flow test setup failed.")