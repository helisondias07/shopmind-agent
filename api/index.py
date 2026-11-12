"""Vercel and uvicorn entrypoint. The exported name is `app`."""

from shopmind.api.app import create_app

app = create_app()
