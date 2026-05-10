"""
rag/retriever.py
Loads the persisted vector store and exposes a retrieve() function
that returns the top-k most relevant ICMR-NIN guideline passages.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from langchain_huggingface import HuggingFaceEmbeddings
from loguru import logger

from backend.config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def _load_vectorstore():
    """Lazily load the vector store once and cache it."""
    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    if settings.vector_store_type == "faiss":
        from langchain_community.vectorstores import FAISS
        store = FAISS.load_local(
            settings.vector_store_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
    else:
        from langchain_community.vectorstores import Chroma
        store = Chroma(
            persist_directory=settings.vector_store_path,
            embedding_function=embeddings,
            collection_name="icmr_nin_guidelines",
        )
    logger.info("Vector store loaded ({})", settings.vector_store_type)
    return store


def retrieve(query: str, k: int | None = None) -> List[str]:
    """
    Retrieve the top-k relevant passages from the ICMR-NIN guidelines.

    Args:
        query: The semantic search query.
        k: Number of passages to return (defaults to settings.top_k_retrieval).

    Returns:
        List of page_content strings.
    """
    k = k or settings.top_k_retrieval
    try:
        store = _load_vectorstore()
        docs = store.similarity_search(query, k=k)
        passages = [d.page_content for d in docs]
        logger.debug("RAG retrieved {} passages for query: '{}'", len(passages), query[:80])
        return passages
    except Exception as exc:
        logger.warning("RAG retrieval failed ({}); returning empty context.", exc)
        return []
