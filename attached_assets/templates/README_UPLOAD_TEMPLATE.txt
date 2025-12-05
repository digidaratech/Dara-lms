# Certificate Template Setup Instructions

## Step 1: Upload Certificate Template Image

**IMPORTANT**: You need to upload your certificate template image to use the custom certificate generator.

### Upload Instructions:

1. Save your certificate template image as: `certificate_template.png`
2. Place it in the directory: `attached_assets/templates/`
3. The full path should be: `attached_assets/templates/certificate_template.png`

### Alternative Method (if upload doesn't work):

If you cannot upload directly, you can:
1. Copy the image file (`_Batch 2 Bishop Internship Completion Certificates.png`)
2. Rename it to `certificate_template.png`
3. Move it to `attached_assets/templates/` folder

### Verification:

After uploading, verify the file exists by checking:
```
attached_assets/
  └── templates/
      └── certificate_template.png  ← Should exist here
```

## Step 2: How the System Works

Once the template is uploaded, the certificate generator will:

1. **Use the template as background** for all generated certificates
2. **Overlay dynamic text** on specific positions:
   - User name (large, centered, blue)
   - Course title and description
   - Course Certificate ID (format: DDT-DA-2025-001)
   - Exam Certificate ID (format: DDCE-DA-2025-001)
   - Date of issue

3. **Save certificates** as: `attached_assets/certificates/certificate_DD001.pdf`

## Step 3: Customization Options

### Change Company Prefix (DD → something else):

Edit `services/certificate_service.py`, line 18:
```python
CERTIFICATE_PREFIX = "DD"  # Change to your preferred prefix
```

### Update Course Descriptions:

Edit `services/certificate_service.py`, function `get_course_description()`, lines 20-53:
```python
descriptions = {
    'your course name': "Your custom description here",
    ...
}
```

### Adjust Text Positioning:

If text doesn't align properly with your template, edit `services/certificate_service.py`, function `generate_certificate()`:

- **User name position**: Line 150 → `c.drawString(name_x, height - 370, user_name)`
  - Decrease `370` to move name UP
  - Increase `370` to move name DOWN

- **Description start position**: Line 157 → `description_y_start = height - 450`
  - Adjust this value to move description text

- **Certificate ID position**: Line 219 → `c.drawString((width - cert_id_width) / 2, 120, cert_id_text)`
  - Adjust `120` to move ID up/down

- **Date position**: Line 226 → `c.drawString((width - date_width) / 2, 90, date_text)`
  - Adjust `90` to move date up/down

### Change Font Sizes:

- **User name**: Line 143 → `c.setFont("Helvetica-Bold", 48)`
- **Description**: Line 163 → `text_object.setFont("Helvetica", 12)`
- **Certificate ID**: Line 217 → `c.setFont("Helvetica-Bold", 14)`

## Step 4: Testing

After uploading the template:

1. Complete a course (100% progress)
2. Click "Download Certificate"
3. Check generated PDF in `attached_assets/certificates/`
4. Verify text alignment and readability

## Notes

- The system will automatically fall back to text-only certificate if template is missing
- Template should be PNG format, ideally 1920x1080 or A4 size (595x842 points)
- All text is rendered on top of the template image
- Course Certificate ID format: `DDT-DA-2025-XXX` where XXX is auto-incremented
- Exam Certificate ID format: `DDCE-DA-2025-XXX` where XXX is auto-incremented
