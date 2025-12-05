import mysql.connector as mysql_connector
from datetime import datetime, timedelta
import hashlib
import secrets
import re
from werkzeug.security import generate_password_hash, check_password_hash

# Remove the standalone MySQL connection - we'll use Flask's MySQL connection
# mysql = MySQLdb.connect(
#     host='localhost',
#     user='root',
#     password='',
#     db='digidara_lms',
#     charset='utf8mb4'
# )

# USER FUNCTIONS

def get_connection(mysql):
    """Helper function to get connection from either MySQLWrapper or direct connection."""
    if hasattr(mysql, 'get_connection'):
        # MySQLWrapper class
        connection = mysql.get_connection()
        if not connection:
            print("[get_connection] ERROR: No connection available")
            return None
        return connection
    else:
        # Direct connection object
        return mysql

def create_user(name, email, mobile, password, mysql):
    """Create a new user account."""
    try:
        # Hash the password
        password_hash = generate_password_hash(password)
        
        connection = get_connection(mysql)
        if not connection:
            print("[create_user] ERROR: No connection available")
            return None
            
        cur = connection.cursor()
        cur.execute("INSERT INTO users (name, email, mobile, password_hash) VALUES (%s, %s, %s, %s)",
                    (name, email, mobile, password_hash))
        connection.commit()
        user_id = cur.lastrowid
        cur.close()
        return user_id
    except Exception as e:
        print("[create_user] ERROR:", e)
        return None

def login_user(email, password, mysql):
    """Authenticate user login."""
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        connection = get_connection(mysql)
        if not connection:
            print("[login_user] ERROR: No connection available")
            return None
            
        cur = connection.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None
    except Exception as e:
        print("[login_user] ERROR:", e)
        return None

def get_user_by_email(email, mysql):
    """Get user by email."""
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[get_user_by_email] ERROR: No connection available")
            return None
            
        cur = connection.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        return user
    except Exception as e:
        print(f"[get_user_by_email] ERROR: {e}")
        return None

def get_user_by_id(user_id, mysql):
    """Get user by ID."""
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[get_user_by_id] ERROR: No connection available")
            return None
            
        cur = connection.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        return user
    except Exception as e:
        print(f"[get_user_by_id] ERROR: {e}")
        return None

# COURSE FUNCTIONS

def get_all_courses(mysql):
    """Get all available courses."""
    try:
        print(f"[get_all_courses] Starting with mysql object: {type(mysql)}")
        
        connection = get_connection(mysql)
        if not connection:
            print("[get_all_courses] ERROR: No connection available")
            return []
        
        cur = connection.cursor(dictionary=True)
        
        # Test if the courses table exists first
        cur.execute("SHOW TABLES LIKE 'courses'")
        table_exists = cur.fetchone()
        if not table_exists:
            print("[get_all_courses] ERROR: Courses table does not exist")
            cur.close()
            return []
        
        # Check table structure
        cur.execute("DESCRIBE courses")
        columns = cur.fetchall()
        column_names = [col['Field'] for col in columns]
        print(f"[get_all_courses] Available columns: {column_names}")
        
        # Build query based on available columns
        required_columns = ['id', 'title', 'description', 'instructor', 'duration', 'price']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"[get_all_courses] ERROR: Missing required columns: {missing_columns}")
            cur.close()
            return []
        
        # Check if optional columns exist
        has_status = 'status' in column_names
        has_category = 'category' in column_names
        has_level = 'level' in column_names
        has_created_at = 'created_at' in column_names
        
        # Build the query dynamically
        select_columns = ['id', 'title', 'description', 'instructor', 'duration', 'price']
        if has_status:
            select_columns.append("COALESCE(status, 'active') as status")
        else:
            select_columns.append("'active' as status")
            
        if has_category:
            select_columns.append("COALESCE(category, 'programming') as category")
        else:
            select_columns.append("'programming' as category")
            
        if has_level:
            select_columns.append("COALESCE(level, 'beginner') as level")
        else:
            select_columns.append("'beginner' as level")
        
        query = f"""
            SELECT {', '.join(select_columns)}
            FROM courses 
            WHERE COALESCE(status, 'active') = 'active'
        """
        
        if has_created_at:
            query += " ORDER BY created_at DESC"
        else:
            query += " ORDER BY id DESC"
        
        print(f"[get_all_courses] Executing query: {query}")
        
        cur.execute(query)
        rows = cur.fetchall()
        print(f"[get_all_courses] Found {len(rows)} courses")
        
        data = []
        for row in rows:
            try:
                course_data = {
                    "id": row["id"],
                    "title": row["title"],
                    "description": row["description"],
                    "instructor": row["instructor"],
                    "duration": row["duration"],
                    "price": float(row["price"]) if row["price"] else 0.0,
                    "status": row["status"],
                    "category": row["category"],
                    "level": row["level"],
                    "modules": []  # will be loaded separately
                }
                data.append(course_data)
            except Exception as row_error:
                print(f"[get_all_courses] ERROR processing row {row.get('id', 'unknown')}: {row_error}")
                continue
        
        cur.close()
        print(f"[get_all_courses] Successfully processed {len(data)} courses")
        return data
        
    except Exception as e:
        print(f"[get_all_courses] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_course_by_id(course_id, mysql):
    """Get course by ID, with modules."""
    try:
        print(f"[get_course_by_id] Looking for course ID: {course_id}")
        connection = get_connection(mysql)
        if not connection:
            print("[get_course_by_id] ERROR: No connection available")
            return None
            
        cur = connection.cursor(dictionary=True)
        cur.execute("""
            SELECT id, title, description, instructor, duration, price, 
                   COALESCE(status, 'active') as status,
                   COALESCE(category, 'programming') as category,
                   COALESCE(level, 'beginner') as level
            FROM courses WHERE id = %s
        """, (course_id,))
        row = cur.fetchone()
        cur.close()
        if not row:
            print(f"[get_course_by_id] Course ID {course_id} not found")
            return None
        print(f"[get_course_by_id] Found course: {row['title']}")
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "instructor": row["instructor"],
            "duration": row["duration"],
            "price": float(row["price"]),
            "status": row["status"],
            "category": row["category"],
            "level": row["level"],
            "modules": get_modules_by_course(row["id"], mysql)
        }
    except Exception as e:
        print(f"[get_course_by_id] ERROR: {e}")
        return None

def get_modules_by_course(course_id, mysql):
    """Return a list of modules for a given course."""
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[get_modules_by_course] ERROR: No connection available")
            return []
            
        cur = connection.cursor(dictionary=True)
        cur.execute("""
            SELECT id, title, description, video_url, duration, order_index 
            FROM course_modules 
            WHERE course_id = %s 
            ORDER BY order_index
        """, (course_id,))
        modules = cur.fetchall()
        cur.close()
        return [{"id": m["id"], "name": m["title"], "description": m["description"], 
                "video_url": m["video_url"], "duration": m["duration"], "status": "active"} for m in modules]
    except Exception as e:
        print("[get_modules_by_course] ERROR:", e)
        return []

# ENROLLMENT FUNCTIONS

def is_user_enrolled(user_id, course_id, mysql):
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[is_user_enrolled] ERROR: No connection available")
            return False
            
        cur = connection.cursor()
        cur.execute("SELECT id FROM user_course WHERE user_id = %s AND course_id = %s", (user_id, course_id))
        res = cur.fetchone()
        cur.close()
        return res is not None
    except Exception as e:
        print(f"[is_user_enrolled] ERROR: {e}")
        return False

def enroll_user(user_id, course_id, mysql):
    try:
        if is_user_enrolled(user_id, course_id, mysql):
            return False
        connection = get_connection(mysql)
        if not connection:
            print("[enroll_user] ERROR: No connection available")
            return False
            
        cur = connection.cursor()
        cur.execute("INSERT INTO user_course (user_id, course_id, enrolled_at) VALUES (%s, %s, NOW())", (user_id, course_id))
        connection.commit()
        cur.close()
        return True
    except Exception as e:
        print("[enroll_user] ERROR:", e)
        return False

def get_enrollment(user_id, course_id, mysql):
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[get_enrollment] ERROR: No connection available")
            return None
            
        cur = connection.cursor(dictionary=True)
        cur.execute("SELECT * FROM user_course WHERE user_id = %s AND course_id = %s", (user_id, course_id))
        enrollment = cur.fetchone()
        cur.close()
        return enrollment
    except Exception as e:
        print(f"[get_enrollment] ERROR: {e}")
        return None

def get_enrolled_course_ids(user_id, mysql):
    try:
        # Handle both MySQLWrapper and direct connection objects
        if hasattr(mysql, 'get_connection'):
            # MySQLWrapper class
            connection = mysql.get_connection()
            if not connection:
                print("[get_enrolled_course_ids] ERROR: No connection available")
                return []
        else:
            # Direct connection object
            connection = mysql
        
        cur = connection.cursor(dictionary=True)
        cur.execute("SELECT course_id FROM user_course WHERE user_id = %s", (user_id,))
        rows = cur.fetchall()
        cur.close()
        return [r["course_id"] for r in rows]
    except Exception as e:
        print(f"[get_enrolled_course_ids] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_courses_by_user(user_id, mysql):
    """Return all courses a user is enrolled in with progress."""
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[get_courses_by_user] ERROR: No connection available")
            return []
            
        cur = connection.cursor(dictionary=True)
        cur.execute("""
            SELECT c.*, uc.progress, uc.enrolled_at, uc.completed_at
            FROM courses c
            JOIN user_course uc ON c.id = uc.course_id
            WHERE uc.user_id = %s
            ORDER BY uc.enrolled_at DESC
        """, (user_id,))
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        print(f"[get_courses_by_user] ERROR: {e}")
        return []

# PROGRESS TRACKING FUNCTIONS

def get_user_course_progress(user_id, course_id, mysql):
    """Get detailed progress for a user in a specific course."""
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[get_user_course_progress] ERROR: No connection available")
            return []
            
        cur = connection.cursor(dictionary=True)
        cur.execute("""
            SELECT 
                cm.id as module_id,
                cm.title as module_title,
                cm.duration as module_duration,
                COALESCE(ump.is_completed, FALSE) as is_completed,
                COALESCE(ump.watched_duration, 0) as watched_duration,
                COALESCE(ump.total_duration, 0) as total_duration,
                COALESCE(ump.last_watched_at, NULL) as last_watched_at
            FROM course_modules cm
            LEFT JOIN user_module_progress ump ON cm.id = ump.module_id AND ump.user_id = %s
            WHERE cm.course_id = %s
            ORDER BY cm.order_index
        """, (user_id, course_id))
        modules = cur.fetchall()
        cur.close()
        return modules
    except Exception as e:
        print(f"[get_user_course_progress] ERROR: {e}")
        return []

def update_module_progress(user_id, course_id, module_id, watched_duration, mysql, is_completed=False):
    """Update user's progress for a specific module."""
    connection = None
    cur = None
    
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[update_module_progress] ERROR: No connection available")
            return False
        
        print("[update_module_progress] Database connection established")
        cur = connection.cursor()
        
        # Get module total duration
        cur.execute("SELECT duration FROM course_modules WHERE id = %s", (module_id,))
        module = cur.fetchone()
        if not module:
            print(f"[update_module_progress] ERROR: Module {module_id} not found")
            if cur:
                cur.close()
            return False
        
        # Convert duration string to seconds (format: MM:SS or seconds)
        duration_str = module[0]
        total_seconds = 0
        if duration_str:
            try:
                # Handle different duration formats
                if ':' in duration_str:
                    # Format: MM:SS
                    parts = duration_str.split(':')
                    if len(parts) == 2:
                        total_seconds = int(parts[0]) * 60 + int(parts[1])
                elif duration_str.isdigit():
                    # Format: seconds as string
                    total_seconds = int(duration_str)
                else:
                    # Try to convert to float as fallback
                    total_seconds = int(float(duration_str))
            except (ValueError, TypeError):
                total_seconds = 0  # Don't use default if parsing fails
        
        print(f"[update_module_progress] Module duration: {duration_str} ({total_seconds} seconds)")
        
        # Auto-complete logic: If watched 100% of video, mark as completed
        # Only mark as completed when watched duration is equal to or greater than total duration
        if total_seconds > 0 and not is_completed:
            # Check if watched duration is at least equal to total duration (with small tolerance for floating point)
            if watched_duration >= total_seconds:
                is_completed = True
                print(f"[update_module_progress] ✅ AUTO-COMPLETE: Watched {watched_duration}s (≥{total_seconds}s) - marking as completed")
            # Additional check to prevent premature completion
            elif watched_duration > 0 and total_seconds > 0:
                watch_percentage = watched_duration / total_seconds
                if watch_percentage >= 0.995:  # 99.5% threshold to account for floating point precision
                    is_completed = True
                    print(f"[update_module_progress] ✅ AUTO-COMPLETE: Watched {watched_duration}s ({watch_percentage*100:.2f}% of {total_seconds}s) - marking as completed")
        
        # Insert or update progress
        print(f"[update_module_progress] Inserting/updating progress record (is_completed={is_completed})")
        cur.execute("""
            INSERT INTO user_module_progress 
            (user_id, course_id, module_id, watched_duration, total_duration, is_completed, completed_at, last_watched_at)
            VALUES (%s, %s, %s, %s, %s, %s, IF(%s = TRUE, NOW(), NULL), NOW())
            ON DUPLICATE KEY UPDATE
            watched_duration = %s,
            is_completed = %s,
            completed_at = IF(%s = TRUE AND completed_at IS NULL, NOW(), completed_at),
            last_watched_at = NOW()
        """, (user_id, course_id, module_id, watched_duration, total_seconds, is_completed, is_completed,
               watched_duration, is_completed, is_completed))
        
        connection.commit()
        print("[update_module_progress] Progress record committed to database")
        
        if cur:
            cur.close()
        
        # Recalculate course progress
        print("[update_module_progress] Recalculating course progress")
        calculate_course_progress(user_id, course_id, mysql)
        print("[update_module_progress] SUCCESS")
        return True
        
    except Exception as e:
        print(f"[update_module_progress] ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Rollback on error
        if connection:
            try:
                connection.rollback()
                print("[update_module_progress] Transaction rolled back")
            except Exception as rb_error:
                print(f"[update_module_progress] Rollback error: {rb_error}")
        
        # Return more specific error information
        return False
    finally:
        # Ensure cursor is always closed
        if cur:
            try:
                cur.close()
            except:
                pass

def calculate_course_progress(user_id, course_id, mysql):
    """Calculate and update overall course progress for a user."""
    print(f"\n[calculate_course_progress] START - user_id: {user_id}, course_id: {course_id}")
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[calculate_course_progress] ERROR: No connection available")
            return 0
        
        print("[calculate_course_progress] Database connection established")
        cur = connection.cursor()
        
        # Optimize: Get total and completed modules in a single query
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM course_modules WHERE course_id = %s) as total_modules,
                COALESCE(SUM(CASE 
                    WHEN ump.is_completed = TRUE THEN 100.0
                    WHEN ump.watched_duration > 0 AND ump.total_duration > 0 THEN (ump.watched_duration / ump.total_duration) * 100.0
                    ELSE 0 
                END), 0) as completed_modules,
                GROUP_CONCAT(CONCAT('watched:', COALESCE(ump.watched_duration, 0), ', total:', COALESCE(ump.total_duration, 0)) SEPARATOR '; ') as debug_info
            FROM course_modules cm
            LEFT JOIN user_module_progress ump ON cm.id = ump.module_id AND ump.user_id = %s
            WHERE cm.course_id = %s
        """, (course_id, user_id, course_id))
        result = cur.fetchone()
        
        total_modules = result[0] if result and result[0] is not None else 0
        completed_modules = result[1] if result and len(result) > 1 and result[1] is not None else 0
        debug_info = result[2] if result and len(result) > 2 and result[2] is not None else ""
        
        print(f"[calculate_course_progress] Total modules: {total_modules}, Completed: {completed_modules}")
        print(f"[calculate_course_progress] Debug info: {debug_info}")
        if total_modules == 0:
            print("[calculate_course_progress] No modules found for course")
            cur.close()
            return 0
        
        # Calculate progress percentage based on actual module progress
        # The SQL query calculates the SUM of progress percentages for all modules
        # So we need to divide by total_modules to get the average progress percentage
        progress_percentage = completed_modules / total_modules if total_modules > 0 else 0
        print(f"[calculate_course_progress] Progress percentage: {progress_percentage}%")
        
        # Check if course was previously completed (combined with update query)
        cur.execute("SELECT completed_at FROM user_course WHERE user_id = %s AND course_id = %s", (user_id, course_id))
        previous_result = cur.fetchone()
        was_previously_completed = previous_result and previous_result[0] is not None
        print(f"[calculate_course_progress] Was previously completed: {was_previously_completed}")
        
        # Update user_course table
        print(f"[calculate_course_progress] Updating user_course table with progress: {progress_percentage}%")
        cur.execute("""
            UPDATE user_course 
            SET progress = %s,
                completed_at = CASE WHEN %s >= 100 AND completed_at IS NULL THEN NOW() ELSE completed_at END
            WHERE user_id = %s AND course_id = %s
        """, (progress_percentage, progress_percentage, user_id, course_id))
        
        connection.commit()
        print("[calculate_course_progress] Progress committed to database")
        
        # Check if course is now completed (100% progress)
        is_now_completed = progress_percentage >= 100
        print(f"[calculate_course_progress] Is now completed: {is_now_completed}")
        
        # If course was just completed, check if exam is required and passed before generating certificate
        if is_now_completed and not was_previously_completed:
            print("[calculate_course_progress] Course just completed! Generating course completion certificate...")
            
            # Generate course completion certificate (exam not required for this)
            print("[calculate_course_progress] Generating course completion certificate...")
            try:
                # Import certificate service
                from services.certificate_service import generate_certificate, save_certificate_record
                
                # Optimize: Get user and course details in a single query
                cur.execute("""
                    SELECT u.name, u.email, u.mobile, c.title 
                    FROM users u, courses c 
                    WHERE u.id = %s AND c.id = %s
                """, (user_id, course_id))
                details_result = cur.fetchone()
                
                if details_result:
                    user_name = details_result[0] if details_result[0] else "User"
                    user_email = details_result[1] if details_result[1] else ""
                    user_phone = details_result[2] if details_result[2] else None
                    course_title = details_result[3] if details_result[3] else "Course"
                    
                    print(f"[calculate_course_progress] Generating course certificate for {user_name} - {course_title}")
                    
                    # Generate course completion certificate (with duplicate check built-in)
                    certificate_id = save_certificate_record(user_id, course_id, "", mysql, 'course')
                    if certificate_id:
                        try:
                            certificate_path = generate_certificate(user_name, course_title, datetime.now(), certificate_id, 'course')
                            print(f"[calculate_course_progress] Course certificate generated: {certificate_path}")
                            
                            # Update certificate path in database
                            cur.execute("""
                                UPDATE certificates 
                                SET certificate_path = %s 
                                WHERE id = %s
                            """, (certificate_path, certificate_id))
                            connection.commit()
                            
                            # Send email with certificate
                            try:
                                from services.email_service import send_certificate_email
                                email_sent = send_certificate_email(user_name, user_email, course_title, certificate_path)
                                if email_sent:
                                    print(f"[calculate_course_progress] Course certificate email sent to {user_email}")
                                else:
                                    print(f"[calculate_course_progress] Failed to send course certificate email to {user_email}")
                            except Exception as email_error:
                                print(f"[calculate_course_progress] Course certificate email sending error: {email_error}")
                                import traceback
                                traceback.print_exc()
                            
                            # Send WhatsApp notification (if user has phone number)
                            if user_phone:
                                try:
                                    from services.whatsapp_service import send_certificate_whatsapp
                                    certificate_url = f"https://your-lms-domain.com/certificate/{course_id}/download?type=course"
                                    whatsapp_sent = send_certificate_whatsapp(user_name, user_phone, course_title, certificate_url)
                                    if whatsapp_sent:
                                        print(f"[calculate_course_progress] WhatsApp notification sent to {user_phone}")
                                    else:
                                        print(f"[calculate_course_progress] Failed to send WhatsApp notification to {user_phone}")
                                except Exception as whatsapp_error:
                                    print(f"[calculate_course_progress] WhatsApp sending error: {whatsapp_error}")
                                    import traceback
                                    traceback.print_exc()
                            
                            print(f"[calculate_course_progress] ✅ Course certificate generated and notifications sent to user {user_id} for course {course_id}")
                        except Exception as cert_gen_error:
                            print(f"[calculate_course_progress] Course certificate generation error: {cert_gen_error}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"[calculate_course_progress] Failed to save course certificate record for user {user_id} course {course_id}")
            except Exception as cert_error:
                print(f"[calculate_course_progress] Course certificate process error: {cert_error}")
                import traceback
                traceback.print_exc()
        else:
            if is_now_completed and was_previously_completed:
                print("[calculate_course_progress] Course was already completed previously")

        cur.close()
        print(f"[calculate_course_progress] SUCCESS - Returning progress: {progress_percentage}%")
        return progress_percentage
    except Exception as e:
        print(f"[calculate_course_progress] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 0

# WATCH TIME TRACKING FUNCTIONS

def record_watch_time(user_id, course_id, module_id, watch_duration, mysql):
    """Record watch time for analytics."""
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[record_watch_time] ERROR: No connection available")
            return False
            
        cur = connection.cursor()
        cur.execute("""
            INSERT INTO user_watch_time 
            (user_id, course_id, module_id, watch_date, watch_duration)
            VALUES (%s, %s, %s, CURDATE(), %s)
        """, (user_id, course_id, module_id, watch_duration))
        connection.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"[record_watch_time] ERROR: {e}")
        return False

def get_user_watch_time(user_id, mysql, days=7):
    """Get user's watch time for the last N days."""
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[get_user_watch_time] ERROR: No connection available")
            return []
            
        cur = connection.cursor(dictionary=True)
        cur.execute("""
            SELECT 
                watch_date,
                SUM(watch_duration) as total_watch_time_seconds,
                COUNT(DISTINCT course_id) as courses_watched
            FROM user_watch_time 
            WHERE user_id = %s AND watch_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            GROUP BY watch_date
            ORDER BY watch_date DESC
        """, (user_id, days))
        data = cur.fetchall()
        cur.close()
        return data
    except Exception as e:
        print(f"[get_user_watch_time] ERROR: {e}")
        return []

# ANALYTICS FUNCTIONS

def get_user_analytics(user_id, mysql):
    """Get comprehensive analytics for a user."""
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[get_user_analytics] ERROR: No connection available")
            return {}
            
        cur = connection.cursor(dictionary=True)
        
        # Basic user stats
        cur.execute("""
            SELECT 
                u.name,
                u.email,
                COALESCE(COUNT(DISTINCT uc.course_id), 0) as enrolled_courses,
                COALESCE(COUNT(DISTINCT CASE WHEN uc.progress >= 100 THEN uc.course_id END), 0) as completed_courses,
                COALESCE(AVG(uc.progress), 0) as avg_progress,
                COALESCE(SUM(uwt.watch_duration), 0) as total_watch_time_seconds,
                COALESCE(COUNT(DISTINCT uwt.watch_date), 0) as active_days
            FROM users u
            LEFT JOIN user_course uc ON u.id = uc.user_id
            LEFT JOIN user_watch_time uwt ON u.id = uwt.user_id
            WHERE u.id = %s
            GROUP BY u.id, u.name, u.email
        """, (user_id,))
        user_stats = cur.fetchone()
        
        # Recent activity
        cur.execute("""
            SELECT 
                c.title as course_title,
                COALESCE(uc.progress, 0) as progress,
                uc.enrolled_at,
                uc.completed_at
            FROM user_course uc
            JOIN courses c ON uc.course_id = c.id
            WHERE uc.user_id = %s
            ORDER BY uc.enrolled_at DESC
            LIMIT 5
        """, (user_id,))
        recent_courses = cur.fetchall()
        
        # Daily watch time for charts
        cur.execute("""
            SELECT 
                watch_date,
                COALESCE(SUM(watch_duration), 0) as watch_time_seconds
            FROM user_watch_time 
            WHERE user_id = %s AND watch_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY watch_date
            ORDER BY watch_date
        """, (user_id,))
        daily_watch_time = cur.fetchall()
        
        cur.close()
        
        return {
            'user_stats': user_stats or {},
            'recent_courses': recent_courses,
            'daily_watch_time': daily_watch_time
        }
    except Exception as e:
        print(f"[get_user_analytics] ERROR: {e}")
        return {}

def get_admin_analytics(mysql):
    """Get comprehensive analytics for admin dashboard."""
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[get_admin_analytics] ERROR: No connection available")
            return {}
            
        cur = connection.cursor(dictionary=True)
        
        # Basic stats
        cur.execute("SELECT COUNT(*) as total_users FROM users")
        result = cur.fetchone()
        total_users = result['total_users'] if result else 0
        
        cur.execute("SELECT COUNT(*) as total_courses FROM courses")
        result = cur.fetchone()
        total_courses = result['total_courses'] if result else 0
        
        cur.execute("SELECT COUNT(*) as total_enrollments FROM user_course")
        result = cur.fetchone()
        total_enrollments = result['total_enrollments'] if result else 0
        
        # Revenue calculation
        cur.execute("""
            SELECT COALESCE(SUM(c.price), 0) as total_revenue 
            FROM user_course uc
            JOIN courses c ON uc.course_id = c.id
        """)
        result = cur.fetchone()
        total_revenue = result['total_revenue'] if result else 0
        
        # Recent activity
        cur.execute("""
            SELECT COUNT(*) as recent_users 
            FROM users 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        result = cur.fetchone()
        recent_users = result['recent_users'] if result else 0
        
        cur.execute("""
            SELECT COUNT(*) as recent_enrollments 
            FROM user_course 
            WHERE enrolled_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        result = cur.fetchone()
        recent_enrollments = result['recent_enrollments'] if result else 0
        
        # Course popularity
        cur.execute("""
            SELECT 
                c.title,
                COALESCE(COUNT(uc.user_id), 0) as enrollment_count,
                COALESCE(AVG(uc.progress), 0) as avg_progress,
                COALESCE(SUM(c.price), 0) as revenue
            FROM courses c
            LEFT JOIN user_course uc ON c.id = uc.course_id
            GROUP BY c.id, c.title
            ORDER BY enrollment_count DESC
            LIMIT 5
        """)
        popular_courses = cur.fetchall()
        
        # User growth (last 30 days)
        cur.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as new_users
            FROM users 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        user_growth = cur.fetchall()
        
        # Daily watch time
        cur.execute("""
            SELECT 
                watch_date,
                COALESCE(COUNT(DISTINCT user_id), 0) as active_users,
                COALESCE(SUM(watch_duration), 0) as total_watch_time_seconds
            FROM user_watch_time 
            WHERE watch_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY watch_date
            ORDER BY watch_date
        """)
        daily_watch_stats = cur.fetchall()
        
        cur.close()
        
        return {
            'total_users': total_users,
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'total_revenue': total_revenue,
            'recent_users': recent_users,
            'recent_enrollments': recent_enrollments,
            'popular_courses': popular_courses,
            'user_growth': user_growth,
            'daily_watch_stats': daily_watch_stats
        }
    except Exception as e:
        print(f"[get_admin_analytics] ERROR: {e}")
        return {
            'total_users': 0,
            'total_courses': 0,
            'total_enrollments': 0,
            'total_revenue': 0,
            'recent_users': 0,
            'recent_enrollments': 0,
            'popular_courses': [],
            'user_growth': [],
            'daily_watch_stats': []
        }

def get_course_analytics(course_id, mysql):
    """Get analytics for a specific course."""
    try:
        connection = get_connection(mysql)
        if not connection:
            print("[get_course_analytics] ERROR: No connection available")
            return {}
            
        cur = connection.cursor(dictionary=True)
        
        # Course stats
        cur.execute("""
            SELECT 
                c.title,
                c.instructor,
                COUNT(DISTINCT uc.user_id) as total_enrollments,
                COUNT(DISTINCT CASE WHEN uc.progress >= 100 THEN uc.user_id END) as completed_enrollments,
                AVG(uc.progress) as avg_progress,
                SUM(c.price) as total_revenue
            FROM courses c
            LEFT JOIN user_course uc ON c.id = uc.course_id
            WHERE c.id = %s
            GROUP BY c.id, c.title, c.instructor
        """, (course_id,))
        course_stats = cur.fetchone()
        
        # Module completion rates
        cur.execute("""
            SELECT 
                cm.title as module_title,
                COUNT(DISTINCT ump.user_id) as users_started,
                COUNT(DISTINCT CASE WHEN ump.is_completed THEN ump.user_id END) as users_completed,
                AVG(CASE WHEN ump.is_completed THEN 100 ELSE ump.watched_duration / ump.total_duration * 100 END) as avg_progress
            FROM course_modules cm
            LEFT JOIN user_module_progress ump ON cm.id = ump.module_id
            WHERE cm.course_id = %s
            GROUP BY cm.id, cm.title
            ORDER BY cm.order_index
        """, (course_id,))
        module_stats = cur.fetchall()
        
        cur.close()
        
        return {
            'course_stats': course_stats,
            'module_stats': module_stats
        }
    except Exception as e:
        print(f"[get_course_analytics] ERROR: {e}")
        return {}

# UTILITY FUNCTIONS

def format_duration(seconds):
    """Convert seconds to MM:SS format."""
    if not seconds:
        return "00:00"
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:02d}"

def format_watch_time(seconds):
    """Convert seconds to human readable format."""
    if not seconds:
        return "0 minutes"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def calculate_completion_percentage(completed_modules, total_modules):
    """Calculate completion percentage."""
    if total_modules == 0:
        return 0
    return round((completed_modules / total_modules) * 100, 2)
