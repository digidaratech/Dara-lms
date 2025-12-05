import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response, send_file
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector as mysql_connector
from flask_cors import CORS
from config import Config
from datetime import datetime, timedelta, date, timezone
import secrets
import json
import requests
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import json
import random
import logging

#pdf miner
logging.getLogger("pdfminer").setLevel(logging.ERROR)



# Certificate service imports
from services.certificate_service import get_certificate_path
from services.email_service import send_certificate_email
from services.whatsapp_service import send_certificate_whatsapp

# Course Assistant Chatbot import
from chatbot import course_chatbot_api

# Email Configuration - Using environment variables for security
EMAIL_HOST = os.environ.get('EMAIL_HOST') or 'smtp.gmail.com'
EMAIL_PORT = int(os.environ.get('EMAIL_PORT') or 587)
EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME') or 'premkumar18082002@gmail.com'
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD') or 'gyqp zdee gkxq cjoa'


# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize the Flask app
app = Flask(__name__)

# Register the course assistant chatbot blueprint
app.register_blueprint(course_chatbot_api.course_chatbot_bp)

# Load configuration
app.config.from_object(Config)

# Make config available to templates
@app.context_processor
def inject_config():
    return dict(config=app.config)

# --- MySQL Helpers ----------------------------------------------------------
def get_mysql_connection():
    """Get MySQL connection (no unsupported kwargs)."""
    try:
        connection = mysql_connector.connect(
            host=app.config.get('MYSQL_HOST'),
            user=app.config.get('MYSQL_USER'),
            password=app.config.get('MYSQL_PASSWORD'),
            database=app.config.get('MYSQL_DB'),
            charset='utf8mb4',
            connection_timeout=10,
            autocommit=True
        )
        # Optionally set a session sql_mode
        try:
            cur = connection.cursor()
            cur.execute("SET SESSION sql_mode = %s", (
                "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,"
                "ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION",
            ))
            cur.close()
        except Exception:
            # If setting sql_mode fails, it's non-fatal
            pass

        return connection
    except mysql_connector.Error as e:
        print(f"❌ MySQL Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Failed to connect to MySQL: {e}")
        return None

# MySQL wrapper class
class MySQLWrapper:
    def __init__(self, app):
        self.app = app
        self.connection = None
    
    def get_connection(self):
        """Get or create a MySQL connection."""
        try:
            # Always try to get a fresh connection to avoid timeout issues
            self.connection = get_mysql_connection()
            return self.connection
        except Exception as e:
            print(f"❌ Connection error: {e}")
            # Try to create a new connection
            try:
                self.connection = get_mysql_connection()
                return self.connection
            except Exception as e2:
                print(f"❌ Failed to create new connection: {e2}")
                return None

# Initialize MySQL wrapper
mysql = MySQLWrapper(app)

def safe_close_cursor(cur):
    try:
        if cur:
            cur.close()
    except Exception:
        pass

def safe_close_connection(conn):
    try:
        if conn:
            conn.close()
    except Exception:
        pass

# ---------------------------------------------------------------------------

def send_otp_email(to_email, otp_code, user_name):
    """Send OTP email to user."""
    # If EMAIL_USERNAME or EMAIL_PASSWORD missing, skip sending and return False
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        print("⚠️ Email credentials not configured. Skipping email send.")
        return False

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USERNAME
        msg['To'] = to_email
        msg['Subject'] = "Password Reset OTP - EduFlow LMS"
        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #2c3e50; margin-bottom: 10px;">🔐 Password Reset Request</h2>
                    <p style="color: #7f8c8d; margin: 0;">EduFlow Learning Management System</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                    <p>Hello <strong>{user_name}</strong>,</p>
                    <p>We received a request to reset your password. Use the following verification code to complete the process:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="background-color: #3498db; color: white; padding: 15px 30px; border-radius: 6px; display: inline-block; font-size: 24px; font-weight: bold; letter-spacing: 3px;">
                            {otp_code}
                        </div>
                    </div>
                    <p><strong>Important:</strong></p>
                    <ul>
                        <li>This code will expire in 10 minutes</li>
                        <li>If you didn't request this reset, please ignore this email</li>
                        <li>Never share this code with anyone</li>
                    </ul>
                </div>
                <div style="text-align: center; color: #7f8c8d; font-size: 14px;">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; 2024 EduFlow LMS. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        # Create SMTP session
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        server.starttls()  # Enable TLS
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)

        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_USERNAME, to_email, text)
        server.quit()
        
        print(f"✅ OTP email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send OTP email to {to_email}: {e}")
        return False

# Certificate download route
@app.route('/certificate/<int:course_id>/download')
@app.route('/certificate/<int:course_id>/download/<string:type>')
def download_certificate(course_id, type='course'):
    print(f"[DOWNLOAD CERTIFICATE] Request received for course_id={course_id}, type={type}")
    if 'user_id' not in session:
        flash("Please login to access your certificate", "warning")
        return redirect(url_for('login'))
    
    try:
        print(f"\n=== CERTIFICATE DOWNLOAD REQUEST ===")
        print(f"User ID: {session['user_id']}, Course ID: {course_id}")
        
        connection = mysql.get_connection()
        if connection is None:
            print("ERROR: Database connection not available")
            flash("❌ Database connection not available", "danger")
            return redirect(url_for('dashboard'))
        
        # Check if user is eligible for the certificate based on type
        cur = connection.cursor()
        
        if type == 'exam':
            # For exam certificates, check if user has passed the exam
            cur.execute("""
                SELECT uea.exam_date, c.title as course_title, u.name as user_name
                FROM user_exam_attempts uea
                JOIN courses c ON uea.course_id = c.id
                JOIN users u ON uea.user_id = u.id
                WHERE uea.user_id = %s AND uea.course_id = %s AND uea.passed = TRUE
                ORDER BY uea.exam_date DESC LIMIT 1
            """, (session['user_id'], course_id))
        else:
            # For course certificates, check if user has completed the course
            cur.execute("""
                SELECT uc.completed_at, c.title as course_title, u.name as user_name
                FROM user_course uc
                JOIN courses c ON uc.course_id = c.id
                JOIN users u ON uc.user_id = u.id
                WHERE uc.user_id = %s AND uc.course_id = %s AND uc.completed_at IS NOT NULL
            """, (session['user_id'], course_id))
        
        result = cur.fetchone()
        cur.close()
        
        if not result:
            if type == 'exam':
                print("ERROR: Exam not passed or not found")
                flash("Exam certificate not available. Please pass the exam first.", "warning")
            else:
                print("ERROR: Course not completed or not found")
                flash("Certificate not available. Please complete the course first.", "warning")
            return redirect(url_for('course_detail', course_id=course_id))
        
        print(f"Course completed, fetching/generating certificate...")
        
        # Import certificate service
        from services.certificate_service import get_certificate_path, generate_certificate, save_certificate_record
        
        # Check if certificate already exists
        certificate_path = get_certificate_path(session['user_id'], course_id, mysql, type)
        
        if not certificate_path or not os.path.exists(certificate_path):
            print("Certificate file not found, generating new certificate...")
            
            # Generate new certificate
            certificate_id = save_certificate_record(session['user_id'], course_id, "", mysql, type)
            if not certificate_id:
                print("ERROR: Failed to save certificate record to database")
                flash("Error generating certificate: Database save failed", "danger")
                return redirect(url_for('course_detail', course_id=course_id))
            
            print(f"Certificate record saved with ID: {certificate_id}")
            
            # Extract values from result tuple (date, course_title, user_name)
            # Handle both dictionary and tuple cursor results
            if isinstance(result, dict):
                course_title = result['course_title']
                completed_at = result['completed_at'] if 'completed_at' in result else result.get('exam_date')
                user_name = result['user_name']
            else:
                completed_at = result[0]  # completed_at or exam_date
                course_title = result[1]  # course_title
                user_name = result[2]  # user_name
            
            print(f"Generating PDF for {user_name} - {course_title}")
            
            try:
                certificate_path = generate_certificate(
                    user_name, 
                    course_title,
                    completed_at,
                    certificate_id,
                    type
                )
                print(f"Certificate generated successfully: {certificate_path}")
            except Exception as cert_gen_error:
                print(f"ERROR generating certificate PDF: {cert_gen_error}")
                import traceback
                traceback.print_exc()
                flash(f"Error generating certificate: {str(cert_gen_error)}", "danger")
                return redirect(url_for('course_detail', course_id=course_id))
            
            # Update certificate path in database
            cur = connection.cursor()
            cur.execute("""
                UPDATE certificates 
                SET certificate_path = %s 
                WHERE user_id = %s AND course_id = %s AND certificate_type = %s
            """, (certificate_path, session['user_id'], course_id, type))
            connection.commit()
            cur.close()
            print("Certificate path updated in database")
        else:
            print(f"Using existing certificate: {certificate_path}")
        
        # Verify file exists before sending
        if not os.path.exists(certificate_path):
            print(f"ERROR: Certificate file not found at path: {certificate_path}")
            flash("Certificate file not found. Please contact support.", "danger")
            return redirect(url_for('course_detail', course_id=course_id))
        
        # Return certificate file
        print(f"Sending certificate file: {certificate_path}")
        download_name = f"exam_certificate_{course_id}.pdf" if type == 'exam' else f"certificate_{course_id}.pdf"
        return send_file(certificate_path, as_attachment=True, download_name=download_name)
        
    except Exception as e:
        print(f"ERROR downloading certificate: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Error downloading certificate: {str(e)}", "danger")
        return redirect(url_for('course_detail', course_id=course_id))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return "Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    return "Internal server error", 500

# Index route
@app.route('/')
def index():
    app.logger.info('Route triggered: / (index)')
    return render_template('index.html')

@app.route('/test-db')
def test_db():
    app.logger.info('Route triggered: /test-db')
    connection = None
    cur = None
    try:
        connection = mysql.get_connection()
        if connection is None:
            return jsonify({'status': 'error', 'message': 'Database connection failed'})

        cur = connection.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        result = cur.fetchone()

        user_count = 0
        if result:
            try:
                user_count = int(result[0]) if result[0] is not None else 0
            except (ValueError, TypeError, IndexError):
                user_count = 0

        return jsonify({
            'status': 'success',
            'message': 'Database connection working',
            'user_count': user_count
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'})

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("❌ Passwords do not match", "danger")
            return render_template("signup.html")

        password_hash = generate_password_hash(password)

        connection = None
        cur = None
        try:
            connection = mysql.get_connection()
            if connection is None:
                flash("❌ Database connection not available", "danger")
                return render_template("signup.html")
            cur = connection.cursor()
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                flash("❌ Email already registered", "danger")
                return render_template("signup.html")
            
            cur.execute("INSERT INTO users (name, email, mobile, password_hash) VALUES (%s, %s, %s, %s)",
                        (name, email, mobile, password_hash))
            connection.commit()
            cur.close()
            
            flash("✅ Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Signup error: {e}")
            flash("❌ Registration failed. Please try again.", "danger")
            return render_template("signup.html")

    return render_template("signup.html")

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = None
        cur = None
        try:
            connection = mysql.get_connection()
            if connection is None:
                flash("❌ Database connection not available", "danger")
                return render_template("login.html")
            
            cur = connection.cursor(dictionary=True)
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()
            cur.close()

            # Check if account is locked
            # Handle both dictionary and tuple cursor results
            account_locked_until = None
            user_id = None
            user_name = None
            user_email = None
            password_hash = None
            
            if user:
                if isinstance(user, dict):
                    account_locked_until = user.get('account_locked_until')
                    user_id = user.get('id')
                    user_name = user.get('name')
                    user_email = user.get('email')
                    password_hash = user.get('password_hash')
                else:
                    # For tuple results, we need to know the column index
                    # Based on the users table schema: id, name, email, mobile, password_hash, failed_login_attempts, account_locked_until
                    user_id = user[0] if len(user) > 0 else None
                    user_name = user[1] if len(user) > 1 else None
                    user_email = user[2] if len(user) > 2 else None
                    password_hash = user[4] if len(user) > 4 else None
                    account_locked_until = user[6] if len(user) > 6 else None
            
            # Check if account is locked
            if user and account_locked_until:
                try:
                    # Handle different data types for account_locked_until
                    if isinstance(account_locked_until, str):
                        locked_until = datetime.fromisoformat(account_locked_until.replace('Z', '+00:00'))
                    elif isinstance(account_locked_until, (datetime, date)):
                        locked_until = account_locked_until
                    else:
                        # Try to convert to datetime
                        locked_until = datetime.fromtimestamp(account_locked_until) if isinstance(account_locked_until, (int, float)) else None
                    
                    if locked_until and locked_until > datetime.now():
                        remaining_time = locked_until - datetime.now()
                        hours = int(remaining_time.total_seconds() // 3600)
                        minutes = int((remaining_time.total_seconds() % 3600) // 60)
                        flash(f"❌ Account is temporarily locked. Please try again in {hours}h {minutes}m", "danger")
                        return render_template("login.html")
                except Exception as e:
                    # If conversion fails, continue with login process
                    print(f"Error converting account_locked_until: {e}")
            
            # Ensure password_hash is a string before using it
            password_hash_str = str(password_hash) if password_hash else None
            
            # Ensure user_id is an integer
            user_id_int = None
            if user_id:
                # Safely convert user_id to integer
                try:
                    user_id_int = int(float(str(user_id)))
                except (ValueError, TypeError):
                    user_id_int = None
            
            if user and password_hash_str and check_password_hash(password_hash_str, password):
                # Reset failed login attempts on successful login
                
                cur = connection.cursor()
                cur.execute("UPDATE users SET failed_login_attempts=0, account_locked_until=NULL WHERE id=%s", (user_id_int,))
                connection.commit()
                cur.close()
                
                session['user_id'] = user_id_int
                session['user_name'] = str(user_name) if user_name else ""
                session['user_email'] = str(user_email) if user_email else ""
                
                # Create session token
                session_token = secrets.token_urlsafe(32)
                session['session_token'] = session_token
                
                # Store session in database
                cur = connection.cursor()
                cur.execute("INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent) VALUES (%s, %s, %s, %s)",
                            (user_id_int, session_token, str(request.remote_addr) if request.remote_addr else "", str(request.headers.get('User-Agent')) if request.headers.get('User-Agent') else ""))
                connection.commit()
                cur.close()
                
                flash("✅ Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                # Increment failed login attempts
                if user:
                    cur = connection.cursor()
                    # Handle both dictionary and tuple cursor results for failed_login_attempts
                    failed_attempts_raw = None
                    if isinstance(user, dict):
                        failed_attempts_raw = user.get('failed_login_attempts', 0)
                    else:
                        # For tuple results, failed_login_attempts is at index 5 based on the users table schema
                        failed_attempts_raw = user[5] if len(user) > 5 else 0
                    
                    # Convert to integer safely
                    try:
                        # Handle different data types for failed_attempts_raw
                        if failed_attempts_raw is not None:
                            if isinstance(failed_attempts_raw, (int, float)):
                                failed_attempts = int(failed_attempts_raw) + 1
                            elif isinstance(failed_attempts_raw, str):
                                failed_attempts = int(failed_attempts_raw) + 1 if failed_attempts_raw.isdigit() else 1
                            else:
                                failed_attempts = 1
                        else:
                            failed_attempts = 1
                    except (ValueError, TypeError):
                        failed_attempts = 1
                    
                    if failed_attempts >= 3:
                        # Lock account for 24 hours
                        lock_until = datetime.now() + timedelta(hours=24)
                        cur.execute("UPDATE users SET failed_login_attempts=%s, account_locked_until=%s WHERE id=%s", 
                                  (failed_attempts, lock_until, user_id_int))
                        flash("❌ Account locked for 24 hours due to multiple failed login attempts", "danger")
                    else:
                        cur.execute("UPDATE users SET failed_login_attempts=%s WHERE id=%s", (failed_attempts, user_id_int))
                        remaining_attempts = 3 - failed_attempts
                        flash(f"❌ Invalid email or password. {remaining_attempts} attempts remaining", "danger")
                    
                    connection.commit()
                    cur.close()
                else:
                    flash("❌ Invalid email or password", "danger")
                
                return render_template("login.html")
        except Exception as e:
            print(f"Login error: {e}")
            flash("❌ Login failed. Please try again.", "danger")
            return render_template("login.html")
        finally:
            safe_close_cursor(cur)
            safe_close_connection(connection)

    return render_template("login.html")

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    app.logger.info('Route triggered: /forgot-password')
    if request.method == 'POST':
        verification_method = request.form.get('verification_method')
        email = request.form.get('email')
        phone = request.form.get('phone')

        connection = None
        cur = None
        try:
            connection = mysql.get_connection()
            if connection is None:
                flash("❌ Database connection not available", "danger")
                return render_template("forgot_password.html")
            
            cur = connection.cursor(dictionary=True)
            
            # Find user by email or phone
            if verification_method == 'email':
                if not email:
                    flash("❌ Please enter your email address", "danger")
                    return render_template("forgot_password.html")
                
                cur.execute("SELECT * FROM users WHERE email=%s", (email,))
                user = cur.fetchone()
                verification_target = email
            else:  # phone
                if not phone:
                    flash("❌ Please enter your phone number", "danger")
                    return render_template("forgot_password.html")
                
                cur.execute("SELECT * FROM users WHERE mobile=%s", (phone,))
                user = cur.fetchone()
                verification_target = phone
            
            if not user:
                flash("❌ No account found with the provided information", "danger")
                return render_template("forgot_password.html")
            
            # Check if account is locked
            # Handle both dictionary and tuple cursor results
            account_locked_until = None
            user_id = None
            user_email = None
            user_mobile = None
            user_name = None
            
            if user:
                if isinstance(user, dict):
                    account_locked_until = user.get('account_locked_until')
                    user_id = user.get('id')
                    user_email = user.get('email')
                    user_mobile = user.get('mobile')
                    user_name = user.get('name')
                else:
                    # For tuple results, we need to know the column index
                    # Based on the users table schema: id, name, email, mobile, password_hash, failed_login_attempts, account_locked_until
                    user_id = user[0] if len(user) > 0 else None
                    user_name = user[1] if len(user) > 1 else None
                    user_email = user[2] if len(user) > 2 else None
                    user_mobile = user[3] if len(user) > 3 else None
                    account_locked_until = user[6] if len(user) > 6 else None
            
            # Check if account is locked
            if account_locked_until:
                try:
                    # Handle different data types for account_locked_until
                    if isinstance(account_locked_until, str):
                        locked_until = datetime.fromisoformat(account_locked_until.replace('Z', '+00:00'))
                    elif isinstance(account_locked_until, (datetime, date)):
                        locked_until = account_locked_until
                    else:
                        # Try to convert to datetime
                        locked_until = datetime.fromtimestamp(account_locked_until) if isinstance(account_locked_until, (int, float)) else None
                    
                    if locked_until and locked_until > datetime.now():
                        flash("❌ Account is temporarily locked. Please try again later.", "danger")
                        return render_template("forgot_password.html")
                except Exception as e:
                    # If conversion fails, continue with process
                    print(f"Error converting account_locked_until: {e}")
            
            # Generate OTP
            otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            expires_at = datetime.now() + timedelta(minutes=10)
            
            # Store OTP in database
            # Ensure user_id is an integer
            user_id_int = None
            if user_id:
                # Safely convert user_id to integer
                try:
                    user_id_int = int(float(str(user_id)))
                except (ValueError, TypeError):
                    user_id_int = None
            
            cur.execute("""
                INSERT INTO password_reset_otp (user_id, email, mobile, otp_code, otp_type, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id_int,
                str(user_email) if user_email else "",
                str(user_mobile) if user_mobile else None,
                otp_code,
                verification_method,
                expires_at
            ))
            connection.commit()
            cur.close()
            
            # Send OTP via email or show demo message
            if verification_method == 'email':
                # Send actual email
                email_sent = send_otp_email(email, otp_code, str(user_name) if user_name else "User")
                if email_sent:
                    flash(f"✅ Verification code sent to {email}. Please check your email.", "success")
                else:
                    flash(f"❌ Failed to send email. Demo code: {otp_code}", "warning")
            else:
                # For phone verification, still show demo code (SMS integration would be added here)
                flash(f"✅ Verification code sent to {phone}. Demo code: {otp_code}", "success")
            
            return redirect(url_for('verify_otp', user_id=user_id_int, method=verification_method))
            
        except Exception as e:
            print(f"Forgot password error: {e}")
            flash("❌ An error occurred. Please try again.", "danger")
            return render_template("forgot_password.html")
        finally:
            safe_close_cursor(cur)
            safe_close_connection(connection)

    return render_template("forgot_password.html")

@app.route('/verify-otp/<int:user_id>/<method>', methods=['GET', 'POST'])
def verify_otp(user_id, method):
    app.logger.info(f'Route triggered: /verify-otp/{user_id}/{method}')
    if request.method == 'POST':
        otp_digits = []
        for i in range(1, 7):
            digit = request.form.get(f'otp_{i}')
            if not digit or not digit.isdigit():
                flash("❌ Please enter a valid 6-digit code", "danger")
                return render_template("verify_otp.html", user_id=user_id, verification_method=method, verification_target="")

            otp_digits.append(digit)

        otp_code = ''.join(otp_digits)

        connection = None
        cur = None
        try:
            connection = mysql.get_connection()
            if connection is None:
                flash("❌ Database connection not available", "danger")
                return render_template("verify_otp.html", user_id=user_id, verification_method=method, verification_target="")

            cur = connection.cursor(dictionary=True)

            cur.execute("""
                SELECT * FROM password_reset_otp 
                WHERE user_id=%s AND otp_code=%s AND otp_type=%s AND is_used=FALSE AND expires_at > NOW()
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, otp_code, method))
            
            otp_record = cur.fetchone()
            
            if not otp_record:
                flash("❌ Invalid or expired verification code", "danger")
                return render_template("verify_otp.html", user_id=user_id, verification_method=method, verification_target="")
            
            # Mark OTP as used
            # Handle both dictionary and tuple cursor results
            otp_id = None
            if isinstance(otp_record, dict):
                otp_id = otp_record.get('id')
            else:
                # For tuple results, id is at index 0
                otp_id = otp_record[0] if len(otp_record) > 0 else None
            
            # Safely convert otp_id to integer if it's not None
            if otp_id is not None:
                try:
                    otp_id_int = int(float(str(otp_id)))
                except (ValueError, TypeError):
                    otp_id_int = None
                
                if otp_id_int is not None:
                    
                    cur.execute("UPDATE password_reset_otp SET is_used=TRUE WHERE id=%s", (otp_id_int,))
                else:
                    print("Warning: Could not convert OTP record ID to integer")
            else:
                print("Warning: Could not get OTP record ID")
            connection.commit()
            cur.close()
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            session['reset_token'] = reset_token
            session['reset_user_id'] = user_id
            
            flash("✅ Verification successful! Please set your new password.", "success")
            return redirect(url_for('reset_password', user_id=user_id, token=reset_token))
            
        except Exception as e:
            print(f"OTP verification error: {e}")
            flash("❌ An error occurred. Please try again.", "danger")
            return render_template("verify_otp.html", user_id=user_id, verification_method=method, verification_target="")
        finally:
            safe_close_cursor(cur)
            safe_close_connection(connection)

    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("❌ Database connection not available", "danger")
            return redirect(url_for('forgot_password'))
        
        cur = connection.cursor(dictionary=True)
        cur.execute("SELECT email, mobile FROM users WHERE id=%s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        
        if not user:
            flash("❌ User not found", "danger")
            return redirect(url_for('forgot_password'))
        
        # Handle both dictionary and tuple cursor results
        user_email = None
        user_mobile = None
        
        if user:
            if isinstance(user, dict):
                user_email = user.get('email')
                user_mobile = user.get('mobile')
            else:
                # For tuple results, email is at index 0, mobile is at index 1
                user_email = user[0] if len(user) > 0 else None
                user_mobile = user[1] if len(user) > 1 else None
        
        verification_target = user_email if method == 'email' else (user_mobile or '')
        
        return render_template("verify_otp.html", 
                             user_id=user_id, 
                             verification_method=method, 
                             verification_target=verification_target)
    
    except Exception as e:
        print(f"Error loading verify OTP page: {e}")
        flash("❌ An error occurred", "danger")
        return redirect(url_for('forgot_password'))

@app.route('/reset-password/<int:user_id>/<token>', methods=['GET', 'POST'])
def reset_password(user_id, token):
    app.logger.info(f'Route triggered: /reset-password/{user_id}/<token>')
    if 'reset_token' not in session or session['reset_token'] != token or session.get('reset_user_id') != user_id:
        flash("❌ Invalid or expired reset link", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not new_password or not confirm_password:
            flash("❌ Please fill in all fields", "danger")
            return render_template("reset_password.html", user_id=user_id, token=token)

        if new_password != confirm_password:
            flash("❌ Passwords do not match", "danger")
            return render_template("reset_password.html", user_id=user_id, token=token)

        if len(new_password) < 8:
            flash("❌ Password must be at least 8 characters long", "danger")
            return render_template("reset_password.html", user_id=user_id, token=token)

        if not any(c.isupper() for c in new_password):
            flash("❌ Password must contain at least one uppercase letter", "danger")
            return render_template("reset_password.html", user_id=user_id, token=token)

        if not any(c.islower() for c in new_password):
            flash("❌ Password must contain at least one lowercase letter", "danger")
            return render_template("reset_password.html", user_id=user_id, token=token)

        if not any(c.isdigit() for c in new_password):
            flash("❌ Password must contain at least one number", "danger")
            return render_template("reset_password.html", user_id=user_id, token=token)

        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in new_password):
            flash("❌ Password must contain at least one special character", "danger")
            return render_template("reset_password.html", user_id=user_id, token=token)

        connection = None
        cur = None
        try:
            connection = mysql.get_connection()
            if connection is None:
                flash("❌ Database connection not available", "danger")
                return render_template("reset_password.html", user_id=user_id, token=token)
            
            # Update password and reset failed login attempts
            password_hash = generate_password_hash(new_password)
            cur = connection.cursor()
            cur.execute("""
                UPDATE users 
                SET password_hash=%s, failed_login_attempts=0, account_locked_until=NULL 
                WHERE id=%s
            """, (password_hash, user_id))
            connection.commit()

            session.pop('reset_token', None)
            session.pop('reset_user_id', None)

            flash("✅ Password updated successfully! You can now login with your new password.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            print(f"Password reset error: {e}")
            flash("❌ An error occurred while updating password", "danger")
            return render_template("reset_password.html", user_id=user_id, token=token)
        finally:
            safe_close_cursor(cur)
            safe_close_connection(connection)

    return render_template("reset_password.html", user_id=user_id, token=token)

@app.route('/logout')
def logout():
    app.logger.info('Route triggered: /logout')
    connection = None
    cur = None
    try:
        if 'session_token' in session:
            connection = mysql.get_connection()
            if connection:
                cur = connection.cursor()
                cur.execute("DELETE FROM user_sessions WHERE session_token=%s", (session['session_token'],))
                connection.commit()
                cur.close()
    except Exception as e:
        print(f"Error removing session: {e}")
    
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('index'))

@app.route('/courses')
def courses():
    app.logger.info('Route triggered: /courses')
    connection = None
    try:
        print("[courses route] Starting courses page load")

        connection = mysql.get_connection()
        if not connection:
            print("[courses route] ERROR: MySQL connection is None")
            flash("❌ Database connection not available", "danger")
            return render_template('courses.html', courses=[], user_enrolled_course_ids=[])
        enrolled_ids = []
        if 'user_id' in session:
            try:
                from data import get_enrolled_course_ids
                enrolled_ids = get_enrolled_course_ids(session['user_id'], mysql)
                print(f"[courses route] Found {len(enrolled_ids)} enrolled courses for user {session['user_id']}")
            except Exception as e:
                print(f"[courses route] ERROR getting enrolled courses: {e}")
                enrolled_ids = []
        try:
            from data import get_all_courses
            all_courses = get_all_courses(mysql)
            print(f"[courses route] Successfully loaded {len(all_courses)} courses")
        except Exception as e:
            print(f"[courses route] ERROR in get_all_courses: {e}")
            import traceback
            traceback.print_exc()
            flash("❌ Error loading courses", "danger")
            all_courses = []
        
        return render_template('courses.html', courses=all_courses, user_enrolled_course_ids=enrolled_ids)
        
    except Exception as e:
        print(f"[courses route] CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        flash("❌ Error loading courses", "danger")
        return render_template('courses.html', courses=[], user_enrolled_course_ids=[])
    finally:
        safe_close_connection(connection)

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    app.logger.info(f'Route triggered: /course/{course_id}')
    connection = None
    cur = None
    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("❌ Database connection not available", "danger")
            return redirect(url_for('courses'))

        cur = connection.cursor(dictionary=True)

        cur.execute("""
            SELECT id, title, description, instructor, duration, price, 
                   COALESCE(status, 'active') as status,
                   COALESCE(category, 'programming') as category,
                   COALESCE(level, 'beginner') as level
            FROM courses WHERE id = %s
        """, (course_id,))
        course = cur.fetchone()
        
        if not course:
            flash("Course not found", "danger")
            return redirect(url_for('courses'))
        
        # Get course modules
        cur.execute("""
            SELECT cm.id, cm.title, cm.description, cm.video_url, cm.duration, cm.order_index,
                   COALESCE(ump.is_completed, FALSE) as is_completed
            FROM course_modules cm
            LEFT JOIN user_module_progress ump ON cm.id = ump.module_id AND ump.user_id = %s
            WHERE cm.course_id = %s 
            ORDER BY cm.order_index
        """, (session.get('user_id', 0), course_id))
        modules = cur.fetchall()
        
        # Convert modules to dictionaries if they're tuples for easier manipulation
        modules = [dict(mod) if not isinstance(mod, dict) else mod for mod in modules]
        
        # Add 'is_locked' property for sequential access
        for idx, mod in enumerate(modules):
            if idx == 0:
                mod['is_locked'] = False
            else:
                previous_module = modules[idx - 1]
                mod['is_locked'] = not previous_module.get('is_completed', False)
        
        # Get user info if logged in
        user = None
        is_enrolled = False
        enrollment = None
        exam_required_courses = set()
        exam_passed_courses = set()
        
        if 'user_id' in session:
            cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
            user = cur.fetchone()
            
            # Check if user is enrolled
            cur.execute("SELECT * FROM user_course WHERE user_id = %s AND course_id = %s", 
                        (session['user_id'], course_id))
            enrollment = cur.fetchone()
            is_enrolled = enrollment is not None
            
            # Check if course requires exam (for now, we'll assume all courses require exams)
            # In a real implementation, this would be based on course settings
            exam_required_courses.add(course_id)
            
            # Check if user has passed the exam for this course
            cur.execute("""
                SELECT passed FROM user_exam_attempts 
                WHERE user_id = %s AND course_id = %s AND passed = TRUE
                ORDER BY exam_date DESC LIMIT 1
            """, (session['user_id'], course_id))
            passed_exam = cur.fetchone()
            
            if passed_exam:
                exam_passed_courses.add(course_id)
        
        cur.close()
        
        return render_template('course_detail.html', 
                             course=course, 
                             modules=modules, 
                             user=user, 
                             is_enrolled=is_enrolled, 
                             enrollment=enrollment,
                             exam_required_courses=exam_required_courses,
                             exam_passed_courses=exam_passed_courses)
    except Exception as e:
        print(f"Error loading course detail: {e}")
        flash("Error loading course", "danger")
        return redirect(url_for('courses'))

# Module video route
@app.route('/course/<int:course_id>/module/<int:module_id>')
def module_video(course_id, module_id):
    print(f"=== DEBUG TRACE: Module video route START ===")
    print(f"Module video route called with course_id: {course_id}, module_id: {module_id}")
    print(f"Session keys: {list(session.keys())}")
    
    # Validate parameters
    if not course_id or not module_id:
        print(f"Invalid parameters: course_id={course_id}, module_id={module_id}")
        flash("Invalid course or module", "danger")
        return redirect(url_for('courses'))
    
    if 'user_id' not in session:
        print("User not logged in, redirecting to login")
        flash("Please login to access course content", "warning")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    if not user_id:
        print("Invalid user ID in session")
        flash("Invalid user session", "danger")
        return redirect(url_for('login'))
    
    print(f"User ID from session: {user_id}")
    try:
        print(f"Attempting to get database connection for user {user_id}, course {course_id}, module {module_id}")
        connection = mysql.get_connection()
        if connection is None:
            print("Database connection is None, redirecting to courses")
            flash("❌ Database connection not available", "danger")
            return redirect(url_for('courses'))
        print("Database connection successful")
        
        # Test the connection
        try:
            test_cur = connection.cursor()
            test_cur.execute("SELECT 1")
            test_result = test_cur.fetchone()
            print(f"Database connection test result: {test_result}")
            test_cur.close()
        except Exception as test_error:
            print(f"Database connection test failed: {test_error}")
            flash("❌ Database connection test failed", "danger")
            return redirect(url_for('courses'))
        
        cur = connection.cursor(dictionary=True)
        print(f"Cursor created successfully for user {user_id}")
        
        # Check if user is enrolled in the course
        print(f"Checking enrollment for user {user_id} in course {course_id}")
        try:
            cur.execute("SELECT * FROM user_course WHERE user_id = %s AND course_id = %s", 
                        (user_id, course_id))
            enrollment = cur.fetchone()
            print(f"Enrollment check result: {enrollment}")
            if enrollment is None:
                print(f"User {user_id} is not enrolled in course {course_id}")
                flash("Please enroll in this course to access content", "warning")
                return redirect(url_for('course_detail', course_id=course_id))
        except Exception as query_error:
            print(f"Error executing enrollment query: {query_error}")
            flash("Error checking enrollment status", "danger")
            return redirect(url_for('course_detail', course_id=course_id))
        print("=== DEBUG TRACE: Enrollment check passed ===")
        
        # Get course details
        print(f"Getting course details for course {course_id}")
        try:
            cur.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
            course = cur.fetchone()
            print(f"Course details result: {course}")
            if course is None:
                print(f"Course with ID {course_id} not found in database")
                flash("Course not found", "danger")
                return redirect(url_for('courses'))
        except Exception as query_error:
            print(f"Error executing course details query: {query_error}")
            flash("Error retrieving course information", "danger")
            return redirect(url_for('courses'))
        print("=== DEBUG TRACE: Course details retrieved ===")
        
        # Get module details
        print(f"Getting module details for module {module_id} in course {course_id}")
        try:
            cur.execute("""
                SELECT cm.*
                FROM course_modules cm
                WHERE cm.id = %s AND cm.course_id = %s
            """, (module_id, course_id))
            module = cur.fetchone()
            print(f"Module details result: {module}")
            if module is None:
                print(f"Module with ID {module_id} not found in course {course_id}")
                flash("Module not found", "danger")
                return redirect(url_for('course_detail', course_id=course_id))
            
            # Check if this module is locked (requires previous module completion)
            cur.execute("""
                SELECT cm.order_index,
                       (SELECT MAX(order_index) FROM course_modules WHERE course_id = %s) as max_order
                FROM course_modules cm
                WHERE cm.id = %s
            """, (course_id, module_id))
            module_order_result = cur.fetchone()
            
            # Remove module locking - all modules are now accessible
            # if module_order_result:
            #     current_order = module_order_result['order_index'] if isinstance(module_order_result, dict) else module_order_result[0]
            #     
            #     # If not the first module, check if previous module is completed
            #     # Ensure current_order is an integer before comparison
            #     current_order_int = int(current_order) if current_order is not None else 0
            #     if current_order_int > 1:
            #         cur.execute("""
            #             SELECT cm.id, cm.title
            #             FROM course_modules cm
            #             LEFT JOIN user_module_progress ump ON cm.id = ump.module_id AND ump.user_id = %s
            #             WHERE cm.course_id = %s AND cm.order_index = %s
            #             AND COALESCE(ump.is_completed, FALSE) = FALSE
            #         """, (user_id, course_id, current_order_int - 1))
            #         
            #         locked_check = cur.fetchone()
            #         if locked_check:
            #             previous_module_title = locked_check['title'] if isinstance(locked_check, dict) else locked_check[1]
            #             print(f"Module {module_id} is locked - previous module not completed")
            #             flash(f"🔒 Please complete '{previous_module_title}' before accessing this module", "warning")
            #             return redirect(url_for('course_detail', course_id=course_id))
                        
        except Exception as query_error:
            print(f"Error executing module details query: {query_error}")
            flash("Error retrieving module information", "danger")
            return redirect(url_for('course_detail', course_id=course_id))
        print("=== DEBUG TRACE: Module details retrieved ===")
        
        # Get all modules for this course (for sidebar)
        print(f"Getting all modules for course {course_id}")
        try:
            cur.execute("""
                SELECT cm.id, cm.title, cm.description, cm.video_url, cm.duration, cm.order_index,
                       COALESCE(ump.is_completed, FALSE) as is_completed
                FROM course_modules cm
                LEFT JOIN user_module_progress ump ON cm.id = ump.module_id AND ump.user_id = %s
                WHERE cm.course_id = %s 
                ORDER BY cm.order_index
            """, (user_id, course_id))
            modules = cur.fetchall()
            
            # Convert modules to list of dictionaries for easier manipulation
            # We need to handle both dict-like and tuple-like row results
            module_dicts = []
            for mod in modules:
                if hasattr(mod, 'keys'):
                    # It's a dict-like row
                    mod_dict = dict(mod)
                else:
                    # It's a tuple-like row, map to known column names
                    mod_dict = {
                        'id': mod[0] if len(mod) > 0 else None,
                        'title': mod[1] if len(mod) > 1 else None,
                        'description': mod[2] if len(mod) > 2 else None,
                        'video_url': mod[3] if len(mod) > 3 else None,
                        'duration': mod[4] if len(mod) > 4 else None,
                        'order_index': mod[5] if len(mod) > 5 else None,
                        'is_completed': mod[6] if len(mod) > 6 else False
                    }
                module_dicts.append(mod_dict)
            
            # Add 'is_locked' property for sequential access
            for idx, mod in enumerate(module_dicts):
                # Remove module locking - all modules are now accessible
                mod['is_locked'] = False
                # if idx == 0:
                #     mod['is_locked'] = False
                # else:
                #     previous_module = module_dicts[idx - 1]
                #     mod['is_locked'] = not previous_module.get('is_completed', False)
            
            all_modules = module_dicts
            print(f"All modules result with lock status: {all_modules}")
        except Exception as query_error:
            print(f"Error executing all modules query: {query_error}")
            all_modules = []
        print("=== DEBUG TRACE: All modules retrieved ===")
        
        # Get user progress for this specific module
        print(f"Getting user progress for user {user_id} in course {course_id} module {module_id}")
        try:
            cur.execute("""
                SELECT is_completed, watched_duration, total_duration
                FROM user_module_progress 
                WHERE user_id = %s AND course_id = %s AND module_id = %s
            """, (user_id, course_id, module_id))
            progress = cur.fetchone()
            print(f"User progress result: {progress}")
        except Exception as query_error:
            print(f"Error executing user progress query: {query_error}")
            progress = None
        print("=== DEBUG TRACE: User progress retrieved ===")
        
        # Get overall course progress
        print(f"Getting overall course progress for user {user_id} in course {course_id}")
        try:
            cur.execute("SELECT progress FROM user_course WHERE user_id = %s AND course_id = %s", 
                       (user_id, course_id))
            course_progress_result = cur.fetchone()
            course_progress_value = 0
            if course_progress_result:
                # Handle both dictionary and tuple cursor results
                if isinstance(course_progress_result, dict):
                    progress_raw = course_progress_result.get('progress', 0)
                else:
                    # For tuple results, progress is at index 0
                    progress_raw = course_progress_result[0] if len(course_progress_result) > 0 else 0
                
                # Safely convert to float
                try:
                    if isinstance(progress_raw, (int, float)):
                        course_progress_value = float(progress_raw)
                    elif progress_raw is not None:
                        course_progress_value = float(str(progress_raw))
                    else:
                        course_progress_value = 0
                except (ValueError, TypeError):
                    course_progress_value = 0
            print(f"Course progress for user {user_id} in course {course_id}: {course_progress_value}")
            # Add progress to course object
            if course and isinstance(course, dict):
                course['progress'] = course_progress_value
        except Exception as query_error:
            print(f"Error executing course progress query: {query_error}")
            # Add progress to course object
            if course and isinstance(course, dict):
                course['progress'] = 0
        print("=== DEBUG TRACE: Course progress retrieved ===")
        
        cur.close()
        connection.close()
        
        print(f"Course data being passed to template: {course}")
        print(f"Module data being passed to template: {module}")
        
        print(f"About to render template with: module={module is not None}, all_modules={len(all_modules) if all_modules else 0}, progress={progress is not None}, course={course is not None}")
        
        try:
            result = render_template('module_video.html', 
                                 module=module, 
                                 all_modules=all_modules, 
                                 progress=progress,
                                 course=course,
                                 config=app.config)
            print("Template rendered successfully")
            return result
        except Exception as render_error:
            print(f"Error rendering template: {render_error}")
            raise render_error
    except Exception as module_error:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error loading module video for user {session.get('user_id', 'unknown')}, course {course_id}, module {module_id}: {module_error}")
        print(f"Full traceback: {error_details}")
        # If the error is a number (like 0), provide a more descriptive message
        error_message = str(module_error) if str(module_error) != '0' else 'Unknown error occurred while loading module'
        # If we're getting a 0 error, it might be from a return statement, try to show a more helpful message
        if str(module_error) == '0':
            error_message = 'Module content could not be loaded. Please check if the course and module exist and you have proper access.'
        flash(f"Error loading module: {error_message}", "danger")
        # Try to redirect to a safe page
        try:
            if course_id:
                return redirect(url_for('course_detail', course_id=course_id))
            else:
                return redirect(url_for('courses'))
        except:
            return redirect(url_for('courses'))

# Checkout route
@app.route('/checkout/<int:course_id>', methods=['GET', 'POST'])
def checkout(course_id):
    app.logger.info(f'Route triggered: /checkout/{course_id}')
    if 'user_id' not in session:
        flash("Please login to enroll in courses", "warning")
        return redirect(url_for('login'))

    connection = None
    cur = None
    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("❌ Database connection not available", "danger")
            return redirect(url_for('courses'))

        cur = connection.cursor(dictionary=True)

        cur.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
        course = cur.fetchone()
        if not course:
            flash("Course not found", "danger")
            return redirect(url_for('courses'))

        cur.execute("SELECT * FROM user_course WHERE user_id = %s AND course_id = %s",
                    (session['user_id'], course_id))
        enrollment = cur.fetchone()
        if enrollment:
            flash("You are already enrolled in this course", "info")
            return redirect(url_for('course_detail', course_id=course_id))

        if request.method == 'POST':
            try:
                cur2 = connection.cursor()
                cur2.execute("INSERT INTO user_course (user_id, course_id) VALUES (%s, %s)",
                             (session['user_id'], course_id))
                connection.commit()
                safe_close_cursor(cur2)

                flash("✅ Successfully enrolled in the course!", "success")
                return redirect(url_for('course_detail', course_id=course_id))
            except Exception as e:
                app.logger.error(f"Enrollment error: {e}", exc_info=True)
                flash("❌ Enrollment failed. Please try again.", "danger")
                return render_template('checkout.html', course=course)

        return render_template('checkout.html', course=course)
    except Exception as e:
        app.logger.error(f"Error in checkout: {e}", exc_info=True)
        flash("❌ Error processing checkout", "danger")
        return redirect(url_for('courses'))
    finally:
        safe_close_cursor(cur)
        safe_close_connection(connection)

# Dashboard route
@app.route('/dashboard')
def dashboard():
    app.logger.info('Route triggered: /dashboard')
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = None
    cur = None
    try:
        session_token = session.get('session_token')
        if session_token:
            connection_ping = mysql.get_connection()
            if connection_ping:
                try:
                    connection_ping.ping(reconnect=True)
                except Exception:
                    pass
                safe_close_connection(connection_ping)

        user_id = session['user_id']
        connection = mysql.get_connection()
        if connection is None:
            flash("❌ Database connection not available", "danger")
            return redirect(url_for('login'))

        cur = connection.cursor(dictionary=True)
        user = None
        enrolled_courses = []
        recommended_courses = []
        analytics = {'enrolled_courses': 0, 'completed_courses': 0, 'avg_progress': 0, 'total_watch_time_seconds': 0}
        user_stats = {'enrolled_courses': 0, 'completed_courses': 0, 'avg_progress': 0, 'total_watch_time_seconds': 0}
        progress_data = {'in_progress': 0, 'completed': 0, 'not_started': 0}
        daily_labels = []
        daily_data = []
        yearly_labels = []
        yearly_hours = []
        yearly_completed = []

        try:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user:
                session.clear()
                return redirect(url_for('login'))

            # Enrolled courses
            try:
                cur.execute("""
                    SELECT c.*, uc.progress, uc.enrolled_at
                    FROM user_course uc
                    JOIN courses c ON uc.course_id = c.id
                    WHERE uc.user_id = %s
                    ORDER BY uc.enrolled_at DESC
                """, (user_id,))
                enrolled_courses = cur.fetchall()
            except Exception as e:
                app.logger.error(f"[dashboard] Error fetching enrolled_courses: {e}", exc_info=True)
                enrolled_courses = []

            # Recommended courses
            try:
                cur.execute("""
                    SELECT * FROM courses 
                    WHERE COALESCE(status, 'active') = 'active'
                    AND id NOT IN (
                        SELECT course_id FROM user_course WHERE user_id = %s
                    )
                    ORDER BY created_at DESC LIMIT 4
                """, (user_id,))
                recommended_courses = cur.fetchall()
            except Exception as e:
                app.logger.error(f"[dashboard] Error fetching recommended_courses: {e}", exc_info=True)
                recommended_courses = []

            # Analytics
            try:
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT uc.course_id) as enrolled_courses,
                        COUNT(DISTINCT CASE WHEN uc.progress >= 100 THEN uc.course_id END) as completed_courses,
                        AVG(uc.progress) as avg_progress,
                        SUM(uwt.watch_duration) as total_watch_time_seconds
                    FROM users u
                    LEFT JOIN user_course uc ON u.id = uc.user_id
                    LEFT JOIN user_watch_time uwt ON u.id = uwt.user_id
                    WHERE u.id = %s
                """, (user_id,))
                analytics = cur.fetchone() or analytics
            except Exception as e:
                app.logger.error(f"[dashboard] Error fetching analytics: {e}", exc_info=True)
                analytics = {'enrolled_courses': 0, 'completed_courses': 0, 'avg_progress': 0, 'total_watch_time_seconds': 0}

            user_stats = {
                'enrolled_courses': analytics.get('enrolled_courses', 0) or 0,
                'completed_courses': analytics.get('completed_courses', 0) or 0,
                'avg_progress': round(analytics.get('avg_progress', 0) or 0, 1),
                'total_watch_time_seconds': analytics.get('total_watch_time_seconds', 0) or 0
            }

            total_courses = len(enrolled_courses) + len(recommended_courses)
            in_progress_courses = user_stats['enrolled_courses'] - user_stats['completed_courses']
            progress_data = {
                'in_progress': in_progress_courses,
                'completed': user_stats['completed_courses'],
                'not_started': total_courses - user_stats['enrolled_courses']
            }

            total_watch_time_seconds = user_stats['total_watch_time_seconds']
            monthly_watch_time = total_watch_time_seconds / 3600
            avg_daily_time = monthly_watch_time / 30 if monthly_watch_time > 0 else 0
            user_stats.update({
                'monthly_watch_time': round(monthly_watch_time, 1),
                'avg_daily_time': round(avg_daily_time, 1)
            })

            # Daily study time (last 7 days)
            try:
                cur.execute("""
                    SELECT watch_date, SUM(watch_duration)/3600 as hours
                    FROM user_watch_time
                    WHERE user_id = %s AND watch_date >= CURDATE() - INTERVAL 6 DAY
                    GROUP BY watch_date
                    ORDER BY watch_date
                """, (user_id,))
                daily_rows = cur.fetchall()
                daily_map = {}
                for row in daily_rows:
                    watch_date = row.get('watch_date')
                    hours = row.get('hours') or 0
                    if watch_date:
                        try:
                            label = watch_date.strftime('%m/%d')
                        except Exception:
                            label = str(watch_date)
                        daily_map[label] = float(hours)
                daily_labels = []
                daily_data = []
                for i in range(7):
                    date = (datetime.now() - timedelta(days=6 - i)).strftime('%m/%d')
                    daily_labels.append(date)
                    daily_data.append(round(daily_map.get(date, 0), 2))
            except Exception as e:
                app.logger.error(f"[dashboard] Error fetching daily study time: {e}", exc_info=True)
                daily_labels = []
                daily_data = []

            # Yearly analytics (last 12 months)
            try:
                cur.execute("""
                    SELECT DATE_FORMAT(watch_date, '%b %Y') as month, 
                           SUM(watch_duration)/3600 as hours
                    FROM user_watch_time
                    WHERE user_id = %s AND watch_date >= CURDATE() - INTERVAL 12 MONTH
                    GROUP BY YEAR(watch_date), MONTH(watch_date)
                    ORDER BY YEAR(watch_date), MONTH(watch_date)
                """, (user_id,))
                yearly_rows = cur.fetchall()
                yearly_map = {}
                for row in yearly_rows:
                    month = row.get('month')
                    hours = row.get('hours') or 0
                    if month:
                        yearly_map[month] = float(hours)

                yearly_labels = []
                yearly_hours = []
                for i in range(12):
                    month = (datetime.now() - timedelta(days=365 - i * 30)).strftime('%b %Y')
                    yearly_labels.append(month)
                    yearly_hours.append(round(yearly_map.get(month, 0), 2))
            except Exception as e:
                app.logger.error(f"[dashboard] Error fetching yearly analytics: {e}", exc_info=True)
                yearly_labels = []
                yearly_hours = []

            # Completed courses per month (last 12 months)
            try:
                cur.execute("""
                    SELECT DATE_FORMAT(completed_at, '%b %Y') as month, COUNT(*) as completed
                    FROM user_course
                    WHERE user_id = %s AND completed_at IS NOT NULL
                      AND completed_at >= CURDATE() - INTERVAL 12 MONTH
                    GROUP BY YEAR(completed_at), MONTH(completed_at)
                    ORDER BY YEAR(completed_at), MONTH(completed_at)
                """, (user_id,))
                completed_rows = cur.fetchall()
                completed_map = {}
                for row in completed_rows:
                    month = row.get('month')
                    completed = row.get('completed') or 0
                    if month:
                        completed_map[month] = int(completed)
                yearly_completed = [completed_map.get(month, 0) for month in yearly_labels]
            except Exception as e:
                app.logger.error(f"[dashboard] Error fetching yearly completed courses: {e}", exc_info=True)
                yearly_completed = []

            # Ensure yearly_hours exists
            if 'yearly_hours' not in locals():
                yearly_hours = []

            # Placeholder: Find courses needing certification (customize as needed)
            courses_needing_certification = []
            return render_template(
                'dashboard.html',
                user=user,
                enrolled_courses=enrolled_courses,
                recommended_courses=recommended_courses,
                user_stats=user_stats,
                progress_data=progress_data,
                daily_labels=daily_labels,
                daily_data=daily_data,
                yearly_labels=yearly_labels,
                yearly_completed=yearly_completed,
                yearly_hours=yearly_hours,
                courses_needing_certification=courses_needing_certification
            )

        finally:
            safe_close_cursor(cur)
            safe_close_connection(connection)

    except Exception as e:
        import traceback
        app.logger.critical(f"[dashboard] CRITICAL ERROR: {e}\n{traceback.format_exc()}")
        flash("❌ An error occurred while loading the dashboard", "danger")
        return redirect(url_for('login'))

# Update last active
@app.before_request
def update_last_active():
    if 'session_token' in session:
        try:
            connection = mysql.get_connection()
            if connection:
                # Test connection before using
                try:
                    connection.ping(reconnect=True, attempts=1, delay=0)
                except Exception:
                    # If ping fails, try to get a new connection
                    connection = mysql.get_connection()
                
                if connection:
                    try:
                        cur = connection.cursor()
                        cur.execute("UPDATE user_sessions SET last_active=%s WHERE session_token=%s",
                                    (datetime.now(timezone.utc), session['session_token']))
                        connection.commit()
                        cur.close()
                    except Exception as e:
                        print(f"Error updating last active: {e}")
                        # Don't let this error crash the application
                        pass
        except Exception as e:
            print(f"Error updating last active: {e}")
            # Don't let this error crash the application
            pass

# Admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Simple admin check (in production, use proper admin table)
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            session['admin_email'] = username
            flash("✅ Admin login successful!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("❌ Invalid admin credentials", "danger")
            return render_template("admin/login.html")
    
    return render_template("admin/login.html")

# Admin dashboard route
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("❌ Database connection not available", "danger")
            return render_template("admin/dashboard.html",
                                 stats={'total_users': 0, 'total_courses': 0, 'total_enrollments': 0, 'total_revenue': 0, 'recent_users': 0, 'recent_enrollments': 0},
                                 recent_users=[],
                                 recent_enrollments=[],
                                 courses=[],
                                 user_growth_labels=[],
                                 user_growth_data=[],
                                 course_popularity_labels=[],
                                 course_popularity_data=[])
        
        try:
            connection.ping(reconnect=True)
        except Exception:
            pass

        cur = connection.cursor(dictionary=True)

        try:
            # Get basic stats
            cur.execute("SELECT COUNT(*) as total_users FROM users")
            user_result = cur.fetchone()
            if isinstance(user_result, dict):
                total_users = user_result.get('total_users', 0)
            elif user_result:
                total_users = user_result[0] if len(user_result) > 0 else 0
            else:
                total_users = 0

            cur.execute("SELECT COUNT(*) as total_courses FROM courses")
            course_result = cur.fetchone()
            if isinstance(course_result, dict):
                total_courses = course_result.get('total_courses', 0)
            elif course_result:
                total_courses = course_result[0] if len(course_result) > 0 else 0
            else:
                total_courses = 0

            cur.execute("SELECT COUNT(*) as total_enrollments FROM user_course")
            enrollment_result = cur.fetchone()
            if isinstance(enrollment_result, dict):
                total_enrollments = enrollment_result.get('total_enrollments', 0)
            elif enrollment_result:
                total_enrollments = enrollment_result[0] if len(enrollment_result) > 0 else 0
            else:
                total_enrollments = 0

        except Exception as e:
            print(f"❌ Database error in admin dashboard: {e}")
            total_users = 0
            total_courses = 0
            total_enrollments = 0            
            cur.execute("""
                SELECT SUM(c.price) as total_revenue 
                FROM user_course uc
                JOIN courses c ON uc.course_id = c.id
            """)
            revenue_result = cur.fetchone()
            total_revenue = 0
            if revenue_result:
                if isinstance(revenue_result, dict):
                    total_revenue = revenue_result.get('total_revenue', 0) or 0
                else:
                    total_revenue = revenue_result[0] if len(revenue_result) > 0 else 0
            
            # Get recent users
            cur.execute("SELECT name, email, created_at FROM users ORDER BY created_at DESC LIMIT 5")
            recent_users = cur.fetchall()
            
            # Get recent enrollments
            cur.execute("""
                SELECT u.name as user_name, c.title as course_title, uc.enrolled_at, uc.progress
                FROM user_course uc
                JOIN users u ON uc.user_id = u.id
                JOIN courses c ON uc.course_id = c.id
                ORDER BY uc.enrolled_at DESC LIMIT 5
            """)
            recent_enrollments = cur.fetchall()
            cur.execute("""
                SELECT c.id, c.title, c.instructor, COUNT(uc.user_id) as enrollment_count, 
                       AVG(uc.progress) as avg_progress, SUM(c.price) as revenue, 
                       COALESCE(c.status, 'active') as status
                FROM courses c
                LEFT JOIN user_course uc ON c.id = uc.course_id
                GROUP BY c.id, c.title, c.instructor, c.status
                ORDER BY enrollment_count DESC
            """)
            courses = cur.fetchall()
            
        except Exception as e:
            print(f"❌ Database error in admin dashboard: {e}")
            # Return default values on error
            total_users = 0
            total_courses = 0
            total_enrollments = 0
            total_revenue = 0
            recent_users = []
            recent_enrollments = []
            courses = []
        finally:
            cur.close()
        
        stats = {
            'total_users': total_users,
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'total_revenue': total_revenue,
            'recent_users': len(recent_users),
            'recent_enrollments': len(recent_enrollments)
        }
        
        # Generate chart data
        # User growth data (last 7 days)
        user_growth_labels = []
        user_growth_data = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).strftime('%m/%d')
            user_growth_labels.append(date)
            user_growth_data.append(0)  # Placeholder data
        
        # Course popularity data
        course_popularity_labels = []
        course_popularity_data = []
        for course in courses[:5]:  # Top 5 courses
            # Handle both dictionary and tuple cursor results
            if isinstance(course, dict):
                title = course.get('title', '')
                enrollment_count = course.get('enrollment_count', 0)
            else:
                # For tuple results, title is at index 1, enrollment_count is at index 2
                title = course[1] if len(course) > 1 else ''
                enrollment_count = course[2] if len(course) > 2 else 0
            
            # Safely truncate title
            try:
                title_str = str(title)
                truncated_title = title_str[:20] + '...' if len(title_str) > 20 else title_str
            except:
                truncated_title = 'Unknown Course'
            course_popularity_labels.append(truncated_title)
            # Handle both dictionary and tuple cursor results
            if isinstance(course, dict):
                enrollment_count = course.get('enrollment_count', 0)
            else:
                # For tuple results, enrollment_count is at index 2
                enrollment_count = course[2] if len(course) > 2 else 0
            
            # Safely convert enrollment_count to int
            try:
                enrollment_count_int = int(str(enrollment_count)) if enrollment_count is not None else 0
            except (ValueError, TypeError):
                enrollment_count_int = 0
            course_popularity_data.append(enrollment_count_int)
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             recent_users=recent_users,
                             recent_enrollments=recent_enrollments,
                             courses=courses,
                             user_growth_labels=user_growth_labels,
                             user_growth_data=user_growth_data,
                             course_popularity_labels=course_popularity_labels,
                             course_popularity_data=course_popularity_data)
    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        flash("❌ Error loading admin dashboard", "danger")
        return render_template("admin/dashboard.html",
                             stats={'total_users': 0, 'total_courses': 0, 'total_enrollments': 0, 'total_revenue': 0, 'recent_users': 0, 'recent_enrollments': 0},
                             recent_users=[],
                             recent_enrollments=[],
                             courses=[],
                             user_growth_labels=[],
                             user_growth_data=[],
                             course_popularity_labels=[],
                             course_popularity_data=[])
    finally:
        safe_close_connection(connection)

# Remaining admin routes keep same safe close pattern
@app.route('/admin/courses')
def admin_courses():
    app.logger.info('Route triggered: /admin/courses')
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    connection = None
    cur = None
    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("❌ Database connection not available", "danger")
            return render_template("admin/courses.html", courses=[])
        cur = connection.cursor(dictionary=True)
        cur.execute("""
            SELECT id, title, description, instructor, price, duration, 
                   COALESCE(status, 'active') as status,
                   COALESCE(created_at, NOW()) as created_at,
                   COALESCE(category, 'programming') as category,
                   COALESCE(level, 'beginner') as level
            FROM courses
            ORDER BY created_at DESC
        """)
        courses = cur.fetchall()
        cur.close()
        
        return render_template("admin/courses.html", courses=courses)
    except Exception as e:
        print(f"Error loading admin courses: {e}")
        flash("❌ Error loading courses", "danger")
        return render_template("admin/courses.html", courses=[])


from werkzeug.utils import secure_filename

# Allowed file extensions
ALLOWED_DOC_EXTENSIONS = {'pdf', 'docx', 'pptx', 'txt'}

def allowed_doc_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS


# Admin users route
@app.route('/admin/users')
def admin_users():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("❌ Database connection not available", "danger")
            return render_template("admin/users.html", users=[])
        
        cur = connection.cursor(dictionary=True)
        cur.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = cur.fetchall()
        cur.close()
        
        return render_template("admin/users.html", users=users)
    except Exception as e:
        print(f"Error loading admin users: {e}")
        flash("❌ Error loading users", "danger")
        return render_template("admin/users.html", users=[])
    finally:
        safe_close_cursor(cur)
        safe_close_connection(connection)

@app.route('/admin/enrollments')
def admin_enrollments():
    app.logger.info('Route triggered: /admin/enrollments')
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    connection = None
    cur = None
    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("❌ Database connection not available", "danger")
            return render_template("admin/enrollments.html", enrollments=[])
        cur = connection.cursor(dictionary=True)
        cur.execute("""
            SELECT uc.*, u.name as user_name, u.email as user_email, 
                   c.title as course_title, c.instructor
            FROM user_course uc
            JOIN users u ON uc.user_id = u.id
            JOIN courses c ON uc.course_id = c.id
            ORDER BY uc.enrolled_at DESC
        """)
        enrollments = cur.fetchall()
        cur.close()
        
        return render_template("admin/enrollments.html", enrollments=enrollments)
    except Exception as e:
        print(f"Error loading admin enrollments: {e}")
        flash("❌ Error loading enrollments", "danger")
        return render_template("admin/enrollments.html", enrollments=[])
    finally:
        safe_close_cursor(cur)
        safe_close_connection(connection)

@app.route('/admin/analytics')
def admin_analytics():
    app.logger.info('Route triggered: /admin/analytics')
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template("admin/analytics.html")

@app.route('/admin/settings')
def admin_settings():
    app.logger.info('Route triggered: /admin/settings')
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template("admin/settings.html")

@app.route('/admin/profile')
def admin_profile():
    app.logger.info('Route triggered: /admin/profile')
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template("admin/profile.html")

@app.route('/admin/logout')
def admin_logout():
    app.logger.info('Route triggered: /admin/logout')
    session.pop('admin', None)
    session.pop('admin_email', None)
    flash("Admin logged out successfully.", "success")
    return redirect(url_for('admin_login'))

@app.route('/admin/course/create', methods=['GET', 'POST'])
def admin_create_course():
    app.logger.info('Route triggered: /admin/course/create')
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    connection = None
    cur = None
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        instructor = request.form['instructor']
        duration = request.form['duration']
        price = request.form['price']
        category = request.form.get('category', 'programming')
        level = request.form.get('level', 'beginner')
        try:
            connection = mysql.get_connection()
            if connection is None:
                flash("❌ Database connection not available", "danger")
                return render_template("admin/create_course.html")
            cur = connection.cursor()
            cur.execute("""
                INSERT INTO courses (title, description, instructor, duration, price, category, level)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (title, description, instructor, duration, price, category, level))
            connection.commit()
            cur.close()
            
            flash("✅ Course created successfully!", "success")
            return redirect(url_for('admin_courses'))
        except Exception as e:
            print(f"Error creating course: {e}")
            flash("❌ Error creating course", "danger")
            return render_template("admin/create_course.html")
    
    return render_template("admin/create_course.html")


# ADMIN: Rebuild FAISS Index

@app.route("/admin/rebuild-faiss", methods=["POST"])
def admin_rebuild_faiss():
    try:
        from chatbot.faiss_vector_store import FaissVectorStore
        store = FaissVectorStore()
        store.build_all_courses_index()
        return jsonify({"success": True, "message": "FAISS index rebuilt successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to rebuild index: {str(e)}"}), 500


# ADMIN: Upload Course Document

@app.route('/admin/document/upload', methods=['POST'])
def admin_upload_document():
    try:
        course_id = request.form.get("course_id")
        file = request.files.get("document_file")

        if not file:
            return jsonify({"success": False, "message": "No file uploaded"}), 400

        import os
        upload_dir = os.path.join("courses", str(course_id), "documents")
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)

        # Rebuild FAISS automatically
        from chatbot.faiss_vector_store import FaissVectorStore
        store = FaissVectorStore()
        store.rebuild_index(course_id)

        return jsonify({"success": True, "message": "Document uploaded & AI index rebuilt successfully!"})

    except Exception as e:
        print("Error uploading document:", e)
        return jsonify({"success": False, "message": "Upload failed"})



# Admin video upload route
@app.route('/admin/video/upload', methods=['GET', 'POST'])
def admin_video_upload():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        course_id = request.form['course_id']
        title = request.form['title']
        description = request.form['description']
        duration = request.form.get('duration', '')
        order_index = request.form.get('order_index', 1)
        
        # Handle video URL or file upload
        video_url = request.form.get('video_url', '')
        
        # If no video URL provided, check for file upload
        if not video_url and 'videoFile' in request.files:
            video_file = request.files['videoFile']
            if video_file and video_file.filename:
                # For now, we'll store the filename as the video_url
                # In a production environment, you'd upload to a cloud service
                video_url = f"uploads/{video_file.filename}"
                # Save the file (basic implementation)
                import os
                upload_folder = 'attached_assets/videos'
                os.makedirs(upload_folder, exist_ok=True)
                video_file.save(os.path.join(upload_folder, video_file.filename))
        try:
            connection = mysql.get_connection()
            if connection is None:
                flash("❌ Database connection not available", "danger")
                return render_template("admin/video_upload.html")
            cur = connection.cursor()
            cur.execute("""
                INSERT INTO course_modules (course_id, title, description, video_url, duration, order_index)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (course_id, title, description, video_url, duration, order_index))
            connection.commit()
            cur.close()
            
            flash("✅ Video uploaded successfully!", "success")
            return redirect(url_for('admin_courses'))
        except Exception as e:
            print(f"Error uploading video: {e}")
            flash("❌ Error uploading video", "danger")
            return render_template("admin/video_upload.html")
        finally:
            safe_close_cursor(cur)
            safe_close_connection(connection)

    try:
        connection = mysql.get_connection()
        if connection:
            cur = connection.cursor(dictionary=True)
            cur.execute("SELECT id, title FROM courses ORDER BY title")
            courses = cur.fetchall()
            cur.close()
        else:
            courses = []
    except Exception as e:
        print(f"Error loading courses: {e}")
        courses = []
    finally:
        safe_close_cursor(cur)
        safe_close_connection(connection)

    return render_template("admin/video_upload.html", courses=courses)

@app.route('/admin/course/<int:course_id>/edit', methods=['GET', 'POST'])
def admin_edit_course(course_id):
    app.logger.info(f'Route triggered: /admin/course/{course_id}/edit')
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    connection = None
    cur = None
    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("❌ Database connection not available", "danger")
            return redirect(url_for('admin_courses'))
        
        cur = connection.cursor(dictionary=True)
        cur.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
        course = cur.fetchone()
        
        if not course:
            flash("Course not found", "danger")
            return redirect(url_for('admin_courses'))
        
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            instructor = request.form['instructor']
            duration = request.form['duration']
            price = request.form['price']
            category = request.form.get('category', 'programming')
            level = request.form.get('level', 'beginner')
            status = request.form.get('status', 'active')

            cur2 = connection.cursor()
            cur2.execute("""
                UPDATE courses 
                SET title = %s, description = %s, instructor = %s, duration = %s, 
                    price = %s, category = %s, level = %s, status = %s
                WHERE id = %s
            """, (title, description, instructor, duration, price, category, level, status, course_id))
            connection.commit()
            
            flash("✅ Course updated successfully!", "success")
            return redirect(url_for('admin_courses'))
        
        cur.close()
        return render_template("admin/edit_course.html", course=course)
    except Exception as e:
        print(f"Error editing course: {e}")
        flash("❌ Error editing course", "danger")
        return redirect(url_for('admin_courses'))
    finally:
        safe_close_cursor(cur)
        safe_close_connection(connection)

@app.route('/admin/course/<int:course_id>/view')
def admin_view_course(course_id):
    app.logger.info(f'Route triggered: /admin/course/{course_id}/view')
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    connection = None
    cur = None
    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("❌ Database connection not available", "danger")
            return redirect(url_for('admin_courses'))
        
        cur = connection.cursor(dictionary=True)
        
        # Get course details
        cur.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
        course = cur.fetchone()
        
        if not course:
            flash("Course not found", "danger")
            return redirect(url_for('admin_courses'))
        
        # Get course modules
        cur.execute("SELECT * FROM course_modules WHERE course_id = %s ORDER BY order_index", (course_id,))
        modules = cur.fetchall()
        
        # Get enrollment stats
        cur.execute("""
            SELECT COUNT(*) as total_enrollments, AVG(progress) as avg_progress
            FROM user_course WHERE course_id = %s
        """, (course_id,))
        stats = cur.fetchone()
        
        cur.close()
        
        return render_template("admin/view_course.html", course=course, modules=modules, stats=stats)
    except Exception as e:
        print(f"Error viewing course: {e}")
        flash("❌ Error viewing course", "danger")
        return redirect(url_for('admin_courses'))
    finally:
        safe_close_cursor(cur)
        safe_close_connection(connection)

@app.route('/admin/course/<int:course_id>/delete', methods=['POST'])
def admin_delete_course(course_id):
    app.logger.info(f'Route triggered: /admin/course/{course_id}/delete')
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Not authorized'})

    connection = None
    cur = None
    try:
        connection = mysql.get_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection not available'})
        
        cur = connection.cursor()
        cur.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Course deleted successfully'})
    except Exception as e:
        print(f"Error deleting course: {e}")
        return jsonify({'success': False, 'message': 'Error deleting course'})

@app.route('/api/module/<int:module_id>/has-questions')
def module_has_questions(module_id):
    """API endpoint to check if a module has quiz questions."""
    try:
        from services.topic_quiz_service import get_topic_questions_for_module
        
        # Get questions for this module
        questions = get_topic_questions_for_module(module_id, mysql)
        
        print(f"[API MODULE QUESTIONS] Module {module_id} has {len(questions)} questions")
        
        # Return JSON response
        return jsonify({
            'has_questions': len(questions) > 0,
            'question_count': len(questions)
        })
    except Exception as e:
        print(f"Error checking module questions: {e}")
        # Return True by default if there's an error to maintain existing behavior
        return jsonify({
            'has_questions': True,
            'question_count': 0
        })


# Admin delete module route
@app.route('/admin/module/<int:module_id>/delete', methods=['POST'])
def admin_delete_module(module_id):
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        connection = mysql.get_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection not available'})
        
        cur = connection.cursor()
        cur.execute("DELETE FROM course_modules WHERE id = %s", (module_id,))
        connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Module deleted successfully'})
    except Exception as e:
        print(f"Error deleting module: {e}")
        return jsonify({'success': False, 'message': 'Error deleting module'})

# Admin edit module route
@app.route('/admin/module/<int:module_id>/edit', methods=['POST'])
def admin_edit_module(module_id):
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        video_url = data.get('video_url')
        duration = data.get('duration')
        order_index = data.get('order_index')
        
        connection = mysql.get_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection not available'})
        
        cur = connection.cursor()
        cur.execute("""
            UPDATE course_modules 
            SET title = %s, description = %s, video_url = %s, duration = %s, order_index = %s
            WHERE id = %s
        """, (title, description, video_url, duration, order_index, module_id))
        connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Module updated successfully'})
    except Exception as e:
        print(f"Error updating module: {e}")
        return jsonify({'success': False, 'message': 'Error updating module'})

# Google OAuth routes
@app.route('/google-login', methods=['POST'])
def google_login():
    try:
        print("=== Google Login Debug ===")
        data = request.get_json()
        print(f"Received data: {data}")
        
        credential = data.get('credential')
        print(f"Credential received: {'Yes' if credential else 'No'}")
        
        if not credential:
            return jsonify({'success': False, 'message': 'No credential provided'})
        
        # Verify the Google ID token
        print("Verifying Google token...")
        google_response = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': credential},
            timeout=10
        )

        print(f"Google response status: {google_response.status_code}")

        if google_response.status_code != 200:
            print(f"Google response error: {google_response.text}")
            return jsonify({'success': False, 'message': f'Invalid Google token: {google_response.status_code}'})

        user_info = google_response.json()
        print(f"User info from Google: {user_info}")

        email = user_info.get('email')
        name = user_info.get('name')

        print(f"Email: {email}, Name: {name}")

        if not email:
            return jsonify({'success': False, 'message': 'Email not provided by Google'})

        connection = mysql.get_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection not available'})

        cur = connection.cursor(dictionary=True)
        cur.execute("SELECT id, name FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        print(f"User found in database: {'Yes' if user else 'No'}")

        if user:
            session_token = secrets.token_hex(16)
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['session_token'] = session_token

            print(f"Creating session for user: {user['id']}")

            cur2 = connection.cursor()
            cur2.execute(
                """INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, login_time)
                   VALUES (%s, %s, %s, %s, %s)""",
                (user['id'], session_token, request.remote_addr, request.headers.get('User-Agent'), datetime.now(timezone.utc))
            )
            connection.commit()
            safe_close_cursor(cur2)

            print("Login successful!")
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            print("User not found in database")
            return jsonify({'success': False, 'message': 'Account not found. Please sign up first.'})

    except Exception as e:
        print(f"Exception in google_login: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        safe_close_cursor(cur)
        safe_close_connection(connection)

@app.route('/google-signup', methods=['POST'])
def google_signup():
    app.logger.info('Route triggered: /google-signup')
    connection = None
    cur = None
    try:
        print("=== Google Signup Debug ===")
        data = request.get_json()
        print(f"Received data: {data}")

        credential = data.get('credential')
        print(f"Credential received: {'Yes' if credential else 'No'}")

        if not credential:
            return jsonify({'success': False, 'message': 'No credential provided'})

        google_response = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': credential},
            timeout=10
        )

        print(f"Google response status: {google_response.status_code}")

        if google_response.status_code != 200:
            print(f"Google response error: {google_response.text}")
            return jsonify({'success': False, 'message': f'Invalid Google token: {google_response.status_code}'})

        user_info = google_response.json()
        print(f"User info from Google: {user_info}")

        email = user_info.get('email')
        name = user_info.get('name')

        print(f"Email: {email}, Name: {name}")

        if not email or not name:
            return jsonify({'success': False, 'message': 'Email and name required from Google'})

        connection = mysql.get_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection not available'})

        cur = connection.cursor()
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        existing_user = cur.fetchone()
        print(f"User already exists: {'Yes' if existing_user else 'No'}")

        if existing_user:
            return jsonify({'success': False, 'message': 'Email already registered'})

        print("Creating new user...")
        cur2 = connection.cursor()
        cur2.execute(
            "INSERT INTO users (name, email, mobile, password_hash) VALUES (%s, %s, %s, %s)",
            (name, email, '', 'google_oauth_user')
        )
        connection.commit()
        user_id = cur2.lastrowid
        safe_close_cursor(cur2)

        session_token = secrets.token_hex(16)
        session['user_id'] = user_id
        session['user_name'] = name
        session['session_token'] = session_token

        cur3 = connection.cursor()
        cur3.execute(
            """INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, login_time)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, session_token, request.remote_addr, request.headers.get('User-Agent'), datetime.now(timezone.utc))
        )
        connection.commit()
        safe_close_cursor(cur3)

        print("Signup successful!")
        return jsonify({'success': True, 'message': 'Sign up successful'})

    except Exception as e:
        print(f"Exception in google_signup: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        safe_close_cursor(cur)
        safe_close_connection(connection)

@app.route('/api/chat', methods=['POST'])
def chatbot_api():
    app.logger.info('Route triggered: /api/chat')
    try:
        data = request.get_json()
        message = data.get('message', '')

        responses = {
            'hello': 'Hello! How can I help you with your learning journey?',
            'help': 'I can help you with course information, enrollment, and technical support.',
            'courses': 'We offer courses in programming, web development, data science, and machine learning.',
            'enroll': 'To enroll in a course, please visit the course page and click the enroll button.',
            'payment': 'We accept various payment methods including credit cards and digital wallets.',
            'progress': 'You can track your progress in the dashboard section of your account.'
        }
        
        # Simple keyword matching
        message_lower = message.lower()
        response = "I'm here to help! Please ask me about courses, enrollment, or any other questions."
        
        for keyword, reply in responses.items():
            if keyword in message_lower:
                response = reply
                break
        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        print(f"Chatbot API error: {e}")
        return jsonify({
            'success': False,
            'response': 'Sorry, I encountered an error. Please try again.'
        })

# Progress tracking API route
@app.route('/api/progress/update', methods=['POST'])
def update_progress():
    print("\n=== PROGRESS UPDATE API CALLED ===")
    if 'user_id' not in session:
        print("[AUTO-TRACK] ERROR: User not logged in")
        return jsonify({'success': False, 'message': 'User not logged in'})
    
    print(f"[AUTO-TRACK] User ID: {session['user_id']}")
    
    try:
        data = request.get_json()
        print(f"[AUTO-TRACK] Received data: {data}")
        
        if not data:
            print("[AUTO-TRACK] ERROR: No data provided")
            return jsonify({'success': False, 'message': 'No data provided'})
            
        course_id = data.get('course_id')
        module_id = data.get('module_id')
        watched_duration = data.get('watched_duration', 0)
        is_completed = data.get('is_completed', False)
        
        print(f"[AUTO-TRACK] Parsed - course_id: {course_id}, module_id: {module_id}, watched_duration: {watched_duration}s, is_completed: {is_completed}")
        
        if not course_id or not module_id:
            print("[AUTO-TRACK] ERROR: Missing required parameters")
            return jsonify({'success': False, 'message': 'Missing required parameters'})
        
        # Validate data types with safe conversion
        try:
            course_id = int(float(str(course_id))) if course_id is not None else 0
            module_id = int(float(str(module_id))) if module_id is not None else 0
            watched_duration = float(str(watched_duration)) if watched_duration is not None else 0
            is_completed = bool(is_completed)
            # Get total_duration from client data if available
            total_duration = data.get('total_duration', None)
            
            # Calculate progress percentage for logging (this is just for display, actual logic is in data.py)
            # We'll get the actual duration from the database in update_module_progress
            print(f"[AUTO-TRACK] Converted - user_id={session['user_id']}, module_id={module_id}, watched_duration={watched_duration}s, completed={is_completed}")
        except (ValueError, TypeError) as e:
            print(f"[AUTO-TRACK] ERROR: Invalid data types: {e}")
            return jsonify({'success': False, 'message': f'Invalid data types: {str(e)}'})
        
        # Import progress tracking function
        from data import update_module_progress, calculate_course_progress
        
        print("[AUTO-TRACK] Calling update_module_progress...")
        # Update progress (this internally calls calculate_course_progress)
        print(f"[AUTO-TRACK] Calling update_module_progress with is_completed={is_completed}")
        success = update_module_progress(
            session['user_id'], 
            course_id, 
            module_id, 
            watched_duration, 
            mysql,
            is_completed,
            total_duration  # Pass the client-provided total duration
        )
        
        print(f"[AUTO-TRACK] update_module_progress returned: {success}")
        
        if success:
            # Get the updated course progress (already calculated by update_module_progress)
            print("[AUTO-TRACK] Fetching updated course progress from database...")
            try:
                connection = mysql.get_connection()
                if connection:
                    cur = connection.cursor()
                    cur.execute("SELECT progress FROM user_course WHERE user_id = %s AND course_id = %s", 
                               (session['user_id'], course_id))
                    result = cur.fetchone()
                    # Safe conversion handling both tuple and dict cursors
                    if result:
                        try:
                            progress_value = result[0] if isinstance(result, (tuple, list)) else result.get('progress', 0)
                            course_progress = float(str(progress_value)) if progress_value is not None else 0.0
                        except (ValueError, TypeError, AttributeError):
                            course_progress = 0.0
                    else:
                        course_progress = 0.0
                    cur.close()
                    
                    print(f"[AUTO-TRACK] Current course progress: {course_progress}%")
                    
                    # Check if course is completed (100% progress)
                    is_course_completed = course_progress >= 100
                    
                    return jsonify({
                        'success': True, 
                        'message': 'Progress updated successfully', 
                        'course_progress': course_progress,
                        'course_completed': is_course_completed,
                        'redirect_url': url_for('course_detail', course_id=course_id) if is_course_completed else None
                    })
                else:
                    print("[AUTO-TRACK] ERROR: No database connection for fetching progress")
                    return jsonify({'success': True, 'message': 'Progress updated but could not fetch course progress'})
            except Exception as progress_error:
                print(f"[AUTO-TRACK] ERROR fetching course progress: {progress_error}")
                return jsonify({'success': True, 'message': 'Progress updated but could not fetch course progress'})
        else:
            print("[AUTO-TRACK] ERROR: Failed to update progress in database")
            
            # Diagnostic information
            try:
                # Test database connection
                test_connection = mysql.get_connection()
                if test_connection:
                    print("[AUTO-TRACK] Database connection is available")
                    test_connection.close()
                else:
                    print("[AUTO-TRACK] Database connection is not available")
            except Exception as conn_error:
                print(f"[AUTO-TRACK] Database connection error: {conn_error}")
            
            return jsonify({'success': False, 'message': 'Failed to update progress - Database operation failed. Please check database connectivity and table structure.'})
            
    except Exception as e:
        print(f"[AUTO-TRACK] ❌ EXCEPTION: Progress update error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error updating progress: {str(e)}'})
# Admin API routes for dashboard functionality
@app.route('/api/admin/export-data', methods=['POST'])
def admin_export_data():
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        # Handle case where request.json might be None
        data_type = 'all'
        if request.json:
            data_type = request.json.get('type', 'all')
        connection = mysql.get_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection not available'})
        
        cur = connection.cursor(dictionary=True)
        
        if data_type == 'users' or data_type == 'all':
            cur.execute("SELECT * FROM users ORDER BY created_at DESC")
            users = cur.fetchall()
        else:
            users = []
        if data_type == 'courses' or data_type == 'all':
            cur.execute("SELECT * FROM courses ORDER BY created_at DESC")
            courses = cur.fetchall()
        else:
            courses = []
        if data_type == 'enrollments' or data_type == 'all':
            cur.execute("""
                SELECT uc.*, u.name as user_name, u.email as user_email, 
                       c.title as course_title, c.instructor
                FROM user_course uc
                JOIN users u ON uc.user_id = u.id
                JOIN courses c ON uc.course_id = c.id
                ORDER BY uc.enrolled_at DESC
            """)
            enrollments = cur.fetchall()
        else:
            enrollments = []
        
        cur.close()
        
        # Convert datetime objects to strings for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        export_data = {
            'users': convert_datetime(users),
            'courses': convert_datetime(courses),
            'enrollments': convert_datetime(enrollments),
            'export_date': datetime.now().isoformat()
        }
        return jsonify({
            'success': True,
            'data': export_data,
            'message': f'Data exported successfully. {len(users)} users, {len(courses)} courses, {len(enrollments)} enrollments.'
        })

    except Exception as e:
        print(f"Export data error: {e}")
        return jsonify({'success': False, 'message': 'Error exporting data'})
    finally:
        safe_close_cursor(cur)
        safe_close_connection(connection)

@app.route('/api/admin/refresh-dashboard', methods=['POST'])
def admin_refresh_dashboard():
    app.logger.info('Route triggered: /api/admin/refresh-dashboard')
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Not authorized'})

    connection = None
    cur = None
    try:
        connection = mysql.get_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection not available'})

        cur = connection.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cur.fetchone()['total_users']

        cur.execute("SELECT COUNT(*) as total_courses FROM courses")
        total_courses = cur.fetchone()['total_courses']

        cur.execute("SELECT COUNT(*) as total_enrollments FROM user_course")
        total_enrollments = cur.fetchone()['total_enrollments']

        cur.execute("""
            SELECT SUM(c.price) as total_revenue 
            FROM user_course uc
            JOIN courses c ON uc.course_id = c.id
        """)
        revenue_result = cur.fetchone()
        total_revenue = revenue_result['total_revenue'] or 0

        cur.execute("SELECT name, email, created_at FROM users ORDER BY created_at DESC LIMIT 5")
        recent_users = cur.fetchall()

        cur.execute("""
            SELECT u.name as user_name, c.title as course_title, uc.enrolled_at, uc.progress
            FROM user_course uc
            JOIN users u ON uc.user_id = u.id
            JOIN courses c ON uc.course_id = c.id
            ORDER BY uc.enrolled_at DESC LIMIT 5
        """)
        recent_enrollments = cur.fetchall()
        
        # Get course management data
        cur.execute("""
            SELECT c.id, c.title, c.instructor, COUNT(uc.user_id) as enrollment_count, 
                   AVG(uc.progress) as avg_progress, SUM(c.price) as revenue, 
                   COALESCE(c.status, 'active') as status
            FROM courses c
            LEFT JOIN user_course uc ON c.id = uc.course_id
            GROUP BY c.id, c.title, c.instructor, c.status
            ORDER BY enrollment_count DESC
        """)
        courses = cur.fetchall()
        
        cur.close()
        
        # Convert datetime objects to strings
        def convert_datetime(obj):
            if isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        dashboard_data = {
            'stats': {
                'total_users': total_users,
                'total_courses': total_courses,
                'total_enrollments': total_enrollments,
                'total_revenue': total_revenue,
                'recent_users': len(recent_users),
                'recent_enrollments': len(recent_enrollments)
            },
            'recent_users': convert_datetime(recent_users),
            'recent_enrollments': convert_datetime(recent_enrollments),
            'courses': convert_datetime(courses)
        }
        
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'message': 'Dashboard data refreshed successfully'
        })
        
    except Exception as e:
        print(f"Refresh dashboard error: {e}")
        return jsonify({'success': False, 'message': 'Error refreshing dashboard data'})

# Certification exam route
# Certification exam introduction route
@app.route('/exam/<int:course_id>/intro')
def certification_exam_intro(course_id):
    try:
        print(f"=== DEBUG: Certification exam intro route called with course_id={course_id} ===")
        
        if 'user_id' not in session:
            print("DEBUG: User not logged in")
            flash("Please login to access the certification exam", "warning")
            return redirect(url_for('login'))
        
        print(f"DEBUG: User ID from session: {session['user_id']}")
        
        connection = mysql.get_connection()
        if connection is None:
            print("DEBUG: Database connection is None")
            flash("❌ Database connection not available", "danger")
            return redirect(url_for('dashboard'))
        
        print("DEBUG: Database connection successful")
        cur = connection.cursor(dictionary=True)
        
        # Get course details
        cur.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
        course = cur.fetchone()
        
        if not course:
            flash("Course not found", "danger")
            return redirect(url_for('courses'))
        
        # Check if user is enrolled in the course
        print(f"DEBUG: Checking enrollment for user {session['user_id']} in course {course_id}")
        cur.execute("SELECT * FROM user_course WHERE user_id = %s AND course_id = %s", 
                    (session['user_id'], course_id))
        enrollment = cur.fetchone()
        print(f"DEBUG: Enrollment result: {enrollment}")
        
        if not enrollment:
            print("DEBUG: User not enrolled in course")
            flash("You must be enrolled in this course to take the certification exam", "warning")
            return redirect(url_for('course_detail', course_id=course_id))
        
        # Check if course has exam questions
        print(f"DEBUG: Checking for exam questions in course {course_id}")
        cur.execute("SELECT COUNT(*) as question_count FROM questions WHERE course_id = %s", (course_id,))
        question_result = cur.fetchone()
        print(f"DEBUG: Question count result: {question_result}")
        
        # Handle both dictionary and tuple cursor results
        question_count = 0
        if question_result:
            if isinstance(question_result, dict):
                question_count = question_result.get('question_count', 0)
                print(f"DEBUG: Dictionary result, question_count: {question_count}")
            else:
                # For tuple results, question_count is at index 0
                question_count = question_result[0] if len(question_result) > 0 else 0
                print(f"DEBUG: Tuple result, question_count: {question_count}")
        
        # Safely convert question_count to a number for comparison
        question_count_num = 0
        if question_count is not None:
            try:
                # Handle different data types that might come from database
                if isinstance(question_count, (int, float)):
                    question_count_num = float(question_count)
                elif isinstance(question_count, str):
                    question_count_num = float(question_count)
                print(f"DEBUG: Converted question_count_num: {question_count_num}")
                # For other types, keep question_count_num as 0
            except (ValueError, TypeError) as convert_error:
                print(f"DEBUG: Error converting question_count: {convert_error}")
                question_count_num = 0
        
        has_questions = question_count_num > 0
        print(f"DEBUG: has_questions: {has_questions}")
        
        if not has_questions:
            print("DEBUG: No exam questions found for course")
            flash("This course does not have a certification exam", "warning")
            return redirect(url_for('course_detail', course_id=course_id))
        
        # Get exam questions
        print(f"DEBUG: Fetching exam questions for course {course_id}")
        cur.execute("""
            SELECT id, question_text, option_a, option_b, option_c, option_d, correct_option
            FROM questions 
            WHERE course_id = %s 
            ORDER BY id
        """, (course_id,))
        all_exam_questions = cur.fetchall()
        print(f"DEBUG: Found {len(all_exam_questions)} exam questions")
        
        # Convert all exam questions to proper format
        formatted_questions = []
        for i, question in enumerate(all_exam_questions):
            print(f"DEBUG: Processing question {i}: {question}")
            if isinstance(question, dict):
                formatted_questions.append(question)
                print(f"DEBUG: Added dictionary question: {question}")
            else:
                # Convert tuple to dictionary
                formatted_questions.append({
                    'id': question[0],
                    'question_text': question[1],
                    'option_a': question[2],
                    'option_b': question[3],
                    'option_c': question[4],
                    'option_d': question[5],
                    'correct_option': question[6]
                })
                print(f"DEBUG: Added converted tuple question: {formatted_questions[-1]}")
        
        # Randomly select 10 questions (or all if less than 10)
        if len(formatted_questions) > 10:
            exam_questions = random.sample(formatted_questions, 10)
            print(f"DEBUG: Randomly selected 10 questions from {len(formatted_questions)}")
        else:
            exam_questions = formatted_questions
            print(f"DEBUG: Using all {len(formatted_questions)} questions (less than or equal to 10)")
        print(f"DEBUG: Final exam_questions count: {len(exam_questions)}")
        
        # Check if user has already passed the exam
        print(f"DEBUG: Checking if user has passed exam for course {course_id}")
        cur.execute("""
            SELECT passed FROM user_exam_attempts 
            WHERE user_id = %s AND course_id = %s AND passed = TRUE
            ORDER BY exam_date DESC LIMIT 1
        """, (session['user_id'], course_id))
        passed_exam = cur.fetchone()
        print(f"DEBUG: Passed exam result: {passed_exam}")
        
        if passed_exam:
            print("DEBUG: User has already passed the exam")
            flash("You have already passed the certification exam for this course", "info")
            return redirect(url_for('course_detail', course_id=course_id))
        
        # Check number of previous attempts (maximum 3 attempts allowed)
        print(f"DEBUG: Checking number of previous attempts for course {course_id}")
        cur.execute("""
            SELECT COUNT(*) as attempt_count FROM user_exam_attempts 
            WHERE user_id = %s AND course_id = %s
        """, (session['user_id'], course_id))
        attempt_result = cur.fetchone()
        print(f"DEBUG: Attempt result: {attempt_result}")
        
        # Handle both dictionary and tuple cursor results
        attempt_count = 0
        if attempt_result:
            if isinstance(attempt_result, dict):
                attempt_count = attempt_result.get('attempt_count', 0)
                print(f"DEBUG: Dictionary result, attempt_count: {attempt_count}")
            else:
                # For tuple results, attempt_count is at index 0
                attempt_count = attempt_result[0] if len(attempt_result) > 0 else 0
                print(f"DEBUG: Tuple result, attempt_count: {attempt_count}")
        
        # Safely convert attempt_count to a number
        attempt_count_num = 0
        if attempt_count is not None:
            try:
                # Handle different data types that might come from database
                if isinstance(attempt_count, (int, float)):
                    attempt_count_num = int(attempt_count)
                elif isinstance(attempt_count, str):
                    attempt_count_num = int(attempt_count)
                print(f"DEBUG: Converted attempt_count_num: {attempt_count_num}")
                # For other types, keep attempt_count_num as 0
            except (ValueError, TypeError) as convert_error:
                print(f"DEBUG: Error converting attempt_count: {convert_error}")
                attempt_count_num = 0
        
        print(f"DEBUG: Final attempt_count_num: {attempt_count_num}")
        
        # Check if maximum attempts reached
        if attempt_count_num >= 3:
            print("DEBUG: Maximum attempts reached")
            flash("You have reached the maximum number of attempts (3) for this certification exam", "warning")
            return redirect(url_for('course_detail', course_id=course_id))
        
        cur.close()
        
        print(f"DEBUG: Rendering certification_exam_intro.html with course_id={course_id} and {len(exam_questions)} questions")
        return render_template('certification_exam_intro.html', 
                             course=course,
                             course_id=course_id, 
                             exam_questions=exam_questions)
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR loading certification exam intro: {e}")
        print(f"Full traceback: {error_details}")
        flash(f"Error loading certification exam: {str(e)}", "danger")
        return redirect(url_for('course_detail', course_id=course_id))

# Certification exam route
@app.route('/exam/<int:course_id>')
def certification_exam(course_id):
    try:
        print(f"=== DEBUG: Certification exam route called with course_id={course_id} ===")
        
        if 'user_id' not in session:
            print("DEBUG: User not logged in")
            flash("Please login to access the certification exam", "warning")
            return redirect(url_for('login'))
        
        print(f"DEBUG: User ID from session: {session['user_id']}")
        
        connection = mysql.get_connection()
        if connection is None:
            print("DEBUG: Database connection is None")
            flash("❌ Database connection not available", "danger")
            return redirect(url_for('dashboard'))
        
        print("DEBUG: Database connection successful")
        cur = connection.cursor(dictionary=True)
        
        # Check if user is enrolled in the course
        print(f"DEBUG: Checking enrollment for user {session['user_id']} in course {course_id}")
        cur.execute("SELECT * FROM user_course WHERE user_id = %s AND course_id = %s", 
                    (session['user_id'], course_id))
        enrollment = cur.fetchone()
        print(f"DEBUG: Enrollment result: {enrollment}")
        
        if not enrollment:
            print("DEBUG: User not enrolled in course")
            flash("You must be enrolled in this course to take the certification exam", "warning")
            return redirect(url_for('course_detail', course_id=course_id))
        
        # Check if course has exam questions
        print(f"DEBUG: Checking for exam questions in course {course_id}")
        cur.execute("SELECT COUNT(*) as question_count FROM questions WHERE course_id = %s", (course_id,))
        question_result = cur.fetchone()
        print(f"DEBUG: Question count result: {question_result}")
        
        # Handle both dictionary and tuple cursor results
        question_count = 0
        if question_result:
            if isinstance(question_result, dict):
                question_count = question_result.get('question_count', 0)
                print(f"DEBUG: Dictionary result, question_count: {question_count}")
            else:
                # For tuple results, question_count is at index 0
                question_count = question_result[0] if len(question_result) > 0 else 0
                print(f"DEBUG: Tuple result, question_count: {question_count}")
        
        # Safely convert question_count to a number for comparison
        question_count_num = 0
        if question_count is not None:
            try:
                # Handle different data types that might come from database
                if isinstance(question_count, (int, float)):
                    question_count_num = float(question_count)
                elif isinstance(question_count, str):
                    question_count_num = float(question_count)
                print(f"DEBUG: Converted question_count_num: {question_count_num}")
                # For other types, keep question_count_num as 0
            except (ValueError, TypeError) as convert_error:
                print(f"DEBUG: Error converting question_count: {convert_error}")
                question_count_num = 0
        
        has_questions = question_count_num > 0
        print(f"DEBUG: has_questions: {has_questions}")
        
        if not has_questions:
            print("DEBUG: No exam questions found for course")
            flash("This course does not have a certification exam", "warning")
            return redirect(url_for('course_detail', course_id=course_id))
        
        # Get exam questions
        print(f"DEBUG: Fetching exam questions for course {course_id}")
        cur.execute("""
            SELECT id, question_text, option_a, option_b, option_c, option_d, correct_option
            FROM questions 
            WHERE course_id = %s 
            ORDER BY id
        """, (course_id,))
        all_exam_questions = cur.fetchall()
        print(f"DEBUG: Found {len(all_exam_questions)} exam questions")
        
        # Convert all exam questions to proper format
        formatted_questions = []
        for i, question in enumerate(all_exam_questions):
            print(f"DEBUG: Processing question {i}: {question}")
            if isinstance(question, dict):
                formatted_questions.append(question)
                print(f"DEBUG: Added dictionary question: {question}")
            else:
                # Convert tuple to dictionary
                formatted_questions.append({
                    'id': question[0],
                    'question_text': question[1],
                    'option_a': question[2],
                    'option_b': question[3],
                    'option_c': question[4],
                    'option_d': question[5],
                    'correct_option': question[6]
                })
                print(f"DEBUG: Added converted tuple question: {formatted_questions[-1]}")
        
        # Randomly select 10 questions (or all if less than 10)
        if len(formatted_questions) > 10:
            exam_questions = random.sample(formatted_questions, 10)
            print(f"DEBUG: Randomly selected 10 questions from {len(formatted_questions)}")
        else:
            exam_questions = formatted_questions
            print(f"DEBUG: Using all {len(formatted_questions)} questions (less than or equal to 10)")
        print(f"DEBUG: Final exam_questions count: {len(exam_questions)}")
        
        # Check if user has already passed the exam
        print(f"DEBUG: Checking if user has passed exam for course {course_id}")
        cur.execute("""
            SELECT passed FROM user_exam_attempts 
            WHERE user_id = %s AND course_id = %s AND passed = TRUE
            ORDER BY exam_date DESC LIMIT 1
        """, (session['user_id'], course_id))
        passed_exam = cur.fetchone()
        print(f"DEBUG: Passed exam result: {passed_exam}")
        
        if passed_exam:
            print("DEBUG: User has already passed the exam")
            flash("You have already passed the certification exam for this course", "info")
            return redirect(url_for('course_detail', course_id=course_id))
        
        # Check number of previous attempts (maximum 3 attempts allowed)
        print(f"DEBUG: Checking number of previous attempts for course {course_id}")
        cur.execute("""
            SELECT COUNT(*) as attempt_count FROM user_exam_attempts 
            WHERE user_id = %s AND course_id = %s
        """, (session['user_id'], course_id))
        attempt_result = cur.fetchone()
        print(f"DEBUG: Attempt result: {attempt_result}")
        
        # Handle both dictionary and tuple cursor results
        attempt_count = 0
        if attempt_result:
            if isinstance(attempt_result, dict):
                attempt_count = attempt_result.get('attempt_count', 0)
                print(f"DEBUG: Dictionary result, attempt_count: {attempt_count}")
            else:
                # For tuple results, attempt_count is at index 0
                attempt_count = attempt_result[0] if len(attempt_result) > 0 else 0
                print(f"DEBUG: Tuple result, attempt_count: {attempt_count}")
        
        # Safely convert attempt_count to a number
        attempt_count_num = 0
        if attempt_count is not None:
            try:
                # Handle different data types that might come from database
                if isinstance(attempt_count, (int, float)):
                    attempt_count_num = int(attempt_count)
                elif isinstance(attempt_count, str):
                    attempt_count_num = int(attempt_count)
                print(f"DEBUG: Converted attempt_count_num: {attempt_count_num}")
                # For other types, keep attempt_count_num as 0
            except (ValueError, TypeError) as convert_error:
                print(f"DEBUG: Error converting attempt_count: {convert_error}")
                attempt_count_num = 0
        
        print(f"DEBUG: Final attempt_count_num: {attempt_count_num}")
        
        # Check if maximum attempts reached
        if attempt_count_num >= 3:
            print("DEBUG: Maximum attempts reached")
            flash("You have reached the maximum number of attempts (3) for this certification exam", "warning")
            return redirect(url_for('course_detail', course_id=course_id))
        
        cur.close()
        
        print(f"DEBUG: Rendering certification_exam.html with course_id={course_id} and {len(exam_questions)} questions")
        return render_template('certification_exam.html', 
                             course_id=course_id, 
                             exam_questions=exam_questions)
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR loading certification exam: {e}")
        print(f"Full traceback: {error_details}")
        flash(f"Error loading certification exam: {str(e)}", "danger")
        return redirect(url_for('course_detail', course_id=course_id))

# Exam submit route
@app.route('/exam/submit', methods=['POST'])
def submit_exam():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'})
        
        data = request.get_json()
        course_id = data.get('course_id')
        user_answers = data.get('answers', {})
        time_taken = data.get('time_taken', 0)
        
        connection = mysql.get_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection not available'})
        
        cur = connection.cursor(dictionary=True)
        
        # Get exam questions with correct answers
        cur.execute("""
            SELECT id, correct_option 
            FROM questions 
            WHERE course_id = %s
        """, (course_id,))
        questions = cur.fetchall()
        
        # Calculate score
        correct_count = 0
        total_questions = len(questions)
        
        for question in questions:
            # Handle both dictionary and tuple cursor results
            if isinstance(question, dict):
                question_id = str(question['id'])
                correct_answer = question['correct_option']
            else:
                # For tuple results, id is at index 0, correct_option is at index 1
                question_id = str(question[0])
                correct_answer = question[1]
            user_answer = user_answers.get(question_id)
            
            # Ensure consistent data types for comparison
            user_answer_str = str(user_answer) if user_answer is not None else ''
            correct_answer_str = str(correct_answer) if correct_answer is not None else ''
            
            print(f"DEBUG: Checking question {question_id}, user answer: '{user_answer_str}' (type: {type(user_answer_str)}), correct: '{correct_answer_str}' (type: {type(correct_answer_str)})")
            print(f"DEBUG: Comparison result: {user_answer_str == correct_answer_str}")
            if user_answer_str == correct_answer_str:
                correct_count += 1
                print(f"DEBUG: Correct answer found, count now: {correct_count}")
            else:
                print(f"DEBUG: Incorrect answer for question {question_id}")
        
        # Calculate score - each question worth 10 marks
        score = 0
        if total_questions > 0:
            score = round(correct_count * 10, 2)  # Each question worth 10 marks
        
        print(f"DEBUG: Final score calculation - correct: {correct_count}, total: {total_questions}, score: {score}")
        print(f"DEBUG: Score type before conversion: {type(score)}, value: {score}")
        
        # Determine pass/fail (60% required to pass)
        passed = False
        if total_questions > 0:
            percentage = (correct_count / total_questions) * 100
            passed = percentage >= 60
        
        # Get next attempt number
        cur.execute("""
            SELECT COALESCE(MAX(attempt_number), 0) + 1 as next_attempt
            FROM user_exam_attempts 
            WHERE user_id = %s AND course_id = %s
        """, (session['user_id'], course_id))
        attempt_result = cur.fetchone()
        # Handle both dictionary and tuple cursor results
        attempt_number = 1
        if attempt_result:
            if isinstance(attempt_result, dict):
                attempt_number = attempt_result.get('next_attempt', 1)
            else:
                # For tuple results, next_attempt is at index 0
                attempt_number = attempt_result[0] if len(attempt_result) > 0 else 1
        
        # Save exam attempt
        print(f"DEBUG: Inserting exam attempt - score: {score} (type: {type(score)}), converted: {float(str(score)) if score is not None else 0.0}")
        cur.execute("""
            INSERT INTO user_exam_attempts 
            (user_id, course_id, score, passed, time_taken, attempt_number, exam_date)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (session['user_id'], course_id, float(str(score)) if score is not None else 0.0, bool(passed), int(str(time_taken)) if time_taken is not None else 0, int(str(attempt_number)) if attempt_number is not None else 1))
        
        connection.commit()
        
        # If passed, mark course as completed if not already
        if passed:
            cur.execute("""
                UPDATE user_course 
                SET completed_at = NOW(), progress = 100
                WHERE user_id = %s AND course_id = %s AND completed_at IS NULL
            """, (session['user_id'], course_id))
            connection.commit()
            
            # Generate exam certificate
            try:
                # Use the dedicated exam certificate service
                from services.exam_certificate_service import generate_exam_certificate
                from services.certificate_service import save_certificate_record
                from services.email_service import send_certificate_email                
                # Get user and course info
                cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
                user = cur.fetchone()
                
                cur.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
                course = cur.fetchone()
                
                # First save certificate record to get certificate_id
                cert_id = save_certificate_record(
                    user_id=session['user_id'],
                    course_id=course_id,
                    certificate_path="",  # Will be updated after generation
                    mysql=mysql,
                    certificate_type='exam'  # Specify this is an exam certificate
                )
                
                certificate_path = None
                if cert_id:
                    # Generate certificate with the certificate_id
                    certificate_path = generate_exam_certificate(
                        user_name=user['name'] if isinstance(user, dict) else user[1] if user else 'Unknown User',
                        course_title=course['title'] if isinstance(course, dict) else course[1] if course else 'Unknown Course',
                        completion_date=datetime.now(),
                        certificate_id=cert_id  # Pass the certificate_id
                    )                    
                    # Update certificate path in database
                    try:
                        cur.execute("""
                            UPDATE certificates 
                            SET certificate_path = %s 
                            WHERE id = %s
                        """, (certificate_path, cert_id))
                        connection.commit()
                        print(f"Certificate path updated in database for cert ID: {cert_id}")
                    except Exception as update_error:
                        print(f"Error updating certificate path: {update_error}")
                
                # Send email with certificate (only if certificate was generated)
                if certificate_path:
                    try:
                        send_certificate_email(
                            user_email=user['email'] if isinstance(user, dict) else user[2] if user and len(user) > 2 else '',
                            user_name=user['name'] if isinstance(user, dict) else user[1] if user and len(user) > 1 else 'Unknown User',
                            course_title=course['title'] if isinstance(course, dict) else course[1] if course and len(course) > 1 else 'Unknown Course',
                            certificate_path=certificate_path,
                        )
                    except Exception as email_error:
                        print(f"Error sending certificate email: {email_error}")
                
            except Exception as cert_error:
                print(f"Error generating certificate: {cert_error}")
        
        cur.close()
        
        return jsonify({
            'success': True,
            'message': 'Exam submitted successfully',
            'score': score,
            'passed': passed,
            'total_questions': total_questions,
            'correct_answers': correct_count,
            'status': 'passed' if passed else 'failed'
        })
        
    except Exception as e:
        print(f"Error submitting exam: {e}")
        return jsonify({'success': False, 'message': 'Error submitting exam'})

# Save partial exam progress (for tab switching detection)
@app.route('/exam/save_partial', methods=['POST'])
def save_partial_exam_progress():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'})
        
        data = request.get_json()
        course_id = data.get('course_id')
        user_answers = data.get('answers', {})
        status = data.get('status', 'in_progress')
        time_taken = data.get('time_taken', 0)
        
        connection = mysql.get_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection not available'})
        
        cur = connection.cursor(dictionary=True)
        
        # Check number of previous attempts (maximum 3 attempts allowed)
        print(f"DEBUG: Checking number of previous attempts for course {course_id}")
        cur.execute("""
            SELECT COUNT(*) as attempt_count FROM user_exam_attempts 
            WHERE user_id = %s AND course_id = %s
        """, (session['user_id'], course_id))
        attempt_result = cur.fetchone()
        print(f"DEBUG: Attempt result: {attempt_result}")
        
        # Handle both dictionary and tuple cursor results
        attempt_count = 0
        if attempt_result:
            if isinstance(attempt_result, dict):
                attempt_count = attempt_result.get('attempt_count', 0)
                print(f"DEBUG: Dictionary result, attempt_count: {attempt_count}")
            else:
                # For tuple results, attempt_count is at index 0
                attempt_count = attempt_result[0] if len(attempt_result) > 0 else 0
                print(f"DEBUG: Tuple result, attempt_count: {attempt_count}")
        
        # Safely convert attempt_count to a number
        attempt_count_num = 0
        if attempt_count is not None:
            try:
                # Handle different data types that might come from database
                if isinstance(attempt_count, (int, float)):
                    attempt_count_num = int(attempt_count)
                elif isinstance(attempt_count, str):
                    attempt_count_num = int(attempt_count)
                print(f"DEBUG: Converted attempt_count_num: {attempt_count_num}")
                # For other types, keep attempt_count_num as 0
            except (ValueError, TypeError) as convert_error:
                print(f"DEBUG: Error converting attempt_count: {convert_error}")
                attempt_count_num = 0
        
        print(f"DEBUG: Final attempt_count_num: {attempt_count_num}")
        
        # Check if maximum attempts reached
        if attempt_count_num >= 3:
            print("DEBUG: Maximum attempts reached")
            return jsonify({'success': False, 'message': 'You have reached the maximum number of attempts (3) for this certification exam'})
        
        # Get exam questions with correct answers
        cur.execute("""
            SELECT id, correct_option 
            FROM questions 
            WHERE course_id = %s
        """, (course_id,))
        questions = cur.fetchall()
        
        # Calculate score based on provided answers
        correct_count = 0
        total_answered = len(user_answers)
        total_questions = len(questions)
        
        print(f"DEBUG: Calculating score for {total_questions} questions, user answered {total_answered}")
        print(f"DEBUG: User answers received: {user_answers}")
        
        for question in questions:
            # Handle both dictionary and tuple cursor results
            if isinstance(question, dict):
                question_id = str(question['id'])
                correct_answer = question['correct_option']
            else:
                # For tuple results, id is at index 0, correct_option is at index 1
                question_id = str(question[0])
                correct_answer = question[1]
            user_answer = user_answers.get(question_id)
            
            # Ensure consistent data types for comparison
            user_answer_str = str(user_answer) if user_answer is not None else ''
            correct_answer_str = str(correct_answer) if correct_answer is not None else ''
            
            print(f"DEBUG: Checking question {question_id}, user answer: '{user_answer_str}' (type: {type(user_answer_str)}), correct: '{correct_answer_str}' (type: {type(correct_answer_str)})")
            print(f"DEBUG: Comparison result: {user_answer_str == correct_answer_str}")
            if user_answer_str == correct_answer_str:
                correct_count += 1
                print(f"DEBUG: Correct answer found, count now: {correct_count}")
            else:
                print(f"DEBUG: Incorrect answer for question {question_id}")
        
        # Calculate score - each question worth 10 marks
        score = 0
        if total_questions > 0:
            score = round(correct_count * 10, 2)  # Each question worth 10 marks
        
        print(f"DEBUG: Final score calculation - correct: {correct_count}, total: {total_questions}, score: {score}")
        print(f"DEBUG: Score type before conversion: {type(score)}, value: {score}")
        
        # Determine pass/fail (60% required to pass)
        passed = False
        if total_questions > 0:
            percentage = (correct_count / total_questions) * 100
            passed = percentage >= 60
        
        # Get next attempt number
        cur.execute("""
            SELECT COALESCE(MAX(attempt_number), 0) + 1 as next_attempt
            FROM user_exam_attempts 
            WHERE user_id = %s AND course_id = %s
        """, (session['user_id'], course_id))
        attempt_result = cur.fetchone()
        # Handle both dictionary and tuple cursor results
        attempt_number = 1
        if attempt_result:
            if isinstance(attempt_result, dict):
                attempt_number = attempt_result.get('next_attempt', 1)
            else:
                # For tuple results, next_attempt is at index 0
                attempt_number = attempt_result[0] if len(attempt_result) > 0 else 1
        
        # Check if there's an existing failed attempt that we should update instead of creating a new one
        # This is for the case where a user fails an exam and then switches tabs
        existing_attempt_id = None
        if status == "failed_due_to_tab_switch":
            print(f"DEBUG: Checking for existing failed attempts for user {session['user_id']} course {course_id}")
            cur.execute("""
                SELECT id FROM user_exam_attempts 
                WHERE user_id = %s AND course_id = %s AND passed = 0 AND status != 'failed_due_to_tab_switch'
                ORDER BY exam_date DESC LIMIT 1
            """, (session['user_id'], course_id))
            existing_attempt = cur.fetchone()
            if existing_attempt:
                if isinstance(existing_attempt, dict):
                    existing_attempt_id = existing_attempt.get('id')
                else:
                    existing_attempt_id = existing_attempt[0] if len(existing_attempt) > 0 else None
                print(f"DEBUG: Found existing failed attempt to update: {existing_attempt_id}")
            else:
                print("DEBUG: No existing failed attempt found")
        
        if existing_attempt_id:
            # Update existing failed attempt instead of creating a new one
            print(f"DEBUG: Updating existing attempt {existing_attempt_id} with tab switch status")
            print(f"DEBUG: Updating attempt - score: {score} (type: {type(score)}), converted: {float(str(score)) if score is not None else 0.0}")
            
            # Get the existing attempt number
            cur.execute("SELECT attempt_number FROM user_exam_attempts WHERE id = %s", (int(str(existing_attempt_id)) if existing_attempt_id is not None else 0,))
            attempt_record = cur.fetchone()
            existing_attempt_number = 1
            if attempt_record:
                if isinstance(attempt_record, dict):
                    existing_attempt_number = attempt_record.get('attempt_number', 1)
                else:
                    existing_attempt_number = attempt_record[0] if len(attempt_record) > 0 else 1
            
            cur.execute("""
                UPDATE user_exam_attempts 
                SET score = %s, passed = %s, time_taken = %s, attempt_number = %s, status = %s, exam_date = NOW()
                WHERE id = %s
            """, (float(str(score)) if score is not None else 0.0, bool(passed), int(str(time_taken)) if time_taken is not None else 0, int(str(existing_attempt_number)) if existing_attempt_number is not None else 1, status, int(str(existing_attempt_id)) if existing_attempt_id is not None else 0))
        else:
            # Save new exam attempt with status
            print(f"DEBUG: Creating new attempt with attempt_number: {attempt_number}")
            print(f"DEBUG: Inserting new attempt - score: {score} (type: {type(score)}), converted: {float(str(score)) if score is not None else 0.0}")
            cur.execute("""
                INSERT INTO user_exam_attempts 
                (user_id, course_id, score, passed, time_taken, attempt_number, exam_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
            """, (session['user_id'], course_id, float(str(score)) if score is not None else 0.0, bool(passed), int(str(time_taken)) if time_taken is not None else 0, int(str(attempt_number)) if attempt_number is not None else 1, status))
        
        connection.commit()
        cur.close()
        
        # Determine the attempt ID to return (existing ID if updated, new ID if inserted)
        attempt_id_to_return = existing_attempt_id if existing_attempt_id else (cur.lastrowid if hasattr(cur, 'lastrowid') else 0)
        
        # Return appropriate response based on status
        if status == "failed_due_to_tab_switch":
            return jsonify({
                'success': False,
                'message': 'Exam terminated due to tab switching',
                'attempt_id': attempt_id_to_return,
                'status': 'failed_due_to_tab_switch'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Progress saved',
                'attempt_id': attempt_id_to_return,
                'status': 'in_progress'
            })
            
    except Exception as e:
        print(f"Error saving partial exam progress: {e}")
        return jsonify({'success': False, 'message': 'Error saving exam progress'})

# Run the app

# Topic Quiz Routes

@app.route('/module/<int:module_id>/quiz')
def module_quiz(module_id):
    """Display the topic quiz for a completed module."""
    if 'user_id' not in session:
        flash("Please login to access the quiz", "warning")
        return redirect(url_for('login'))
    
    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("Database connection not available", "danger")
            return redirect(url_for('dashboard'))
        
        # Get module details
        cur = connection.cursor(dictionary=True)
        cur.execute("""
            SELECT cm.*, c.id as course_id, c.title as course_title
            FROM course_modules cm
            JOIN courses c ON cm.course_id = c.id
            WHERE cm.id = %s
        """, (module_id,))
        
        module = cur.fetchone()
        cur.close()
        
        if not module:
            flash("Module not found", "danger")
            return redirect(url_for('courses'))
        
        # Check if user has access to this course
        cur = connection.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM user_course 
            WHERE user_id = %s AND course_id = %s
        """, (session['user_id'], module['course_id']))
        
        result = cur.fetchone()
        has_access = result[0] if isinstance(result, tuple) else result.get('COUNT(*)', 0)
        cur.close()
        
        if not has_access:
            flash("You don't have access to this module", "danger")
            return redirect(url_for('courses'))
        
        # Check if user has completed this module
        cur = connection.cursor()
        cur.execute("""
            SELECT is_completed FROM user_module_progress 
            WHERE user_id = %s AND module_id = %s
        """, (session['user_id'], module_id))
        
        result = cur.fetchone()
        is_module_completed = False
        if result:
            is_module_completed = result[0] if isinstance(result, tuple) else result.get('is_completed', False)
        cur.close()
        
        if not is_module_completed:
            flash("Please complete the module before taking the quiz", "warning")
            return redirect(url_for('module_video', course_id=module['course_id'], module_id=module_id))
        
        # Check if user has already completed the quiz
        from services.topic_quiz_service import has_user_completed_topic_quiz
        if has_user_completed_topic_quiz(session['user_id'], module_id, mysql):
            flash("You have already completed the quiz for this module", "info")
            return redirect(url_for('module_video', course_id=module['course_id'], module_id=module_id))
        
        # Get 5 random questions for this module
        from services.topic_quiz_service import get_random_topic_questions
        questions = get_random_topic_questions(module_id, 5, mysql)
        
        if not questions:
            flash("No quiz questions available for this module", "warning")
            return redirect(url_for('module_video', course_id=module['course_id'], module_id=module_id))
        
        return render_template('topic_quiz.html', 
                             module=module, 
                             questions=questions)
        
    except Exception as e:
        print(f"Error loading module quiz: {e}")
        flash("Error loading quiz", "danger")
        return redirect(url_for('module_video', course_id=module['course_id'], module_id=module_id))


@app.route('/module/<int:module_id>/quiz/question/<int:question_index>', methods=['GET', 'POST'])
def module_quiz_question(module_id, question_index):
    """Display a single question in the topic quiz."""
    if 'user_id' not in session:
        flash("Please login to access the quiz", "warning")
        return redirect(url_for('login'))
    
    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("Database connection not available", "danger")
            return redirect(url_for('dashboard'))
        
        # Get module details
        cur = connection.cursor(dictionary=True)
        cur.execute("""
            SELECT cm.*, c.id as course_id, c.title as course_title
            FROM course_modules cm
            JOIN courses c ON cm.course_id = c.id
            WHERE cm.id = %s
        """, (module_id,))
        
        module = cur.fetchone()
        cur.close()
        
        if not module:
            flash("Module not found", "danger")
            return redirect(url_for('courses'))
        
        # Check if user has access to this course
        cur = connection.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM user_course 
            WHERE user_id = %s AND course_id = %s
        """, (session['user_id'], module['course_id']))
        
        result = cur.fetchone()
        has_access = result[0] if isinstance(result, tuple) else result.get('COUNT(*)', 0)
        cur.close()
        
        if not has_access:
            flash("You don't have access to this module", "danger")
            return redirect(url_for('courses'))
        
        # Check if user has completed this module
        cur = connection.cursor()
        cur.execute("""
            SELECT is_completed FROM user_module_progress 
            WHERE user_id = %s AND module_id = %s
        """, (session['user_id'], module_id))
        
        result = cur.fetchone()
        is_module_completed = False
        if result:
            is_module_completed = result[0] if isinstance(result, tuple) else result.get('is_completed', False)
        cur.close()
        
        if not is_module_completed:
            flash("Please complete the module before taking the quiz", "warning")
            return redirect(url_for('module_video', course_id=module['course_id'], module_id=module_id))
        
        # Check if user has already completed the quiz
        from services.topic_quiz_service import has_user_completed_topic_quiz
        if has_user_completed_topic_quiz(session['user_id'], module_id, mysql):
            flash("You have already completed the quiz for this module", "info")
            return redirect(url_for('module_video', course_id=module['course_id'], module_id=module_id))
        
        # Get 5 random questions for this module
        from services.topic_quiz_service import get_random_topic_questions
        questions = get_random_topic_questions(module_id, 5, mysql)
        
        if not questions:
            flash("No quiz questions available for this module", "warning")
            return redirect(url_for('module_video', course_id=module['course_id'], module_id=module_id))
        
        # Validate question index
        if question_index < 1 or question_index > len(questions):
            flash("Invalid question index", "danger")
            return redirect(url_for('module_quiz', module_id=module_id))
        
        # Get the specific question
        question = questions[question_index - 1]
        
        return render_template('topic_quiz_question.html', 
                             module=module, 
                             question=question,
                             question_index=question_index,
                             total_questions=len(questions))
        
    except Exception as e:
        print(f"Error loading module quiz question: {e}")
        flash("Error loading quiz question", "danger")
        return redirect(url_for('module_video', course_id=module['course_id'], module_id=module_id))


@app.route('/module/<int:module_id>/quiz/submit', methods=['POST'])
def submit_module_quiz(module_id):
    """Submit the topic quiz answers and show results."""
    if 'user_id' not in session:
        flash("Please login to submit the quiz", "warning")
        return redirect(url_for('login'))
    
    try:
        connection = mysql.get_connection()
        if connection is None:
            flash("Database connection not available", "danger")
            return redirect(url_for('dashboard'))
        
        # Get module details
        cur = connection.cursor(dictionary=True)
        cur.execute("""

            SELECT cm.*, c.id as course_id, c.title as course_title
            FROM course_modules cm
            JOIN courses c ON cm.course_id = c.id
            WHERE cm.id = %s
        """, (module_id,))
        
        module = cur.fetchone()
        cur.close()
        
        if not module:
            flash("Module not found", "danger")
            return redirect(url_for('courses'))
        
        # Check if user has access to this course
        cur = connection.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM user_course 
            WHERE user_id = %s AND course_id = %s
        """, (session['user_id'], module['course_id']))
        
        result = cur.fetchone()
        has_access = result[0] if isinstance(result, tuple) else result.get('COUNT(*)', 0)
        cur.close()
        
        if not has_access:
            flash("You don't have access to this module", "danger")
            return redirect(url_for('courses'))
        
        # Check if user has completed this module
        cur = connection.cursor()
        cur.execute("""
            SELECT is_completed FROM user_module_progress 
            WHERE user_id = %s AND module_id = %s
        """, (session['user_id'], module_id))
        
        result = cur.fetchone()
        is_module_completed = False
        if result:
            is_module_completed = result[0] if isinstance(result, tuple) else result.get('is_completed', False)
        cur.close()
        
        print(f"[MODULE QUIZ] Module completion status: is_module_completed={is_module_completed}, user_id={session['user_id']}, module_id={module_id}")
        
        if not is_module_completed:
            flash("Please complete the module before taking the quiz", "warning")
            return redirect(url_for('module_video', course_id=module['course_id'], module_id=module_id))
        
        # Get the submitted answers
        answers = {}
        for key, value in request.form.items():
            if key.startswith('question_'):
                question_id = int(key.replace('question_', ''))
                answers[question_id] = value
        
        # Save the quiz attempt
        from services.topic_quiz_service import save_topic_quiz_attempt
        print(f"[QUIZ SUBMISSION] Saving quiz attempt for user_id={session['user_id']}, module_id={module_id}")
        attempt_id = save_topic_quiz_attempt(
            session['user_id'], 
            module_id, 
            module['course_id'], 
            answers, 
            mysql
        )
        print(f"[QUIZ SUBMISSION] Quiz attempt saved with attempt_id: {attempt_id}")
        
        if not attempt_id:
            flash("Error saving quiz results", "danger")
            return redirect(url_for('module_quiz', module_id=module_id))
        
        # Get the results
        from services.topic_quiz_service import get_topic_quiz_results
        results = get_topic_quiz_results(attempt_id, mysql)
        
        # Unlock the next module
        from services.topic_quiz_service import unlock_next_module
        unlock_next_module(session['user_id'], module['course_id'], module_id, mysql)
        
        # Check if this is the last module in the course
        cur = connection.cursor()
        
        # Get the current module's order index
        cur.execute("SELECT order_index FROM course_modules WHERE id = %s", (module_id,))
        current_module = cur.fetchone()
        current_order = current_module[0] if current_module else 0
        
        # Get the maximum order index in the course
        cur.execute("SELECT MAX(order_index) FROM course_modules WHERE course_id = %s", (module['course_id'],))
        max_order_result = cur.fetchone()
        max_order = max_order_result[0] if max_order_result else 0
        
        # Check if this is the last module
        is_last_module = (current_order == max_order) and max_order > 0
        
        # If this is the last module, recalculate course progress to ensure course completion
        if is_last_module:
            print(f"[QUIZ SUBMISSION] Last module quiz completed, recalculating course progress...")
            from data import calculate_course_progress
            calculate_course_progress(session['user_id'], module['course_id'], mysql)
        
        # Get the next module ID if this is not the last module
        next_module_id = None
        if not is_last_module:
            cur.execute("""
                SELECT id FROM course_modules 
                WHERE course_id = %s AND order_index = %s
            """, (module['course_id'], current_order + 1))
            next_module_result = cur.fetchone()
            next_module_id = next_module_result[0] if next_module_result else None
        
        cur.close()
        connection.close()
        
        return render_template('topic_quiz_results.html', 
                             module=module, 
                             results=results,
                             attempt_id=attempt_id,
                             is_last_module=is_last_module,
                             next_module_id=next_module_id)
        
    except Exception as e:
        print(f"Error submitting module quiz: {e}")
        # Close connection if it exists
        if 'connection' in locals():
            try:
                connection.close()
            except:
                pass
        flash("Error submitting quiz", "danger")
        return redirect(url_for('module_quiz', module_id=module_id))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files from the attached_assets/videos directory."""
    try:
        # Normalize the filename to prevent directory traversal attacks
        filename = os.path.basename(filename)
        
        # Try to serve from attached_assets/videos directory (new location)
        file_path = os.path.join('attached_assets', 'videos', filename)
        if os.path.exists(file_path):
            return send_file(file_path)
            
        # Try to serve from uploads directory (legacy location)
        file_path = os.path.join('uploads', filename)
        if os.path.exists(file_path):
            return send_file(file_path)
            
        # Try just the filename in uploads directory (for legacy data)
        file_path = os.path.join('uploads', filename.split('/')[-1])
        if os.path.exists(file_path):
            return send_file(file_path)
            
        # File not found
        flash("File not found", "danger")
        return redirect(url_for('index'))
    except FileNotFoundError:
        flash("File not found", "danger")
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error serving file: {e}")
        flash("Error serving file", "danger")
        return redirect(url_for('index')) 



# Run the app
if __name__ == '__main__':
    print("🚀 Starting Flask app...")
    print(f"📋 Registered routes: {[rule.rule for rule in app.url_map.iter_rules()]}")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False, threaded=True)
