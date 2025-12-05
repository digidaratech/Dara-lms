# Forgot Password Functionality

This document describes the implementation of the forgot password functionality for the Learning Management System (LMS).

## Features Implemented

### 1. Forgot Password Page
- **Location**: `/forgot-password`
- **Features**:
  - Choose between email or phone verification
  - Dynamic form fields based on selection
  - User-friendly interface with Bootstrap styling
  - Form validation for required fields

### 2. OTP Verification
- **Location**: `/verify-otp/<user_id>/<method>`
- **Features**:
  - 6-digit OTP code input with auto-focus
  - 10-minute expiration timer
  - Real-time countdown display
  - Resend functionality (placeholder)
  - Secure OTP validation

### 3. Password Reset
- **Location**: `/reset-password/<user_id>/<token>`
- **Features**:
  - Password strength validation
  - Real-time strength meter
  - Password visibility toggle
  - Confirm password matching
  - Strong password requirements

### 4. Account Locking
- **Features**:
  - Account locked after 3 failed login attempts
  - 24-hour lock duration
  - Automatic unlock after lock period
  - Failed attempt counter reset on successful login

## Database Changes

### New Columns in `users` Table
```sql
ALTER TABLE users ADD COLUMN failed_login_attempts INT DEFAULT 0;
ALTER TABLE users ADD COLUMN account_locked_until TIMESTAMP NULL;
```

### New Table: `password_reset_otp`
```sql
CREATE TABLE password_reset_otp (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email VARCHAR(100) NOT NULL,
    mobile VARCHAR(20) NULL,
    otp_code VARCHAR(6) NOT NULL,
    otp_type ENUM('email', 'sms') NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### New Indexes
- `idx_users_mobile` - For phone number lookups
- `idx_users_failed_login_attempts` - For account locking
- `idx_users_account_locked_until` - For lock status checks
- `idx_password_reset_otp_*` - Various indexes for OTP table performance

## User Flow

### 1. Initiate Password Reset
1. User clicks "Forgot your password?" on login page
2. User selects email or phone verification method
3. User enters email/phone and submits
4. System generates 6-digit OTP and stores in database
5. User receives OTP (demo shows in flash message)

### 2. Verify OTP
1. User enters 6-digit OTP code
2. System validates OTP against database
3. If valid, user proceeds to password reset
4. If invalid, user can retry or request new OTP

### 3. Reset Password
1. User enters new password with strength requirements
2. User confirms new password
3. System validates password strength
4. Password is updated and account is unlocked
5. User is redirected to login page

## Security Features

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### Account Protection
- 3 failed login attempts trigger 24-hour lock
- OTP expires after 10 minutes
- OTP can only be used once
- Secure token-based password reset

### Database Security
- Passwords are hashed using Werkzeug's `generate_password_hash`
- OTP codes are randomly generated using `secrets.randbelow`
- All database queries use parameterized statements
- Foreign key constraints ensure data integrity

## Files Modified/Created

### New Templates
- `templates/forgot_password.html` - Forgot password selection page
- `templates/verify_otp.html` - OTP verification page
- `templates/reset_password.html` - Password reset page

### Modified Files
- `templates/login.html` - Added link to forgot password
- `app.py` - Added new routes and updated login logic
- `complete_database_schema.sql` - Updated schema with new tables
- `setup_database.py` - Database migration script

### New Scripts
- `test_forgot_password.py` - Test script for functionality
- `FORGOT_PASSWORD_README.md` - This documentation

## Testing

### Manual Testing
1. Start the application: `python app.py`
2. Navigate to `http://localhost:5000/login`
3. Click "Forgot your password?"
4. Test both email and phone verification methods
5. Test OTP verification with valid/invalid codes
6. Test password reset with various password strengths
7. Test account locking by entering wrong passwords 3 times

### Automated Testing
Run the test script: `python test_forgot_password.py`

## Production Considerations

### Email/SMS Integration
The current implementation shows OTP codes in flash messages for demo purposes. In production:

1. **Email Integration**:
   ```python
   # Use libraries like Flask-Mail or SendGrid
   from flask_mail import Mail, Message
   
   def send_otp_email(email, otp_code):
       msg = Message('Password Reset OTP', recipients=[email])
       msg.body = f'Your OTP code is: {otp_code}'
       mail.send(msg)
   ```

2. **SMS Integration**:
   ```python
   # Use services like Twilio or AWS SNS
   import twilio
   
   def send_otp_sms(phone, otp_code):
       client = twilio.Client(account_sid, auth_token)
       client.messages.create(
           body=f'Your OTP code is: {otp_code}',
           from_=twilio_number,
           to=phone
       )
   ```

### Security Enhancements
1. Rate limiting for OTP requests
2. IP-based blocking for suspicious activity
3. Audit logging for password reset attempts
4. Email notifications for password changes

### Error Handling
- Graceful handling of database connection failures
- User-friendly error messages
- Proper session management
- Input validation and sanitization

## Troubleshooting

### Common Issues
1. **Database connection errors**: Check MySQL configuration in `config.py`
2. **Template not found**: Ensure all template files are in the `templates/` directory
3. **OTP not working**: Check if the `password_reset_otp` table was created
4. **Account not locking**: Verify the new columns were added to the `users` table

### Debug Mode
Enable debug mode in `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/forgot-password` | GET/POST | Forgot password page and form submission |
| `/verify-otp/<user_id>/<method>` | GET/POST | OTP verification page and validation |
| `/reset-password/<user_id>/<token>` | GET/POST | Password reset page and update |

## Dependencies

The implementation uses standard Flask libraries:
- `flask` - Web framework
- `werkzeug.security` - Password hashing
- `secrets` - Secure random number generation
- `datetime` - Time calculations
- `MySQLdb` - Database connectivity

No additional dependencies are required beyond the existing project setup. 