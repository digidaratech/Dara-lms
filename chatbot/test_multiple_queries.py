"""
Test script for the Course Assistant Chatbot with multiple queries
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.course_chatbot_api import document_search

def test_chatbot():
    print("Testing Course Assistant Chatbot with multiple queries...")
    
    # Test queries
    queries = [
        "What is Python?",
        "What are variables in Python?",
        "How do functions work in Python?",
        "Tell me about lists in Python",
        "What is OOP?",
        "hello",
        "help"
    ]
    
    course_id = 1
    
    for query in queries:
        print(f"\nQuery: {query}")
        response = document_search.search_relevant_documents(query, course_id, k=1)
        if response:
            print(f"Response: {response[0]['content']}")
        else:
            print("No relevant documents found")

if __name__ == "__main__":
    test_chatbot()