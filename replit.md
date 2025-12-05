# EduFlow LMS - Learning Management System

## Overview

EduFlow LMS is a comprehensive Learning Management System built with Flask, designed to provide online course enrollment, payment processing, and course content delivery. The application follows a traditional web architecture with server-side rendering and includes user authentication, course management, and a dashboard for enrolled students.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python 3.11)
- **Data Storage**: In-memory data structures (transitional approach)
- **Authentication**: Session-based authentication with secure password hashing
- **Deployment**: Gunicorn WSGI server with autoscale deployment target

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default)
- **CSS Framework**: Bootstrap 5 with dark theme
- **JavaScript**: Vanilla JavaScript with Bootstrap components
- **Icons**: Font Awesome 6.4.0
- **Responsive Design**: Mobile-first approach with Bootstrap grid system

### Application Structure
```
├── app.py              # Flask app initialization
├── main.py             # Application entry point
├── routes.py           # Route handlers and business logic
├── models.py           # Data models (User, Course, Enrollment)
├── data.py             # Data management and sample data
├── templates/          # HTML templates
├── static/            # CSS, JS, and static assets
└── pyproject.toml     # Python dependencies
```

## Key Components

### 1. User Management System
- **Registration**: Full name, email, mobile, password validation
- **Authentication**: Email/password login with session management
- **Profile Management**: User data persistence and enrolled courses tracking

### 2. Course Management
- **Course Catalog**: Dynamic course listing with detailed information
- **Course Details**: Comprehensive course information including modules, videos, and materials
- **Enrollment System**: Course registration with unique login credentials

### 3. Payment Processing
- **Course Selection**: Available courses display for non-enrolled users
- **Enrollment Flow**: Simulated payment processing for course access
- **Access Control**: Course-specific authentication and authorization

### 4. Learning Dashboard
- **Video Content**: Embedded YouTube videos for course lessons
- **Course Materials**: Downloadable resources and supplementary content
- **Progress Tracking**: Module-based course structure with visual progress indicators
- **User Credentials**: Course-specific login ID and password display

### 5. Interactive Features
- **Responsive Navigation**: Bootstrap-based navigation with user session awareness
- **Form Validation**: Client-side and server-side validation for all forms
- **Flash Messaging**: User feedback system for actions and errors
- **Chatbot Interface**: JavaScript-based chat functionality (framework ready)

## Data Flow

### User Registration Flow
1. User fills registration form (`/signup`)
2. Server validates input data and checks for existing users
3. Password is hashed using Werkzeug security utilities
4. User data is stored in memory (ready for database integration)
5. User is redirected to payment page for course selection

### Course Enrollment Flow
1. Authenticated user selects course from payment page
2. System generates unique course credentials (login ID + password)
3. Enrollment record is created linking user to course
4. User gains access to course dashboard

### Content Access Flow
1. User authenticates with main credentials
2. System checks enrollment status for requested course
3. If enrolled, course dashboard loads with personalized content
4. Videos, materials, and progress tracking become available

## External Dependencies

### Python Packages
- **Flask 3.1.1**: Web framework and routing
- **Werkzeug 3.1.3**: Password hashing and security utilities
- **Gunicorn 23.0.0**: Production WSGI server
- **Email-validator 2.2.0**: Email format validation
- **psycopg2-binary 2.9.10**: PostgreSQL adapter (ready for database migration)
- **Flask-SQLAlchemy 3.1.1**: ORM integration (prepared for future use)

### Frontend Dependencies
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome 6.4.0**: Icon library
- **JavaScript**: Form validation, tooltips, and interactive features

### Infrastructure
- **Replit Environment**: Python 3.11 with PostgreSQL packages
- **OpenSSL**: Secure connections and cryptographic operations

## Deployment Strategy

### Development Environment
- **Local Development**: Flask development server with debug mode
- **Hot Reload**: Automatic server restart on code changes
- **Environment Variables**: Session secret key configuration

### Production Deployment
- **WSGI Server**: Gunicorn with bind configuration for 0.0.0.0:5000
- **Autoscale Target**: Replit's autoscale deployment for traffic handling
- **Port Configuration**: Standardized on port 5000 with wait-for-port health checks
- **Process Management**: Parallel workflow execution with shell task integration

### Database Migration Path
The application is designed for easy migration from in-memory storage to PostgreSQL:
- Data models are structured for ORM compatibility
- PostgreSQL packages are pre-installed in the environment
- Connection parameters can be added through environment variables

## Changelog
- June 25, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.