"""
rag/ingest.py
One-time ingestion of the ICMR-NIN PDF into dense FAISS and sparse BM25 indexes.

Usage:
    python -m backend.rag.ingest
"""
from __future__ import annotations

import os
import pickle
import re
from pathlib import Path

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from loguru import logger

from backend.config import get_settings

settings = get_settings()


def load_and_split_pdf(pdf_path: str) -> list:
    """Load PDF and split into overlapping chunks."""
    if not Path(pdf_path).exists():
        raise FileNotFoundError(
            f"PDF not found at '{pdf_path}'. "
            "Please place 'Dietary_Guidelines_ICMR_NIN.pdf' in the data/ folder."
        )
    logger.info("Loading PDF: {}", pdf_path)
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(pages)
    logger.info("Split into {} chunks", len(chunks))
    return chunks


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)


def build_faiss_store(chunks: list, embeddings: HuggingFaceEmbeddings) -> None:
    from langchain_community.vectorstores import FAISS

    store_path = settings.vector_store_path
    os.makedirs(store_path, exist_ok=True)
    logger.info("Building FAISS index ...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(store_path)
    logger.info("FAISS index saved to {}", store_path)


def build_bm25_store(chunks: list) -> None:
    from rank_bm25 import BM25Okapi

    store_path = Path(settings.vector_store_path)
    store_path.mkdir(parents=True, exist_ok=True)
    logger.info("Building RankBM25 sparse index ...")
    texts = [chunk.page_content for chunk in chunks]
    tokens = [_tokenize(text) for text in texts]
    payload = {
        "texts": texts,
        "metadatas": [getattr(chunk, "metadata", {}) for chunk in chunks],
        "tokens": tokens,
        "bm25": BM25Okapi(tokens),
    }
    with (store_path / "bm25.pkl").open("wb") as fh:
        pickle.dump(payload, fh)
    logger.info("BM25 index saved to {}", store_path / "bm25.pkl")


def build_chroma_store(chunks: list, embeddings: HuggingFaceEmbeddings) -> None:
    from langchain_community.vectorstores import Chroma

    store_path = settings.vector_store_path
    logger.info("Building ChromaDB collection ...")
    Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=store_path,
        collection_name="icmr_nin_guidelines",
    )
    logger.info("ChromaDB persisted to {}", store_path)


def ingest() -> None:
    chunks = load_and_split_pdf(settings.pdf_path)
    embeddings = get_embeddings()
    build_faiss_store(chunks, embeddings)
    build_bm25_store(chunks)
    if settings.vector_store_type != "faiss":
        build_chroma_store(chunks, embeddings)
    logger.info("Ingestion complete")


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


if __name__ == "__main__":
    ingest()
