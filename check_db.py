import mysql.connector as mysql
from config import Config

# Connect to database
conn = mysql.connect(
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DB
)

cur = conn.cursor()
cur.execute("DESCRIBE certificates")
result = cur.fetchall()

print("Certificates table structure:")
for row in result:
    print(row)

cur.close()
conn.close()