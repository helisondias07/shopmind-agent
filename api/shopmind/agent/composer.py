"""Reply rendering.

The template composer is the source of truth in fake mode and the fallback when
a model draft fails the output guard.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from shopmind.agent.prompts import COMPOSE_SYSTEM
from shopmind.schemas import (
    OrderView,
    PolicyView,
    ProductCard,
    ShippingQuote,
    Source,
    TokenUsage,
)
from shopmind.textutil import format_money

STATUS_LABELS = {
    "processing": ("em separação", "being prepared"),
    "shipped": ("enviado", "shipped"),
    "delivered": ("entregue", "delivered"),
    "cancelled": ("cancelado", "cancelled"),
}


class Grounding(BaseModel):
    locale: str = "pt"
    intent: str = "out_of_scope"
    products: list[ProductCard] = Field(default_factory=list)
    recommendations: list[ProductCard] = Field(default_factory=list)
    order: OrderView | None = None
    order_id: str | None = None
    order_found: bool | None = None
    shipping: ShippingQuote | None = None
    policies: list[PolicyView] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    handoff: bool = False
    handoff_reason: str | None = None
    protocol: str | None = None
    blocked: bool = False
    sources: list[Source] = Field(default_factory=list)


class AnswerComposer(Protocol):
    def compose(self, grounding: Grounding, history: str) -> tuple[str, TokenUsage, bool]: ...


class TemplateComposer:
    def compose(self, grounding: Grounding, history: str = "") -> tuple[str, TokenUsage, bool]:
        del history
        text = self.render(grounding)
        usage = TokenUsage(
            prompt=max(1, len(grounding.model_dump_json()) // 4),
            completion=max(1, len(text) // 4),
            estimated=True,
        )
        return text, usage, False

    def render(self, grounding: Grounding) -> str:
        locale = grounding.locale if grounding.locale in {"pt", "en"} else "pt"
        if grounding.blocked:
            return _blocked(locale)
        if grounding.handoff:
            return _handoff(locale, grounding.protocol or "LM-H-PENDING", grounding.handoff_reason)
        if grounding.intent == "greeting":
            return _greeting(locale)
        if grounding.intent == "out_of_scope":
            return _out_of_scope(locale)
        if grounding.intent == "order":
            return _order(locale, grounding)
        if grounding.intent == "shipping":
            return _shipping(locale, grounding)
        if grounding.intent == "policy":
            return _policy(locale, grounding)
        return _products(locale, grounding)


class LlmComposer:
    def __init__(self, llm, fallback: TemplateComposer) -> None:
        from pydantic import BaseModel as PydanticModel

        class Draft(PydanticModel):
            message: str

        self._draft_type = Draft
        self._runnable = llm.with_structured_output(Draft, include_raw=True)
        self._fallback = fallback

    def compose(self, grounding: Grounding, history: str) -> tuple[str, TokenUsage, bool]:
        from langchain_core.messages import HumanMessage, SystemMessage

        from shopmind.agent.guardrails import draft_is_grounded

        payload = grounding.model_dump_json()
        try:
            raw = self._runnable.invoke(
                [
                    SystemMessage(content=COMPOSE_SYSTEM),
                    HumanMessage(content=f"history:\n{history}\n\ngrounding:\n{payload}"),
                ]
            )
            parsed = raw["parsed"] if isinstance(raw, dict) else raw
            message = getattr(parsed, "message", "")
            if not message:
                raise ValueError("empty draft")
            if not draft_is_grounded(
                message,
                grounding.products,
                grounding.recommendations,
                grounding.order,
                grounding.shipping,
                grounding.policies,
            ):
                text, usage, _rewritten = self._fallback.compose(grounding, history)
                return text, usage, True
            from shopmind.agent.classifier import _usage_from_raw

            return message, _usage_from_raw(raw), False
        except Exception:
            text, usage, _rewritten = self._fallback.compose(grounding, history)
            return text, usage, True


def _blocked(locale: str) -> str:
    if locale == "en":
        return (
            "I can't change my instructions or reveal internal notes. "
            "Ask me about a product, an order, shipping, or a store policy."
        )
    return (
        "Não posso alterar minhas instruções nem revelar dados internos. "
        "Se quiser, pergunte sobre um produto, um pedido, o frete ou uma política da loja."
    )


def _greeting(locale: str) -> str:
    if locale == "en":
        return (
            "Hello, I'm ShopMind, the support assistant for Lume & Co. "
            "I can help with products, stock, orders, shipping, and store policies."
        )
    return (
        "Olá, eu sou o ShopMind, o atendimento da Lume & Co. "
        "Posso falar de produtos, estoque, pedidos, frete e das políticas da loja."
    )


def _out_of_scope(locale: str) -> str:
    if locale == "en":
        return (
            "I can help with Lume & Co. products, orders, shipping, and policies. "
            "That question is outside this shop."
        )
    return (
        "Consigo ajudar com os produtos, os pedidos, o frete e as políticas da Lume & Co. "
        "Essa pergunta fica fora desse escopo."
    )


def _handoff(locale: str, protocol: str, reason: str | None) -> str:
    if reason == "user_request":
        because = (
            "You asked to talk to a person."
            if locale == "en"
            else "Você pediu para falar com uma pessoa."
        )
    else:
        because = (
            "I'm not confident enough to answer this on my own."
            if locale == "en"
            else "Não tenho segurança suficiente para responder sozinho."
        )
    if locale == "en":
        return f"I'm handing this conversation to a person. Protocol {protocol}. {because}"
    return f"Vou passar você para um atendente humano. Protocolo {protocol}. {because}"


def _products(locale: str, grounding: Grounding) -> str:
    products = grounding.products
    if not products:
        if locale == "en":
            return (
                "I couldn't find that item in the Lume & Co. catalog. "
                "Try another name, or ask me what the shop carries.\nSource: catalog."
            )
        return (
            "Não achei esse item no catálogo da Lume & Co. "
            "Posso procurar por outro nome ou listar o que temos na loja.\nFonte: catálogo."
        )
    if len(products) > 1:
        lines = []
        for product in products:
            stock = _stock_phrase(product.stock, locale)
            lines.append(
                f"- {product.name(locale)} ({product.sku}): "
                f"{format_money(product.price_cents, locale)}. {stock}"
            )
        header = (
            "These are the pieces currently in the Lume & Co. catalog:"
            if locale == "en"
            else "Estes são os itens do catálogo da Lume & Co.:"
        )
        source = "Source: store catalog." if locale == "en" else "Fonte: catálogo da loja."
        return header + "\n" + "\n".join(lines) + "\n" + source

    product = products[0]
    stock = _stock_phrase(product.stock, locale)
    price = format_money(product.price_cents, locale)
    extra = ""
    if grounding.recommendations:
        names = ", ".join(item.name(locale) for item in grounding.recommendations)
        extra = (
            f" In the same category: {names}."
            if locale == "en"
            else f" Na mesma categoria: {names}."
        )
    if locale == "en":
        return (
            f"{product.name(locale)} ({product.sku}) is {price}. {stock} "
            f"{product.blurb(locale)}{extra}\nSource: catalog {product.sku}."
        )
    return (
        f"{product.name(locale)} ({product.sku}) custa {price}. {stock} "
        f"{product.blurb(locale)}{extra}\nFonte: catálogo {product.sku}."
    )


def _stock_phrase(stock: int, locale: str) -> str:
    if stock <= 0:
        return "It is out of stock right now." if locale == "en" else "Está esgotada no momento."
    if locale == "en":
        unit = "unit" if stock == 1 else "units"
        return f"{stock} {unit} in stock."
    unit = "unidade" if stock == 1 else "unidades"
    return f"Há {stock} {unit} em estoque."


def _order(locale: str, grounding: Grounding) -> str:
    if not grounding.order_id:
        if locale == "en":
            return (
                "I can look up an order once you share the id, in the form LM-1042.\n"
                "Source: store orders."
            )
        return (
            "Consigo consultar o pedido se você me passar o número, no formato LM-1042.\n"
            "Fonte: pedidos da loja."
        )
    if not grounding.order_found or grounding.order is None:
        if locale == "en":
            return (
                f"I could not find order {grounding.order_id}. "
                "Ids look like LM-1042.\nSource: store orders."
            )
        return (
            f"Não encontrei o pedido {grounding.order_id}. "
            "Os pedidos usam o formato LM- seguido de números, por exemplo LM-1042.\n"
            "Fonte: pedidos da loja."
        )
    order = grounding.order
    status = STATUS_LABELS[order.status][1 if locale == "en" else 0]
    note = order.note_en if locale == "en" else order.note_pt
    items = []
    for item in order.items:
        label = item.name_en if locale == "en" else item.name_pt
        items.append(f"{label} ({item.qty} × {format_money(item.unit_price_cents, locale)})")
    tracking = ""
    if order.tracking_code:
        carrier = order.carrier or ""
        tracking = (
            f" Carrier {carrier}, tracking {order.tracking_code}."
            if locale == "en"
            else f" Transportadora {carrier}, rastreio {order.tracking_code}."
        )
    item_text = ", ".join(items)
    if locale == "en":
        return (
            f"Order {order.public_id} for {order.customer_first_name}: {status}.{tracking} "
            f"{note} Items: {item_text}.\nSource: order {order.public_id}."
        )
    return (
        f"Pedido {order.public_id} de {order.customer_first_name}: {status}.{tracking} "
        f"{note} Itens: {item_text}.\nFonte: pedido {order.public_id}."
    )


def _shipping(locale: str, grounding: Grounding) -> str:
    if grounding.shipping is None:
        if locale == "en":
            return (
                "To quote shipping I need the postal code, eight digits, for example 01001-000.\n"
                "Source: shipping policy."
            )
        return (
            "Para calcular o frete preciso do CEP, com 8 dígitos, por exemplo 01001-000.\n"
            "Fonte: política de frete."
        )
    quote = grounding.shipping
    threshold = format_money(quote.threshold_cents, locale)
    region = quote.region_en if locale == "en" else quote.region_pt
    if quote.free_shipping:
        if locale == "en":
            return (
                f"Shipping to {quote.postal_code} ({region}) is free, because the order "
                f"is at or above {threshold}. Delivery in up to {quote.eta_business_days} "
                f"business days.\nSource: shipping policy."
            )
        return (
            f"Frete para {quote.postal_code} ({region}): grátis, porque o pedido chega a "
            f"{threshold} ou mais. Prazo de até {quote.eta_business_days} dias úteis.\n"
            "Fonte: política de frete."
        )
    price = format_money(quote.price_cents, locale)
    if locale == "en":
        return (
            f"Shipping to {quote.postal_code} ({region}): {price}, in up to "
            f"{quote.eta_business_days} business days. Shipping is free from {threshold}.\n"
            "Source: shipping policy."
        )
    return (
        f"Frete para {quote.postal_code} ({region}): {price}, em até "
        f"{quote.eta_business_days} dias úteis. Frete grátis a partir de {threshold}.\n"
        "Fonte: política de frete."
    )


def _policy(locale: str, grounding: Grounding) -> str:
    if not grounding.policies:
        if locale == "en":
            return (
                "I don't have a policy that matches that question. "
                "I can explain returns, shipping, warranty, payment, or privacy.\n"
                "Source: store policies."
            )
        return (
            "Não achei uma política que responda a essa pergunta. "
            "Posso explicar trocas, frete, garantia, pagamento ou privacidade.\n"
            "Fonte: políticas da loja."
        )
    policy = grounding.policies[0]
    if locale == "en":
        return f"{policy.title_en}: {policy.body_en}\nSource: policy {policy.slug}."
    return f"{policy.title_pt}: {policy.body_pt}\nFonte: política {policy.slug}."
