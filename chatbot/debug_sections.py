"""
Debug script to see what sections are being extracted
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.document_processor import document_processor

def debug_sections():
    print("Debugging document sections...")
    
    # Read the file content directly
    file_path = r"d:\Digidara-Academy - Copy\Digidara-Academy - Copy\courses\1\documents\python_intro.txt"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("File content:")
    print(repr(content))
    
    print("\nExtracted sections:")
    sections = document_processor.extract_sections(content)
    print(f"Total sections: {len(sections)}")
    
    for i, section in enumerate(sections):
        print(f"\n--- Section {i+1} ---")
        print(section)
        print("---")

if __name__ == "__main__":
    debug_sections()