"""Retriever over the catalog and the policy set.

Lexical matches on names and synonyms win when the shopper names a product.
The vector index covers paraphrases. Prices are not stored in the passages:
the inventory tool is the only place a price is read.
"""

from __future__ import annotations

import re

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from shopmind.schemas import PolicyView, ProductCard
from shopmind.textutil import first_sentence, normalize

_OVERVIEW = re.compile(
    r"(o que voces vendem|quais produtos|catalogo|catalog|what do you sell|"
    r"show me the products|product list|what do you have)",
    re.IGNORECASE,
)


def product_document(
    card: ProductCard,
    description_pt: str,
    description_en: str,
    synonyms: str,
) -> Document:
    text = "\n".join(
        [
            card.sku,
            card.name_pt,
            card.name_en,
            card.category,
            synonyms,
            description_pt,
            description_en,
        ]
    )
    return Document(
        page_content=text,
        metadata={
            "kind": "product",
            "sku": card.sku,
            "title": card.name_pt,
            "snippet": first_sentence(description_pt),
            "source_id": f"catalog:{card.sku}",
        },
    )


def policy_document(policy: PolicyView) -> Document:
    text = "\n".join(
        [
            policy.slug,
            policy.topic,
            policy.title_pt,
            policy.title_en,
            policy.body_pt,
            policy.body_en,
        ]
    )
    return Document(
        page_content=text,
        metadata={
            "kind": "policy",
            "slug": policy.slug,
            "title": policy.title_pt,
            "snippet": first_sentence(policy.body_pt),
            "source_id": f"policy:{policy.slug}",
        },
    )


class CatalogIndex:
    def __init__(
        self,
        store: VectorStore,
        products: list[ProductCard],
        policies: list[PolicyView],
        descriptions: dict[str, tuple[str, str, str]],
        min_similarity: float,
    ) -> None:
        self.store = store
        self.retriever = store.as_retriever(search_kwargs={"k": 6})
        self.products = products
        self.policies = policies
        self.by_sku = {product.sku: product for product in products}
        self.by_slug = {policy.slug: policy for policy in policies}
        self.descriptions = descriptions
        self.min_similarity = min_similarity

    def search_products(self, query: str, limit: int = 3) -> list[tuple[ProductCard, float]]:
        if query.strip() in {"*", "catalog", "catalogo"} or _OVERVIEW.search(normalize(query)):
            return [(product, 1.0) for product in self.products]
        lexical = self._lexical_products(query)
        if lexical:
            return [(product, 0.85) for product in lexical[:limit]]
        return self._vector_products(query, limit)

    def search_policies(self, query: str, limit: int = 1) -> list[tuple[PolicyView, float]]:
        direct = self.by_slug.get(query.strip().lower())
        if direct is not None:
            return [(direct, 1.0)]
        scored = self.store.similarity_search_with_score(query, k=8)
        hits: list[tuple[PolicyView, float]] = []
        seen: set[str] = set()
        for document, score in scored:
            if document.metadata.get("kind") != "policy":
                continue
            if float(score) < self.min_similarity:
                continue
            slug = str(document.metadata.get("slug"))
            policy = self.by_slug.get(slug)
            if policy is None or slug in seen:
                continue
            seen.add(slug)
            hits.append((policy, float(score)))
        if hits:
            return hits[:limit]
        return self._lexical_policies(query)[:limit]

    def _vector_products(self, query: str, limit: int) -> list[tuple[ProductCard, float]]:
        scored = self.store.similarity_search_with_score(query, k=8)
        hits: list[tuple[ProductCard, float]] = []
        seen: set[str] = set()
        for document, score in scored:
            if document.metadata.get("kind") != "product":
                continue
            if float(score) < self.min_similarity:
                continue
            sku = str(document.metadata.get("sku"))
            product = self.by_sku.get(sku)
            if product is None or sku in seen:
                continue
            seen.add(sku)
            hits.append((product, float(score)))
            if len(hits) >= limit:
                break
        return hits

    def _lexical_products(self, query: str) -> list[ProductCard]:
        folded = normalize(query)
        compact = folded.replace(" ", "")
        hits: list[ProductCard] = []
        for product in self.products:
            synonyms, _pt, _en = self.descriptions.get(product.sku, ("", "", ""))
            if self._name_hit(product, synonyms, folded, compact):
                hits.append(product)
        return hits

    def _name_hit(self, product: ProductCard, synonyms: str, folded: str, compact: str) -> bool:
        sku = normalize(product.sku).replace(" ", "")
        if sku and sku in compact:
            return True
        for name in (product.name_pt, product.name_en):
            normalized_name = normalize(name)
            if normalized_name and normalized_name in folded:
                return True
            for token in normalized_name.split():
                if len(token) >= 5 and token in folded:
                    return True
        for piece in synonyms.split(","):
            synonym = normalize(piece)
            if len(synonym) >= 4 and synonym in folded:
                return True
        return False

    def _lexical_policies(self, query: str) -> list[tuple[PolicyView, float]]:
        folded = normalize(query)
        hits: list[tuple[PolicyView, float]] = []
        for policy in self.policies:
            haystack = normalize(
                f"{policy.slug} {policy.topic} {policy.title_pt} {policy.title_en}"
            )
            if any(token in folded for token in haystack.split() if len(token) >= 5):
                hits.append((policy, 0.6))
        return hits
