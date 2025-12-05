from .faiss_vector_store import FaissVectorStore
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    store = FaissVectorStore()
    print("Building FAISS vector index for all course documents...")
    store.build_all_courses_index()
    print("FAISS index build completed successfully!")
