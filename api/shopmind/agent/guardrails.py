"""Input and output guards.

The output guard is the last word on money and stock: if a draft cites a figure
that is not in the grounding payload, the draft is replaced by the deterministic
template built from that same payload.
"""

from __future__ import annotations

import re

from shopmind.schemas import PolicyView, ProductCard, ShippingQuote
from shopmind.textutil import CARD_RE, extract_money_cents, redact_payment_cards

INJECTION_RE = re.compile(
    r"(ignore (all|any|previous|above|prior) (instructions|prompts|rules))"
    r"|(ignore (the |as )?instru[cç][oõ]es)"
    r"|(esque[cç]a (todas )?(as )?(regras|instru[cç][oõ]es))"
    r"|((reveal|show|print|dump) (your |the )?(system |hidden )?(prompt|instructions))"
    r"|(you are now)"
    r"|(\bact as (dan|root|system)\b)"
    r"|(jailbreak)"
    r"|(do anything now)",
    re.IGNORECASE,
)

STOCK_UNIT_RE = re.compile(
    r"\b(\d+)\s+(unidades|unidade|units|unit)\b",
    re.IGNORECASE,
)


class InputGuard:
    def inspect(self, text: str) -> tuple[str, bool, bool]:
        """Return redacted text, whether the turn is blocked, and whether a card was removed."""
        redacted, had_card = redact_payment_cards(text)
        blocked = INJECTION_RE.search(redacted) is not None
        return redacted, blocked, had_card


def allowed_cents(
    products: list[ProductCard],
    recommendations: list[ProductCard],
    order,
    shipping,
    policies: list[PolicyView],
) -> set[int]:
    cents: set[int] = set()
    for product in [*products, *recommendations]:
        cents.add(product.price_cents)
    if order is not None:
        cents.add(order.total_cents)
        cents.update(extract_money_cents(order.note_pt))
        cents.update(extract_money_cents(order.note_en))
        for item in order.items:
            cents.add(item.unit_price_cents)
    if shipping is not None:
        cents.add(shipping.price_cents)
        cents.add(shipping.threshold_cents)
        if shipping.free_shipping:
            cents.add(0)
    for policy in policies:
        cents.update(extract_money_cents(policy.body_pt))
        cents.update(extract_money_cents(policy.body_en))
    return cents


def allowed_stock(products: list[ProductCard], recommendations: list[ProductCard]) -> set[int]:
    return {product.stock for product in [*products, *recommendations]}


def draft_is_grounded(draft: str, products, recommendations, order, shipping, policies) -> bool:
    if CARD_RE.search(draft):
        return False
    permitted = allowed_cents(products, recommendations, order, shipping, policies)
    for cents in extract_money_cents(draft):
        if cents not in permitted:
            return False
    stocks = allowed_stock(products, recommendations)
    for match in STOCK_UNIT_RE.finditer(draft):
        if int(match.group(1)) not in stocks:
            return False
    return True


def shipping_quote_or_none(payload: dict | None) -> ShippingQuote | None:
    if not payload:
        return None
    return ShippingQuote.model_validate(payload)
