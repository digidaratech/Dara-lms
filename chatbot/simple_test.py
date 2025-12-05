"""
Simple test for the course chatbot
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.course_chatbot_api import course_rag, generate_fallback_response

def test_chatbot():
    """Test the chatbot functionality"""
    print("Testing Course Assistant Chatbot...")
    
    # Test fallback response
    test_message = "hello"
    response = generate_fallback_response(test_message)
    print(f"Query: {test_message}")
    print(f"Response: {response}")
    
    # Test with a course
    course_id = 1
    try:
        documents = course_rag.load_course_documents(course_id)
        print(f"\nLoaded {len(documents)} documents for course {course_id}")
        
        # Test search (will return empty if RAG is not available)
        query = "What is Python?"
        relevant_docs = course_rag.search_relevant_documents(query, course_id)
        print(f"\nSearch query: {query}")
        print(f"Found {len(relevant_docs)} relevant documents")
        
        if relevant_docs:
            print("Top result:", relevant_docs[0]['content'])
        else:
            print("RAG is not available, using fallback responses")
    except Exception as e:
        print(f"Error testing course documents: {e}")
        print("Using sample documents instead")

if __name__ == "__main__":
    test_chatbot()