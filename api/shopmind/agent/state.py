"""Typed state for the ShopMind graph. The message list is the session memory."""

from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]
    session_id: str
    locale_hint: str
    locale: str
    blocked: bool
    block_reason: str | None
    redacted_card: bool
    intent: str
    confidence: float
    order_id: str | None
    postal_code: str | None
    product_query: str | None
    policy_query: str | None
    last_sku: str | None
    last_order_id: str | None
    candidate_skus: list[str]
    offers: list[dict]
    recommendations: list[dict]
    order: dict | None
    order_found: bool | None
    shipping: dict | None
    policies: list[dict]
    missing: list[str]
    sources: list[dict]
    answer: str
    handoff: bool
    handoff_reason: str | None
    protocol: str | None
    tool_trace: list[dict]
    trace_detail: str
    trace_tools: list[str]
    usage: dict
    guard_rewritten: bool
