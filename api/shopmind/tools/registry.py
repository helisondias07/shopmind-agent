"""Tool definitions. Graph nodes call these; they do not invent tool results."""

from __future__ import annotations

import json

from langchain_core.tools import BaseTool, tool

from shopmind.rag.index import CatalogIndex
from shopmind.schemas import Source
from shopmind.services.inventory import InventoryService
from shopmind.services.orders import OrderService
from shopmind.services.shipping import ShippingService
from shopmind.textutil import first_sentence


class SupportTools:
    def __init__(
        self,
        index: CatalogIndex,
        inventory: InventoryService,
        orders: OrderService,
        shipping: ShippingService,
    ) -> None:
        self.index = index
        self.inventory = inventory
        self.orders = orders
        self.shipping = shipping
        self.search_knowledge = self._search_tool()
        self.check_inventory = self._inventory_tool()
        self.recommend_products = self._recommend_tool()
        self.get_order_status = self._order_tool()
        self.quote_shipping = self._shipping_tool()
        self.by_name: dict[str, BaseTool] = {
            "search_knowledge": self.search_knowledge,
            "check_inventory": self.check_inventory,
            "recommend_products": self.recommend_products,
            "get_order_status": self.get_order_status,
            "quote_shipping": self.quote_shipping,
        }

    def call(self, name: str, payload: dict) -> dict:
        raw = self.by_name[name].invoke(payload)
        if isinstance(raw, str):
            return json.loads(raw)
        if isinstance(raw, dict):
            return raw
        raise TypeError(f"tool {name} returned {type(raw).__name__}")

    def _search_tool(self):
        index = self.index

        @tool
        def search_knowledge(query: str, kind: str) -> str:
            """Search the store index.

            kind is 'product' or 'policy'. Returns ids and passages, not prices.
            """
            if kind == "policy":
                hits = []
                for policy, score in index.search_policies(query, limit=1):
                    hits.append(
                        {
                            "kind": "policy",
                            "slug": policy.slug,
                            "topic": policy.topic,
                            "title_pt": policy.title_pt,
                            "title_en": policy.title_en,
                            "body_pt": policy.body_pt,
                            "body_en": policy.body_en,
                            "score": round(score, 4),
                        }
                    )
                return json.dumps({"hits": hits}, ensure_ascii=False)
            hits = []
            for product, score in index.search_products(query):
                hits.append(
                    {
                        "kind": "product",
                        "sku": product.sku,
                        "title_pt": product.name_pt,
                        "title_en": product.name_en,
                        "snippet_pt": product.blurb_pt,
                        "snippet_en": product.blurb_en,
                        "score": round(score, 4),
                    }
                )
            return json.dumps({"hits": hits}, ensure_ascii=False)

        return search_knowledge

    def _inventory_tool(self):
        inventory = self.inventory

        @tool
        def check_inventory(skus: str) -> str:
            """Read price and stock for comma-separated SKUs from the store database."""
            parsed = [piece.strip() for piece in skus.split(",") if piece.strip()]
            offers = [card.model_dump() for card in inventory.offers(parsed)]
            return json.dumps({"offers": offers}, ensure_ascii=False)

        return check_inventory

    def _recommend_tool(self):
        inventory = self.inventory

        @tool
        def recommend_products(sku: str) -> str:
            """Suggest up to two alternatives in the same category, with database prices."""
            cards = [card.model_dump() for card in inventory.alternatives(sku)]
            return json.dumps({"recommendations": cards}, ensure_ascii=False)

        return recommend_products

    def _order_tool(self):
        orders = self.orders

        @tool
        def get_order_status(order_id: str) -> str:
            """Look up one order by its public id, for example LM-1042."""
            order = orders.get(order_id)
            if order is None:
                return json.dumps(
                    {"found": False, "order_id": order_id.strip().upper()},
                    ensure_ascii=False,
                )
            return json.dumps({"found": True, "order": order.model_dump()}, ensure_ascii=False)

        return get_order_status

    def _shipping_tool(self):
        shipping = self.shipping

        @tool
        def quote_shipping(postal_code: str, subtotal_cents: int) -> str:
            """Quote shipping in BRL cents for a Brazilian postal code and a cart subtotal."""
            quote = shipping.quote(postal_code, int(subtotal_cents))
            if quote is None:
                return json.dumps({"quoted": False, "reason": "invalid_postal_code"})
            return json.dumps({"quoted": True, "quote": quote.model_dump()}, ensure_ascii=False)

        return quote_shipping


def catalog_source(offer: dict, locale: str = "pt") -> dict:
    title = offer["name_pt"] if locale == "pt" else offer["name_en"]
    snippet = offer["blurb_pt"] if locale == "pt" else offer["blurb_en"]
    return Source(
        id=f"catalog:{offer['sku']}",
        title=title,
        snippet=first_sentence(snippet),
        kind="catalog",
    ).model_dump()
