# Course Assistant Chatbot with RAG

This directory contains the implementation of the Course Assistant chatbot using Retrieval-Augmented Generation (RAG) technology.

## Components

1. **course_chatbot_api.py** - Main API implementation with RAG functionality
2. **document_processor.py** - Handles processing of course documents (PDF, DOCX, TXT, etc.)
3. **test_rag.py** - Test script for verifying RAG functionality

## RAG Implementation

The Course Assistant uses the following technologies:

- **Sentence Transformers** - For generating document embeddings
- **FAISS** - For efficient similarity search
- **PyPDF2** - For PDF text extraction
- **python-docx** - For DOCX text extraction

## How It Works

1. **Document Processing**: Course documents are processed and split into chunks
2. **Embedding Generation**: Each chunk is converted to embeddings using Sentence Transformers
3. **Indexing**: Embeddings are stored in a FAISS index for fast retrieval
4. **Query Processing**: User questions are converted to embeddings
5. **Similarity Search**: FAISS finds the most relevant document chunks
6. **Response Generation**: Relevant content is used to generate answers

## Installation

The required dependencies are listed in `pyproject.toml`:

```toml
sentence-transformers>=2.2.0
faiss-cpu>=1.7.0
numpy>=1.21.0
pypdf2>=3.0.0
python-docx>=0.8.11
```

## Usage

The chatbot is automatically integrated with the course video pages and provides context-aware assistance based on course materials.