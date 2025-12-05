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
    
    # Read the SQL migration file
    with open('migrations/certification_module.sql', 'r') as sql_file:
        sql_script = sql_file.read()
    
    # Split the script into individual statements
    statements = sql_script.split(';')
    
    # Execute each statement
    for statement in statements:
        statement = statement.strip()
        if statement:
            try:
                cur.execute(statement)
                print(f"Executed: {statement[:50]}...")
            except Exception as e:
                print(f"Error executing statement: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('Certification tables created successfully')
    
except Exception as e:
    print(f"Error: {e}")