#!/bin/bash

# LMS End-to-End Test Script
# This script runs the Python end-to-end test for the LMS system

echo "=== LMS End-to-End Test ==="
echo "Test started at: $(date)"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "Error: app.py not found. Please run this script from the project root directory."
    exit 1
fi

echo ""
echo "1. Checking Python environment..."
if ! command -v python &> /dev/null; then
    echo "Error: Python not found. Please install Python 3.7 or later."
    exit 1
fi

echo "   Python version: $(python --version)"

echo ""
echo "2. Running end-to-end test..."
python scripts/e2e_check.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    echo "🎉 LMS progress tracking and certificate generation are working correctly."
else
    echo ""
    echo "❌ Some tests failed!"
    echo "Please check the output above for details."
    exit 1
fi

echo ""
echo "=== Test completed at: $(date) ==="