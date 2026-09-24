from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from pulso.models import Base
from tests.conftest import alembic_config


def test_health(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['cache-control'] == 'no-store'


def test_unknown_route_uses_json_error_contract(client):
    response = client.get('/api/no-existe')
    assert response.status_code == 404
    assert response.json()['error']['code'] == 'http_404'


def test_migrations_match_models(migrated):
    engine = create_engine(migrated)
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    engine.dispose()
    assert diff == []


def test_migrations_downgrade_and_upgrade(migrated):
    config = alembic_config(migrated)
    command.downgrade(config, 'base')
    command.upgrade(config, 'head')


def test_names_are_unique_case_insensitive(app):
    with app.state.engine.connect() as connection:
        connection.execute(text("INSERT INTO rol (rol_descripcion) VALUES ('Desarrollo')"))
        try:
            connection.execute(text("INSERT INTO rol (rol_descripcion) VALUES ('DESARROLLO')"))
        except IntegrityError:
            return
        finally:
            connection.rollback()
    raise AssertionError('Se esperaba un conflicto de unicidad sin distinguir mayúsculas.')
