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
    
    cursor = conn.cursor(dictionary=True)
    
    # Test random question selection for course 1
    cursor.execute("SELECT id, question_text FROM questions WHERE course_id = 1 ORDER BY RAND() LIMIT 5")
    questions = cursor.fetchall()
    print("Random questions for course 1:")
    for q in questions:
        # Handle both dictionary and tuple results
        if isinstance(q, dict):
            q_id = q.get('id', 'Unknown')
            q_text = q.get('question_text', 'Unknown')
        else:
            q_id = q[0] if len(q) > 0 else 'Unknown'
            q_text = q[1] if len(q) > 1 else 'Unknown'
        print(f"  {q_id}: {q_text[:50]}...")
    
    # Check total questions per course
    cursor.execute("SELECT course_id, COUNT(*) as count FROM questions GROUP BY course_id")
    course_counts = cursor.fetchall()
    print("\nQuestions per course:")
    for course in course_counts:
        # Handle both dictionary and tuple results
        if isinstance(course, dict):
            course_id = course.get('course_id', 'Unknown')
            count = course.get('count', 0)
        else:
            course_id = course[0] if len(course) > 0 else 'Unknown'
            count = course[1] if len(course) > 1 else 0
        print(f"  Course {course_id}: {count} questions")
    
    conn.close()
    print("\n✅ Question selection test completed successfully!")
    
except Exception as e:
    print(f"❌ Question selection test failed: {e}")
    import traceback
    traceback.print_exc()