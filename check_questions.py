import mysql.connector
import os

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Vishwanath1604@',
        database='digidara_lms'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT id, question_text, option_a, option_b, option_c, option_d, correct_option FROM questions LIMIT 5')
    result = cursor.fetchall()
    print('Sample questions:')
    for row in result:
        print("ID:", row[0])
        print("Question:", row[1])
        print("A:", row[2])
        print("B:", row[3])
        print("C:", row[4])
        print("D:", row[5])
        print("Correct:", row[6])
        print("---")
    conn.close()
except Exception as e:
    print(f"Error: {e}")