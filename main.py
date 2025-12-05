"""
Startup script for LMS application with better error handling
"""
import sys
import os
import time
from app import app, mysql

def check_database_connection():
    """Check if database connection is available"""
    print("[*] Checking database connection...")
    try:
        connection = mysql.get_connection()
        if connection and connection.is_connected():
            print("[OK] Database connection successful!")
            # Don't close the connection, let the wrapper manage it
            return True
        else:
            print("[ERROR] Database connection failed!")
            return False
    except Exception as e:
        print(f"[ERROR] Database connection error: {e}")
        return False

def main():
    print("=" * 60)
    print("Starting LMS Application")
    print("=" * 60)
    print(f"Port: 5000")
    print(f"Host: 0.0.0.0 (accessible from all interfaces)")
    print(f"Debug Mode: True")
    print("-" * 60)
    
    # Check database connection
    db_ok = check_database_connection()
    if not db_ok:
        print("\n[WARNING] Database connection failed!")
        print("   The application will start but may not function correctly.")
        print("   You can continue and test the server, but database features may not work.")
        print("   Press Enter to continue or Ctrl+C to cancel...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n[INFO] Startup cancelled.")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Starting Flask server...")
    print("=" * 60)
    print("Access the application at: http://localhost:5000")
    print("Admin panel at: http://localhost:5000/admin/login")
    print("Press Ctrl+C to stop the server")
    print("-" * 60 + "\n")
    
    try:
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=True,
            use_reloader=False,  # Disable reloader to prevent port conflicts
            threaded=True  # Enable threading for better performance
        )
    except KeyboardInterrupt:
        print("\n\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
