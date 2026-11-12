"""Intent classification.

`FakeIntentClassifier` is a deterministic stand-in with the same return type as
the LLM classifier, so the graph and the evals do not depend on a provider.
"""

from __future__ import annotations

import re
from typing import Protocol

from shopmind.agent.prompts import CLASSIFY_SYSTEM
from shopmind.rag.index import CatalogIndex
from shopmind.schemas import IntentClassification, TokenUsage
from shopmind.textutil import find_cep, find_order_id, normalize

_HUMAN = re.compile(
    r"\b(atendente|humano|humana|pessoa real|falar com (uma )?(pessoa|alguem|alguém)|"
    r"human|representative|real person|talk to (a |an )?(human|person))\b",
    re.IGNORECASE,
)
_ORDER = re.compile(r"\b(pedido|order|rastreio|rastrear|tracking)\b", re.IGNORECASE)
_SHIP = re.compile(r"\b(frete|shipping|delivery fee)\b", re.IGNORECASE)
_PRODUCT = re.compile(
    r"\b(quanto|custa|preco|preço|price|estoque|stock|catalogo|catálogo|produtos|"
    r"products|disponivel|disponível|available|how much)\b",
    re.IGNORECASE,
)
_GREET = re.compile(
    r"^(oi|ola|olá|hello|hi|hey|bom dia|boa tarde|boa noite|"
    r"good morning|good afternoon|good evening)\b",
    re.IGNORECASE,
)
_OOS = re.compile(
    r"\b(copa|futebol|weather|clima|previs[aã]o|piada|joke|capital of|"
    r"quem ganhou|who won|programar|write code|receita de bolo)\b",
    re.IGNORECASE,
)
_OVERVIEW = re.compile(
    r"(o que voc[eê]s vendem|quais produtos|cat[aá]logo completo|"
    r"what do you sell|show me (the |your )?products)",
    re.IGNORECASE,
)
_REFERENTIAL = re.compile(
    r"\b(ele|ela|dele|dela|isso|esse|essa|aquele|aquela|that|this|same|mesmo)\b",
    re.IGNORECASE,
)
_POLICIES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(troca|trocas|devolu|devolver|return policy|exchange)\b", re.I), "returns"),
    (re.compile(r"\b(garantia|warranty)\b", re.I), "warranty"),
    (re.compile(r"\b(pagamento|pix|payment|meio de pagamento)\b", re.I), "payment"),
    (re.compile(r"\b(privacidade|privacy|meus dados|my data)\b", re.I), "privacy"),
    (re.compile(r"(pol[ií]tica de frete|shipping policy)", re.I), "shipping"),
)
_PT = re.compile(
    r"\b(n[aã]o|voc[eê]|pedido|frete|quanto|custa|troca|obrigad|ol[aá]|estoque|voc[eê]s|"
    r"qual|onde|meu|minha)\b",
    re.IGNORECASE,
)
_EN = re.compile(
    r"\b(the|what|how|order|shipping|price|return|please|stock|hello|does|much|where|my)\b",
    re.IGNORECASE,
)


def detect_locale(message: str, hint: str | None) -> str:
    pt_hits = len(_PT.findall(message))
    en_hits = len(_EN.findall(message))
    if pt_hits > en_hits:
        return "pt"
    if en_hits > pt_hits:
        return "en"
    if hint in {"pt", "en"}:
        return hint
    return "pt"


def estimate_usage(prompt: str, completion: str) -> TokenUsage:
    return TokenUsage(
        prompt=max(1, len(prompt) // 4),
        completion=max(1, len(completion) // 4),
        estimated=True,
    )


class IntentClassifier(Protocol):
    def classify(
        self,
        message: str,
        history: str,
        last_sku: str | None,
        last_order_id: str | None,
        locale_hint: str,
    ) -> tuple[IntentClassification, TokenUsage]: ...


class FakeIntentClassifier:
    def __init__(self, index: CatalogIndex) -> None:
        self.index = index

    def classify(
        self,
        message: str,
        history: str,
        last_sku: str | None,
        last_order_id: str | None,
        locale_hint: str,
    ) -> tuple[IntentClassification, TokenUsage]:
        locale = detect_locale(message, locale_hint)
        order_id = find_order_id(message)
        postal_code = find_cep(message)
        lexical = self.index._lexical_products(message)
        product_query = lexical[0].name_pt if lexical else None
        policy_query = next((slug for pattern, slug in _POLICIES if pattern.search(message)), None)

        def finish(
            intent: str,
            confidence: float,
            reason: str = "",
            order: str | None = order_id,
            product: str | None = product_query,
            policy: str | None = None,
            postal: str | None = postal_code,
        ) -> tuple[IntentClassification, TokenUsage]:
            result = IntentClassification(
                intent=intent,  # type: ignore[arg-type]
                confidence=confidence,
                locale=locale,  # type: ignore[arg-type]
                order_id=order,
                postal_code=postal,
                product_query=product,
                policy_query=policy,
                reason=reason,
            )
            usage = estimate_usage(message, result.model_dump_json())
            return result, usage

        if _HUMAN.search(message):
            return finish("human", 0.97, reason="user_request")

        if order_id or _ORDER.search(message):
            resolved = order_id or last_order_id
            return finish(
                "order",
                0.94 if resolved else 0.78,
                order=resolved,
                reason="order_id" if resolved else "missing_order_id",
            )

        if policy_query and not postal_code:
            return finish("policy", 0.9, policy=policy_query, reason=policy_query)

        if postal_code or _SHIP.search(message):
            product = product_query
            if product is None and last_sku and _SHIP.search(message):
                product = last_sku
            return finish("shipping", 0.91, product=product, reason="shipping_quote")

        if _OVERVIEW.search(normalize(message)) or _OVERVIEW.search(message):
            return finish("product", 0.9, product="*", reason="catalog_overview")

        if lexical or _PRODUCT.search(message):
            product = product_query
            if product is None and last_sku and _REFERENTIAL.search(message):
                product = last_sku
            confidence = 0.9 if product else 0.62
            return finish("product", confidence, product=product or message, reason="catalog")

        if _GREET.search(message.strip()) and len(message) < 60:
            return finish("greeting", 0.95, reason="greeting")

        if _OOS.search(message):
            return finish("out_of_scope", 0.88, reason="out_of_scope")

        if last_sku and _REFERENTIAL.search(message):
            return finish("product", 0.74, product=last_sku, reason="memory")

        return finish("out_of_scope", 0.28, reason="low_confidence")


class LlmIntentClassifier:
    """Structured-output classifier. Any provider error falls back to the fake one."""

    def __init__(self, llm, fallback: FakeIntentClassifier, catalog_brief: str) -> None:
        self._runnable = llm.with_structured_output(IntentClassification, include_raw=True)
        self._fallback = fallback
        self._brief = catalog_brief

    def classify(
        self,
        message: str,
        history: str,
        last_sku: str | None,
        last_order_id: str | None,
        locale_hint: str,
    ) -> tuple[IntentClassification, TokenUsage]:
        prompt = CLASSIFY_SYSTEM.format(catalog=self._brief)
        user = (
            f"locale_hint: {locale_hint}\n"
            f"last_sku: {last_sku or ''}\n"
            f"last_order_id: {last_order_id or ''}\n"
            f"history:\n{history}\n"
            f"message:\n{message}"
        )
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            raw = self._runnable.invoke([SystemMessage(content=prompt), HumanMessage(content=user)])
            parsed = raw["parsed"] if isinstance(raw, dict) else raw
            if not isinstance(parsed, IntentClassification):
                raise TypeError("classifier returned no structured intent")
            usage = _usage_from_raw(raw)
            return parsed, usage
        except Exception:
            return self._fallback.classify(message, history, last_sku, last_order_id, locale_hint)


def _usage_from_raw(raw) -> TokenUsage:
    message = raw.get("raw") if isinstance(raw, dict) else None
    metadata = getattr(message, "usage_metadata", None) or {}
    if not metadata:
        return estimate_usage("", "")
    return TokenUsage(
        prompt=int(metadata.get("input_tokens") or 0),
        completion=int(metadata.get("output_tokens") or 0),
        estimated=False,
    )
