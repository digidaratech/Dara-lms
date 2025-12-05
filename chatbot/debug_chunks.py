"""
Debug script to see what chunks are being generated
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.document_processor import document_processor

def debug_chunks():
    print("Debugging document chunks...")
    chunks = document_processor.process_course_documents(1)
    print(f"Total chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ---")
        print(chunk)
        print("---")

if __name__ == "__main__":
    debug_chunks()