#!/usr/bin/env python3
"""
Debug script to check session behavior
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app correctly
import importlib.util
spec = importlib.util.spec_from_file_location("app", os.path.join(os.path.dirname(__file__), "app.py"))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = app_module.app

from flask import session
import unittest

class SessionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_session_flow(self):
        # First, let's check if we can access the login page
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        print("✅ Login page accessible")
        
        # Now let's try to login with our test user
        response = self.app.post('/login', data={
            'email': 'sessiontest@example.com',
            'password': 'sessiontest123'
        }, follow_redirects=True)
        
        print(f"Login response status: {response.status_code}")
        # Print response content for debugging
        print(f"Response content length: {len(response.get_data())}")
        
        # Check if we were redirected to the dashboard
        if b'dashboard' in response.get_data().lower():
            print("✅ Redirected to dashboard")
        elif response.status_code == 302:
            print(f"✅ Redirect response: {response.headers.get('Location')}")
        else:
            print("❌ Login may have failed")
            # Print some of the response content for debugging
            content = response.get_data(as_text=True)
            print(f"Response content preview: {content[:500]}")

if __name__ == '__main__':
    print("=== Session Debug Test ===")
    unittest.main(argv=['first-arg-is-ignored'], exit=False, verbosity=2)