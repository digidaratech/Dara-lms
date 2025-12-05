#!/usr/bin/env python3
"""
Setup script to create essential tables for the LMS
"""

import mysql.connector as mysql_connector
from config import Config

def setup_essential_tables():
    print("Setting up essential LMS tables...")
    
    try:
        # Connect to MySQL server and select database
        print("1. Connecting to database...")
        conn = mysql_connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset='utf8mb4'
        )
        print("✅ Connected to database!")
        
        cursor = conn.cursor()
        
        # Create essential tables
        print("2. Creating essential tables...")
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                mobile VARCHAR(20),
                password_hash VARCHAR(255) NOT NULL,
                failed_login_attempts INT DEFAULT 0,
                account_locked_until TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("✅ Users table created!")
        
        # Password reset OTP table
        cursor.execute("""
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
        print("✅ Password reset OTP table created!")
        
        # User sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        print("✅ User sessions table created!")
        
        # Courses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                requirements TEXT,
                outcomes TEXT,
                instructor VARCHAR(100),
                category VARCHAR(50) DEFAULT 'programming',
                level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
                duration VARCHAR(50),
                status ENUM('active', 'draft', 'archived') DEFAULT 'active',
                price DECIMAL(10,2) DEFAULT 0.00,
                image_url VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("✅ Courses table created!")
        
        # Course modules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_modules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_id INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                video_url VARCHAR(255),
                thumbnail_url VARCHAR(255),
                duration VARCHAR(50),
                order_index INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            )
        """)
        print("✅ Course modules table created!")
        
        # User course enrollments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_course (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                course_id INT NOT NULL,
                login_id VARCHAR(100),
                course_password VARCHAR(100),
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                progress DECIMAL(5,2) DEFAULT 0.00,
                completed_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE KEY unique_enrollment (user_id, course_id)
            )
        """)
        print("✅ User course enrollments table created!")
        
        # User module progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_module_progress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                course_id INT NOT NULL,
                module_id INT NOT NULL,
                watched_duration INT DEFAULT 0,
                total_duration INT DEFAULT 0,
                is_completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP NULL,
                last_watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (module_id) REFERENCES course_modules(id) ON DELETE CASCADE,
                UNIQUE KEY unique_progress (user_id, course_id, module_id)
            )
        """)
        print("✅ User module progress table created!")
        
        # User watch time tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_watch_time (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                course_id INT NOT NULL,
                module_id INT NOT NULL,
                watch_date DATE NOT NULL,
                watch_duration INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (module_id) REFERENCES course_modules(id) ON DELETE CASCADE
            )
        """)
        print("✅ User watch time tracking table created!")
        
        # Commit changes
        conn.commit()
        
        # Verify tables were created
        print("3. Verifying tables...")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            table_name = table[0] if isinstance(table, tuple) else str(table)
            print(f"  - {table_name}")
            
        cursor.close()
        conn.close()
        print("\n🎉 Essential tables setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    setup_essential_tables()