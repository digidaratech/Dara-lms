"""
Simple test for the lightweight course chatbot
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_lightweight_chatbot():
    """Test the lightweight chatbot functionality"""
    print("Testing Lightweight Course Assistant Chatbot...")
    
    # Import the document search directly
    from chatbot.course_chatbot_api import document_search, generate_document_response
    
    # Test with a course
    course_id = 1
    try:
        # Load course documents
        documents = document_search.load_course_documents(course_id)
        print(f"Loaded {len(documents)} documents for course {course_id}")
        
        # Test a simple query
        query = "What is Python?"
        response = generate_document_response(query, course_id, 1)
        print(f"Query: {query}")
        print(f"Response: {response}")
        
        print("Lightweight chatbot test completed successfully!")
        
    except Exception as e:
        print(f"Error testing chatbot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lightweight_chatbot()