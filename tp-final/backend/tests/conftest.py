"""Each test session runs against a throwaway Postgres database migrated with Alembic.

Requires a reachable Postgres (dev: `podman compose up -d db` from tp-final/). Override the
server with TEST_DATABASE_URL (a URL whose user can CREATE/DROP DATABASE).
"""

import os
import uuid

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from pulso.config import Settings
from pulso.main import create_app

SERVER_URL = os.environ.get('TEST_DATABASE_URL', 'postgresql+psycopg://pulso:pulso@localhost:5432/pulso')
ALEMBIC_INI = os.path.join(os.path.dirname(__file__), '..', 'alembic.ini')


def alembic_config(url: str) -> Config:
    config = Config(ALEMBIC_INI)
    config.attributes['database_url'] = url
    config.attributes['configure_logger'] = False
    return config


@pytest.fixture(scope='session')
def database_url():
    name = f'pulso_test_{uuid.uuid4().hex[:8]}'
    admin = create_engine(SERVER_URL, isolation_level='AUTOCOMMIT')
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE {name}'))
    url = make_url(SERVER_URL).set(database=name).render_as_string(hide_password=False)
    try:
        yield url
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS {name} WITH (FORCE)'))
        admin.dispose()


@pytest.fixture(scope='session')
def migrated(database_url):
    command.upgrade(alembic_config(database_url), 'head')
    return database_url


@pytest.fixture
def app(migrated):
    app = create_app(Settings(secret_key='x' * 32, database_url=migrated))
    yield app
    with app.state.engine.begin() as connection:
        tables = ', '.join(['consumo', 'proyecto', 'rol', 'sesion', 'recurso'])
        connection.execute(text(f'TRUNCATE {tables} RESTART IDENTITY CASCADE'))
    app.state.engine.dispose()


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client
