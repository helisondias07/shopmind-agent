"""Pydantic contracts shared by the graph, the tools, and the HTTP API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

IntentName = Literal[
    "greeting",
    "product",
    "order",
    "shipping",
    "policy",
    "human",
    "out_of_scope",
    "blocked",
]
LocaleName = Literal["pt", "en"]


class ProductCard(BaseModel):
    sku: str
    name_pt: str
    name_en: str
    price_cents: int
    stock: int
    category: str
    image_key: str
    blurb_pt: str
    blurb_en: str

    def name(self, locale: str) -> str:
        return self.name_pt if locale == "pt" else self.name_en

    def blurb(self, locale: str) -> str:
        return self.blurb_pt if locale == "pt" else self.blurb_en


class PublicProduct(BaseModel):
    sku: str
    name: str
    price_cents: int
    currency: str = "BRL"
    stock: int
    category: str
    image_key: str
    blurb: str
    weight_grams: int


class Source(BaseModel):
    id: str
    title: str
    snippet: str
    kind: Literal["catalog", "policy", "order", "shipping"]


class OrderItemView(BaseModel):
    sku: str
    name_pt: str
    name_en: str
    qty: int
    unit_price_cents: int


class OrderView(BaseModel):
    public_id: str
    customer_first_name: str
    status: Literal["processing", "shipped", "delivered", "cancelled"]
    carrier: str | None = None
    tracking_code: str | None = None
    total_cents: int
    items: list[OrderItemView]
    note_pt: str
    note_en: str


class ShippingQuote(BaseModel):
    postal_code: str
    subtotal_cents: int
    price_cents: int
    eta_business_days: int
    free_shipping: bool
    region: str
    region_pt: str
    region_en: str
    threshold_cents: int


class PolicyView(BaseModel):
    slug: str
    topic: str
    title_pt: str
    title_en: str
    body_pt: str
    body_en: str

    def title(self, locale: str) -> str:
        return self.title_pt if locale == "pt" else self.title_en

    def body(self, locale: str) -> str:
        return self.body_pt if locale == "pt" else self.body_en


class IntentClassification(BaseModel):
    """Structured output of the intent node. The fake classifier returns the same shape."""

    intent: IntentName
    confidence: float = Field(ge=0, le=1)
    locale: LocaleName
    order_id: str | None = None
    postal_code: str | None = Field(
        default=None, description="Eight Brazilian postal digits, no hyphen."
    )
    product_query: str | None = None
    policy_query: str | None = None
    reason: str = ""


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(default="default", pattern=r"^[A-Za-z0-9_-]{1,64}$")
    locale: Literal["pt", "en", "auto"] = "auto"
    history: list[HistoryItem] = Field(default_factory=list, max_length=12)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message is empty")
        return cleaned

    @field_validator("history")
    @classmethod
    def strip_history(cls, value: list[HistoryItem]) -> list[HistoryItem]:
        kept: list[HistoryItem] = []
        for item in value:
            content = item.content.strip()
            if content:
                kept.append(HistoryItem(role=item.role, content=content))
        return kept


class ToolTrace(BaseModel):
    tool: str
    summary: str


class NodeTrace(BaseModel):
    name: str
    latency_ms: float
    detail: str = ""
    tools: list[str] = Field(default_factory=list)


class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0
    estimated: bool = True


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    intent: str
    confidence: float
    locale: LocaleName
    handoff: bool
    handoff_reason: str | None = None
    protocol: str | None = None
    sources: list[Source] = Field(default_factory=list)
    products: list[PublicProduct] = Field(default_factory=list)
    recommendations: list[PublicProduct] = Field(default_factory=list)
    tools: list[ToolTrace] = Field(default_factory=list)
    nodes: list[NodeTrace] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    latency_ms: float
    provider: str
    guard_rewritten: bool = False
    blocked: bool = False
    redacted_card: bool = False


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "shopmind"
    version: str
    provider: str
    model: str
    embeddings: str
    vector_store: str
    handoff_confidence: float


class EvalCaseResult(BaseModel):
    id: str
    passed: bool
    intent: str
    handoff: bool
    errors: list[str]
    reply: str


class EvalReport(BaseModel):
    provider: str
    total: int
    passed: int
    failed: int
    results: list[EvalCaseResult]
