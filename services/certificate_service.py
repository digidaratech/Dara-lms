"""
Certificate Generation Service for LMS
This module handles the creation and delivery of course completion certificates.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import mysql.connector as mysql_connector

# Certificate configuration
CERTIFICATE_PREFIX = "DD"  # Company code prefix for certificate IDs
EXAM_CERTIFICATE_PREFIX = "DDCE"  # Company code prefix for exam certificate IDs

# Try to find template in multiple formats (PNG or JPG)
def get_template_path():
    """Find certificate template in supported formats."""
    base_path = os.path.join('attached_assets', 'templates', 'certificate_template')
    for ext in ['.png', '.jpg', '.jpeg']:
        path = base_path + ext
        if os.path.exists(path):
            return path
    # Fallback to PNG path (will trigger fallback certificate if not found)
    return os.path.join('attached_assets', 'templates', 'certificate_template.png')

def get_exam_template_path():
    """Find exam certificate template in supported formats."""
    base_path = os.path.join('attached_assets', 'templates', 'exam_certificate_template')
    for ext in ['.png', '.jpg', '.jpeg']:
        path = base_path + ext
        if os.path.exists(path):
            return path
    # Fallback to PNG path (will trigger fallback certificate if not found)
    return os.path.join('attached_assets', 'templates', 'exam_certificate_template.png')

TEMPLATE_PATH = get_template_path()
EXAM_TEMPLATE_PATH = get_exam_template_path()

def get_course_description(course_title):
    """
    Get course-specific description based on course title.
    
    Args:
        course_title (str): Title of the course
    
    Returns:
        str: Description text for the course
    """
    # Normalize course title for matching (case-insensitive, strip whitespace)
    course_key = course_title.lower().strip()
    
    # Course description mapping
    descriptions = {
        'python': "The Course covered Python fundamentals, data structures, and object-oriented programming, with real-world projects demonstrating automation and analysis.",
        'python programming': "The Course covered Python fundamentals, data structures, and object-oriented programming, with real-world projects demonstrating automation and analysis.",
        'web development': "The Course focused on full-stack web technologies including HTML, CSS, JavaScript, and frameworks for building responsive applications.",
        'data analytics': "The Course covered essential tools such as Python, MySQL, and Power BI for transforming raw data into actionable insights.",
        'data analysis': "The Course covered essential tools such as Python, MySQL, and Power BI for transforming raw data into actionable insights.",
        'data science': "The Course explored statistical analysis, machine learning fundamentals, and data visualization techniques using Python, enabling students to extract meaningful insights from complex datasets.",
        'machine learning': "The Course covered supervised and unsupervised learning algorithms, neural networks, model evaluation techniques, and practical implementation of ML solutions for real-world problems.",
        'ui/ux design': "The internship emphasized user-centered design, wireframing, and prototyping to create intuitive digital experiences.",
        'ui ux design': "The internship emphasized user-centered design, wireframing, and prototyping to create intuitive digital experiences.",
        'flask': "The Course focused on full-stack web technologies including HTML, CSS, JavaScript, and frameworks for building responsive applications.",
    }
    
    # Try exact match first
    if course_key in descriptions:
        return descriptions[course_key]
    
    # Try partial match
    for key, desc in descriptions.items():
        if key in course_key or course_key in key:
            return descriptions[key]
    
    # Default description if no match found
    return f"The Course covered essential concepts and practical applications in {course_title}, equipping students with industry-relevant skills."

def get_next_certificate_sequence(certificate_type, year):
    """
    Get the next sequential number for a certificate type in a given year by checking existing files.
    
    Args:
        certificate_type (str): Type of certificate ('course' or 'exam')
        year (int): Year for which to get the sequence
    
    Returns:
        int: Next sequential number
    """
    try:
        certificates_dir = os.path.join('attached_assets', 'certificates')
        if not os.path.exists(certificates_dir):
            return 1
        
        # Determine prefix pattern based on certificate type
        if certificate_type == 'exam':
            prefix_start = "exam_certificate_DDCE-DA-"
        else:
            prefix_start = "certificate_DDT-DA-"
        
        max_seq = 0
        
        # Check existing certificate files
        if os.path.exists(certificates_dir):
            for filename in os.listdir(certificates_dir):
                # Check if file matches our pattern
                if filename.startswith(prefix_start) and filename.endswith('.pdf'):
                    try:
                        # Extract year and sequence number
                        # Format: certificate_DDT-DA-2025-001.pdf or exam_certificate_DDCE-DA-2025-001.pdf
                        parts = filename.replace('.pdf', '').split('-')
                        if len(parts) >= 4:
                            file_year = int(parts[-2])  # Year is second to last part
                            seq_num = int(parts[-1])    # Sequence is last part
                            
                            # Only consider files from the same year
                            if file_year == year and seq_num > max_seq:
                                max_seq = seq_num
                    except (ValueError, IndexError):
                        # Skip files that don't match the pattern
                        continue
        
        return max_seq + 1
    except Exception as e:
        print(f"Error getting next certificate sequence: {e}")
        return 1

def generate_certificate_id(certificate_id, certificate_type='course'):
    """
    Generate formatted certificate ID with company prefix.
    
    Args:
        certificate_id (int): Numeric ID from database
        certificate_type (str): Type of certificate ('course' or 'exam')
    
    Returns:
        str: Formatted certificate ID (e.g., DDT-DA-2025-001, DDCE-DA-2025-012)
    """
    # Format: PREFIX + zero-padded 3-digit number
    prefix = EXAM_CERTIFICATE_PREFIX if certificate_type == 'exam' else CERTIFICATE_PREFIX
    return f"{prefix}{str(certificate_id).zfill(3)}"

def generate_certificate(user_name, course_title, completion_date, certificate_id, certificate_type='course'):
    """
    Generate a PDF certificate using template background image with overlaid text.
    Matches the exact layout of the DigiDARA certificate template.
    
    Args:
        user_name (str): Name of the user who completed the course
        course_title (str): Title of the completed course
        completion_date (datetime): Date when the course was completed
        certificate_id (int): Numeric identifier for this certificate
        certificate_type (str): Type of certificate ('course' or 'exam')
    
    Returns:
        str: Path to the generated certificate file
    """
    
    try:
        print(f"[generate_certificate] Starting certificate generation for ID: {certificate_id}, type: {certificate_type}")
        
        # Create certificates directory if it doesn't exist
        certificates_dir = os.path.join('attached_assets', 'certificates')
        print(f"[generate_certificate] Creating directory: {certificates_dir}")
        os.makedirs(certificates_dir, exist_ok=True)
        
        # Get next sequential number for this certificate type and year
        sequence_number = get_next_certificate_sequence(certificate_type, completion_date.year)
        
        # Generate formatted certificate ID (DDT-DA-2025-001, DDT-DA-2025-002, etc. or DDCE-DA-2025-001, DDCE-DA-2025-002, etc.)
        if certificate_type == 'exam':
            formatted_cert_id = f"DDCE-DA-{completion_date.year}-{str(sequence_number).zfill(3)}"
        else:
            formatted_cert_id = f"DDT-DA-{completion_date.year}-{str(sequence_number).zfill(3)}"
        print(f"[generate_certificate] Formatted certificate ID: {formatted_cert_id}")
        
        # Define certificate file path
        certificate_filename = f"{'exam_' if certificate_type == 'exam' else ''}certificate_{formatted_cert_id}.pdf"
        certificate_path = os.path.join(certificates_dir, certificate_filename)
        print(f"[generate_certificate] Certificate will be saved to: {certificate_path}")
        
        # Choose template based on certificate type - USE SAME TEMPLATE FOR BOTH
        # As per requirements, use the same template for both certificate types
        template_path = TEMPLATE_PATH  # Always use the same template
        print(f"[generate_certificate] Looking for template at: {template_path}")
        print(f"[generate_certificate] Absolute path: {os.path.abspath(template_path)}")
        print(f"[generate_certificate] Template exists: {os.path.exists(template_path)}")
        
        if not os.path.exists(template_path):
            print(f"[generate_certificate] WARNING: Template not found at {template_path}")
            print(f"[generate_certificate] Falling back to text-only certificate")
            return generate_text_only_certificate(user_name, course_title, completion_date, certificate_id, certificate_path, formatted_cert_id, certificate_type)
        
        # Create PDF with template background (A4 size to match template)
        print(f"[generate_certificate] Creating PDF with template background...")
        c = canvas.Canvas(certificate_path, pagesize=A4)
        width, height = A4  # 595 x 842 points
        
        # Draw background template image - fill entire page
        print(f"[generate_certificate] Drawing background template...")
        c.drawImage(template_path, 0, 0, width=width, height=height, preserveAspectRatio=False, mask='auto')
        
        # Get course description based on certificate type
        if certificate_type == 'course':
            # Course completion description
            course_description = f"has successfully completed the {course_title} course."
            print(f"[generate_certificate] Course description: {course_description[:60]}...")
        else:
            # Exam certification description
            course_description = f"has successfully passed the {course_title} Certification Exam with the required proficiency."
            print(f"[generate_certificate] Exam description: {course_description[:60]}...")
        
        # === USER NAME (Large, Bold, Blue, Centered) ===
        # Position: Below "This certificate is proudly awarded to"
        c.setFont("Helvetica-Bold", 44)
        c.setFillColor(colors.HexColor("#003B73"))  # Dark blue matching template
        
        # Center the name horizontally
        name_width = c.stringWidth(user_name, "Helvetica-Bold", 44)
        name_x = (width - name_width) / 2
        name_y = 475  # Adjusted to match template position
        c.drawString(name_x, name_y, user_name)
        
        # === DESCRIPTION PARAGRAPH (Course details only) ===
        # Show only course-based description, not the student/college info
        c.setFont("Helvetica", 13)
        c.setFillColor(colors.black)
        
        # Position for description paragraph
        para_y_start = 420
        para_x_margin = 85  # Left margin
        para_max_width = 425  # Maximum width for text wrapping
        
        # Word wrap the course description
        desc_words = course_description.split()
        desc_lines = []
        current_line = []
        
        for word in desc_words:
            test_line = ' '.join(current_line + [word])
            if c.stringWidth(test_line, "Helvetica", 13) <= para_max_width:
                current_line.append(word)
            else:
                if current_line:
                    desc_lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            desc_lines.append(' '.join(current_line))
        
        # Draw description paragraph lines
        y_pos = para_y_start
        for line in desc_lines:
            c.drawString(para_x_margin, y_pos, line)
            y_pos -= 18  # Line spacing
        
        # === CERTIFICATE ID (Bottom center, Gold color) ===
        # Format: "Certificate ID: DDT-DA-2025-098"
        c.setFont("Helvetica-Bold", 15)
        c.setFillColor(colors.HexColor("#B8860B"))  # Gold color
        
        # Create full certificate ID with prefix and formatting based on certificate type
        if certificate_type == 'exam':
            # Format: DDCE-DA-2025-012
            full_cert_id = f"DDCE-DA-{completion_date.year}-{str(sequence_number).zfill(3)}"
        else:
            # Format: DDT-DA-2025-002
            full_cert_id = f"DDT-DA-{completion_date.year}-{str(sequence_number).zfill(3)}"
        cert_id_text = f"Certificate ID: {full_cert_id}"
        
        cert_id_width = c.stringWidth(cert_id_text, "Helvetica-Bold", 15)
        cert_id_x = (width - cert_id_width) / 2
        cert_id_y = 105  # Position matching template
        c.drawString(cert_id_x, cert_id_y, cert_id_text)
        
        # === DATE OF ISSUE (Bottom center, Gold color) ===
        c.setFont("Helvetica-Bold", 15)
        c.setFillColor(colors.HexColor("#B8860B"))  # Gold color
        
        # Format date with ordinal suffix (29th Sep 2025)
        day = completion_date.day
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][day % 10 - 1]
        
        date_text = f"Date of Issue: {day}{suffix} {completion_date.strftime('%b %Y')}"
        
        date_width = c.stringWidth(date_text, "Helvetica-Bold", 15)
        date_x = (width - date_width) / 2
        date_y = 75  # Position matching template
        c.drawString(date_x, date_y, date_text)
        
        # Save the PDF
        c.save()
        print(f"[generate_certificate] ✅ Certificate generated successfully: {certificate_path}")
        
        return certificate_path
        
    except Exception as e:
        print(f"[generate_certificate] ❌ ERROR generating certificate: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise to be caught by calling function

def generate_text_only_certificate(user_name, course_title, completion_date, certificate_id, certificate_path, formatted_cert_id, certificate_type='course'):
    """
    Fallback function to generate text-only certificate if template is missing.
    
    Args:
        user_name (str): Name of the user
        course_title (str): Course title
        completion_date (datetime): Completion date
        certificate_id (int): Numeric certificate ID
        certificate_path (str): Path to save certificate
        formatted_cert_id (str): Formatted certificate ID
        certificate_type (str): Type of certificate ('course' or 'exam')
    
    Returns:
        str: Path to generated certificate
    """
    print(f"[generate_text_only_certificate] Generating fallback text-only certificate...")
    
    c = canvas.Canvas(certificate_path, pagesize=letter)
    width, height = letter
    
    # Draw border
    c.setStrokeColor(colors.darkblue)
    c.setLineWidth(2)
    c.rect(50, 50, width-100, height-100)
    
    # Title
    c.setFont("Helvetica-Bold", 36)
    c.setFillColor(colors.darkblue)
    title = "CERTIFICATION EXAM" if certificate_type == 'exam' else "CERTIFICATE"
    title_width = c.stringWidth(title, "Helvetica-Bold", 36)
    c.drawString((width - title_width) / 2, height - 150, title)
    
    if certificate_type == 'exam':
        c.setFont("Helvetica-Bold", 24)
        subtitle = "CERTIFICATE"
        subtitle_width = c.stringWidth(subtitle, "Helvetica-Bold", 24)
        c.drawString((width - subtitle_width) / 2, height - 190, subtitle)
    else:
        c.setFont("Helvetica-Bold", 24)
        subtitle = "OF COMPLETION"
        subtitle_width = c.stringWidth(subtitle, "Helvetica-Bold", 24)
        c.drawString((width - subtitle_width) / 2, height - 190, subtitle)
    
    # Awarded to text
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.black)
    awarded_text = "This certificate is proudly awarded to"
    awarded_width = c.stringWidth(awarded_text, "Helvetica", 14)
    c.drawString((width - awarded_width) / 2, height - 250, awarded_text)
    
    # User name
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(colors.darkblue)
    name_width = c.stringWidth(user_name, "Helvetica-Bold", 32)
    c.drawString((width - name_width) / 2, height - 300, user_name)
    
    # Course/exam text
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.black)
    if certificate_type == 'exam':
        exam_text = f"for successfully passing the {course_title} Certification Exam"
        exam_text_width = c.stringWidth(exam_text, "Helvetica", 14)
        c.drawString((width - exam_text_width) / 2, height - 350, exam_text)
    else:
        course_text = f"for successfully completing the course"
        course_text_width = c.stringWidth(course_text, "Helvetica", 14)
        c.drawString((width - course_text_width) / 2, height - 350, course_text)
        
        # Course title
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(colors.darkblue)
        course_width = c.stringWidth(course_title, "Helvetica-Bold", 18)
        c.drawString((width - course_width) / 2, height - 385, course_title)
    
    # Certificate ID
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    
    # Get next sequential number for this certificate type and year
    sequence_number = get_next_certificate_sequence(certificate_type, completion_date.year)
    
    # Create full certificate ID with prefix and formatting based on certificate type
    if certificate_type == 'exam':
        # Format: DDCE-DA-2025-012
        full_cert_id = f"DDCE-DA-{completion_date.year}-{str(sequence_number).zfill(3)}"
    else:
        # Format: DDT-DA-2025-002
        full_cert_id = f"DDT-DA-{completion_date.year}-{str(sequence_number).zfill(3)}"
    cert_id_text = f"Certificate ID: {full_cert_id}"
    c.drawString(100, 150, cert_id_text)
    
    # Date
    date_text = f"Date: {completion_date.strftime('%B %d, %Y')}"
    c.drawString(100, 130, date_text)
    
    c.save()
    return certificate_path

def save_certificate_record(user_id, course_id, certificate_path, mysql, certificate_type='course'):
    """
    Save certificate record to database.
    
    Args:
        user_id (int): ID of the user
        course_id (int): ID of the course
        certificate_path (str): Path to the certificate file
        mysql: MySQL connection object
        certificate_type (str): Type of certificate ('course' or 'exam')
    
    Returns:
        int: ID of the created certificate record, or None if failed
    """
    # Add comprehensive logging for debugging
    print(f"\n[save_certificate_record] START - user_id: {user_id}, course_id: {course_id}, path: '{certificate_path}', type: {certificate_type}")
    
    connection = None
    cur = None
    
    try:
        # Handle both MySQLWrapper and direct connection objects
        if hasattr(mysql, 'get_connection'):
            # MySQLWrapper class
            connection = mysql.get_connection()
            if not connection:
                print("[save_certificate_record] ERROR: No connection available")
                return None
            print("[save_certificate_record] Database connection obtained")
        else:
            # Direct connection object
            connection = mysql
            print("[save_certificate_record] Using direct connection")
        
        cur = connection.cursor()
        print("[save_certificate_record] Cursor created")
        
        # Check if certificate already exists to prevent duplicates
        print(f"[save_certificate_record] Checking for existing certificate...")
        cur.execute("""
            SELECT id, certificate_path FROM certificates 
            WHERE user_id = %s AND course_id = %s AND certificate_type = %s
        """, (int(user_id), int(course_id), certificate_type))
        existing = cur.fetchone()
        
        if existing:
            certificate_id = existing[0]
            existing_path = existing[1] if len(existing) > 1 else None
            print(f"[save_certificate_record] Certificate already exists with ID: {certificate_id}, path: '{existing_path}'")
            cur.close()
            return certificate_id
        
        print("[save_certificate_record] No existing certificate found, inserting new record...")
        
        # Validate parameters
        user_id_int = int(user_id)
        course_id_int = int(course_id)
        path_str = str(certificate_path) if certificate_path else ""
        
        print(f"[save_certificate_record] Validated params - user_id: {user_id_int}, course_id: {course_id_int}, path: '{path_str}', type: {certificate_type}")
        
        # Insert certificate record only if it doesn't exist
        insert_sql = """
            INSERT INTO certificates (user_id, course_id, certificate_path, certificate_type)
            VALUES (%s, %s, %s, %s)
        """
        print(f"[save_certificate_record] Executing INSERT query...")
        cur.execute(insert_sql, (user_id_int, course_id_int, path_str, certificate_type))
        
        # Commit the transaction
        print(f"[save_certificate_record] Committing transaction...")
        connection.commit()
        
        certificate_id = cur.lastrowid
        print(f"[save_certificate_record] ✅ New certificate created with ID: {certificate_id}")
        
        cur.close()
        return certificate_id
        
    except Exception as e:
        print(f"[save_certificate_record] ❌ ERROR: {e}")
        print(f"[save_certificate_record] Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # Rollback on error
        if connection:
            try:
                connection.rollback()
                print("[save_certificate_record] Transaction rolled back")
            except Exception as rb_error:
                print(f"[save_certificate_record] Rollback error: {rb_error}")
        
        return None
    finally:
        # Ensure cursor is always closed
        if cur:
            try:
                cur.close()
                print("[save_certificate_record] Cursor closed")
            except:
                pass

def get_certificate_path(user_id, course_id, mysql, certificate_type='course'):
    """
    Get the path to an existing certificate for a user and course.
    
    Args:
        user_id (int): ID of the user
        course_id (int): ID of the course
        mysql: MySQL connection object
        certificate_type (str): Type of certificate ('course' or 'exam')
    
    Returns:
        str: Path to the certificate file, or None if not found
    """
    # Add logging for debugging
    print(f"\n[get_certificate_path] Searching for certificate - user_id: {user_id}, course_id: {course_id}, type: {certificate_type}")
    
    try:
        # Handle both MySQLWrapper and direct connection objects
        if hasattr(mysql, 'get_connection'):
            # MySQLWrapper class
            connection = mysql.get_connection()
            if not connection:
                print("[get_certificate_path] ERROR: No connection available")
                return None
        else:
            # Direct connection object
            connection = mysql
        
        cur = connection.cursor(dictionary=True)
        cur.execute("""
            SELECT certificate_path FROM certificates 
            WHERE user_id = %s AND course_id = %s AND certificate_type = %s
        """, (user_id, course_id, certificate_type))
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            cert_path = result['certificate_path']
            print(f"[get_certificate_path] Found certificate path: '{cert_path}'")
            # Return None if path is empty string
            return cert_path if cert_path else None
        else:
            print("[get_certificate_path] No certificate record found in database")
            return None
            
    except Exception as e:
        print(f"[get_certificate_path] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None