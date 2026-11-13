"""FastAPI routes for the storefront and the agent."""

from __future__ import annotations

import asyncio
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from shopmind import __version__
from shopmind.container import Container
from shopmind.schemas import ChatRequest, ChatResponse, HealthResponse, PublicProduct


def build_router() -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/health", response_model=HealthResponse)
    def health(request: Request) -> HealthResponse:
        settings = _container(request).settings
        return HealthResponse(
            version=__version__,
            provider=settings.resolved_provider,
            model=settings.model_name,
            embeddings=settings.resolved_embeddings,
            vector_store=settings.vector_store,
            handoff_confidence=settings.handoff_confidence,
        )

    @router.get("/products")
    def products(request: Request, locale: Literal["pt", "en"] = "pt") -> dict:
        container = _container(request)
        cards = container.catalog.product_cards()
        payload = [
            PublicProduct(
                sku=card.sku,
                name=card.name(locale),
                price_cents=card.price_cents,
                stock=card.stock,
                category=card.category,
                image_key=card.image_key,
                blurb=card.blurb(locale),
                weight_grams=container.weights.get(card.sku, 0),
            )
            for card in cards
        ]
        return {"locale": locale, "products": [item.model_dump() for item in payload]}

    @router.post("/chat", response_model=ChatResponse)
    def chat(body: ChatRequest, request: Request) -> ChatResponse:
        container = _guard_rate(request)
        response = container.agent.chat(body)
        _log_turn(container, body, response)
        return response

    @router.post("/chat/stream")
    async def chat_stream(body: ChatRequest, request: Request) -> StreamingResponse:
        container = _guard_rate(request)
        pace = container.settings.stream_pace_ms / 1000

        async def events():
            done = None
            for event in container.agent.iter_events(body):
                if event.kind == "node" and event.node is not None:
                    yield _sse("node", event.node.model_dump_json())
                    if pace:
                        await asyncio.sleep(pace)
                elif event.response is not None:
                    done = event.response
            if done is None:
                return
            words = done.reply.split(" ")
            step = 3
            for index in range(0, len(words), step):
                chunk = " ".join(words[index : index + step])
                prefix = "" if index == 0 else " "
                yield _sse("token", json_text({"text": prefix + chunk}))
                if pace:
                    await asyncio.sleep(pace / 2)
            _log_turn(container, body, done)
            yield _sse("done", done.model_dump_json())

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @router.get("/evals")
    def evals(request: Request) -> dict:
        report = _container(request).evals.run()
        return report.model_dump()

    return router


def _container(request: Request) -> Container:
    return request.app.state.container


def _guard_rate(request: Request) -> Container:
    container = _container(request)
    allowed, remaining = container.limiter.check(_client_ip(request))
    if not allowed:
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    request.state.rate_remaining = remaining
    return container


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client is None:
        return "unknown"
    return request.client.host


def _log_turn(container: Container, body: ChatRequest, response: ChatResponse) -> None:
    container.log.emit(
        "chat.completed",
        session_id=body.session_id,
        intent=response.intent,
        handoff=response.handoff,
        blocked=response.blocked,
        provider=response.provider,
        latency_ms=response.latency_ms,
        nodes=[node.name for node in response.nodes],
        tools=[tool.tool for tool in response.tools],
        message_chars=len(body.message),
    )


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


def json_text(payload: dict) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False)
