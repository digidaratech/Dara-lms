import mysql.connector as mysql

try:
    # Connect to the database with correct credentials
    conn = mysql.connect(
        host='localhost',
        user='root',
        password='Vishwanath1604@',
        database='digidara_lms'
    )
    
    cur = conn.cursor()
    
    # Check if questions table exists
    cur.execute("SHOW TABLES LIKE 'questions'")
    questions_table = cur.fetchone()
    print(f"Questions table exists: {questions_table is not None}")
    
    # Check if user_exam_attempts table exists
    cur.execute("SHOW TABLES LIKE 'user_exam_attempts'")
    exam_attempts_table = cur.fetchone()
    print(f"User exam attempts table exists: {exam_attempts_table is not None}")
    
    # List all tables
    cur.execute("SHOW TABLES")
    tables = cur.fetchall()
    print("\nAll database tables:")
    for table in tables:
        table_name = table[0] if isinstance(table, tuple) else str(table)
        print(f"  - {table_name}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")