"""Deterministic hashed embeddings, plus an optional OpenAI backend.

Hash embeddings keep retrieval working in CI, in Docker, and on a demo that has
no API key. They are not a semantic model: tokens that actually appear in the
catalog overlap in the vector, which is enough for this store.
"""

from __future__ import annotations

import hashlib
import math
import re

from langchain_core.embeddings import Embeddings

from shopmind.textutil import strip_accents

_TOKEN = re.compile(r"[a-z0-9]{2,}")


def _tokens(text: str) -> list[str]:
    folded = strip_accents(text.lower())
    words = _TOKEN.findall(folded)
    grams: list[str] = []
    for word in words:
        grams.append(word)
        if len(word) >= 5:
            grams.append(word[:4])
    return grams


class HashEmbeddings(Embeddings):
    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = _tokens(text)
        if not tokens:
            vector[0] = 1.0
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def build_embeddings(
    backend: str,
    openai_api_key: str | None,
    model: str = "text-embedding-3-small",
):
    if backend == "openai":
        if not openai_api_key:
            return HashEmbeddings()
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(api_key=openai_api_key, model=model)
    return HashEmbeddings()
