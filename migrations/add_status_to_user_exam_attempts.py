import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_status_column():
    connection = None
    cursor = None
    
    try:
        # Database connection
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DB', 'lms_db')
        )
        
        cursor = connection.cursor()
        
        # Add status column to user_exam_attempts table
        cursor.execute("""
            ALTER TABLE user_exam_attempts 
            ADD COLUMN status VARCHAR(50) DEFAULT NULL
        """)
        
        connection.commit()
        print("Successfully added status column to user_exam_attempts table")
        
    except mysql.connector.Error as error:
        print(f"Error adding status column: {error}")
        
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    add_status_column()