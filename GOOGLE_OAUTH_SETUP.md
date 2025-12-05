# Google OAuth Setup Guide

This guide will help you set up Google OAuth for your Learning Management System.

## Prerequisites

1. A Google account
2. Access to Google Cloud Console

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API (if not already enabled)

## Step 2: Configure OAuth Consent Screen

1. In the Google Cloud Console, go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type (unless you have a Google Workspace organization)
3. Fill in the required information:
   - App name: "Your LMS Name"
   - User support email: Your email
   - Developer contact information: Your email
4. Add scopes:
   - `openid`
   - `email`
   - `profile`
5. Add test users (your email address)
6. Save and continue

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Set the following:
   - Name: "Your LMS Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:5000` (for development - CURRENT PORT)
     - `http://127.0.0.1:5000` (for development - alternative)
     - `https://yourdomain.com` (for production)
   - Authorized redirect URIs:
     - `http://localhost:5000` (for development - CURRENT PORT)
     - `http://127.0.0.1:5000` (for development - alternative)
     - `https://yourdomain.com` (for production)
5. Click "Create"
6. Copy the Client ID and Client Secret

## Step 4: Update Your Application

### Option 1: Environment Variables (Recommended)

Create a `.env` file in your project root:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
SECRET_KEY=your-secret-key
```

### Option 2: Direct Configuration

Update the `config.py` file:

```python
GOOGLE_CLIENT_ID = 'your-actual-client-id.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'your-actual-client-secret'
```

## Step 5: Update Templates

In both `templates/login.html` and `templates/signup.html`, replace:

```javascript
client_id: 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com'
```

with your actual Client ID:

```javascript
client_id: 'your-actual-client-id.apps.googleusercontent.com'
```

## Step 6: Install Dependencies

Run the following command to install the required dependencies:

```bash
pip install requests
```

Or if using uv:

```bash
uv sync
```

## Step 7: Test the Integration

1. Start your Flask application
2. Go to the login or signup page
3. Click "Continue with Google"
4. You should be redirected to Google's OAuth consent screen
5. After authorization, you should be logged in

## Troubleshooting

### Common Issues:

1. **"Invalid Client ID" error**
   - Make sure you're using the correct Client ID
   - Ensure the domain is added to authorized origins

2. **"Redirect URI mismatch" error**
   - Check that your redirect URI matches exactly what's configured in Google Console
   - Include the protocol (http:// or https://)

3. **"Access blocked" error**
   - Make sure your app is published or you're using a test user
   - Check that all required scopes are added

4. **CORS errors**
   - Ensure your domain is in the authorized JavaScript origins
   - Check that you're using the correct protocol

### Security Notes:

1. Never commit your Client Secret to version control
2. Use environment variables for sensitive configuration
3. Regularly rotate your Client Secret
4. Monitor your OAuth usage in Google Cloud Console

## Production Deployment

For production deployment:

1. Update authorized origins to your production domain
2. Use HTTPS for all OAuth endpoints
3. Set up proper environment variables
4. Consider using a secrets management service
5. Monitor OAuth usage and errors

## Support

If you encounter issues:

1. Check the Google Cloud Console for error logs
2. Verify your OAuth configuration
3. Test with a simple OAuth flow first
4. Check browser console for JavaScript errors 