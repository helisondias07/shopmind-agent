"""Local vector indexes. Memory is the default; FAISS is optional."""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore, VectorStore


class VectorStoreError(RuntimeError):
    pass


def build_vector_store(
    documents: list[Document], embeddings: Embeddings, backend: str
) -> VectorStore:
    """Build a local vector store.

    `memory` uses LangChain's in-memory cosine index (NumPy). It deploys without
    native libraries. `faiss` is available when `faiss-cpu` and
    `langchain-community` are installed.
    """
    choice = backend.strip().lower()
    if choice == "memory":
        if not documents:
            return InMemoryVectorStore(embedding=embeddings)
        return InMemoryVectorStore.from_documents(documents, embeddings)
    if choice == "faiss":
        try:
            from langchain_community.vectorstores import FAISS
        except ImportError as exc:
            raise VectorStoreError(
                "VECTOR_STORE=faiss needs the optional packages faiss-cpu and "
                "langchain-community. The default backend is memory."
            ) from exc
        return FAISS.from_documents(documents, embeddings)
    raise VectorStoreError(f"Unknown vector store backend: {backend}")
