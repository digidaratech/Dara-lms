import mysql.connector
from config import Config

try:
    # Connect to database
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )
    
    cursor = conn.cursor()
    
    # Check certificates table structure
    cursor.execute("DESCRIBE certificates")
    columns = cursor.fetchall()
    print("Certificates table structure:")
    for column in columns:
        col_name = column[0] if len(column) > 0 else ""
        col_type = column[1] if len(column) > 1 else ""
        col_null = column[2] if len(column) > 2 else ""
        col_key = column[3] if len(column) > 3 else ""
        col_default = column[4] if len(column) > 4 else ""
        col_extra = column[5] if len(column) > 5 else ""
        print(f"  {col_name}: {col_type} {col_null} {col_key} {col_default} {col_extra}")
    
    # Check if certificate_type column exists
    certificate_type_exists = any((column[0] if len(column) > 0 else "") == 'certificate_type' for column in columns)
    print(f"\nCertificate type column exists: {certificate_type_exists}")
    
    # Check indexes
    cursor.execute("SHOW INDEX FROM certificates")
    indexes = cursor.fetchall()
    print("\nCertificates table indexes:")
    for index in indexes:
        index_name = index[2] if len(index) > 2 else ""
        column_name = index[4] if len(index) > 4 else ""
        print(f"  {index_name}: {column_name}")
    
    conn.close()
    print("\n✅ Database test completed successfully!")
    
except Exception as e:
    print(f"❌ Database test failed: {e}")