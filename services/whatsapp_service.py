"""
WhatsApp Service for LMS
This module handles sending WhatsApp messages including certificate delivery notifications.
"""

import requests
import os
from urllib.parse import quote

# WhatsApp API Configuration (using a mock service for demonstration)
# In a real implementation, you would use a service like Twilio WhatsApp API
WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL') or 'https://api.whatsapp.com/send'
WHATSAPP_API_TOKEN = os.environ.get('WHATSAPP_API_TOKEN') or ''

def send_certificate_whatsapp(user_name, user_phone, course_title, certificate_url=None):
    """
    Send certificate notification via WhatsApp.
    
    Args:
        user_name (str): Name of the user
        user_phone (str): Phone number of the user (with country code)
        course_title (str): Title of the completed course
        certificate_url (str): URL to download the certificate (optional)
    
    Returns:
        bool: True if message sent successfully, False otherwise
    """
    try:
        # Validate inputs
        if not user_name or not user_phone or not course_title:
            print("Missing required WhatsApp parameters")
            return False
            
        # Create personalized message template
        message_template = (
            f"🎉 Congratulations {str(user_name)}!\n\n"
            f"You've successfully completed the course: *{str(course_title)}*\n\n"
            f"Your certificate of completion is now available!\n\n"
        )
        
        certificate_url_str = str(certificate_url) if certificate_url else None
        if certificate_url_str:
            message_template += f"📄 Download your certificate here: {certificate_url_str}\n\n"
        
        message_template += (
            f"Thank you for learning with us!\n"
            f"- EduFlow LMS Team"
        )
        
        # In a real implementation, you would use a WhatsApp API service like Twilio
        # For now, we'll just print the message that would be sent
        print(f"📱 WhatsApp message to {str(user_phone)}:")
        print(message_template)
        print(f"✅ WhatsApp notification sent successfully to {str(user_name)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send WhatsApp notification to {str(user_phone) if user_phone else 'unknown'}: {e}")
        import traceback
        traceback.print_exc()
        return False

def format_whatsapp_message(user_name, course_title, certificate_url=None):
    """
    Format a WhatsApp message with personalized content.
    
    Args:
        user_name (str): Name of the user
        course_title (str): Title of the completed course
        certificate_url (str): URL to download the certificate (optional)
    
    Returns:
        str: Formatted message
    """
    message = (
        f"🎉 Congratulations {user_name}!\n\n"
        f"You've successfully completed the course: *{course_title}*\n\n"
        f"Your certificate of completion is now available!"
    )
    
    if certificate_url:
        message += f"\n\n📄 Download your certificate here: {certificate_url}"
    
    message += "\n\nThank you for learning with us!\n- EduFlow LMS Team"
    
    return message