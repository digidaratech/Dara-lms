"""
Course Assistant Chatbot API
This module provides course-specific chatbot functionality for the LMS using a lightweight approach.
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import logging
import os
import re
import ollama
from .faiss_vector_store import FaissVectorStore

course_chatbot_bp = Blueprint('course_chatbot', __name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
vector_store = FaissVectorStore()

try:
    from .document_processor import document_processor
except Exception as e:
    logger.warning(f"Document processor not available: {e}")
    document_processor = None

# -------------------------
# GENERIC RESPONSES
# -------------------------
GENERIC_RESPONSES = {
    'hello': "Hello! I'm your Course Assistant. How can I help you in this course?",
    'hi': "Hi! I'm your Course Assistant. Ask me anything about this video or course content!",
    'help': "You can ask doubts about this course topics, concepts, logic, or steps. Just type your question.",
    'exercise': "Tell me a topic name, I will suggest a small practice task for you.",
    'resources': "I can suggest extra learning pointers based on this course. Ask for resources on a topic.",
    'tips': "Study regularly, take notes, revise often, practice questions, and ask doubts whenever you get stuck.",
    'debug': "Describe your issue and error message clearly, I will help you think through the problem step by step.",
    'best practices': "Follow clear structure, good naming, modular design, and always test your work properly.",
    'python': "Python is a simple and powerful programming language used for many areas like web, data and AI.",
    'coding': "Tell me which topic or concept you want help with, I will try to guide you in a simple way."
}

# -------------------------
# LIGHTWEIGHT DOCUMENT SEARCH
# -------------------------
class LightweightDocumentSearch:
    def __init__(self):
        self.course_documents = {}
    
    def load_course_documents(self, course_id):
        if course_id in self.course_documents:
            return self.course_documents[course_id]
        
        documents = []
        if document_processor:
            documents = document_processor.process_course_documents(course_id)
        
        if not documents:
            logger.info(f"No documents found for course {course_id}, using fallback generic internal docs")
            documents = [
                "This course covers fundamental and advanced concepts. Ask any topic and I will help you understand.",
                "You can request beginner level or interview level explanation for any concept in this course.",
                "Practice and revision are important to master the concepts in this course."
            ]
        
        self.course_documents[course_id] = documents
        return documents
    
    def preprocess_text(self, text):
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        text = ' '.join(text.split())
        return text
    
    def extract_keywords(self, text):
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'what', 'how', 'why', 'when', 'where', 'who', 'it', 'its'
        }
        words = self.preprocess_text(text).split()
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def calculate_similarity(self, query, document):
        query_keywords = set(self.extract_keywords(query))
        doc_keywords = set(self.extract_keywords(document))
        
        if not query_keywords:
            return 0
        
        intersection = query_keywords.intersection(doc_keywords)
        union = query_keywords.union(doc_keywords)
        
        if not union:
            return 0
            
        return len(intersection) / len(union)
    
    def search_relevant_documents(self, query, course_id, k=3):
        try:
            documents = self.load_course_documents(course_id)
            
            scores = []
            for i, doc in enumerate(documents):
                score = self.calculate_similarity(query, doc)
                scores.append((i, score, doc))
            
            scores.sort(key=lambda x: x[1], reverse=True)
            results = [doc for i, score, doc in scores[:k] if score > 0]
            return results
        except Exception as e:
            logger.error(f"Document search error: {e}")
            return []

document_search = LightweightDocumentSearch()

# -------------------------
# LLM RESPONSE GENERATOR
# -------------------------
def generate_llm_response(message, course_id=None, module_id=None, context: str = "") -> str:
    try:
        # Detect Tanglish (Tamil typed in English letters)
        tanglish_words = [
            "enna", "enna?", "enaku", "enku", "epdi", "eppadi", "pannu", "solunga",
            "sollu", "sol", "panra", "podu", "tharalam", "pass", "type conversion na",
            "puriyala", "puriyala?", "simple ah", "explain pannunga", "example kudunga"
        ]

        is_tanglish = any(word in message.lower() for word in tanglish_words)

        context_block = ""
        if context and context.strip():
            context_block = f"""
Use this course material as the primary reference while responding:

{context}

You must use this context to answer the question in a natural tone.
"""

        # Updated SYSTEM Prompt for Tanglish function
        system_prompt = """
You are a friendly Course Assistant for an LMS platform.
Your job is to reply in the language style of the student.

### LANGUAGE RULES ###
1) If the user writes in Tamil script → reply in Tamil.
2) If the user writes Tamil using English letters (Tanglish) → reply in Tanglish.
   Example Tanglish style: "enna panrathu", "epdi", "enaku puriyala", "simple ah sollunga"
3) If the user writes in English → reply in English.
4) Never answer in Hindi, Telugu, Malayalam, or Kannada.
5) Response must be friendly like a supportive teacher.

### EXPLANATION RULES ###
- For beginner / simple / school-level requests → explain with small steps and easy words.
- For advanced or interview level → explain deeply with bullet points + structure.
- Use examples when helpful.
- If course material context is provided, prioritize using it.
"""

        # Final prompt for model
        final_prompt = f"""
Student Question:
{message}

{"Detected Language: Tanglish. Reply in Tanglish style." if is_tanglish else ""}

{context_block}

Give your best explanation now.
"""

        response = ollama.chat(
            model="qwen2.5:7b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_prompt}
            ]
        )

        content = ""
        # Handle different response types from Ollama
        if hasattr(response, 'message') and hasattr(response.message, 'content'):
            # New Ollama response format (object)
            content = response.message.content
        elif isinstance(response, dict):
            # Old Ollama response format (dict)
            content = response.get("message", {}).get("content", "") or response.get("content", "")
        
        if not isinstance(content, str):
            content = ""

        content = content.strip()

        if not content:
            return "Please try again with a different question 🙂"

        return content

    except Exception as e:
        logger.error(f"Error generating LLM response: {e}", exc_info=True)
        return "Something went wrong. Please try again."

# -------------------------
# BUILD RESPONSE WITH RAG
# -------------------------
def generate_document_response(message, course_id, module_id):
    try:
        # Validate parameters
        if not course_id or not module_id:
            return "Course or module information missing."
        
        message_lower = message.lower()

        # FIRST: Generic quick intent responses (exact match only)
        if message_lower in GENERIC_RESPONSES:
            return GENERIC_RESPONSES[message_lower]
        
        # Special handling for common greetings
        if message_lower in ['hello', 'hi']:
            return GENERIC_RESPONSES[message_lower]
        
        # SECOND: FAISS Vector Search
        faiss_results = vector_store.search(course_id, message, top_k=5)
        if faiss_results:
            context_text = "\n\n".join(faiss_results)
            return generate_llm_response(message, course_id, module_id, context=context_text)

        # THIRD: Lightweight keyword matching
        relevant_docs = document_search.search_relevant_documents(message, course_id, k=3)
        if relevant_docs:
            context_text = "\n\n".join(relevant_docs)
            return generate_llm_response(message, course_id, module_id, context=context_text)

        # LAST FALLBACK: General LLM answer
        return generate_llm_response(message, course_id=course_id, module_id=module_id, context="")

    except Exception as e:
        logger.error(f"Document response generation error: {e}", exc_info=True)
        return "I’m here to help. Try asking in a different way."

# -------------------------
# MAIN API ROUTE
# -------------------------
@course_chatbot_bp.route('/course-assistant', methods=['POST'])
def course_assistant_api():
    try:
        data = request.get_json() or {}
        message = (data.get('message') or "").strip()
        course_id = data.get("course_id")
        module_id = data.get("module_id")

        if 'user_id' not in session:
            return jsonify({'success': False, 'response': 'Please log in to use the Course Assistant.'}), 401

        if not message:
            return jsonify({'success': True, 'response': 'Ask a question about this course.'})
        
        # Validate course_id and module_id
        if not course_id or not module_id:
            return jsonify({'success': False, 'response': 'Course or module information missing.'}), 400

        response = generate_document_response(message, course_id, module_id)

        return jsonify({'success': True, 'response': response})

    except Exception as e:
        logger.error(f"API Error: {e}", exc_info=True)
        return jsonify({'success': False, 'response': 'Server error. Try again in a moment.'}), 500
