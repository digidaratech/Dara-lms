# Certificate Template Usage Guide

## Overview

The LMS now generates professional PDF certificates using a custom template background image with dynamically overlaid text fields. This guide explains how to use, customize, and maintain the certificate generation system.

---

## 1. How to Update the Background Template

### Current Template Location
```
attached_assets/templates/certificate_template.png
```

### Steps to Update:

1. **Prepare Your Template**:
   - Format: PNG image
   - Recommended size: A4 dimensions (595x842 points) or 1920x1080 pixels
   - Design should include:
     - Company logo/branding
     - Decorative borders/graphics
     - Placeholder areas for dynamic text
     - Signature/seal graphics (static)

2. **Upload the Template**:
   ```
   - Save your new template as: certificate_template.png
   - Replace the existing file in: attached_assets/templates/
   ```

3. **Verify Upload**:
   - Check file exists: `attached_assets/templates/certificate_template.png`
   - Test certificate generation
   - Adjust text positions if needed (see Section 4)

### Fallback Behavior

If the template file is missing, the system automatically generates a text-only certificate (no background image) to ensure continuous operation.

---

## 2. How to Change Prefix (DD → Another Code)

The certificate ID prefix (currently "DD") represents your company code.

### Current Format
- Certificate IDs: `DD001`, `DD002`, `DD003`, etc.
- Displayed as: `DDT-DA-2025-098` (in PDF)

### Steps to Change:

1. **Open the certificate service file**:
   ```
   services/certificate_service.py
   ```

2. **Locate the prefix constant** (Line 18):
   ```python
   CERTIFICATE_PREFIX = "DD"  # Company code prefix for certificate IDs
   ```

3. **Change to your preferred code**:
   ```python
   CERTIFICATE_PREFIX = "ABC"  # Example: ABC001, ABC002, etc.
   ```

4. **Save the file**

5. **New certificates will use the updated prefix**

### Notes:
- Prefix is used for filename: `certificate_ABC001.pdf`
- Existing certificates keep their original prefix
- Prefix appears in the Certificate ID displayed on the PDF

---

## 3. How to Update Course Descriptions

Each course can have a custom description displayed on the certificate.

### Current Descriptions

The system includes built-in descriptions for common courses:

| Course Name | Description |
|-------------|-------------|
| Python / Python Programming | "The Course covered Python fundamentals, data structures, and object-oriented programming, with real-world projects demonstrating automation and analysis." |
| Web Development | "The Course focused on full-stack web technologies including HTML, CSS, JavaScript, and frameworks for building responsive applications." |
| Data Analytics | "The Course covered essential tools such as Python, MySQL, and Power BI for transforming raw data into actionable insights." |
| Machine Learning | "The internship explored supervised and unsupervised algorithms, model evaluation, and deployment of ML solutions." |
| UI/UX Design | "The internship emphasized user-centered design, wireframing, and prototyping to create intuitive digital experiences." |

### Steps to Add/Update Descriptions:

1. **Open the certificate service file**:
   ```
   services/certificate_service.py
   ```

2. **Locate the `get_course_description()` function** (Lines 20-60):
   ```python
   def get_course_description(course_title):
       course_key = course_title.lower().strip()
       
       descriptions = {
           'python': \"...\",
           'web development': \"...\",
           # Add your courses here
       }
   ```

3. **Add your course** to the dictionary:
   ```python
   descriptions = {
       'python': \"Python course description...\",
       'web development': \"Web dev description...\",
       'your new course': \"Your custom description here...\",  # NEW
   }
   ```

4. **Save the file**

### Matching Logic

The system matches courses using:
1. **Exact match** (case-insensitive): `'python'` matches `'Python'`, `'PYTHON'`
2. **Partial match**: `'python programming'` matches if it contains `'python'`
3. **Default fallback**: If no match, uses generic description

### Example: Adding a New Course

```python
descriptions = {
    # ... existing courses ...
    
    'blockchain development': \"The Course explored blockchain fundamentals, smart contracts, and decentralized application development using Ethereum and Solidity.\",
    
    'cybersecurity': \"The Course covered network security, ethical hacking, penetration testing, and incident response strategies.\",
}
```

---

## 4. How to Adjust Text Position Coordinates

Text positioning uses **coordinate system** where:
- **Origin (0,0)** is at bottom-left corner
- **X-axis**: Left to right (0 to page width)
- **Y-axis**: Bottom to top (0 to page height)
- **A4 size**: 595 points wide, 842 points high

### Current Text Positions

| Element | Y-Position (from top) | Line Reference |
|---------|----------------------|----------------|
| User Name | 370 | Line 150 |
| Description Start | 450 | Line 157 |
| Certificate ID | 120 (from bottom) | Line 219 |
| Date of Issue | 90 (from bottom) | Line 226 |

### Steps to Adjust Positions:

1. **Open certificate service file**:
   ```
   services/certificate_service.py
   ```

2. **Locate the `generate_certificate()` function** (Lines 75-229)

3. **Adjust Y-coordinates**:

   **User Name** (Line 150):
   ```python
   c.drawString(name_x, height - 370, user_name)
   #                        ^^^
   # Decrease to move UP (height - 350)
   # Increase to move DOWN (height - 400)
   ```

   **Description** (Line 157):
   ```python
   description_y_start = height - 450
   #                              ^^^
   # Adjust this value to move description block
   ```

   **Certificate ID** (Line 219):
   ```python
   c.drawString((width - cert_id_width) / 2, 120, cert_id_text)
   #                                         ^^^
   # Increase to move UP (130, 140, etc.)
   # Decrease to move DOWN (110, 100, etc.)
   ```

   **Date** (Line 226):
   ```python
   c.drawString((width - date_width) / 2, 90, date_text)
   #                                      ^^
   # Adjust to move up/down
   ```

4. **Test and iterate**:
   - Generate a test certificate
   - Check alignment with template
   - Adjust values as needed

### Font Sizes

| Element | Current Size | Line |
|---------|--------------|------|
| User Name | 48 pt (Bold) | 143 |
| Description | 12 pt | 163, 185 |
| Certificate ID | 14 pt (Bold) | 217 |
| Date | 14 pt (Bold) | 224 |

**To change font size**, edit the line:
```python
c.setFont("Helvetica-Bold", 48)
#                           ^^
# Change this number (20-60 for names, 10-16 for text)
```

### Horizontal Alignment

Most text is **center-aligned** automatically:
```python
name_width = c.stringWidth(user_name, "Helvetica-Bold", 48)
name_x = (width - name_width) / 2  # Centers the text
c.drawString(name_x, y_position, user_name)
```

**To left-align**: Use fixed X value
```python
c.drawString(100, y_position, text)  # 100 points from left edge
```

**To right-align**: Calculate from right edge
```python
text_width = c.stringWidth(text, font, size)
c.drawString(width - text_width - 100, y_position, text)
```

---

## 5. Certificate ID Format

### Current Format

**Filename**: `certificate_DD001.pdf`, `certificate_DD042.pdf`

**Displayed on Certificate**: `DDT-DA-2025-098`

### Format Breakdown

```
DDT - DA - 2025 - 098
 │    │     │     │
 │    │     │     └── Certificate number (zero-padded 3 digits)
 │    │     └──────── Year
 │    └────────────── Course code (DA = Data Analytics)
 └─────────────────── Company prefix
```

### To Modify Format

**Edit Line 219** in `generate_certificate()`:
```python
# Current format
cert_id_text = f"Certificate ID: DDT-DA-2025-{str(certificate_id).zfill(3)}"

# Examples of custom formats:
# Simple format:
cert_id_text = f"ID: {formatted_cert_id}"

# With year:
cert_id_text = f"{CERTIFICATE_PREFIX}-{completion_date.year}-{str(certificate_id).zfill(4)}"

# With course abbreviation:
course_abbr = course_title[:2].upper()
cert_id_text = f"{CERTIFICATE_PREFIX}-{course_abbr}-{str(certificate_id).zfill(3)}"
```

---

## 6. Dynamic Text Fields

### Fields Populated Automatically

| Field | Source | Example |
|-------|--------|---------|
| **User Name** | User profile (database) | "Priyadharshini A" |
| **Course Title** | Course table | "Data Analytics" |
| **Description** | Course mapping (code) | "The Course covered essential tools..." |
| **Certificate ID** | Auto-incremented | "DD001" |
| **Issue Date** | Course completion date | "29th Sep 2025" |

### Data Flow

```
User completes course (100% progress)
    ↓
calculate_course_progress() detects completion
    ↓
Calls generate_certificate(user_name, course_title, completion_date, cert_id)
    ↓
Retrieves user name from database
Retrieves course title from database
Gets description from course mapping
Formats certificate ID
    ↓
Overlays all text on template background
    ↓
Saves PDF: attached_assets/certificates/certificate_DD001.pdf
    ↓
Updates database with certificate path
```

---

## 7. Testing & Troubleshooting

### Test Certificate Generation

1. **Complete a course** (reach 100% progress)
2. **Navigate to course page**
3. **Click "Download Certificate"**
4. **Check generated PDF** in `attached_assets/certificates/`

### Common Issues & Solutions

**Issue**: Template not loading, text-only certificate generated

**Solution**: 
- Verify template exists: `attached_assets/templates/certificate_template.png`
- Check file permissions (readable)
- Check file format (must be PNG)

---

**Issue**: Text is cut off or misaligned

**Solution**:
- Adjust Y-coordinates (see Section 4)
- Reduce font size if text is too large
- Check template dimensions match A4 size

---

**Issue**: Certificate ID not incrementing

**Solution**:
- Check database `certificates` table
- Verify `id` column is AUTO_INCREMENT
- Check for database insert errors in logs

---

**Issue**: Course description shows default text

**Solution**:
- Add course to descriptions dictionary
- Check course title spelling matches database
- Use lowercase keys in mapping

---

**Issue**: Date format incorrect

**Solution**:
- Edit Line 226 date format:
  ```python
  completion_date.strftime('%dth %b %Y')  # 29th Sep 2025
  completion_date.strftime('%B %d, %Y')   # September 29, 2025
  completion_date.strftime('%d/%m/%Y')    # 29/09/2025
  ```

---

## 8. Advanced Customization

### Adding Multiple Signatures

```python
# Add after description (around line 210)
c.setFont("Helvetica", 10)
c.setFillColor(colors.black)
c.drawString(150, 180, "Senthil Rajamarthandan")
c.drawString(150, 165, "Managing Director")

c.drawString(400, 180, "Jane Smith")
c.drawString(400, 165, "Head of Training")
```

### Adding QR Code for Verification

```python
from reportlab.graphics import barcode
from reportlab.graphics.shapes import Drawing

# Generate QR code
qr = barcode.qr.QrCodeWidget(f"https://verify.yoursite.com/{formatted_cert_id}")
bounds = qr.getBounds()
width_qr = bounds[2] - bounds[0]
height_qr = bounds[3] - bounds[1]
d = Drawing(100, 100, transform=[100./width_qr,0,0,100./height_qr,0,0])
d.add(qr)

# Draw QR code
renderPDF.draw(d, c, 50, 50)
```

### Using Custom Fonts

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register custom font
pdfmetrics.registerFont(TTFont('CustomFont', 'path/to/font.ttf'))

# Use custom font
c.setFont("CustomFont", 48)
```

---

## 9. File Structure

```
LMS-upstream/
├── attached_assets/
│   ├── templates/
│   │   ├── certificate_template.png        ← Upload your template here
│   │   └── README_UPLOAD_TEMPLATE.txt
│   └── certificates/
│       ├── certificate_DD001.pdf           ← Generated certificates
│       ├── certificate_DD002.pdf
│       └── ...
├── services/
│   └── certificate_service.py              ← Main certificate generator
├── data.py                                  ← Triggers certificate at 100%
└── docs/
    ├── certificate_template_usage.md       ← This file
    └── certificate_fix_report.md
```

---

## 10. Summary Checklist

### Initial Setup
- [ ] Upload template image to `attached_assets/templates/certificate_template.png`
- [ ] Test certificate generation
- [ ] Verify text alignment

### Customization
- [ ] Update company prefix (if needed)
- [ ] Add custom course descriptions
- [ ] Adjust text positions
- [ ] Modify date format (if needed)

### Testing
- [ ] Complete a test course
- [ ] Download certificate
- [ ] Verify all fields populated correctly
- [ ] Check PDF quality and readability

---

## Support & Maintenance

For issues or questions:
1. Check server logs for error messages
2. Verify template file exists and is readable
3. Test with fallback (text-only) certificate
4. Adjust coordinates incrementally (by 10-20 points)
5. Refer to Section 7 (Troubleshooting)

---

**Last Updated**: November 8, 2025  
**Version**: 1.0  
**Certificate System Status**: ✅ Production Ready
