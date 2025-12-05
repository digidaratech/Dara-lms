"""
Test script for certificate generation and email sending functionality
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.certificate_service import generate_certificate
from services.email_service import send_certificate_email

def test_certificate_generation_and_email():
    """Test certificate generation and email sending"""
    print("Testing certificate generation and email sending...")
    
    # Test data
    user_name = "Test User"
    course_title = "Python Programming"
    completion_date = datetime.now()
    certificate_id = 999  # Test ID
    
    try:
        # Generate certificate
        print("Generating certificate...")
        certificate_path = generate_certificate(user_name, course_title, completion_date, certificate_id)
        print(f"Certificate generated at: {certificate_path}")
        
        # Check if file exists
        if os.path.exists(certificate_path):
            print("Certificate file exists")
            
            # Test email sending (using a test email address)
            test_email = "test@example.com"  # Replace with actual test email
            print(f"Sending certificate email to: {test_email}")
            
            # Send email
            email_sent = send_certificate_email(user_name, test_email, course_title, certificate_path)
            if email_sent:
                print("✅ Certificate email sent successfully!")
            else:
                print("❌ Failed to send certificate email")
        else:
            print("❌ Certificate file was not created")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_certificate_generation_and_email()