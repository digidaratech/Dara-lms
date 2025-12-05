#!/usr/bin/env python3
"""
Test script to check the document search for 'data type' query
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.course_chatbot_api import document_search, generate_document_response

def test_data_type_query():
    print("Testing 'data type' query...")
    
    # Test with course ID 1 (Python course)
    course_id = 1
    module_id = 1
    query = "what is data type?"
    
    print(f"Course ID: {course_id}")
    print(f"Query: {query}")
    
    # Load documents
    documents = document_search.load_course_documents(course_id)
    print(f"Loaded {len(documents)} documents")
    
    # Search for relevant documents
    relevant_docs = document_search.search_relevant_documents(query, course_id, k=3)
    print(f"Found {len(relevant_docs)} relevant documents")
    
    for i, doc in enumerate(relevant_docs):
        print(f"Document {i+1}: {doc[:200]}...")
    
    # Test the full response generation
    print("\n--- Testing full response generation ---")
    response = generate_document_response(query, course_id, module_id)
    print(f"Response: {response}")

if __name__ == "__main__":
    test_data_type_query()