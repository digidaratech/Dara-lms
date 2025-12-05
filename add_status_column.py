import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    
    # Add status column to user_exam_attempts table
    print("Adding status column to user_exam_attempts table...")
    cursor.execute("ALTER TABLE user_exam_attempts ADD COLUMN status VARCHAR(50) DEFAULT NULL")
    connection.commit()
    
    print("✓ Status column added successfully!")
    
    # Verify the column was added
    cursor.execute("DESCRIBE user_exam_attempts")
    columns = cursor.fetchall()
    
    print("\nUpdated user_exam_attempts table columns:")
    for col in columns:
        col_data = [str(item) for item in col]
        print(f"  {col_data[0]} - {col_data[1]}")
    
except mysql.connector.Error as error:
    print(f"Error adding status column: {error}")
    
finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()