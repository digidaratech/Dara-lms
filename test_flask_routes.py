#!/usr/bin/env python3
"""
Test script to check Flask routes
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_routes():
    print("Testing Flask routes...")
    
    # Create a test client
    with app.test_client() as client:
        # Test the course assistant route
        print("\n1. Testing /course-assistant route:")
        response = client.post('/course-assistant', 
                             json={'message': 'what is python?', 'course_id': 1, 'module_id': 1})
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Data: {response.get_data(as_text=True)[:200]}")

if __name__ == "__main__":
    test_routes()