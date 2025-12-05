"""
Debug script to see what's happening in chunk_text
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.document_processor import document_processor

def debug_chunk_text():
    print("Debugging chunk_text function...")
    
    # Read the file content directly
    file_path = r"d:\Digidara-Academy - Copy\Digidara-Academy - Copy\courses\1\documents\python_intro.txt"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Original content length:", len(content))
    
    # Clean the text
    cleaned = document_processor.clean_text(content)
    print("Cleaned content length:", len(cleaned))
    
    # Extract sections
    sections = document_processor.extract_sections(cleaned)
    print(f"Extracted {len(sections)} sections:")
    for i, section in enumerate(sections):
        print(f"  Section {i+1}: {len(section)} chars - {section[:50]}...")
    
    # Chunk the text
    chunks = document_processor.chunk_text(content)
    print(f"\nGenerated {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}: {len(chunk)} chars - {chunk[:50]}...")

if __name__ == "__main__":
    debug_chunk_text()