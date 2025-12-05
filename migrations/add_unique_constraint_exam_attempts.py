import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_unique_constraint():
    connection = None
    cursor = None
    
    try:
        # Database connection
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'Vishwanath1604@'),
            database=os.getenv('MYSQL_DB', 'digidara_lms')
        )
        
        cursor = connection.cursor()
        
        # Add unique constraint to prevent duplicate exam attempts for the same user, course, and attempt number within a short time window
        # First, we need to clean up any existing duplicates
        cursor.execute("""
            DELETE t1 FROM user_exam_attempts t1
            INNER JOIN user_exam_attempts t2
            WHERE t1.id > t2.id 
            AND t1.user_id = t2.user_id 
            AND t1.course_id = t2.course_id 
            AND t1.attempt_number = t2.attempt_number
            AND t1.status = t2.status
            AND t1.status = 'failed_due_to_tab_switch'
            AND ABS(TIMESTAMPDIFF(SECOND, t1.exam_date, t2.exam_date)) <= 30
        """)
        
        # Add a comment column to track the source of the record (optional)
        try:
            cursor.execute("""
                ALTER TABLE user_exam_attempts 
                ADD COLUMN source_info VARCHAR(100) DEFAULT NULL
            """)
        except mysql.connector.Error as e:
            if "Duplicate column name" not in str(e):
                raise e
            print("Source info column already exists")
        
        connection.commit()
        print("Successfully cleaned up duplicates and prepared for unique constraint")
        
    except mysql.connector.Error as error:
        print(f"Error in migration: {error}")
        
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    add_unique_constraint()