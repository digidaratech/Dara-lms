"""
Comprehensive test for the lightweight course chatbot
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_comprehensive_chatbot():
    """Test the lightweight chatbot functionality comprehensively"""
    print("Testing Comprehensive Course Assistant Chatbot...")
    
    # Import the document search directly
    from chatbot.course_chatbot_api import document_search, generate_document_response
    
    # Test with a course
    course_id = 1
    try:
        # Load course documents
        documents = document_search.load_course_documents(course_id)
        print(f"Loaded {len(documents)} documents for course {course_id}")
        
        # Print the actual document content
        for i, doc in enumerate(documents):
            print(f"Document {i+1}: {doc[:100]}...")
        
        # Test various queries
        queries = [
            "What is Python?",
            "What are variables in Python?",
            "How do functions work in Python?",
            "Explain Python lists",
            "What are dictionaries in Python?",
            "Hello"
        ]
        
        for query in queries:
            print(f"\n--- Testing Query: '{query}' ---")
            response = generate_document_response(query, course_id, 1)
            print(f"Response: {response}")
        
        print("\nComprehensive chatbot test completed successfully!")
        
    except Exception as e:
        print(f"Error testing chatbot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comprehensive_chatbot()