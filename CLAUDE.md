# CLAUDE.md

Leia [AGENTS.md](AGENTS.md) antes de editar este repositório.

```bash
make lint
make test
make api
```

A demo sobe com `cd web && npm run dev` e fala com a API em `http://127.0.0.1:8000`. Sem chave de modelo, `LLM_PROVIDER=fake` é o caminho correto. Não chame um provedor pago nos testes.
