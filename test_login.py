#!/usr/bin/env python3
"""
Simple test script to verify login functionality
"""
import sys
import os
import mysql.connector as mysql_connector
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash

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

def test_user_login(email, password):
    """Test user login directly with mysql connector"""
    try:
        connection = test_database_connection()
        if not connection:
            return False
            
        cur = connection.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        connection.close()
        
        if not user:
            print(f"❌ User with email '{email}' not found")
            return False
            
        # Handle potential tuple vs dict result
        if isinstance(user, dict):
            user_name = user.get('name', 'Unknown')
            user_email = user.get('email', 'Unknown')
            password_hash = user.get('password_hash')
        else:
            # Assuming tuple result, try to access by index
            # This is a simplified approach - in practice, we'd need to know the exact column order
            try:
                user_name = user[1] if len(user) > 1 else 'Unknown'
                user_email = user[2] if len(user) > 2 else 'Unknown'
                password_hash = user[3] if len(user) > 3 else None
            except:
                print("❌ Unable to parse user data")
                return False
            
        print(f"✅ User found: {user_name} ({user_email})")
        
        # Check password hash
        if password_hash:
            if isinstance(password_hash, str):
                if check_password_hash(password_hash, password):
                    print("✅ Password verification successful")
                    return True
                else:
                    print("❌ Password verification failed")
                    return False
            else:
                print("❌ Password hash is not a string")
                return False
        else:
            print("❌ No password_hash field found in user record")
            return False
            
    except Exception as e:
        print(f"❌ Error during login test: {e}")
        return False

def create_test_user():
    """Create a test user"""
    try:
        connection = test_database_connection()
        if not connection:
            return False
            
        cur = connection.cursor()
        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE email = %s", ("test@example.com",))
        if cur.fetchone():
            print("✅ Test user already exists")
            cur.close()
            connection.close()
            return True
            
        # Create test user
        password_hash = generate_password_hash("testpassword123")
        cur.execute(
            "INSERT INTO users (name, email, mobile, password_hash) VALUES (%s, %s, %s, %s)",
            ("Test User", "test@example.com", "1234567890", password_hash)
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

if __name__ == "__main__":
    print("=== Login Test Script ===")
    
    # Test database connection
    print("\n1. Testing database connection...")
    connection = test_database_connection()
    if not connection:
        sys.exit(1)
    connection.close()
    
    # Create test user
    print("\n2. Creating test user...")
    if not create_test_user():
        sys.exit(1)
    
    # Test login
    print("\n3. Testing login...")
    success = test_user_login("test@example.com", "testpassword123")
    
    if success:
        print("\n🎉 All tests passed! Login functionality is working.")
    else:
        print("\n💥 Login test failed. There may be an issue with the login functionality.")