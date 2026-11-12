import pytest
from fastapi.testclient import TestClient

from shopmind.api.app import create_app
from shopmind.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        llm_provider="fake",
        embeddings="hash",
        vector_store="memory",
        database_url="sqlite://",
        checkpoint_backend="memory",
        stream_pace_ms=0,
        rate_limit_per_minute=1000,
        handoff_confidence=0.45,
    )


@pytest.fixture
def app(settings: Settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def agent(app):
    return app.state.container.agent
