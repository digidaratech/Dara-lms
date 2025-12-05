# LMS Server Startup Guide

## Port Configuration
- **Port**: 5000 (matches Google Cloud Console configuration)
- **Host**: 0.0.0.0 (accessible from all network interfaces)

## How to Start the Server

### Option 1: Using the startup script (Recommended)
```bash
python start_server.py
```

### Option 2: Using main.py
```bash
python main.py
```

### Option 3: Direct Flask run
```bash
python app.py
```

## Access URLs
- **Home Page**: http://localhost:5000
- **Login**: http://localhost:5000/login
- **Signup**: http://localhost:5000/signup
- **Courses**: http://localhost:5000/courses
- **Admin Panel**: http://localhost:5000/admin/login

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, you can change it:
1. Edit `app.py` line 1900
2. Edit `main.py` line 4
3. Change `port=5000` to another port (e.g., `port=8080`)
4. Update Google Cloud Console with the new port

### Database Connection Issues
1. Check MySQL is running
2. Verify database credentials in `config.py`
3. Ensure database `digidara_lms` exists
4. Run `python test_mysql_connection.py` to test connection

### Server Crashes
1. Check error logs in the terminal
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Ensure Python version is 3.11 or higher

## Testing Features

After starting the server, run:
```bash
python test_app_features.py
```

This will test all major features:
- Home page
- Database connection
- Authentication pages
- Course pages
- Admin pages
- API endpoints

## Server Configuration

### Current Settings
- **Debug Mode**: True (shows detailed error messages)
- **Reloader**: Disabled (prevents port conflicts)
- **Threading**: Enabled (allows multiple concurrent requests)
- **Host**: 0.0.0.0 (accessible from network)

### Production Settings
For production, change in `app.py`:
```python
app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
```

## Common Issues

### Issue: "Address already in use"
**Solution**: Change the port number or kill the process using that port

### Issue: "Connection refused"
**Solution**: 
1. Check if MySQL is running
2. Verify database credentials
3. Check firewall settings

### Issue: "Module not found"
**Solution**: Install missing dependencies:
```bash
pip install flask mysql-connector-python werkzeug requests
```

## Logs

Server logs will show:
- Database connection status
- Request handling
- Error messages
- Debug information

Monitor the terminal output for any errors or warnings.

