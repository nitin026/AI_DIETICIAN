"""
config.py
Centralised application settings loaded from environment / .env file.
Supports Gemini, Ollama (local), HuggingFace (router API), and Groq.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # â”€â”€ LLM Provider â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Set to: "gemini" | "ollama" | "huggingface" | "biomistral" | "groq"
    llm_provider: str = "groq"

    # Gemini (Google AI Studio)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # â”€â”€ Ollama (Local) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"              # any model pulled via: ollama pull <model>

    # â”€â”€ HuggingFace (New Router API) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hf_api_token: str = ""                      # from huggingface.co/settings/tokens
    hf_model_id: str = "mistralai/Mistral-7B-Instruct-v0.3"  # free & supported model
    biomistral_model_id: str = "m/biomistral"
    biomistral_base_url: str = "http://localhost:11434"

    # â”€â”€ Groq (Free & Fast - Recommended) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    groq_api_key: str = ""                      # from console.groq.com
    groq_model: str = "llama-3.3-70b-versatile" # free tier model
    clinical_llm_provider: str = "groq"
    clinical_llm_model: str = "Llama3-OpenBioLLM-70B"
    groq_clinical_model: str = "Llama3-OpenBioLLM-70B"
    hf_clinical_model_id: str = "aaditya/Llama3-OpenBioLLM-70B"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # â”€â”€ Embeddings (for RAG) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # â”€â”€ Vector Store â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    vector_store_type: str = "faiss"            # "faiss" | "chroma"
    vector_store_path: str = "./rag/vector_store"
    pdf_path: str = "./data/Dietary_Guidelines_ICMR_NIN.pdf"
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_retrieval: int = 5

    # â”€â”€ FastAPI Server â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 2
    log_level: str = "INFO"

    # â”€â”€ LLM Request Settings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    llm_timeout_seconds: int = 120
    llm_max_retries: int = 3

    # â”€â”€ YouTube Recipe Links â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    youtube_results_per_meal: int = 1

    # Communication provider adapter
    communication_provider: str = "mock"
    plivo_auth_id: str = ""
    plivo_auth_token: str = ""
    plivo_source_number: str = ""
    # â”€â”€ Streamlit Frontend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    backend_url: str = "http://localhost:8000"
    # â”€â”€ Production Readiness â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    storage_path: str = "./data/app_state.json"
    database_url: str = "sqlite:///./data/dietitian.db"
    enable_request_logging: bool = True
    max_chat_history_messages: int = 16
    default_user_id: str = "demo-user"

    # â”€â”€ Derived helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @property
    def active_model_name(self) -> str:
        """Returns the active model name based on selected provider."""
        if self.llm_provider == "gemini":
            return self.gemini_model
        elif self.llm_provider == "groq":
            return self.groq_model
        elif self.llm_provider == "huggingface":
            return self.hf_model_id
        elif self.llm_provider == "biomistral":
            return self.biomistral_model_id
        return self.ollama_model

    @property
    def is_groq(self) -> bool:
        return self.llm_provider == "groq"

    @property
    def is_gemini(self) -> bool:
        return self.llm_provider == "gemini"

    @property
    def is_huggingface(self) -> bool:
        return self.llm_provider == "huggingface"

    @property
    def is_ollama(self) -> bool:
        return self.llm_provider == "ollama"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton (loaded once at startup)."""

    

    # â”€â”€ Production Readiness â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    storage_path: str = "./data/app_state.json"
    enable_request_logging: bool = True
    max_chat_history_messages: int = 16
    default_user_id: str = "demo-user"
    return Settings()

