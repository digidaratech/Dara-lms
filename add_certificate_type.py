import mysql.connector as mysql

try:
    # Connect to the database
    conn = mysql.connect(
        host='localhost',
        user='root',
        password='Vishwanath1604@',
        database='digidara_lms'
    )
    
    cur = conn.cursor()
    
    # Add certificate_type column to certificates table
    cur.execute("ALTER TABLE certificates ADD COLUMN certificate_type ENUM('course', 'exam') DEFAULT 'course'")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('Added certificate_type column to certificates table')
    
except Exception as e:
    print(f"Error: {e}")