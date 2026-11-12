"""Authoritative price and stock. Retrieval never supplies these numbers."""

from __future__ import annotations

from shopmind.schemas import ProductCard
from shopmind.services.catalog import CatalogService


class InventoryService:
    def __init__(self, catalog: CatalogService) -> None:
        self.catalog = catalog

    def offers(self, skus: list[str]) -> list[ProductCard]:
        cards: list[ProductCard] = []
        for sku in skus:
            card = self.catalog.card_for(sku.strip())
            if card is not None:
                cards.append(card)
        return cards

    def alternatives(self, sku: str, limit: int = 2) -> list[ProductCard]:
        anchor = self.catalog.card_for(sku)
        if anchor is None:
            return []
        same_category = [
            card
            for card in self.catalog.product_cards()
            if card.category == anchor.category and card.sku != anchor.sku
        ]
        same_category.sort(key=lambda card: (-card.stock, card.name_pt))
        return same_category[:limit]
