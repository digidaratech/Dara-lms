import os
import logging
import pickle
from typing import List, Dict, Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

try:
    from .document_processor import document_processor
except Exception as e:
    document_processor = None

logger = logging.getLogger(__name__)


class FaissVectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.vector_dir = os.path.join(self.base_dir, "vector_store")
        os.makedirs(self.vector_dir, exist_ok=True)

        self.model_name = model_name
        self.embedder = SentenceTransformer(self.model_name)

        self.index_cache: Dict[str, faiss.Index] = {}
        self.text_cache: Dict[str, List[str]] = {}

    def _course_key(self, course_id) -> str:
        return str(course_id)

    def _index_path(self, course_id) -> str:
        return os.path.join(self.vector_dir, f"index_course_{course_id}.bin")

    def _texts_path(self, course_id) -> str:
        return os.path.join(self.vector_dir, f"texts_course_{course_id}.pkl")

    def _load_or_build_for_course(self, course_id) -> Optional[faiss.Index]:
        key = self._course_key(course_id)
        if key in self.index_cache and key in self.text_cache:
            return self.index_cache[key]

        index_path = self._index_path(course_id)
        texts_path = self._texts_path(course_id)

        if os.path.exists(index_path) and os.path.exists(texts_path):
            try:
                index = faiss.read_index(index_path)
                with open(texts_path, "rb") as f:
                    texts = pickle.load(f)

                self.index_cache[key] = index
                self.text_cache[key] = texts
                logger.info(f"[FAISS] Loaded index for course {course_id}")
                return index
            except Exception as e:
                logger.error(f"[ERROR] Loading FAISS index for {course_id}: {e}")

        return self._build_index_for_course(course_id)

    def _build_index_for_course(self, course_id) -> Optional[faiss.Index]:
        key = self._course_key(course_id)

        if not document_processor:
            logger.error("[ERROR] document_processor not available")
            return None

        try:
            chunks = document_processor.process_course_documents(course_id)
            if not chunks:
                logger.warning(f"[WARN] No document chunks found for course {course_id}")
                return None

            embeddings = self.embedder.encode(
                chunks,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=True
            )

            if embeddings.ndim == 1:
                embeddings = np.expand_dims(embeddings, axis=0)

            dim = embeddings.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(embeddings.astype("float32"))

            index_path = self._index_path(course_id)
            texts_path = self._texts_path(course_id)

            faiss.write_index(index, index_path)
            with open(texts_path, "wb") as f:
                pickle.dump(chunks, f)

            self.index_cache[key] = index
            self.text_cache[key] = chunks

            logger.info(f"[FAISS] Saved index for course {course_id} → {index_path}")
            return index

        except Exception as e:
            logger.error(f"[ERROR] Building FAISS index for {course_id}: {e}", exc_info=True)
            return None

    def rebuild_index(self, course_id) -> bool:
        index = self._build_index_for_course(course_id)
        return index is not None

    def search(self, course_id, query: str, top_k: int = 5) -> List[str]:
        if not query or not str(query).strip():
            return []

        index = self._load_or_build_for_course(course_id)
        key = self._course_key(course_id)

        if index is None or key not in self.text_cache:
            logger.warning(f"[WARN] No FAISS index available for course {course_id}")
            return []

        try:
            query_vec = self.embedder.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            ).astype("float32")

            scores, indices = index.search(query_vec, top_k)
            texts = self.text_cache[key]

            results: List[str] = []
            used = set()

            for idx in indices[0]:
                if idx >= 0 and idx < len(texts) and idx not in used:
                    used.add(idx)
                    results.append(texts[idx])

            return results

        except Exception as e:
            logger.error(f"[ERROR] FAISS search failure for {course_id}: {e}", exc_info=True)
            return []

    def build_all_courses_index(self, courses_base_path="courses") -> None:
        logger.info("[FAISS] Building index for all courses...")

        for folder in os.listdir(courses_base_path):
            course_path = os.path.join(courses_base_path, folder)
            if os.path.isdir(course_path):
                try:
                    course_id = int(folder)
                except ValueError:
                    continue

                logger.info(f"[BUILD] Processing course {course_id}")
                self._build_index_for_course(course_id)

        logger.info("[DONE] FAISS index build for all courses")
