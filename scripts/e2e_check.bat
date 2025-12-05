@echo off
REM LMS End-to-End Test Script for Windows
REM This script runs the Python end-to-end test for the LMS system

echo === LMS End-to-End Test ===
echo Test started at: %date% %time%

REM Check if we're in the right directory
if not exist "app.py" (
    echo Error: app.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

echo.
echo 1. Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python 3.7 or later.
    pause
    exit /b 1
)

echo    Python version:
python --version

echo.
echo 2. Running end-to-end test...
python scripts/e2e_check.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ All tests passed!
    echo 🎉 LMS progress tracking and certificate generation are working correctly.
) else (
    echo.
    echo ❌ Some tests failed!
    echo Please check the output above for details.
    pause
    exit /b 1
)

echo.
echo === Test completed at: %date% %time% ===
pause