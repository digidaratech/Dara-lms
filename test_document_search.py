#!/usr/bin/env python3
"""
Test script to verify the document search functionality
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.course_chatbot_api import document_search

def test_document_search():
    print("Testing Document Search...")
    
    # Test with course ID 1 (Python course)
    course_id = 1
    
    # Test queries
    test_queries = [
        "what is python?",
        "explain variables in python",
        "how do functions work in python?",
        "what are lists in python?"
    ]
    
    # Load documents first
    documents = document_search.load_course_documents(course_id)
    print(f"Loaded {len(documents)} documents for course {course_id}")
    
    for doc in documents:
        print(f"  - {doc[:100]}...")
    
    print("\nTesting search queries:")
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = document_search.search_relevant_documents(query, course_id, k=3)
        print(f"Found {len(results)} relevant documents")
        for i, doc in enumerate(results):
            print(f"  Result {i+1}: {doc[:150]}...")

if __name__ == "__main__":
    test_document_search()