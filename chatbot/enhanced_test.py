"""
Enhanced test for the course chatbot with document search integration
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.course_chatbot_api import document_search, generate_fallback_response, generate_document_response

def test_chatbot():
    """Test the enhanced chatbot functionality"""
    print("Testing Enhanced Course Assistant Chatbot...")
    
    # Test fallback response
    test_message = "hello"
    response = generate_fallback_response(test_message)
    print(f"Query: {test_message}")
    print(f"Fallback Response: {response}")
    
    # Test with a course
    course_id = 1
    try:
        documents = document_search.load_course_documents(course_id)
        print(f"\nLoaded {len(documents)} documents for course {course_id}")
        
        # Test search
        query = "What is Python?"
        relevant_docs = document_search.search_relevant_documents(query, course_id)
        print(f"\nSearch query: {query}")
        print(f"Found {len(relevant_docs)} relevant documents")
        
        if relevant_docs:
            print("Top result:", relevant_docs[0]['content'])
            print("Score:", relevant_docs[0]['score'])
            
            # Test document response generation
            doc_response = generate_document_response(query, course_id, 1)
            print(f"\nDocument Response: {doc_response}")
        else:
            print("No relevant documents found")
            
    except Exception as e:
        print(f"Error testing course documents: {e}")
        import traceback
        traceback.print_exc()

def test_various_queries():
    """Test the chatbot with various types of queries"""
    print("\n" + "="*50)
    print("Testing Various Queries")
    print("="*50)
    
    course_id = 1
    
    # Test queries
    queries = [
        "What is a Python function?",
        "How do lists work in Python?",
        "Explain Python dictionaries",
        "What is the purpose of this course?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        try:
            response = generate_document_response(query, course_id, 1)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")

def test_keyword_extraction():
    """Test keyword extraction functionality"""
    print("\n" + "="*50)
    print("Testing Keyword Extraction")
    print("="*50)
    
    test_texts = [
        "What is a Python variable?",
        "How do I create a function in Python?",
        "Explain lists and dictionaries in Python"
    ]
    
    for text in test_texts:
        keywords = document_search.extract_keywords(text)
        print(f"Text: {text}")
        print(f"Keywords: {keywords}")
        print()

if __name__ == "__main__":
    test_chatbot()
    test_various_queries()
    test_keyword_extraction()