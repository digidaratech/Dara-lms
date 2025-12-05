"""
Test script for RAG functionality
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.course_chatbot_api import course_rag

def test_rag_functionality():
    """Test the RAG functionality"""
    print("Testing RAG functionality...")
    
    # Test if RAG is available
    if not course_rag.model:
        print("RAG is not available - missing dependencies")
        return
    
    print("RAG is available!")
    
    # Test loading course documents
    course_id = 1
    documents = course_rag.load_course_documents(course_id)
    print(f"Loaded {len(documents)} documents for course {course_id}")
    
    # Test searching for relevant documents
    query = "What is a Python variable?"
    relevant_docs = course_rag.search_relevant_documents(query, course_id, k=3)
    
    print(f"\nQuery: {query}")
    print(f"Found {len(relevant_docs)} relevant documents:")
    
    for i, doc in enumerate(relevant_docs):
        print(f"\n{i+1}. {doc['content']}")
        print(f"   Distance: {doc['distance']}")

if __name__ == "__main__":
    test_rag_functionality()