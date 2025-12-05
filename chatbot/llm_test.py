"""
Test for the document-based course chatbot
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.course_chatbot_api import document_search, generate_document_response

def test_document_chatbot():
    """Test the document-based chatbot functionality"""
    print("Testing Document-Based Course Assistant Chatbot...")
    
    # Test with a course
    course_id = 1
    try:
        # Load course documents
        documents = document_search.load_course_documents(course_id)
        print(f"Loaded {len(documents)} documents for course {course_id}")
        
        # Test document response generation
        query = "What is Python?"
        response = generate_document_response(query, course_id, 1)
        print(f"Query: {query}")
        print(f"Response: {response}")
        
        # Test search functionality
        relevant_docs = document_search.search_relevant_documents(query, course_id, k=3)
        print(f"Found {len(relevant_docs)} relevant documents")
        
        if relevant_docs:
            print("Top result:", relevant_docs[0]['content'][:100] + "...")
            
    except Exception as e:
        print(f"Error testing chatbot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_document_chatbot()