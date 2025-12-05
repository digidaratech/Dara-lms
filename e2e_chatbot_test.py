#!/usr/bin/env python3
"""
End-to-end test for the course assistant chatbot
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.course_chatbot_api import generate_document_response

def test_end_to_end():
    print("=== End-to-End Course Assistant Chatbot Test ===")
    
    # Test with course ID 1 (Python course)
    course_id = 1
    module_id = 1
    
    # Test cases
    test_cases = [
        {
            "query": "hello",
            "expected_type": "generic"
        },
        {
            "query": "what is python?",
            "expected_type": "document_based"
        },
        {
            "query": "explain variables in python",
            "expected_type": "document_based"
        },
        {
            "query": "how do functions work in python?",
            "expected_type": "document_based"
        },
        {
            "query": "what are lists in python?",
            "expected_type": "document_based"
        },
        {
            "query": "help",
            "expected_type": "generic"
        }
    ]
    
    print(f"Testing with course_id={course_id}, module_id={module_id}")
    print("-" * 50)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected_type = test_case["expected_type"]
        
        print(f"Test {i}: '{query}'")
        response = generate_document_response(query, course_id, module_id)
        
        # Check if we got a response
        if not response or len(response.strip()) == 0:
            print(f"  ❌ FAIL: No response received")
            all_passed = False
            continue
            
        # Check if response is meaningful
        if "Please try again" in response or "Something went wrong" in response:
            print(f"  ❌ FAIL: Error response received")
            print(f"    Response: {response[:100]}...")
            all_passed = False
            continue
            
        # Check response type
        if expected_type == "generic":
            # Should be a short, predefined response
            if len(response) < 200:
                print(f"  ✅ PASS: Got generic response")
            else:
                print(f"  ⚠️  WARNING: Expected generic but got long response")
        else:
            # Should be a detailed, document-based response
            if len(response) > 100:
                print(f"  ✅ PASS: Got document-based response")
            else:
                print(f"  ⚠️  WARNING: Expected detailed response but got short response")
                
        print(f"    Response preview: {response[:150]}{'...' if len(response) > 150 else ''}")
        print()
    
    print("-" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! The course assistant chatbot is working correctly.")
    else:
        print("❌ SOME TESTS FAILED. Please check the implementation.")
        
    return all_passed

if __name__ == "__main__":
    test_end_to_end()