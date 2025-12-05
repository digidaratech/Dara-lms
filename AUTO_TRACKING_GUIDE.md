# Automatic Course Progress Tracking Guide

## Overview

The LMS system now features **automatic progress tracking** that monitors video playback and automatically marks modules as completed when users watch 100% of the content. This eliminates the need for manual "Mark as Complete" buttons.

---

## How It Works

### 1. **Frontend Tracking (module_video.html)**

The system uses JavaScript to track video progress in real-time:

#### For HTML5 Videos (Local/Direct URLs):
- Monitors the video's `timeupdate` event
- Calculates progress percentage: `(currentTime / duration) × 100`
- Sends updates every **15 seconds** to the backend
- Auto-completes when progress reaches **100%**

#### For Iframe Videos (YouTube/Vimeo):
- **Production Mode**: Estimates progress based on time spent on the page
- **Test Mode**: Fast simulation for testing/demo purposes (completes in ~30 seconds)

### 2. **Backend Processing (app.py)**

The `/api/progress/update` endpoint:
- Receives progress updates via AJAX POST requests
- Validates data types and user authentication
- Calls `update_module_progress()` to save progress
- Returns updated course completion percentage

### 3. **Database Updates (data.py)**

The `update_module_progress()` function:
- Calculates if module should be auto-completed (100% watched)
- Updates `user_module_progress` table
- Triggers `calculate_course_progress()` to update overall course completion
- Automatically generates and emails certificates at 100% course completion

---

## Configuration

### Environment Variables

Add these to your `.env` file or set as environment variables:

```bash
# Enable test mode for fast auto-completion (useful for testing)
AUTO_TRACK_TEST_MODE=False

# Completion threshold percentage (default: 100%)
AUTO_COMPLETE_THRESHOLD=100
```

### Config File (`config.py`)

```python
class Config:
    # Auto-tracking Configuration
    AUTO_TRACK_TEST_MODE = os.environ.get('AUTO_TRACK_TEST_MODE', 'False').lower() == 'true'
    AUTO_COMPLETE_THRESHOLD = float(os.environ.get('AUTO_COMPLETE_THRESHOLD', '100'))
```

---

## Test Mode vs Production Mode

### Test Mode (`AUTO_TRACK_TEST_MODE=True`)
- **Purpose**: Fast testing and demos
- **Duration**: Simulates 60-second videos
- **Completion Time**: ~30 seconds
- **Use Case**: Development, demos, QA testing

**To Enable Test Mode:**
```bash
# Windows PowerShell
$env:AUTO_TRACK_TEST_MODE="true"
python app.py

# Linux/Mac
export AUTO_TRACK_TEST_MODE=true
python app.py
```

### Production Mode (`AUTO_TRACK_TEST_MODE=False`)
- **Purpose**: Real-world usage
- **Duration**: Actual video duration or estimated 5 minutes for iframes
- **Completion Time**: Based on actual watch time
- **Use Case**: Live deployment

---

## Progress Calculation

### Module Progress
```
Progress % = (watched_duration / total_duration) × 100
```

### Auto-Completion Logic
```python
if progress_percentage >= 100:
    mark_as_completed = True
```

### Course Progress
```
Course Progress = (completed_modules / total_modules) × 100
```

---

## UI Components

### Module Progress Bar
Replaces the manual "Mark as Complete" button with a visual progress indicator:

- **0-49%**: Blue badge (`bg-primary`)
- **50-89%**: Info badge (`bg-info`)
- **90-99%**: Info badge (`bg-info`) - "Almost done!"
- **100%**: Success badge (`bg-success`) - "Module completed!"

### Course Progress Bar (Sidebar)
Updates dynamically as modules are completed.

---

## Debug Messages

### Frontend Console Logs

```javascript
[Tracking] Initializing automatic progress tracking
[Tracking] HTML5 video detected - setting up real-time tracking
[Tracking] Watched 85% of Module 2 - Not completed yet
[Tracking] Watched 100% of Module 2 - Marking as completed!
[Tracking] ✅ Progress updated successfully! Course progress: 66.67%
```

### Backend Terminal Logs

```python
[AUTO-TRACK] user_id=5, module_id=2, progress=100%, completed=True
[update_module_progress] ✅ AUTO-COMPLETE: Watched 100% (≥100%) - marking as completed
[calculate_course_progress] ✅ Certificate generated and notifications sent to user 5 for course 3
```

---

## API Endpoint

### POST `/api/progress/update`

**Request Body:**
```json
{
  "course_id": 1,
  "module_id": 2,
  "watched_duration": 275.5,
  "is_completed": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Progress updated successfully",
  "course_progress": 66.67
}
```

---

## Error Handling

### Network Failures
- Progress saved to `localStorage` as fallback
- Automatic retry after 5 seconds
- Queue management prevents duplicate requests

### Database Errors
- Transaction rollback on failure
- Detailed error logging
- Graceful degradation

---

## Certificate Generation

When course progress reaches **100%**:

1. ✅ Certificate automatically generated (`certificate_service.py`)
2. 📧 Email sent with certificate attachment (`email_service.py`)
3. 📱 WhatsApp notification sent (if phone number provided) (`whatsapp_service.py`)

---

## Testing Checklist

### Before Deployment
- [ ] Test with HTML5 video (local file)
- [ ] Test with YouTube iframe
- [ ] Test with Vimeo iframe
- [ ] Verify progress bar updates
- [ ] Confirm auto-completion at 100%
- [ ] Test certificate generation at 100%
- [ ] Verify email notifications
- [ ] Test error recovery (network failures)

### Test Mode Verification
```bash
# Enable test mode
AUTO_TRACK_TEST_MODE=true python app.py

# Expected: Module completes in ~30 seconds
# Expected console message: [Tracking] TEST MODE: Auto-completing in ~30 seconds...
```

---

## Troubleshooting

### Issue: Progress not updating
**Solution:**
1. Check browser console for JavaScript errors
2. Verify user is logged in (`session['user_id']`)
3. Check network tab for failed API calls
4. Review backend logs for database errors

### Issue: Auto-completion not triggering
**Solution:**
1. Verify `AUTO_COMPLETE_THRESHOLD` is set correctly
2. Check if `watched_duration` is being sent properly
3. Review backend logs for auto-complete logic

### Issue: Certificate not generated
**Solution:**
1. Confirm course progress = 100%
2. Check `certificate_service.py` logs
3. Verify SMTP settings for email
4. Check file permissions for certificate storage

---

## Database Schema

### `user_module_progress` Table
```sql
CREATE TABLE user_module_progress (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    module_id INT NOT NULL,
    watched_duration FLOAT DEFAULT 0,
    total_duration FLOAT DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at DATETIME NULL,
    last_watched_at DATETIME NULL,
    UNIQUE KEY (user_id, course_id, module_id)
);
```

### `user_course` Table
```sql
CREATE TABLE user_course (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    progress FLOAT DEFAULT 0,
    enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL
);
```

---

## Performance Optimization

### Debouncing
- Updates throttled to every 2 seconds
- Prevents API flooding

### Queue Management
- Single request at a time
- Queued updates processed sequentially

### Database Optimization
- Combined queries where possible
- Proper indexing on foreign keys

---