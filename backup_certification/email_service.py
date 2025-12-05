import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Email Configuration - Using environment variables for security
EMAIL_HOST = os.environ.get('EMAIL_HOST') or 'smtp.gmail.com'
EMAIL_PORT = int(os.environ.get('EMAIL_PORT') or 587)
EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME') or 'premkumar18082002@gmail.com'
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD') or 'gyqp zdee gkxq cjoa'

def send_certificate_email(user_name, user_email, course_title, certificate_path, certificate_type='course'):
    """
    Send certificate email to user.
    
    Args:
        user_name (str): Name of the user
        user_email (str): Email address of the user
        course_title (str): Title of the completed course
        certificate_path (str): Path to the certificate file
        certificate_type (str): Type of certificate ('course' or 'exam')
    """
    try:
        # Validate inputs
        if not user_name or not user_email or not course_title:
            print("Missing required email parameters")
            return False
            
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USERNAME
        msg['To'] = str(user_email)
        subject_prefix = "Certification Exam" if certificate_type == 'exam' else "Certificate of Completion"
        msg['Subject'] = f"{subject_prefix} - {str(course_title)}"
        
        # Email body
        certificate_text = "Certification Exam" if certificate_type == 'exam' else "course"
        completion_text = "passing the certification exam for" if certificate_type == 'exam' else "completing the course"
        badge_text = "EXAM PASSED" if certificate_type == 'exam' else "COURSE COMPLETED"
        badge_color = "#9b59b6" if certificate_type == 'exam' else "#27ae60"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #2c3e50; margin-bottom: 10px;">🎉 Congratulations, {str(user_name)}!</h2>
                    <p style="color: #7f8c8d; margin: 0;">DigiDARA Learning Management System</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                    <p>Congratulations on successfully {completion_text}:</p>
                    <h3 style="color: #2c3e50; text-align: center;">{str(course_title)}</h3>
                    
                    <p>Your {certificate_text} certificate is attached to this email.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="background-color: {badge_color}; color: white; padding: 12px 24px; border-radius: 6px; display: inline-block;">
                            <strong>{badge_text}</strong>
                        </div>
                    </div>
                    
                    <p>We're proud of your achievement and hope you continue your learning journey with us!</p>
                </div>
                
                <div style="text-align: center; color: #7f8c8d; font-size: 14px;">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; 2025 DigiDARA Technologies Private Limited LMS. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach certificate if it exists
        certificate_path_str = str(certificate_path)
        if certificate_path_str and os.path.exists(certificate_path_str):
            with open(certificate_path_str, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                certificate_prefix = "exam_certificate" if certificate_type == 'exam' else "certificate"
                attach.add_header('Content-Disposition', 'attachment', filename=f"{certificate_prefix}_{str(course_title).replace(' ', '_')}.pdf")
                msg.attach(attach)
        else:
            print(f"Certificate file not found at: {certificate_path_str}")
        
        # Create SMTP session
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()  # Enable TLS
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_USERNAME, str(user_email), text)
        server.quit()
        
        print(f"✅ Certificate email sent successfully to {str(user_email)}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send certificate email to {str(user_email) if user_email else 'unknown'}: {e}")
        import traceback
        traceback.print_exc()
        return False