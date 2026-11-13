"""Run one turn of the compiled graph and shape the public response."""

from __future__ import annotations

import time
import uuid
from collections.abc import Iterator

from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from shopmind.agent.workflow import ShopMindWorkflow
from shopmind.schemas import (
    ChatRequest,
    ChatResponse,
    NodeTrace,
    ProductCard,
    PublicProduct,
    Source,
    TokenUsage,
    ToolTrace,
)


class AgentEvent(BaseModel):
    kind: str
    node: NodeTrace | None = None
    response: ChatResponse | None = None


class ShopMindAgent:
    def __init__(self, workflow: ShopMindWorkflow, provider: str) -> None:
        self.workflow = workflow
        self.provider = provider

    def chat(self, request: ChatRequest) -> ChatResponse:
        response: ChatResponse | None = None
        for event in self.iter_events(request):
            if event.response is not None:
                response = event.response
        if response is None:
            raise RuntimeError("the graph finished without a reply")
        return response

    def iter_events(self, request: ChatRequest) -> Iterator[AgentEvent]:
        config = {"configurable": {"thread_id": request.session_id}}
        payload = self._payload(request, config)
        started = time.perf_counter()
        nodes: list[NodeTrace] = []
        previous = started
        for update in self.workflow.graph.stream(payload, config, stream_mode="updates"):
            now = time.perf_counter()
            for name, data in update.items():
                if not isinstance(data, dict):
                    data = {}
                node = NodeTrace(
                    name=str(name),
                    latency_ms=round((now - previous) * 1000, 2),
                    detail=str(data.get("trace_detail") or ""),
                    tools=[str(tool) for tool in data.get("trace_tools") or []],
                )
                nodes.append(node)
                yield AgentEvent(kind="node", node=node)
            previous = now
        final = self.workflow.graph.get_state(config).values
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        yield AgentEvent(
            kind="done",
            response=self._response(request, final, nodes, elapsed),
        )

    def _payload(self, request: ChatRequest, config: dict) -> dict:
        prior = False
        try:
            snapshot = self.workflow.graph.get_state(config)
            prior = bool(snapshot.values.get("messages")) if snapshot.values else False
        except Exception:
            prior = False
        messages = []
        if not prior:
            for item in request.history:
                kind = HumanMessage if item.role == "user" else AIMessage
                messages.append(kind(content=item.content))
        messages.append(HumanMessage(content=request.message, id=str(uuid.uuid4())))
        return {
            "messages": messages,
            "session_id": request.session_id,
            "locale_hint": request.locale,
            "blocked": False,
            "block_reason": None,
            "redacted_card": False,
            "handoff": False,
            "handoff_reason": None,
            "protocol": None,
            "guard_rewritten": False,
            "tool_trace": [],
            "sources": [],
            "offers": [],
            "recommendations": [],
            "policies": [],
            "missing": [],
            "candidate_skus": [],
            "answer": "",
            "order": None,
            "order_found": None,
            "shipping": None,
            "usage": {"prompt": 0, "completion": 0, "estimated": True},
        }

    def _response(
        self,
        request: ChatRequest,
        state: dict,
        nodes: list[NodeTrace],
        elapsed: float,
    ) -> ChatResponse:
        locale = state.get("locale") if state.get("locale") in {"pt", "en"} else "pt"
        usage = state.get("usage") or {}
        return ChatResponse(
            reply=str(state.get("answer") or ""),
            session_id=request.session_id,
            intent=str(state.get("intent") or "out_of_scope"),
            confidence=float(state.get("confidence") or 0),
            locale=locale,
            handoff=bool(state.get("handoff")),
            handoff_reason=state.get("handoff_reason"),
            protocol=state.get("protocol"),
            sources=[Source.model_validate(item) for item in state.get("sources") or []],
            products=[_public(item, locale) for item in state.get("offers") or []],
            recommendations=[_public(item, locale) for item in state.get("recommendations") or []],
            tools=[
                ToolTrace(tool=item["tool"], summary=item.get("summary", ""))
                for item in state.get("tool_trace") or []
                if isinstance(item, dict) and item.get("tool")
            ],
            nodes=nodes,
            usage=TokenUsage(
                prompt=int(usage.get("prompt") or 0),
                completion=int(usage.get("completion") or 0),
                estimated=bool(usage.get("estimated", True)),
            ),
            latency_ms=elapsed,
            provider=self.provider,
            guard_rewritten=bool(state.get("guard_rewritten")),
            blocked=bool(state.get("blocked")),
            redacted_card=bool(state.get("redacted_card")),
        )


def _public(payload: dict, locale: str) -> PublicProduct:
    card = ProductCard.model_validate(payload)
    return PublicProduct(
        sku=card.sku,
        name=card.name(locale),
        price_cents=card.price_cents,
        stock=card.stock,
        category=card.category,
        image_key=card.image_key,
        blurb=card.blurb(locale),
        weight_grams=int(payload.get("weight_grams") or 0),
    )
