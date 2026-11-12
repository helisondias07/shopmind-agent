"""Read products and policies from SQLite."""

from __future__ import annotations

from sqlalchemy import select

from shopmind.db.database import Database
from shopmind.db.models import PolicyRow, ProductRow
from shopmind.schemas import PolicyView, ProductCard
from shopmind.textutil import first_sentence


class CatalogService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def snapshot(
        self,
    ) -> tuple[
        list[ProductCard],
        list[PolicyView],
        dict[str, tuple[str, str, str]],
        dict[str, int],
    ]:
        """Copy catalog rows out of the session so callers do not touch detached ORM objects."""
        with self.database.session() as session:
            rows = list(session.scalars(select(ProductRow).order_by(ProductRow.name_pt)))
            policies = list(session.scalars(select(PolicyRow).order_by(PolicyRow.slug)))
            cards = [self._card(row) for row in rows]
            views = [PolicyView.model_validate(row, from_attributes=True) for row in policies]
            descriptions = {
                row.sku: (row.synonyms, row.description_pt, row.description_en) for row in rows
            }
            weights = {row.sku: row.weight_grams for row in rows}
            return cards, views, descriptions, weights

    def product_cards(self) -> list[ProductCard]:
        cards, _views, _descriptions, _weights = self.snapshot()
        return cards

    def policy_views(self) -> list[PolicyView]:
        _cards, views, _descriptions, _weights = self.snapshot()
        return views

    def card_for(self, sku: str) -> ProductCard | None:
        with self.database.session() as session:
            row = session.get(ProductRow, sku)
            if row is None:
                return None
            return self._card(row)

    def policy_for(self, slug: str) -> PolicyView | None:
        with self.database.session() as session:
            row = session.get(PolicyRow, slug)
            if row is None:
                return None
            return PolicyView.model_validate(row, from_attributes=True)

    @staticmethod
    def _card(row: ProductRow) -> ProductCard:
        return ProductCard(
            sku=row.sku,
            name_pt=row.name_pt,
            name_en=row.name_en,
            price_cents=row.price_cents,
            stock=row.stock,
            category=row.category,
            image_key=row.image_key,
            blurb_pt=first_sentence(row.description_pt),
            blurb_en=first_sentence(row.description_en),
        )
