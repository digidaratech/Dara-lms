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
    
    # Modify score column to DECIMAL(5,2) to store exact scores with 2 decimal places
    print("Modifying score column in user_exam_attempts table...")
    cursor.execute("ALTER TABLE user_exam_attempts MODIFY COLUMN score DECIMAL(5,2)")
    connection.commit()
    
    print("✓ Score column modified successfully!")
    
    # Verify the column was modified
    cursor.execute("DESCRIBE user_exam_attempts")
    columns = cursor.fetchall()
    
    print("\nUpdated user_exam_attempts table columns:")
    for col in columns:
        col_data = [str(item) for item in col]
        print(f"  {col_data[0]} - {col_data[1]}")
    
except mysql.connector.Error as error:
    print(f"Error modifying score column: {error}")
    
finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()