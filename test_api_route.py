#!/usr/bin/env python3
"""
Test script to check the chatbot API route
"""

import sys
import os
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.course_chatbot_api import course_assistant_api

def test_api_route():
    print("Testing chatbot API route...")
    
    # Mock the request and session
    with patch('chatbot.course_chatbot_api.request') as mock_request, \
         patch('chatbot.course_chatbot_api.session') as mock_session, \
         patch('chatbot.course_chatbot_api.generate_document_response') as mock_generate:
        
        # Test case 1: User not logged in
        print("\n1. Testing with user not logged in:")
        mock_session.__contains__.return_value = False
        mock_request.get_json.return_value = {
            'message': 'what is python?',
            'course_id': 1,
            'module_id': 1
        }
        
        result = course_assistant_api()
        print(f"Result: {result}")
        
        # Test case 2: Missing message
        print("\n2. Testing with missing message:")
        mock_session.__contains__.return_value = True
        mock_request.get_json.return_value = {
            'course_id': 1,
            'module_id': 1
        }
        
        result = course_assistant_api()
        print(f"Result: {result}")
        
        # Test case 3: Missing course_id/module_id
        print("\n3. Testing with missing course_id/module_id:")
        mock_session.__contains__.return_value = True
        mock_request.get_json.return_value = {
            'message': 'what is python?'
        }
        
        result = course_assistant_api()
        print(f"Result: {result}")
        
        # Test case 4: Valid request
        print("\n4. Testing with valid request:")
        mock_session.__contains__.return_value = True
        mock_request.get_json.return_value = {
            'message': 'what is python?',
            'course_id': 1,
            'module_id': 1
        }
        mock_generate.return_value = "Python is a programming language."
        
        result = course_assistant_api()
        print(f"Result: {result}")

if __name__ == "__main__":
    test_api_route()