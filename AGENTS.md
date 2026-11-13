# AGENTS.md

Governança para agentes de código (Cursor, Claude Code e outros) neste repositório.

## O que é este projeto

ShopMind é o atendimento da loja fictícia Lume & Co. Um grafo LangGraph responde sobre catálogo, pedidos, frete e políticas. A demo em `web/` consome a API FastAPI em `api/`.

Os dados de clientes, pedidos e produtos são inventados. Não coloque dados pessoais reais em lugar nenhum.

## Regras

- Segredos só por ambiente (`.env`, painel da Vercel, secrets do CI). Nunca no código, em testes ou em commits.
- `pytest` e o CI rodam com `LLM_PROVIDER=fake`. Não escreva um teste que chame OpenAI ou Anthropic.
- Preço, estoque, status de pedido e prazo de frete saem dos serviços e do SQLite. O índice vetorial não é fonte de número.
- Se mudar os nós do grafo, atualize o diagrama no README e cubra o comportamento com um caso em `api/shopmind/evals/cases.json`.
- Mantenha `ruff check` e `ruff format` limpos.
- A página e a API falam `/api/...`. Não crie uma segunda superfície de chat.

## Comandos

```bash
make lint
make test
make api
cd web && npm run dev
cd web && npm run test:e2e
```

## Mapa

- `api/shopmind/agent/workflow.py` — grafo, roteamento, checkpointer
- `api/shopmind/tools/registry.py` — tools LangChain
- `api/shopmind/services/` — SQLite via SQLAlchemy
- `api/shopmind/rag/` — embeddings e vector store
- `api/shopmind/api/app.py` — FastAPI
- `web/` — Next.js, a demo

## English

ShopMind is the support agent for the fictional shop Lume & Co. Tests and CI use `LLM_PROVIDER=fake`. Do not commit secrets or real personal data. Prices and stock come from SQLite, not from the vector index. If the graph changes, update the README diagram and the eval cases.
