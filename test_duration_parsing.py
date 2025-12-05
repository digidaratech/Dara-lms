#!/usr/bin/env python3
"""
Test script for duration parsing functionality
This script tests the duration parsing logic that we've implemented
"""

def parse_duration_to_seconds(duration_str):
    """Parse duration string (MM:SS or seconds) to seconds"""
    if not duration_str:
        return 0
    
    try:
        # Handle different duration formats
        if ':' in duration_str:
            # Format: MM:SS
            parts = duration_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
        elif duration_str.isdigit():
            # Format: seconds as string
            return int(duration_str)
        else:
            # Try to convert to float as fallback
            return int(float(duration_str))
    except (ValueError, TypeError):
        return 0  # Return 0 if parsing fails
    
    return 0  # Default to 0 if parsing fails

def format_seconds_to_mmss(seconds):
    """Format seconds to MM:SS"""
    if not seconds or seconds <= 0:
        return "00:00"
    
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

def test_duration_parsing():
    """Test the duration parsing function with various inputs"""
    test_cases = [
        # (input, expected_output)
        ("10:30", 630),      # 10 minutes 30 seconds
        ("5:05", 305),       # 5 minutes 5 seconds
        ("0:45", 45),        # 45 seconds
        ("120", 120),        # 120 seconds
        ("600", 600),        # 600 seconds
        ("", 0),             # Empty string
        ("invalid", 0),      # Invalid input
        ("10:90", 690),      # 10 minutes 90 seconds (11 minutes 30 seconds)
        ("1:30:45", 0),      # Invalid format (HH:MM:SS)
    ]
    
    print("Testing duration parsing function:")
    print("=" * 40)
    
    for input_str, expected in test_cases:
        result = parse_duration_to_seconds(input_str)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input: '{input_str}' -> Output: {result} seconds (expected: {expected})")
    
    print("\nTesting seconds to MM:SS formatting:")
    print("=" * 40)
    
    format_test_cases = [
        # (input_seconds, expected_output)
        (630, "10:30"),      # 10 minutes 30 seconds
        (305, "05:05"),      # 5 minutes 5 seconds
        (45, "00:45"),       # 45 seconds
        (120, "02:00"),      # 2 minutes
        (0, "00:00"),        # 0 seconds
        (-5, "00:00"),       # Negative seconds
    ]
    
    for input_seconds, expected in format_test_cases:
        result = format_seconds_to_mmss(input_seconds)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input: {input_seconds} -> Output: '{result}' (expected: '{expected}')")

if __name__ == "__main__":
    test_duration_parsing()