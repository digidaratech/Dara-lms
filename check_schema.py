import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='lms'
    )
    cursor = conn.cursor()
    cursor.execute('DESCRIBE user_exam_attempts')
    result = cursor.fetchall()
    print('user_exam_attempts table structure:')
    for row in result:
        print(row)
    conn.close()
except Exception as e:
    print(f"Error: {e}")