import mysql.connector
import os

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='Dhanush@12',
        database='digidara_lms'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT title, category, level FROM courses ORDER BY id DESC LIMIT 10')
    results = cursor.fetchall()
    print('Latest courses:')
    for r in results:
        print(f'  {r[0]} - {r[1]} - {r[2]}')
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")