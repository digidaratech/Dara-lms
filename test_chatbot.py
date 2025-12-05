#!/usr/bin/env python3
"""
Test script to verify the course assistant chatbot functionality
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.course_chatbot_api import generate_document_response

def test_chatbot():
    print("Testing Course Assistant Chatbot...")
    
    # Test with course ID 1 (Python course)
    course_id = 1
    module_id = 1
    
    # Test queries
    test_queries = [
        "hello",
        "what is python?",
        "explain variables in python",
        "how do functions work in python?",
        "what are lists in python?",
        "help"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = generate_document_response(query, course_id, module_id)
        print(f"Response: {response[:200]}{'...' if len(response) > 200 else ''}")

if __name__ == "__main__":
    test_chatbot()