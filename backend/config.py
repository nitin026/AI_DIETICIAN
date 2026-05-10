"""
config.py
Centralised application settings loaded from environment / .env file.
Supports three LLM providers: Ollama (local), HuggingFace (router API), Groq (free & fast).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM Provider ─────────────────────────────────────────────
    # Set to: "ollama" | "huggingface" | "groq"
    llm_provider: str = "groq"

    # ── Ollama (Local) ───────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"              # any model pulled via: ollama pull <model>

    # ── HuggingFace (New Router API) ─────────────────────────────
    hf_api_token: str = ""                      # from huggingface.co/settings/tokens
    hf_model_id: str = "mistralai/Mistral-7B-Instruct-v0.3"  # free & supported model

    # ── Groq (Free & Fast - Recommended) ─────────────────────────
    groq_api_key: str = ""                      # from console.groq.com
    groq_model: str = "llama-3.3-70b-versatile" # free tier model

    # ── Embeddings (for RAG) ─────────────────────────────────────
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── Vector Store ─────────────────────────────────────────────
    vector_store_type: str = "faiss"            # "faiss" | "chroma"
    vector_store_path: str = "./rag/vector_store"
    pdf_path: str = "./data/Dietary_Guidelines_ICMR_NIN.pdf"
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_retrieval: int = 5

    # ── FastAPI Server ────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 2
    log_level: str = "INFO"

    # ── LLM Request Settings ──────────────────────────────────────
    llm_timeout_seconds: int = 120
    llm_max_retries: int = 3

    # ── YouTube Recipe Links ──────────────────────────────────────
    youtube_results_per_meal: int = 1

    # ── Streamlit Frontend ────────────────────────────────────────
    backend_url: str = "http://localhost:8000"

    # ── Derived helpers ───────────────────────────────────────────
    @property
    def active_model_name(self) -> str:
        """Returns the active model name based on selected provider."""
        if self.llm_provider == "groq":
            return self.groq_model
        elif self.llm_provider == "huggingface":
            return self.hf_model_id
        return self.ollama_model

    @property
    def is_groq(self) -> bool:
        return self.llm_provider == "groq"

    @property
    def is_huggingface(self) -> bool:
        return self.llm_provider == "huggingface"

    @property
    def is_ollama(self) -> bool:
        return self.llm_provider == "ollama"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton (loaded once at startup)."""
    return Settings()