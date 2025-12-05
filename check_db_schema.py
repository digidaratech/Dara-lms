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
    
    # Check if status column exists in user_exam_attempts table
    cursor.execute("DESCRIBE user_exam_attempts")
    columns = cursor.fetchall()
    
    print("user_exam_attempts table columns:")
    status_column_exists = False
    for col in columns:
        # Convert to string to avoid type issues
        col_data = [str(item) for item in col]
        print(f"  {col_data[0]} - {col_data[1]}")
        if col_data[0] == 'status':
            status_column_exists = True
    
    if status_column_exists:
        print("\n✓ Status column exists in user_exam_attempts table")
    else:
        print("\n✗ Status column does NOT exist in user_exam_attempts table")
        print("You need to run the migration to add the status column")
    
except mysql.connector.Error as error:
    print(f"Error connecting to database: {error}")
    
finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()