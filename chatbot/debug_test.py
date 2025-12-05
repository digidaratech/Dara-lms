"""
Debug test for the document processor
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.document_processor import document_processor
import traceback

def debug_document_processing():
    """Debug the document processing"""
    print("Debugging Document Processing...")
    
    try:
        # Test with course 1
        course_id = 1
        print(f"Processing documents for course {course_id}")
        
        # Load documents
        documents = document_processor.process_course_documents(course_id)
        print(f"Loaded {len(documents)} document chunks")
        
        # Print first few documents
        for i, doc in enumerate(documents[:3]):
            print(f"Document {i+1}: {doc[:100]}...")
            
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_document_processing()