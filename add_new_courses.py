import mysql.connector
import os
from config import Config

def get_db_connection():
    """Create a database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST', '127.0.0.1'),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', 'Dhanush@12'),
            database=os.environ.get('MYSQL_DB', 'digidara_lms'),
            charset='utf8mb4',
            autocommit=True
        )
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def add_new_courses():
    """Add the requested courses to the database"""
    connection = get_db_connection()
    if not connection:
        print("Failed to connect to database")
        return
    
    try:
        cursor = connection.cursor()
        
        # Add the new courses
        courses = [
            ('Python Programming', 'Master Python from basics to advanced concepts including OOP, data structures, and best practices.', 'Dr. Sarah Johnson', '12 weeks', 349.99, 'programming', 'beginner'),
            ('Machine Learning', 'Comprehensive introduction to machine learning algorithms, including supervised and unsupervised learning.', 'Prof. David Kim', '16 weeks', 599.99, 'machine-learning', 'intermediate'),
            ('Deep Learning', 'Advanced deep learning concepts with neural networks, CNNs, RNNs, and transformer models.', 'Dr. Emily Rodriguez', '18 weeks', 799.99, 'deep-learning', 'advanced'),
            ('Data Science', 'Complete data science curriculum covering statistics, data analysis, and visualization techniques.', 'Dr. Michael Chen', '14 weeks', 649.99, 'data-science', 'intermediate'),
            ('Data Analytics', 'Practical data analytics skills for business intelligence and decision making.', 'Prof. James Wilson', '10 weeks', 499.99, 'data-analytics', 'beginner'),
            ('Generative AI', 'Cutting-edge generative AI techniques including GANs, diffusion models, and prompt engineering.', 'Dr. Lisa Anderson', '15 weeks', 899.99, 'generative-ai', 'advanced'),
            ('Agentic AI', 'Advanced AI agent development with autonomous decision making and multi-agent systems.', 'Prof. Robert Taylor', '20 weeks', 999.99, 'agentic-ai', 'advanced')
        ]
        
        cursor.executemany("""
            INSERT INTO courses (title, description, instructor, duration, price, category, level) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, courses)
        
        print(f"Added {len(courses)} new courses to the database")
        
        # Add sample modules for each course
        course_ids = []
        cursor.execute("SELECT id FROM courses ORDER BY id DESC LIMIT %s", (len(courses),))
        results = cursor.fetchall()
        course_ids = [row[0] for row in results]
        
        # Sample modules for Python Programming
        python_modules = [
            (course_ids[0], 'Introduction to Python', 'Learn the basics of Python programming language', 'https://www.youtube.com/embed/kqtD5dpn9C8', None, '15:30', 1),
            (course_ids[0], 'Variables and Data Types', 'Understanding variables, strings, numbers, and data types', 'https://www.youtube.com/embed/rfscVS0vtbw', None, '20:15', 2),
            (course_ids[0], 'Control Structures', 'Learn about loops, conditionals, and program flow', 'https://www.youtube.com/embed/YYXdXT2l-Gg', None, '25:45', 3),
            (course_ids[0], 'Functions and Modules', 'Creating reusable code with functions and modules', 'https://www.youtube.com/embed/9Os0o3wzS_I', None, '30:20', 4),
            (course_ids[0], 'Object-Oriented Programming', 'Master classes, objects, inheritance, and polymorphism', 'https://www.youtube.com/embed/JeznW_7DlB0', None, '35:45', 5)
        ]
        
        # Sample modules for Machine Learning
        ml_modules = [
            (course_ids[1], 'Introduction to ML', 'Overview of machine learning concepts and types', 'https://www.youtube.com/embed/KNAWp2S3w94', None, '25:30', 1),
            (course_ids[1], 'Supervised Learning', 'Understanding supervised learning algorithms', 'https://www.youtube.com/embed/KNAWp2S3w94', None, '30:15', 2),
            (course_ids[1], 'Unsupervised Learning', 'Exploring unsupervised learning techniques', 'https://www.youtube.com/embed/KNAWp2S3w94', None, '35:45', 3),
            (course_ids[1], 'Model Evaluation', 'Evaluating and improving machine learning models', 'https://www.youtube.com/embed/KNAWp2S3w94', None, '45:20', 4),
            (course_ids[1], 'Advanced ML Techniques', 'Ensemble methods and advanced algorithms', 'https://www.youtube.com/embed/KNAWp2S3w94', None, '50:15', 5)
        ]
        
        # Sample modules for Deep Learning
        dl_modules = [
            (course_ids[2], 'Neural Networks Basics', 'Introduction to artificial neural networks', 'https://www.youtube.com/embed/aircAruvnKk', None, '30:20', 1),
            (course_ids[2], 'Convolutional Neural Networks', 'CNNs for image recognition and computer vision', 'https://www.youtube.com/embed/4nTZrt4N2Bc', None, '35:45', 2),
            (course_ids[2], 'Recurrent Neural Networks', 'RNNs for sequence data and NLP', 'https://www.youtube.com/embed/SEnXr6v2ifU', None, '40:30', 3),
            (course_ids[2], 'Transformer Models', 'Attention mechanisms and transformer architectures', 'https://www.youtube.com/embed/T0TFa6HhGYY', None, '45:15', 4),
            (course_ids[2], 'Advanced Deep Learning', 'GANs, VAEs, and cutting-edge architectures', 'https://www.youtube.com/embed/8z9kzQJdJdE', None, '50:45', 5)
        ]
        
        # Sample modules for Data Science
        ds_modules = [
            (course_ids[3], 'Statistics for Data Science', 'Fundamental statistics concepts for data analysis', 'https://www.youtube.com/embed/zzkbzx4N9a0', None, '25:30', 1),
            (course_ids[3], 'Data Analysis with Pandas', 'Working with pandas for data manipulation', 'https://www.youtube.com/embed/dcqPhpY7tWk', None, '30:15', 2),
            (course_ids[3], 'Data Visualization', 'Creating charts and graphs with matplotlib and seaborn', 'https://www.youtube.com/embed/Gpkr7RQH3kY', None, '35:45', 3),
            (course_ids[3], 'Machine Learning Integration', 'Applying ML techniques to real-world data', 'https://www.youtube.com/embed/RlQuVL6-g1Y', None, '40:20', 4),
            (course_ids[3], 'Big Data Technologies', 'Working with large datasets and distributed computing', 'https://www.youtube.com/embed/7D1CQ0enxQw', None, '45:30', 5)
        ]
        
        # Sample modules for Data Analytics
        da_modules = [
            (course_ids[4], 'Business Analytics Fundamentals', 'Introduction to business intelligence concepts', 'https://www.youtube.com/embed/5OaK4aUZ52A', None, '20:30', 1),
            (course_ids[4], 'Excel for Data Analysis', 'Advanced Excel techniques for data analysis', 'https://www.youtube.com/embed/Vl0H-qTclOg', None, '25:15', 2),
            (course_ids[4], 'SQL for Data Analysis', 'Querying databases for business insights', 'https://www.youtube.com/embed/HXV3zeQKqGY', None, '30:45', 3),
            (course_ids[4], 'Dashboard Creation', 'Building interactive dashboards with Power BI/Tableau', 'https://www.youtube.com/embed/6DQmA3D5V8c', None, '35:20', 4),
            (course_ids[4], 'Data Storytelling', 'Communicating insights effectively to stakeholders', 'https://www.youtube.com/embed/9Q3w2F9P3eI', None, '25:45', 5)
        ]
        
        # Sample modules for Generative AI
        genai_modules = [
            (course_ids[5], 'Introduction to Generative AI', 'Overview of generative models and applications', 'https://www.youtube.com/embed/xxX81WmXjPg', None, '30:30', 1),
            (course_ids[5], 'Generative Adversarial Networks', 'Understanding GANs and their variants', 'https://www.youtube.com/embed/8L11aMN52cE', None, '35:15', 2),
            (course_ids[5], 'Diffusion Models', 'Exploring diffusion-based generative models', 'https://www.youtube.com/embed/hoIfSw45kFI', None, '40:45', 3),
            (course_ids[5], 'Prompt Engineering', 'Mastering prompt design for LLMs', 'https://www.youtube.com/embed/dOx7c3bAeV0', None, '35:20', 4),
            (course_ids[5], 'Advanced Generative Techniques', 'State-of-the-art generative AI methods', 'https://www.youtube.com/embed/9Q3w2F9P3eI', None, '45:30', 5)
        ]
        
        # Sample modules for Agentic AI
        agentic_modules = [
            (course_ids[6], 'Introduction to AI Agents', 'Overview of autonomous AI systems', 'https://www.youtube.com/embed/xxX81WmXjPg', None, '25:30', 1),
            (course_ids[6], 'Reinforcement Learning', 'Training agents through reward-based learning', 'https://www.youtube.com/embed/2pWv7GOvuf0', None, '35:15', 2),
            (course_ids[6], 'Multi-Agent Systems', 'Coordinating multiple AI agents', 'https://www.youtube.com/embed/8L11aMN52cE', None, '40:45', 3),
            (course_ids[6], 'Decision Making Algorithms', 'Advanced decision-making in complex environments', 'https://www.youtube.com/embed/hoIfSw45kFI', None, '45:20', 4),
            (course_ids[6], 'Real-World Agent Deployment', 'Deploying AI agents in production systems', 'https://www.youtube.com/embed/dOx7c3bAeV0', None, '50:30', 5)
        ]
        
        # Insert all modules
        all_modules = python_modules + ml_modules + dl_modules + ds_modules + da_modules + genai_modules + agentic_modules
        cursor.executemany("""
            INSERT INTO course_modules (course_id, title, description, video_url, thumbnail_url, duration, order_index) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, all_modules)
        
        print(f"Added {len(all_modules)} modules to the courses")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Successfully added all new courses and modules!")
        
    except Exception as e:
        print(f"Error adding courses: {e}")
        if connection:
            connection.close()

if __name__ == "__main__":
    add_new_courses()