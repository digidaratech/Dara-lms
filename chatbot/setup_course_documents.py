"""
Setup script for course documents
This script demonstrates how to organize course documents for the RAG chatbot.
"""

import os

def create_course_directory_structure():
    """Create the directory structure for course documents"""
    # Create the base courses directory
    os.makedirs("courses", exist_ok=True)
    
    # Example: Create directories for courses 1 and 2
    for course_id in [1, 2]:
        course_dir = os.path.join("courses", str(course_id))
        docs_dir = os.path.join(course_dir, "documents")
        os.makedirs(docs_dir, exist_ok=True)
        print(f"Created directory structure for course {course_id}")
    
    print("\nDirectory structure created:")
    print("courses/")
    print("├── 1/")
    print("│   ├── documents/")
    print("├── 2/")
    print("│   ├── documents/")

def create_sample_documents():
    """Create sample documents for testing"""
    # Sample content for course 1
    course1_content = """
    # Introduction to Python Programming
    
    ## What is Python?
    Python is a high-level, interpreted programming language known for its simplicity and readability.
    
    ## Variables in Python
    Variables are used to store data values. Unlike other programming languages, Python has no command for declaring a variable.
    A variable is created the moment you first assign a value to it.
    
    ## Functions in Python
    A function is a block of code which only runs when it is called. You can pass data, known as parameters, into a function.
    A function can return data as a result.
    
    ## Lists in Python
    Lists are used to store multiple items in a single variable. Lists are created using square brackets [].
    Lists are ordered, changeable, and allow duplicate values.
    """
    
    # Sample content for course 2
    course2_content = """
    # Web Development Fundamentals
    
    ## HTML Basics
    HTML (HyperText Markup Language) is the standard markup language for documents designed to be displayed in a web browser.
    It defines the structure and content of web pages.
    
    ## CSS Styling
    CSS (Cascading Style Sheets) is a stylesheet language used to describe the presentation of a document written in HTML.
    CSS describes how elements should be rendered on screen.
    
    ## JavaScript Programming
    JavaScript is a programming language that enables interactive web pages. It is an essential part of web applications.
    JavaScript runs on the client side of the web.
    """
    
    # Write sample documents
    with open("courses/1/documents/python_intro.txt", "w") as f:
        f.write(course1_content)
    
    with open("courses/2/documents/web_dev_basics.txt", "w") as f:
        f.write(course2_content)
    
    print("Sample documents created:")
    print("- courses/1/documents/python_intro.txt")
    print("- courses/2/documents/web_dev_basics.txt")

if __name__ == "__main__":
    create_course_directory_structure()
    create_sample_documents()
    print("\nSetup complete! You can now upload your own course documents to these directories.")