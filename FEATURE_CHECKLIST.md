# LMS Feature Testing Checklist

## Server Setup
- [ ] Server starts without errors
- [ ] Server runs on port 8000
- [ ] Server accessible at http://localhost:8000
- [ ] No port conflicts

## Database Connection
- [ ] Database connection successful
- [ ] Test endpoint `/test-db` returns success
- [ ] Database queries execute correctly

## Public Pages (No Login Required)
- [ ] **Home Page** (`/`)
  - [ ] Page loads correctly
  - [ ] Navigation menu visible
  - [ ] Features section displays
  - [ ] Course previews show
  - [ ] Links work correctly

- [ ] **Courses Page** (`/courses`)
  - [ ] List of courses displays
  - [ ] Course cards show properly
  - [ ] Course details visible (title, price, duration)
  - [ ] Enrolled status shown (if logged in)
  - [ ] Course links work

- [ ] **Course Detail Page** (`/course/<id>`)
  - [ ] Course information displays
  - [ ] Modules list shows
  - [ ] Enroll button visible
  - [ ] Course description shows

## Authentication Features
- [ ] **Signup Page** (`/signup`)
  - [ ] Form displays correctly
  - [ ] All fields present (name, email, mobile, password)
  - [ ] Password confirmation works
  - [ ] Validation works (matching passwords)
  - [ ] Success message on registration
  - [ ] Redirects to login after signup

- [ ] **Login Page** (`/login`)
  - [ ] Form displays correctly
  - [ ] Email and password fields work
  - [ ] Login successful with valid credentials
  - [ ] Error message with invalid credentials
  - [ ] Redirects to dashboard after login
  - [ ] Account lockout after 3 failed attempts

- [ ] **Forgot Password** (`/forgot-password`)
  - [ ] Page loads correctly
  - [ ] Email/Phone option works
  - [ ] OTP sent successfully
  - [ ] OTP verification works
  - [ ] Password reset works

- [ ] **Logout** (`/logout`)
  - [ ] Logout works correctly
  - [ ] Session cleared
  - [ ] Redirects to home page

## User Dashboard (After Login)
- [ ] **Dashboard** (`/dashboard`)
  - [ ] User info displays
  - [ ] Enrolled courses show
  - [ ] Recommended courses show
  - [ ] Progress statistics display
  - [ ] Charts render correctly
  - [ ] Watch time data shows

## Course Features
- [ ] **Enrollment**
  - [ ] Enroll button works
  - [ ] Checkout page loads
  - [ ] Enrollment successful
  - [ ] Course appears in dashboard

- [ ] **Course Content**
  - [ ] Module video page loads
  - [ ] Video player works
  - [ ] Module navigation works
  - [ ] Progress tracking works
  - [ ] Watch time recorded

## Admin Panel
- [ ] **Admin Login** (`/admin/login`)
  - [ ] Login form works
  - [ ] Admin credentials work (admin/admin123)
  - [ ] Redirects to admin dashboard

- [ ] **Admin Dashboard** (`/admin/dashboard`)
  - [ ] Statistics display
  - [ ] User count shows
  - [ ] Course count shows
  - [ ] Enrollment count shows
  - [ ] Revenue shows
  - [ ] Charts render

- [ ] **Course Management** (`/admin/courses`)
  - [ ] Course list displays
  - [ ] Create course works
  - [ ] Edit course works
  - [ ] Delete course works
  - [ ] View course details works

- [ ] **User Management** (`/admin/users`)
  - [ ] User list displays
  - [ ] User details show
  - [ ] User search works (if implemented)

- [ ] **Enrollment Management** (`/admin/enrollments`)
  - [ ] Enrollment list displays
  - [ ] Enrollment details show
  - [ ] Filter by course works (if implemented)

- [ ] **Video Upload** (`/admin/video/upload`)
  - [ ] Upload form displays
  - [ ] File upload works
  - [ ] Video saved correctly
  - [ ] Video associated with course

## API Endpoints
- [ ] **Chatbot API** (`/api/chat`)
  - [ ] POST request works
  - [ ] Returns response
  - [ ] Handles errors gracefully

- [ ] **Database Test** (`/test-db`)
  - [ ] Returns JSON response
  - [ ] Shows connection status
  - [ ] Shows user count

## Google OAuth (If Implemented)
- [ ] Google login button displays
- [ ] Google authentication works
- [ ] User created on first login
- [ ] Existing user logged in

## Error Handling
- [ ] 404 errors handled
- [ ] 500 errors handled
- [ ] Database errors handled gracefully
- [ ] Invalid URLs redirect correctly

## Security Features
- [ ] Password hashing works
- [ ] Session management works
- [ ] CSRF protection (if implemented)
- [ ] SQL injection prevented
- [ ] XSS protection (if implemented)

## Performance
- [ ] Pages load quickly
- [ ] Database queries optimized
- [ ] No memory leaks
- [ ] Server handles multiple requests

## Mobile Responsiveness
- [ ] Pages work on mobile
- [ ] Navigation menu responsive
- [ ] Forms work on mobile
- [ ] Tables responsive

## Testing Commands

### Start Server
```bash
python start_server.py
# or
python main.py
# or
python app.py
```

### Quick Test
```bash
python quick_test.py
```

### Full Feature Test
```bash
python test_app_features.py
```

### Database Test
```bash
python test_mysql_connection.py
```

## Notes
- Test each feature after making changes
- Check server logs for errors
- Verify database operations
- Test with different user accounts
- Test edge cases (empty data, invalid input)

## Common Issues to Check
1. Database connection failures
2. Port conflicts
3. Missing dependencies
4. Template rendering errors
5. JavaScript errors (check browser console)
6. CSS loading issues
7. Image/video loading issues

