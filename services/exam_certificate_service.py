"""
Exam Certificate Generation Service for LMS
This module handles the creation and delivery of exam certification certificates.
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
EXAM_CERTIFICATE_PREFIX = "DDCE"  # Company code prefix for exam certificate IDs

# Try to find template in multiple formats (PNG or JPG)
def get_exam_template_path():
    """Find exam certificate template in supported formats."""
    base_path = os.path.join('attached_assets', 'templates', 'exam_certificate_template')
    for ext in ['.png', '.jpg', '.jpeg']:
        path = base_path + ext
        if os.path.exists(path):
            return path
    # Fallback to PNG path (will trigger fallback certificate if not found)
    return os.path.join('attached_assets', 'templates', 'exam_certificate_template.png')

EXAM_TEMPLATE_PATH = get_exam_template_path()

def get_course_description(course_title):
    """
    Get course-specific description based on course title for exam certificates.
    
    Args:
        course_title (str): Title of the course
    
    Returns:
        str: Description text for the course
    """
    # Normalize course title for matching (case-insensitive, strip whitespace)
    course_key = course_title.lower().strip()
    
    # Course description mapping for exam certificates
    descriptions = {
        'python': "has successfully passed the Python Certification Exam with required proficiency.",
        'python programming': "has successfully passed the Python Programming Certification Exam with required proficiency.",
        'web development': "has successfully passed the Web Development Certification Exam with required proficiency.",
        'data analytics': "has successfully passed the Data Analytics Certification Exam with required proficiency.",
        'data analysis': "has successfully passed the Data Analysis Certification Exam with required proficiency.",
        'data science': "has successfully passed the Data Science Certification Exam with required proficiency.",
        'machine learning': "has successfully passed the Machine Learning Certification Exam with required proficiency.",
        'ui/ux design': "has successfully passed the UI/UX Design Certification Exam with required proficiency.",
        'ui ux design': "has successfully passed the UI/UX Design Certification Exam with required proficiency.",
        'flask': "has successfully passed the Flask Certification Exam with required proficiency.",
    }
    
    # Try exact match first
    if course_key in descriptions:
        return descriptions[course_key]
    
    # Try partial match
    for key, desc in descriptions.items():
        if key in course_key or course_key in key:
            return descriptions[key]
    
    # Default description if no match found
    return f"has successfully passed the {course_title} Certification Exam with required proficiency."

def get_next_certificate_sequence(year):
    """
    Get the next sequential number for exam certificates in a given year by checking existing files.
    
    Args:
        year (int): Year for which to get the sequence
    
    Returns:
        int: Next sequential number
    """
    try:
        certificates_dir = os.path.join('attached_assets', 'certificates')
        if not os.path.exists(certificates_dir):
            return 1
        
        # Determine prefix pattern for exam certificates
        prefix_start = "exam_certificate_DDCE-DA-"
        
        max_seq = 0
        
        # Check existing certificate files
        if os.path.exists(certificates_dir):
            for filename in os.listdir(certificates_dir):
                # Check if file matches our pattern
                if filename.startswith(prefix_start) and filename.endswith('.pdf'):
                    try:
                        # Extract year and sequence number
                        # Format: exam_certificate_DDCE-DA-2025-001.pdf
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

def generate_exam_certificate_id(certificate_id):
    """
    Generate formatted exam certificate ID with company prefix.
    
    Args:
        certificate_id (int): Numeric ID from database
    
    Returns:
        str: Formatted certificate ID (e.g., DDCE-DA-2025-001)
    """
    # Format: PREFIX + zero-padded 3-digit number
    return f"{EXAM_CERTIFICATE_PREFIX}-DA-{str(certificate_id).zfill(3)}"

def generate_exam_certificate(user_name, course_title, completion_date, certificate_id):
    """
    Generate a PDF exam certificate using template background image with overlaid text.
    Matches the exact layout of the DigiDARA exam certificate template.
    
    Args:
        user_name (str): Name of the user who passed the exam
        course_title (str): Title of the course exam
        completion_date (datetime): Date when the exam was passed
        certificate_id (int): Numeric identifier for this certificate
    
    Returns:
        str: Path to the generated certificate file
    """
    
    try:
        print(f"[generate_exam_certificate] Starting exam certificate generation for ID: {certificate_id}")
        
        # Create certificates directory if it doesn't exist
        certificates_dir = os.path.join('attached_assets', 'certificates')
        print(f"[generate_exam_certificate] Creating directory: {certificates_dir}")
        os.makedirs(certificates_dir, exist_ok=True)
        
        # Get next sequential number for this year
        sequence_number = get_next_certificate_sequence(completion_date.year)
        
        # Generate formatted certificate ID (DDCE-DA-2025-001, DDCE-DA-2025-002, etc.)
        formatted_cert_id = f"DDCE-DA-{completion_date.year}-{str(sequence_number).zfill(3)}"
        print(f"[generate_exam_certificate] Formatted certificate ID: {formatted_cert_id}")
        
        # Define certificate file path
        certificate_filename = f"exam_certificate_{formatted_cert_id}.pdf"
        certificate_path = os.path.join(certificates_dir, certificate_filename)
        print(f"[generate_exam_certificate] Certificate will be saved to: {certificate_path}")
        
        # Choose template for exam certificates
        template_path = EXAM_TEMPLATE_PATH
        print(f"[generate_exam_certificate] Looking for template at: {template_path}")
        print(f"[generate_exam_certificate] Absolute path: {os.path.abspath(template_path)}")
        print(f"[generate_exam_certificate] Template exists: {os.path.exists(template_path)}")
        
        if not os.path.exists(template_path):
            print(f"[generate_exam_certificate] WARNING: Template not found at {template_path}")
            print(f"[generate_exam_certificate] Falling back to text-only certificate")
            return generate_text_only_exam_certificate(user_name, course_title, completion_date, certificate_id, certificate_path, formatted_cert_id)
        
        # Create PDF with template background (A4 size to match template)
        print(f"[generate_exam_certificate] Creating PDF with template background...")
        c = canvas.Canvas(certificate_path, pagesize=A4)
        width, height = A4  # 595 x 842 points
        
        # Draw background template image - fill entire page
        print(f"[generate_exam_certificate] Drawing background template...")
        c.drawImage(template_path, 0, 0, width=width, height=height, preserveAspectRatio=False, mask='auto')
        
        # Exam certification description
        course_description = f"has successfully passed the {course_title} Certification Exam with the required proficiency."
        print(f"[generate_exam_certificate] Exam description: {course_description[:60]}...")
        
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
        # Format: "Certificate ID: DDCE-DA-2025-001"
        c.setFont("Helvetica-Bold", 15)
        c.setFillColor(colors.HexColor("#B8860B"))  # Gold color
        
        # Create full certificate ID with prefix and formatting
        full_cert_id = f"DDCE-DA-{completion_date.year}-{str(sequence_number).zfill(3)}"
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
        print(f"[generate_exam_certificate] ✅ Exam certificate generated successfully: {certificate_path}")
        
        return certificate_path
        
    except Exception as e:
        print(f"[generate_exam_certificate] ❌ ERROR generating exam certificate: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise to be caught by calling function

def generate_text_only_exam_certificate(user_name, course_title, completion_date, certificate_id, certificate_path, formatted_cert_id):
    """
    Fallback function to generate text-only exam certificate if template is missing.
    
    Args:
        user_name (str): Name of the user
        course_title (str): Course title
        completion_date (datetime): Completion date
        certificate_id (int): Numeric certificate ID
        certificate_path (str): Path to save certificate
        formatted_cert_id (str): Formatted certificate ID
    
    Returns:
        str: Path to generated certificate
    """
    print(f"[generate_text_only_exam_certificate] Generating fallback text-only exam certificate...")
    
    c = canvas.Canvas(certificate_path, pagesize=letter)
    width, height = letter
    
    # Draw border
    c.setStrokeColor(colors.darkblue)
    c.setLineWidth(2)
    c.rect(50, 50, width-100, height-100)
    
    # Title
    c.setFont("Helvetica-Bold", 36)
    c.setFillColor(colors.darkblue)
    title = "CERTIFICATION EXAM"
    title_width = c.stringWidth(title, "Helvetica-Bold", 36)
    c.drawString((width - title_width) / 2, height - 150, title)
    
    c.setFont("Helvetica-Bold", 24)
    subtitle = "CERTIFICATE"
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
    
    # Exam text
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.black)
    exam_text = f"for successfully passing the {course_title} Certification Exam"
    exam_text_width = c.stringWidth(exam_text, "Helvetica", 14)
    c.drawString((width - exam_text_width) / 2, height - 350, exam_text)
    
    # Certificate ID
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    
    # Get next sequential number for this year
    sequence_number = get_next_certificate_sequence(completion_date.year)
    
    # Create full certificate ID with prefix and formatting
    full_cert_id = f"DDCE-DA-{completion_date.year}-{str(sequence_number).zfill(3)}"
    cert_id_text = f"Certificate ID: {full_cert_id}"
    c.drawString(100, 150, cert_id_text)
    
    # Date
    date_text = f"Date: {completion_date.strftime('%B %d, %Y')}"
    c.drawString(100, 130, date_text)
    
    c.save()
    return certificate_path