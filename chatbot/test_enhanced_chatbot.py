"""
Test script for the enhanced Course Assistant Chatbot with code examples
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.course_chatbot_api import generate_fallback_response

def test_enhanced_chatbot():
    print("Testing Enhanced Course Assistant Chatbot with code examples...")
    
    # Test queries
    queries = [
        "hello",
        "what is function in python",
        "can you send any examples in function",
        "send a any coding for function",
        "give me code example for lists",
        "show me dictionary coding example"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        response = generate_fallback_response(query)
        print(f"Response: {response[:100]}...")  # Show first 100 chars

if __name__ == "__main__":
    test_enhanced_chatbot()