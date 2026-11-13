PYTHONPATH := api
export PYTHONPATH

.PHONY: lint test demo api

lint:
	ruff check api tests
	ruff format --check api tests

test:
	pytest

demo:
	LLM_PROVIDER=fake CHECKPOINT_BACKEND=memory DATABASE_URL=sqlite:// python -m shopmind demo --markdown

api:
	LLM_PROVIDER=fake uvicorn index:app --app-dir api --reload --port 8000
