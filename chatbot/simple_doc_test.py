"""
Simple test for the document search functionality
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.course_chatbot_api import document_search, generate_document_response

def test_document_search():
    """Test the document search functionality"""
    print("Testing Document Search...")
    
    # Test with course 1
    course_id = 1
    try:
        # Load documents
        documents = document_search.load_course_documents(course_id)
        print(f"Loaded {len(documents)} document chunks for course {course_id}")
        
        # Test a simple query
        query = "What is Python?"
        results = document_search.search_relevant_documents(query, course_id, k=3)
        print(f"Query: {query}")
        print(f"Found {len(results)} results")
        
        for i, result in enumerate(results):
            print(f"  {i+1}. Score: {result['score']:.3f}")
            print(f"     Content: {result['content'][:100]}...")
        
        # Test response generation
        response = generate_document_response(query, course_id, 1)
        print(f"\nGenerated Response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_document_search()