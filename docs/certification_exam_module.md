# Certification Exam Module Documentation

## Overview

The Certification Exam Module is an extension to the existing Learning Management System (LMS) that adds exam-based certification functionality. Students must pass a certification exam to receive their course completion certificate.

## Features

1. **Exam Interface**: Interactive exam interface with timer and auto-submit functionality
2. **Random Question Selection**: Selects random questions from a question bank for each exam
3. **Pass/Fail Logic**: Automatic scoring and pass/fail determination based on configurable pass mark
4. **Attempt Limiting**: Limits the number of exam attempts per user and course
5. **Certificate Integration**: Certificate generation only occurs after passing the exam
6. **Progress Tracking**: Tracks exam attempts and results in the database

## Database Schema

### Questions Table
```sql
CREATE TABLE IF NOT EXISTS questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_id INT NOT NULL,
  question_text TEXT,
  option_a VARCHAR(255),
  option_b VARCHAR(255),
  option_c VARCHAR(255),
  option_d VARCHAR(255),
  correct_option CHAR(1),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);
```

### User Exam Attempts Table
```sql
CREATE TABLE IF NOT EXISTS user_exam_attempts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  course_id INT NOT NULL,
  attempt_number INT DEFAULT 1,
  score INT,
  passed BOOLEAN DEFAULT FALSE,
  time_taken INT, -- in seconds
  exam_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
  UNIQUE KEY unique_user_course_attempt (user_id, course_id, attempt_number)
);
```

## Configuration

The certification module uses the following configurable settings:

- **PASS_MARK**: 60 (percentage required to pass)
- **MAX_ATTEMPTS**: 3 (maximum number of exam attempts)
- **EXAM_DURATION**: 30 * 60 (1800 seconds = 30 minutes)

## Workflow

### 1. Exam Availability
- The certification exam becomes available only after a student completes all course modules (100% progress)
- The "Certification Exam" button appears in the course detail page and dashboard for eligible courses

### 2. Starting the Exam
- User clicks the "Certification Exam" button
- System verifies course completion and exam eligibility
- 10 random questions are selected from the question bank for the course
- Exam timer starts (30 minutes)

### 3. Taking the Exam
- User answers multiple-choice questions (A, B, C, D options)
- Timer counts down from 30 minutes
- User can navigate between questions
- Auto-submit occurs when time expires

### 4. Exam Evaluation
- System automatically evaluates answers
- Score is calculated: (correct answers / total questions) * 100
- Result is compared against PASS_MARK (60%)
- If passed:
  - Exam result is saved as passed in user_exam_attempts
  - Certificate generation is triggered
- If failed:
  - Exam attempt is saved with passed = FALSE
  - Attempt counter is incremented
  - User can retry if attempts < MAX_ATTEMPTS (3)

### 5. Certificate Generation
- Certificate is only generated if:
  - Course progress = 100%
  - Exam result = passed (TRUE)
- Certificate is automatically emailed to the user

### 6. Attempt Limiting
- Users are limited to MAX_ATTEMPTS (3) attempts per course
- If all attempts are used without passing:
  - "You have used all attempts. Please contact admin." message is displayed
  - No further exam attempts are allowed

## API Endpoints

### Start Exam
- **Endpoint**: `/api/exam/start`
- **Method**: POST
- **Description**: Fetches random questions for a course exam
- **Request Body**: `{ "course_id": <int> }`
- **Response**: 
  ```json
  {
    "success": true,
    "questions": [<question_objects>],
    "exam_duration": 1800
  }
  ```

### Submit Exam
- **Endpoint**: `/api/exam/submit`
- **Method**: POST
- **Description**: Evaluates exam answers and saves results
- **Request Body**: 
  ```json
  {
    "course_id": <int>,
    "answers": { "<question_id>": "<selected_option>", ... },
    "time_taken": <int_seconds>
  }
  ```
- **Response**: 
  ```json
  {
    "success": true,
    "score": <int>,
    "passed": <boolean>,
    "correct_count": <int>,
    "total_questions": <int>,
    "attempt_number": <int>,
    "max_attempts": 3,
    "can_retry": <boolean>
  }
  ```

### Exam Status
- **Endpoint**: `/api/exam/status/<course_id>`
- **Method**: GET
- **Description**: Checks user's exam status for a course
- **Response**: 
  ```json
  {
    "success": true,
    "exam_status": {
      "attempts": <int>,
      "max_attempts": 3,
      "can_attempt": <boolean>,
      "passed": <boolean>
    }
  }
  ```

## Frontend Components

### Certification Exam Page
- **Template**: `templates/certification_exam.html`
- **Features**:
  - Timer display with color-coded warnings (red when < 5 minutes remaining)
  - Question navigation
  - Multiple-choice question interface
  - Submit button (fixed position)
  - Result display with pass/fail status
  - Retry option if available

### JavaScript Functionality
- **Timer Management**: Countdown timer with auto-submit
- **Question Navigation**: Interactive question selection
- **Answer Selection**: Radio button interface for multiple-choice questions
- **Result Display**: Visual feedback for pass/fail results
- **Retry Logic**: Option to retry exam if attempts remain

## Backend Logic

### Certificate Generation Update
The certificate generation logic has been updated to require both:
1. Course completion progress = 100%
2. Exam result (passed = TRUE)

### Exam Status Checking
Helper functions check exam status:
- `has_passed_exam(user_id, course_id)`: Checks if user has passed exam
- `get_exam_status(user_id, course_id)`: Gets detailed exam status
- `get_courses_needing_certification(user_id)`: Gets courses requiring certification

## Security Considerations

1. **Session Validation**: All exam endpoints require valid user session
2. **Course Completion Verification**: Exams only available after 100% course completion
3. **Attempt Limiting**: Prevents unlimited exam retries
4. **Data Integrity**: Database constraints prevent duplicate exam attempts
5. **Input Validation**: All user inputs are validated and sanitized

## Logging

The system logs important exam events:
- `[CERTIFICATION EXAM] user_id=<id>, score=<percentage>%, result=<PASS/FAIL>`
- `[CERTIFICATION EXAM] user_id=<id> exceeded max attempts (3)`

## Error Handling

The system handles various error conditions:
- Database connection failures
- Invalid user sessions
- Course not found
- User not enrolled in course
- Exam not available (incomplete course)
- Exam already passed
- Maximum attempts exceeded
- No questions available for course

## Integration Points

1. **Certificate Service**: Integrates with existing certificate generation
2. **Email Service**: Sends certificates via email upon exam pass
3. **User Authentication**: Uses existing session management
4. **Course Progress**: Integrates with existing progress tracking
5. **Database**: Uses existing MySQL connection infrastructure

## Future Enhancements

1. **Question Categories**: Categorize questions by difficulty or topic
2. **Exam Customization**: Allow instructors to customize exam settings per course
3. **Review Mode**: Allow users to review their exam answers after completion
4. **Analytics Dashboard**: Provide detailed exam analytics for instructors
5. **Multi-language Support**: Support questions in multiple languages
6. **Image Support**: Allow images in exam questions
7. **Explanation Feedback**: Provide explanations for correct/incorrect answers