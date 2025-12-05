#!/usr/bin/env python3
"""
Database Setup Script for Learning Management System
This script will create the database and tables if they don't exist.
"""

import mysql.connector as mysql_connector
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Setup database with new tables and columns for password reset functionality."""
    try:
        # Connect to MySQL
        connection = mysql_connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset='utf8mb4'
        )
        
        cur = connection.cursor()
        
        # Add new columns to users table if they don't exist
        logger.info("Adding new columns to users table...")
        
        # Check if failed_login_attempts column exists
        cur.execute("SHOW COLUMNS FROM users LIKE 'failed_login_attempts'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE users ADD COLUMN failed_login_attempts INT DEFAULT 0")
            logger.info("Added failed_login_attempts column")
        
        # Check if account_locked_until column exists
        cur.execute("SHOW COLUMNS FROM users LIKE 'account_locked_until'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE users ADD COLUMN account_locked_until TIMESTAMP NULL")
            logger.info("Added account_locked_until column")
        
        # Create password_reset_otp table if it doesn't exist
        logger.info("Creating password_reset_otp table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_otp (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                email VARCHAR(100) NOT NULL,
                mobile VARCHAR(20) NULL,
                otp_code VARCHAR(6) NOT NULL,
                otp_type ENUM('email', 'sms') NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                is_used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        logger.info("Created password_reset_otp table")
        
        # Create indexes for better performance
        logger.info("Creating indexes...")
        
        # Indexes for users table
        try:
            cur.execute("CREATE INDEX idx_users_mobile ON users(mobile)")
            logger.info("Created idx_users_mobile index")
        except:
            logger.info("idx_users_mobile index already exists")
        
        try:
            cur.execute("CREATE INDEX idx_users_failed_login_attempts ON users(failed_login_attempts)")
            logger.info("Created idx_users_failed_login_attempts index")
        except:
            logger.info("idx_users_failed_login_attempts index already exists")
        
        try:
            cur.execute("CREATE INDEX idx_users_account_locked_until ON users(account_locked_until)")
            logger.info("Created idx_users_account_locked_until index")
        except:
            logger.info("idx_users_account_locked_until index already exists")
        
        # Indexes for password_reset_otp table
        try:
            cur.execute("CREATE INDEX idx_password_reset_otp_user_id ON password_reset_otp(user_id)")
            logger.info("Created idx_password_reset_otp_user_id index")
        except:
            logger.info("idx_password_reset_otp_user_id index already exists")
        
        try:
            cur.execute("CREATE INDEX idx_password_reset_otp_email ON password_reset_otp(email)")
            logger.info("Created idx_password_reset_otp_email index")
        except:
            logger.info("idx_password_reset_otp_email index already exists")
        
        try:
            cur.execute("CREATE INDEX idx_password_reset_otp_mobile ON password_reset_otp(mobile)")
            logger.info("Created idx_password_reset_otp_mobile index")
        except:
            logger.info("idx_password_reset_otp_mobile index already exists")
        
        try:
            cur.execute("CREATE INDEX idx_password_reset_otp_otp_code ON password_reset_otp(otp_code)")
            logger.info("Created idx_password_reset_otp_otp_code index")
        except:
            logger.info("idx_password_reset_otp_otp_code index already exists")
        
        try:
            cur.execute("CREATE INDEX idx_password_reset_otp_expires_at ON password_reset_otp(expires_at)")
            logger.info("Created idx_password_reset_otp_expires_at index")
        except:
            logger.info("idx_password_reset_otp_expires_at index already exists")
        
        try:
            cur.execute("CREATE INDEX idx_password_reset_otp_is_used ON password_reset_otp(is_used)")
            logger.info("Created idx_password_reset_otp_is_used index")
        except:
            logger.info("idx_password_reset_otp_is_used index already exists")
        
        connection.commit()
        cur.close()
        connection.close()
        
        logger.info("✅ Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

if __name__ == "__main__":
    setup_database() 