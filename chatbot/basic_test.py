"""
Basic test for the course chatbot
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.course_chatbot_api import generate_fallback_response

def test_basic_functionality():
    """Test basic chatbot functionality"""
    print("Testing basic Course Assistant Chatbot functionality...")
    
    # Test a few sample queries
    test_queries = ["hello", "help", "what is python", "how to use lists"]
    
    for query in test_queries:
        response = generate_fallback_response(query)
        print(f"\nQuery: {query}")
        print(f"Response: {response}")

if __name__ == "__main__":
    test_basic_functionality()