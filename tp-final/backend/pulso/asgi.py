"""ASGI entry point: `uvicorn pulso.asgi:app`."""

from .main import create_app

app = create_app()
