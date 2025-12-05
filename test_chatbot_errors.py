#!/usr/bin/env python3
"""
Test script to check the chatbot error handling
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.course_chatbot_api import generate_document_response

def test_error_handling():
    print("Testing chatbot error handling...")
    
    # Test with missing course_id
    print("\n1. Testing with missing course_id:")
    response = generate_document_response("what is data type?", None, 1)
    print(f"Response: {response}")
    
    # Test with missing module_id
    print("\n2. Testing with missing module_id:")
    response = generate_document_response("what is data type?", 1, None)
    print(f"Response: {response}")
    
    # Test with both missing
    print("\n3. Testing with both missing:")
    response = generate_document_response("what is data type?", None, None)
    print(f"Response: {response}")
    
    # Test with valid parameters
    print("\n4. Testing with valid parameters:")
    response = generate_document_response("what is data type?", 1, 1)
    print(f"Response preview: {response[:100]}...")

if __name__ == "__main__":
    test_error_handling()