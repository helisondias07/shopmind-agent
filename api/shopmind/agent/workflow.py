"""The ShopMind graph: guards, intent routing, tools, a grounded reply."""

from __future__ import annotations

import hashlib

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from shopmind.agent.classifier import IntentClassifier, detect_locale
from shopmind.agent.composer import Grounding, TemplateComposer
from shopmind.agent.guardrails import InputGuard, draft_is_grounded
from shopmind.agent.state import AgentState
from shopmind.schemas import (
    OrderView,
    PolicyView,
    ProductCard,
    ShippingQuote,
    Source,
    TokenUsage,
)
from shopmind.tools.registry import SupportTools, catalog_source


def protocol_for(session_id: str) -> str:
    digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:6].upper()
    return f"LM-H-{digest}"


def _merge_usage(state: AgentState, extra: TokenUsage) -> dict:
    previous = state.get("usage") or {"prompt": 0, "completion": 0, "estimated": True}
    return {
        "prompt": int(previous.get("prompt", 0)) + extra.prompt,
        "completion": int(previous.get("completion", 0)) + extra.completion,
        "estimated": bool(previous.get("estimated", True)) or extra.estimated,
    }


def _history(state: AgentState) -> str:
    messages = state.get("messages") or []
    lines: list[str] = []
    for message in messages[:-1][-6:]:
        content = message.content if isinstance(message.content, str) else str(message.content)
        role = "user" if getattr(message, "type", "") == "human" else "assistant"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _last_text(state: AgentState) -> str:
    messages = state.get("messages") or []
    if not messages:
        return ""
    content = messages[-1].content
    return content if isinstance(content, str) else str(content)


class ShopMindWorkflow:
    """One compiled LangGraph. Nodes are methods so the wiring stays in one class."""

    def __init__(
        self,
        tools: SupportTools,
        classifier: IntentClassifier,
        composer,
        templates: TemplateComposer,
        guards: InputGuard,
        checkpointer,
        handoff_confidence: float,
    ) -> None:
        self.tools = tools
        self.classifier = classifier
        self.composer = composer
        self.templates = templates
        self.guards = guards
        self.handoff_confidence = handoff_confidence
        self.graph: CompiledStateGraph = self._compile(checkpointer)

    def _compile(self, checkpointer) -> CompiledStateGraph:
        graph = StateGraph(AgentState)
        graph.add_node("guard_input", self.guard_input)
        graph.add_node("classify_intent", self.classify_intent)
        graph.add_node("retrieve_catalog", self.retrieve_catalog)
        graph.add_node("check_inventory", self.check_inventory)
        graph.add_node("recommend", self.recommend)
        graph.add_node("retrieve_policy", self.retrieve_policy)
        graph.add_node("lookup_order", self.lookup_order)
        graph.add_node("quote_shipping", self.quote_shipping)
        graph.add_node("compose_answer", self.compose_answer)
        graph.add_node("handoff", self.handoff)
        graph.add_node("decline", self.decline)
        graph.add_node("guard_output", self.guard_output)
        graph.add_edge(START, "guard_input")
        graph.add_conditional_edges(
            "guard_input",
            self.route_after_guard,
            {"decline": "decline", "classify_intent": "classify_intent"},
        )
        graph.add_conditional_edges(
            "classify_intent",
            self.route_after_classify,
            {
                "handoff": "handoff",
                "compose_answer": "compose_answer",
                "retrieve_catalog": "retrieve_catalog",
                "lookup_order": "lookup_order",
                "quote_shipping": "quote_shipping",
                "retrieve_policy": "retrieve_policy",
                "decline": "decline",
            },
        )
        graph.add_edge("retrieve_catalog", "check_inventory")
        graph.add_edge("check_inventory", "recommend")
        graph.add_edge("recommend", "compose_answer")
        graph.add_edge("lookup_order", "compose_answer")
        graph.add_edge("quote_shipping", "compose_answer")
        graph.add_edge("retrieve_policy", "compose_answer")
        graph.add_edge("compose_answer", "guard_output")
        graph.add_edge("handoff", "guard_output")
        graph.add_edge("decline", "guard_output")
        graph.add_edge("guard_output", END)
        return graph.compile(checkpointer=checkpointer)

    def route_after_guard(self, state: AgentState) -> str:
        if state.get("blocked"):
            return "decline"
        return "classify_intent"

    def route_after_classify(self, state: AgentState) -> str:
        intent = state.get("intent") or "out_of_scope"
        confidence = float(state.get("confidence") or 0)
        if intent == "human" or confidence < self.handoff_confidence:
            return "handoff"
        return {
            "greeting": "compose_answer",
            "product": "retrieve_catalog",
            "order": "lookup_order",
            "shipping": "quote_shipping",
            "policy": "retrieve_policy",
            "out_of_scope": "decline",
        }.get(intent, "handoff")

    def guard_input(self, state: AgentState) -> dict:
        messages = state.get("messages") or []
        last = messages[-1]
        text = last.content if isinstance(last.content, str) else str(last.content)
        redacted, blocked, had_card = self.guards.inspect(text)
        locale = detect_locale(redacted, state.get("locale_hint"))
        update: dict = {
            "locale": locale,
            "blocked": blocked,
            "block_reason": "prompt_injection" if blocked else None,
            "redacted_card": had_card,
            "trace_tools": [],
            "trace_detail": "blocked prompt injection" if blocked else "accepted",
        }
        if blocked:
            update["intent"] = "blocked"
            update["confidence"] = 1.0
        if redacted != text:
            update["messages"] = [HumanMessage(content=redacted, id=getattr(last, "id", None))]
            update["trace_detail"] = (
                "blocked prompt injection; card redacted" if blocked else "payment card redacted"
            )
        return update

    def classify_intent(self, state: AgentState) -> dict:
        result, usage = self.classifier.classify(
            message=_last_text(state),
            history=_history(state),
            last_sku=state.get("last_sku"),
            last_order_id=state.get("last_order_id"),
            locale_hint=state.get("locale_hint") or "auto",
        )
        return {
            "intent": result.intent,
            "confidence": result.confidence,
            "locale": result.locale,
            "order_id": result.order_id,
            "postal_code": result.postal_code,
            "product_query": result.product_query,
            "policy_query": result.policy_query,
            "usage": _merge_usage(state, usage),
            "trace_detail": f"{result.intent} · {result.confidence:.2f} · {result.reason}",
            "trace_tools": [],
        }

    def retrieve_catalog(self, state: AgentState) -> dict:
        query = state.get("product_query") or _last_text(state)
        payload = self.tools.call("search_knowledge", {"query": query, "kind": "product"})
        skus = [hit["sku"] for hit in payload.get("hits", []) if hit.get("sku")]
        return {
            "candidate_skus": skus,
            "tool_trace": self._trace(
                state, "search_knowledge", {"query": query, "kind": "product"}
            ),
            "trace_tools": ["search_knowledge"],
            "trace_detail": f"{len(skus)} catalog hit(s)",
        }

    def check_inventory(self, state: AgentState) -> dict:
        skus = state.get("candidate_skus") or []
        if not skus:
            return {
                "offers": [],
                "sources": [],
                "trace_tools": [],
                "trace_detail": "no catalog hit",
            }
        payload = self.tools.call("check_inventory", {"skus": ",".join(skus)})
        offers = payload.get("offers", [])
        locale = state.get("locale") or "pt"
        sources = [catalog_source(offer, locale) for offer in offers]
        update: dict = {
            "offers": offers,
            "sources": sources,
            "tool_trace": self._trace(state, "check_inventory", {"skus": ",".join(skus)}),
            "trace_tools": ["check_inventory"],
            "trace_detail": f"{len(offers)} offer(s) from the database",
        }
        if len(offers) == 1:
            update["last_sku"] = offers[0]["sku"]
        return update

    def recommend(self, state: AgentState) -> dict:
        offers = state.get("offers") or []
        if len(offers) != 1:
            return {"recommendations": [], "trace_tools": [], "trace_detail": "no single product"}
        sku = offers[0]["sku"]
        payload = self.tools.call("recommend_products", {"sku": sku})
        recommendations = payload.get("recommendations", [])
        sources = list(state.get("sources") or [])
        locale = state.get("locale") or "pt"
        for item in recommendations:
            sources.append(catalog_source(item, locale))
        return {
            "recommendations": recommendations,
            "sources": sources,
            "tool_trace": self._trace(state, "recommend_products", {"sku": sku}),
            "trace_tools": ["recommend_products"],
            "trace_detail": f"{len(recommendations)} alternative(s)",
        }

    def retrieve_policy(self, state: AgentState) -> dict:
        query = state.get("policy_query") or _last_text(state)
        payload = self.tools.call("search_knowledge", {"query": query, "kind": "policy"})
        policies = payload.get("hits", [])
        sources = [
            Source(
                id=f"policy:{item['slug']}",
                title=item["title_pt"] if state.get("locale") == "pt" else item["title_en"],
                snippet=item["body_pt" if state.get("locale") == "pt" else "body_en"][:180],
                kind="policy",
            ).model_dump()
            for item in policies
        ]
        return {
            "policies": policies,
            "sources": sources,
            "tool_trace": self._trace(
                state, "search_knowledge", {"query": query, "kind": "policy"}
            ),
            "trace_tools": ["search_knowledge"],
            "trace_detail": policies[0]["slug"] if policies else "no policy",
        }

    def lookup_order(self, state: AgentState) -> dict:
        order_id = state.get("order_id")
        if not order_id:
            return {
                "order": None,
                "order_found": False,
                "missing": ["order_id"],
                "sources": [],
                "trace_tools": [],
                "trace_detail": "order id missing",
            }
        payload = self.tools.call("get_order_status", {"order_id": order_id})
        found = bool(payload.get("found"))
        order = payload.get("order")
        source = Source(
            id=f"order:{order_id}",
            title=f"Pedido {order_id}",
            snippet="encontrado" if found else "não encontrado",
            kind="order",
        ).model_dump()
        update: dict = {
            "order": order,
            "order_found": found,
            "sources": [source],
            "missing": [],
            "tool_trace": self._trace(state, "get_order_status", {"order_id": order_id}),
            "trace_tools": ["get_order_status"],
            "trace_detail": "order found" if found else "order not in the database",
        }
        if found:
            update["last_order_id"] = order_id
        return update

    def quote_shipping(self, state: AgentState) -> dict:
        called: list[str] = []
        subtotal = 0
        product_query = state.get("product_query")
        if product_query and product_query != "*":
            search = self.tools.call(
                "search_knowledge", {"query": product_query, "kind": "product"}
            )
            called.append("search_knowledge")
            skus = [hit["sku"] for hit in search.get("hits", []) if hit.get("sku")]
            if skus:
                inventory = self.tools.call("check_inventory", {"skus": skus[0]})
                called.append("check_inventory")
                offers = inventory.get("offers") or []
                if offers:
                    subtotal = int(offers[0]["price_cents"])
        postal = state.get("postal_code")
        trace = list(state.get("tool_trace") or [])
        for name in called:
            trace.append({"tool": name, "summary": name})
        if not postal:
            return {
                "shipping": None,
                "missing": ["postal_code"],
                "sources": [_shipping_source()],
                "tool_trace": trace,
                "trace_tools": called,
                "trace_detail": "postal code missing",
            }
        payload = self.tools.call(
            "quote_shipping", {"postal_code": postal, "subtotal_cents": subtotal}
        )
        called.append("quote_shipping")
        trace.append({"tool": "quote_shipping", "summary": f"{postal} subtotal={subtotal}"})
        quote = payload.get("quote") if payload.get("quoted") else None
        return {
            "shipping": quote,
            "missing": [] if quote else ["postal_code"],
            "sources": [_shipping_source()],
            "tool_trace": trace,
            "trace_tools": called,
            "trace_detail": "quote ready" if quote else "invalid postal code",
        }

    def compose_answer(self, state: AgentState) -> dict:
        grounding = grounding_from_state(state)
        answer, usage, rewritten = self.composer.compose(grounding, _history(state))
        return {
            "answer": answer,
            "usage": _merge_usage(state, usage),
            "guard_rewritten": rewritten,
            "handoff": False,
            "trace_tools": [],
            "trace_detail": "draft rewritten by guard" if rewritten else "draft accepted",
        }

    def handoff(self, state: AgentState) -> dict:
        reason = "user_request" if state.get("intent") == "human" else "low_confidence"
        protocol = protocol_for(state.get("session_id") or "session")
        grounding = grounding_from_state(state)
        grounding.handoff = True
        grounding.handoff_reason = reason
        grounding.protocol = protocol
        answer = self.templates.render(grounding)
        return {
            "answer": answer,
            "handoff": True,
            "handoff_reason": reason,
            "protocol": protocol,
            "trace_tools": [],
            "trace_detail": reason,
        }

    def decline(self, state: AgentState) -> dict:
        grounding = grounding_from_state(state)
        grounding.blocked = bool(state.get("blocked"))
        if not grounding.blocked:
            grounding.intent = "out_of_scope"
        answer = self.templates.render(grounding)
        return {
            "answer": answer,
            "handoff": False,
            "trace_tools": [],
            "trace_detail": "blocked" if grounding.blocked else "out of scope",
        }

    def guard_output(self, state: AgentState) -> dict:
        grounding = grounding_from_state(state)
        answer = state.get("answer") or ""
        rewritten = bool(state.get("guard_rewritten"))
        if not draft_is_grounded(
            answer,
            grounding.products,
            grounding.recommendations,
            grounding.order,
            grounding.shipping,
            grounding.policies,
        ):
            answer = self.templates.render(grounding)
            rewritten = True
        return {
            "answer": answer,
            "guard_rewritten": rewritten,
            "messages": [AIMessage(content=answer)],
            "trace_tools": [],
            "trace_detail": "rewritten" if rewritten else "passed",
        }

    @staticmethod
    def _trace(state: AgentState, tool: str, payload: dict) -> list[dict]:
        trace = list(state.get("tool_trace") or [])
        summary = ", ".join(f"{key}={value}" for key, value in payload.items())
        trace.append({"tool": tool, "summary": summary[:180]})
        return trace


def _shipping_source() -> dict:
    return Source(
        id="policy:shipping",
        title="Frete e prazos",
        snippet="Frete grátis a partir de R$ 299,00. A cotação usa a tabela vigente.",
        kind="shipping",
    ).model_dump()


def grounding_from_state(state: AgentState) -> Grounding:
    return Grounding(
        locale=state.get("locale") or "pt",
        intent=state.get("intent") or "out_of_scope",
        products=[ProductCard.model_validate(item) for item in state.get("offers") or []],
        recommendations=[
            ProductCard.model_validate(item) for item in state.get("recommendations") or []
        ],
        order=OrderView.model_validate(state["order"]) if state.get("order") else None,
        order_id=state.get("order_id"),
        order_found=state.get("order_found"),
        shipping=ShippingQuote.model_validate(state["shipping"]) if state.get("shipping") else None,
        policies=[PolicyView.model_validate(item) for item in state.get("policies") or []],
        missing=list(state.get("missing") or []),
        handoff=bool(state.get("handoff")),
        handoff_reason=state.get("handoff_reason"),
        protocol=state.get("protocol"),
        blocked=bool(state.get("blocked")),
        sources=[Source.model_validate(item) for item in state.get("sources") or []],
    )
