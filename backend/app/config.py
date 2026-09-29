from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VaultAI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    VAULTAI_API_KEY: str | None = None
    DATABASE_URL: str = "postgresql+psycopg://vaultai@localhost:5432/vaultai"
    SESSION_COOKIE_NAME: str = "vaultai_session"
    SESSION_LIFETIME_SECONDS: int = 1800
    SESSION_COOKIE_SECURE: bool = False

    # Ollama runtime settings
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3.5:latest"
    OLLAMA_TIMEOUT_SECONDS: float = 300.0

    # RAG & Storage Settings
    BASE_DATA_DIR: Path = Path("data")
    DOC_STORE_PATH: Path = Path("data/documents")
    CHROMA_PATH: Path = Path("data/chroma")
    CHROMA_COLLECTION: str = "vaultai_collection"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    UPLOAD_MAX_BYTES: int = 50 * 1024 * 1024

    # RAG Thresholds
    RETRIEVAL_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.25

    # Audit Log Settings
    AUDIT_LOG_PATH: Path = Path("data/audit/audit.log")

    # Sandbox
    SANDBOX_TIMEOUT_SECONDS: int = 5
    SANDBOX_IMAGE: str = "vaultai-sandbox"

    # Local prototype protection
    ENABLE_LOCAL_API_KEY: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def init_directories(self):
        """Ensure runtime directories exist."""
        self.DOC_STORE_PATH.mkdir(parents=True, exist_ok=True)
        self.CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        self.AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.init_directories()
