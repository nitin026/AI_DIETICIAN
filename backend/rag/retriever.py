"""
rag/retriever.py
Hybrid dense+sparse retrieval with optional cross-encoder reranking.
"""
from __future__ import annotations

import pickle
import re
from functools import lru_cache
from pathlib import Path
from typing import List

from langchain_huggingface import HuggingFaceEmbeddings
from loguru import logger

from backend.config import get_settings

settings = get_settings()

HINGLISH_TO_ENGLISH = {
    "aata": "wheat flour",
    "atta": "wheat flour",
    "bhook": "hunger",
    "bimari": "disease",
    "chawal": "rice",
    "cheeni": "sugar",
    "dahi": "curd yogurt",
    "dal": "lentils pulses",
    "dawai": "medicine",
    "dawa": "medicine",
    "khana": "food meal",
    "namak": "salt sodium",
    "roti": "chapati wheat flatbread",
    "sabzi": "vegetable curry",
    "subah": "morning",
    "shaam": "evening",
    "raat": "night dinner",
    "tel": "oil fat",
}


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


@lru_cache(maxsize=1)
def _load_bm25():
    path = Path(settings.vector_store_path) / "bm25.pkl"
    if not path.exists():
        raise FileNotFoundError(f"BM25 index not found at {path}")
    with path.open("rb") as fh:
        payload = pickle.load(fh)
    logger.info("BM25 sparse index loaded")
    return payload


@lru_cache(maxsize=1)
def _load_cross_encoder():
    from sentence_transformers import CrossEncoder

    model_name = getattr(settings, "cross_encoder_model", None) or "cross-encoder/ms-marco-MiniLM-L-6-v2"
    logger.info("Loading cross-encoder reranker: {}", model_name)
    return CrossEncoder(model_name)


def retrieve(query: str, k: int | None = None) -> List[dict]:
    """
    Retrieve relevant ICMR-NIN passages using dense FAISS, sparse BM25, and reranking.
    """
    k = k or settings.top_k_retrieval
    normalized_query = normalize_hinglish_query(query)
    try:
        candidates = _hybrid_candidates(normalized_query, dense_k=10, sparse_k=10)
        passages = _rerank(normalized_query, candidates, k=min(k, 4))
        if passages:
            logger.debug("Hybrid RAG retrieved {} passages for query: '{}'", len(passages), normalized_query[:80])
            return passages
    except Exception as exc:
        logger.warning("Hybrid RAG retrieval failed ({}); trying dense fallback.", exc)

    try:
        store = _load_vectorstore()
        docs = store.similarity_search(normalized_query, k=k)
        passages = [{"text": d.page_content, "page": d.metadata.get("page", 0)} for d in docs]
        logger.debug("RAG retrieved {} passages for query: '{}'", len(passages), normalized_query[:80])
        return passages
    except Exception as exc:
        logger.warning("RAG retrieval failed ({}); returning empty context.", exc)
        return []


def normalize_hinglish_query(query: str) -> str:
    tokens = re.findall(r"\w+|[^\w\s]", query, flags=re.UNICODE)
    expanded: list[str] = []
    for token in tokens:
        replacement = HINGLISH_TO_ENGLISH.get(token.lower())
        expanded.append(f"{token} {replacement}" if replacement else token)
    return " ".join(expanded)


def _hybrid_candidates(query: str, dense_k: int = 10, sparse_k: int = 10) -> list[dict]:
    candidates: list[dict] = []
    seen: set[str] = set()

    store = _load_vectorstore()
    for doc in store.similarity_search(query, k=dense_k):
        text = doc.page_content
        if text not in seen:
            candidates.append({"text": text, "page": doc.metadata.get("page", 0)})
            seen.add(text)

    bm25_payload = _load_bm25()
    scores = bm25_payload["bm25"].get_scores(_tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)[:sparse_k]
    for idx in ranked:
        text = bm25_payload["texts"][idx]
        metadata = bm25_payload.get("metadatas", [])
        page = metadata[idx].get("page", 0) if idx < len(metadata) else 0
        if text not in seen:
            candidates.append({"text": text, "page": page})
            seen.add(text)
    return candidates[: dense_k + sparse_k]


def _rerank(query: str, candidates: list[dict], k: int) -> list[dict]:
    if not candidates:
        return []
    try:
        reranker = _load_cross_encoder()
        scores = reranker.predict([(query, c["text"]) for c in candidates])
        ranked = sorted(zip(candidates, scores), key=lambda item: float(item[1]), reverse=True)
        return [c for c, _ in ranked[:k]]
    except Exception as exc:
        logger.warning("Cross-encoder reranking failed ({}); using first-stage order.", exc)
        return candidates[:k]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())
