FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LLM_PROVIDER=fake

WORKDIR /app

RUN adduser --disabled-password --gecos "" shopmind

COPY api/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY api /app
RUN mkdir -p /app/data && chown -R shopmind:shopmind /app

USER shopmind
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"

CMD ["uvicorn", "index:app", "--host", "0.0.0.0", "--port", "8000"]
