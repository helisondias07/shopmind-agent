"""Wire the database, the index, the tools, and the graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver

from shopmind.agent.classifier import FakeIntentClassifier, LlmIntentClassifier
from shopmind.agent.composer import LlmComposer, TemplateComposer
from shopmind.agent.guardrails import InputGuard
from shopmind.agent.runner import ShopMindAgent
from shopmind.agent.workflow import ShopMindWorkflow
from shopmind.api.ratelimit import RateLimiter
from shopmind.config import Settings
from shopmind.db.database import Database
from shopmind.db.seed import create_schema, seed
from shopmind.evals.runner import EvalRunner
from shopmind.observability import TraceLog
from shopmind.rag.embeddings import build_embeddings
from shopmind.rag.index import CatalogIndex, policy_document, product_document
from shopmind.rag.store import build_vector_store
from shopmind.services.catalog import CatalogService
from shopmind.services.inventory import InventoryService
from shopmind.services.orders import OrderService
from shopmind.services.shipping import ShippingService
from shopmind.tools.registry import SupportTools


@dataclass
class Container:
    settings: Settings
    database: Database
    catalog: CatalogService
    index: CatalogIndex
    tools: SupportTools
    agent: ShopMindAgent
    eval_agent: ShopMindAgent
    evals: EvalRunner
    limiter: RateLimiter
    weights: dict[str, int] = field(default_factory=dict)
    log: TraceLog = field(default_factory=TraceLog)


def build_container(settings: Settings) -> Container:
    settings.apply_tracing()
    _prepare_sqlite(settings.database_url)
    database = Database(settings.database_url)
    create_schema(database.engine)
    with database.session() as session:
        seed(session)

    catalog = CatalogService(database)
    cards, policies, descriptions, weights = catalog.snapshot()
    documents = []
    for card in cards:
        synonyms, description_pt, description_en = descriptions[card.sku]
        documents.append(product_document(card, description_pt, description_en, synonyms))
    documents.extend(policy_document(policy) for policy in policies)
    embeddings = build_embeddings(settings.resolved_embeddings, settings.openai_api_key)
    store = build_vector_store(documents, embeddings, settings.vector_store)
    index = CatalogIndex(
        store=store,
        products=cards,
        policies=policies,
        descriptions=descriptions,
        min_similarity=settings.min_similarity,
    )
    inventory = InventoryService(catalog)
    orders = OrderService(database)
    shipping = ShippingService()
    tools = SupportTools(index, inventory, orders, shipping)
    fake_classifier = FakeIntentClassifier(index)
    templates = TemplateComposer()
    classifier, composer = _language_models(settings, fake_classifier, templates, cards)
    workflow = ShopMindWorkflow(
        tools=tools,
        classifier=classifier,
        composer=composer,
        templates=templates,
        guards=InputGuard(),
        checkpointer=_checkpointer(settings),
        handoff_confidence=settings.handoff_confidence,
    )
    agent = ShopMindAgent(workflow, provider=settings.resolved_provider)
    eval_workflow = ShopMindWorkflow(
        tools=tools,
        classifier=fake_classifier,
        composer=templates,
        templates=templates,
        guards=InputGuard(),
        checkpointer=MemorySaver(),
        handoff_confidence=settings.handoff_confidence,
    )
    eval_agent = ShopMindAgent(eval_workflow, provider="fake")
    return Container(
        settings=settings,
        database=database,
        catalog=catalog,
        index=index,
        tools=tools,
        agent=agent,
        eval_agent=eval_agent,
        evals=EvalRunner(eval_agent),
        limiter=RateLimiter(settings.rate_limit_per_minute),
        weights=weights,
    )


def _language_models(settings, fallback, templates, cards):
    provider = settings.resolved_provider
    if provider == "fake":
        return fallback, templates
    llm = _build_chat_model(settings)
    if llm is None:
        return fallback, templates
    brief = "\n".join(f"{card.sku}: {card.name_pt} / {card.name_en}" for card in cards)
    return (
        LlmIntentClassifier(llm, fallback, brief),
        LlmComposer(llm, templates),
    )


def _build_chat_model(settings: Settings):
    provider = settings.resolved_provider
    if provider == "openai" and settings.openai_api_key:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            timeout=25,
            max_retries=1,
        )
    if provider == "anthropic" and settings.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0,
            timeout=25,
            max_retries=1,
        )
    return None


def _checkpointer(settings: Settings):
    if settings.checkpoint_backend == "memory":
        return MemorySaver()
    import sqlite3

    from langgraph.checkpoint.sqlite import SqliteSaver

    path = Path(settings.checkpoint_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    saver = SqliteSaver(connection)
    saver.setup()
    return saver


def _prepare_sqlite(url: str) -> None:
    if url in {"sqlite://", "sqlite:///:memory:"} or not url.startswith("sqlite:///"):
        return
    raw = url[len("sqlite:///") :]
    if raw in {"", ":memory:"}:
        return
    Path(raw).parent.mkdir(parents=True, exist_ok=True)
