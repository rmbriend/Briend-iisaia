#!/bin/sh
# Starts an isolated API for the E2E run: recreates the `pulso_e2e` database on the dev Postgres
# (`podman compose up -d db`), seeds admin/Proyecto1 and serves on port 5001.
set -e
cd "$(dirname "$0")/../../backend"
SERVER=${E2E_SERVER_URL:-postgresql+psycopg://pulso:pulso@localhost:5432/pulso}
export DATABASE_URL="${SERVER%/*}/pulso_e2e"
export SECRET_KEY=e2e-only-secret-key-0123456789abcdef
uv run python - "$SERVER" <<'PY'
import sys
from sqlalchemy import create_engine, text
engine = create_engine(sys.argv[1], isolation_level='AUTOCOMMIT')
with engine.connect() as connection:
    connection.execute(text('DROP DATABASE IF EXISTS pulso_e2e WITH (FORCE)'))
    connection.execute(text('CREATE DATABASE pulso_e2e'))
PY
uv run python -m pulso.cli init-db
exec uv run uvicorn pulso.asgi:app --host 127.0.0.1 --port 5001
