"""Runtime configuration. Secrets come from the environment, never from source."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


def load_dotenv(path: str | Path = ".env") -> None:
    """Load a local env file without overriding variables that are already set."""
    file_path = Path(path)
    if not file_path.is_file():
        return
    for raw in file_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    llm_provider: str = "auto"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-haiku-latest"
    embeddings: str = "auto"
    vector_store: str = "memory"
    database_url: str = "sqlite:///data/shopmind.db"
    checkpoint_backend: str = "sqlite"
    checkpoint_path: str = "data/checkpoints.sqlite"
    handoff_confidence: float = Field(default=0.45, ge=0, le=1)
    rate_limit_per_minute: int = 30
    stream_pace_ms: int = 50
    cors_origins: str = "*"
    min_similarity: float = 0.12
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "shopmind"

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        on_vercel = bool(os.environ.get("VERCEL"))
        database_url = os.environ.get("DATABASE_URL")
        checkpoint_path = os.environ.get("CHECKPOINT_PATH")
        if on_vercel and not database_url:
            database_url = "sqlite:////tmp/shopmind.db"
        if on_vercel and not checkpoint_path:
            checkpoint_path = "/tmp/shopmind-checkpoints.sqlite"
        return cls(
            llm_provider=os.environ.get("LLM_PROVIDER", "auto"),
            openai_api_key=os.environ.get("OPENAI_API_KEY") or None,
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
            anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
            embeddings=os.environ.get("EMBEDDINGS", "auto"),
            vector_store=os.environ.get("VECTOR_STORE", "memory"),
            database_url=database_url or "sqlite:///data/shopmind.db",
            checkpoint_backend=os.environ.get("CHECKPOINT_BACKEND", "sqlite"),
            checkpoint_path=checkpoint_path or "data/checkpoints.sqlite",
            handoff_confidence=float(os.environ.get("HANDOFF_CONFIDENCE", "0.45")),
            rate_limit_per_minute=int(os.environ.get("RATE_LIMIT_PER_MINUTE", "30")),
            stream_pace_ms=int(os.environ.get("SHOPMIND_STREAM_PACE_MS", "50")),
            cors_origins=os.environ.get("CORS_ORIGINS", "*"),
            min_similarity=float(os.environ.get("MIN_SIMILARITY", "0.12")),
            langsmith_tracing=_flag("LANGSMITH_TRACING") or _flag("LANGCHAIN_TRACING_V2"),
            langsmith_api_key=os.environ.get("LANGSMITH_API_KEY")
            or os.environ.get("LANGCHAIN_API_KEY")
            or None,
            langsmith_project=os.environ.get("LANGSMITH_PROJECT", "shopmind"),
        )

    @property
    def resolved_provider(self) -> str:
        choice = self.llm_provider.strip().lower()
        if choice == "fake":
            return "fake"
        if choice == "openai" and self.openai_api_key:
            return "openai"
        if choice == "anthropic" and self.anthropic_api_key:
            return "anthropic"
        if choice == "auto":
            if self.openai_api_key:
                return "openai"
            if self.anthropic_api_key:
                return "anthropic"
        return "fake"

    @property
    def resolved_embeddings(self) -> str:
        choice = self.embeddings.strip().lower()
        if choice == "openai" and self.openai_api_key:
            return "openai"
        if choice == "auto" and self.resolved_provider == "openai":
            return "openai"
        return "hash"

    @property
    def model_name(self) -> str:
        provider = self.resolved_provider
        if provider == "openai":
            return self.openai_model
        if provider == "anthropic":
            return self.anthropic_model
        return "deterministic-template"

    @property
    def cors_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def apply_tracing(self) -> None:
        """Turn on LangSmith only when a key is present. LangChain reads these env vars."""
        if not (self.langsmith_tracing and self.langsmith_api_key):
            return
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = self.langsmith_project
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = self.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = self.langsmith_project
