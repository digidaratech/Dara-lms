import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()
"""
This file contains configuration variables for the Flask application.
These variables can be set in a .env file or directly in the code.
"""
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') 
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') 
    
    # Database Configuration - Flask-MySQLdb expects these specific keys
    MYSQL_HOST = os.environ.get('DB_HOST') or os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('DB_USER') or os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD') or os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DB = os.environ.get('DB_NAME') or os.environ.get('MYSQL_DB') or 'digidara_lms'
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # App Configuration
    DEBUG = os.environ.get('DEBUG') or True
    
    # Auto-tracking Configuration
    AUTO_TRACK_TEST_MODE = os.environ.get('AUTO_TRACK_TEST_MODE', 'False').lower() == 'true'
    AUTO_COMPLETE_THRESHOLD = float(os.environ.get('AUTO_COMPLETE_THRESHOLD', '100'))  # Percentage (100%)
