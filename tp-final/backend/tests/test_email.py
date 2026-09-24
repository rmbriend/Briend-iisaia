import pytest
from pydantic import ValidationError

from pulso.config import Settings
from pulso.schemas import RecursoIn
from tests.conftest import login, mutate, post


def test_settings_without_secret(monkeypatch):
    monkeypatch.delenv('SECRET_KEY', raising=False)
    assert Settings(_env_file=None)
    assert 'secret_key' not in Settings.model_fields


@pytest.mark.parametrize('email', ['ana@example.com', 'a@b.co', 'ana.perez+proyecto@equipo.example.com'])
def test_email_valid(email):
    assert RecursoIn(recurso_nombre='ana', email=email).email == email


@pytest.mark.parametrize(
    'email',
    [
        'ana',
        'ana@example',
        '@example.com',
        'ana@',
        'a b@x.com',
        'a@@x.com',
        'a@x..com',
        'a@.com',
        'a@-x.com',
        'a..b@x.com',
        123,
    ],
)
def test_email_invalid(email):
    with pytest.raises(ValidationError):
        RecursoIn(recurso_nombre='ana', email=email)


def test_email_optional_and_trimmed():
    assert RecursoIn(recurso_nombre='ana').email is None
    assert RecursoIn(recurso_nombre='ana', email='  ').email is None
    assert RecursoIn(recurso_nombre='ana', email=' ana@example.com ').email == 'ana@example.com'


def test_email_roundtrip(client):
    login(client)
    payload = {'recurso_nombre': 'mail-user', 'password': 'Inicial123', 'email': 'ana@example.com'}
    result = post(client, '/api/recursos', payload)
    assert result.status_code == 201
    identifier = result.json()['recurso_id']
    assert result.json()['email'] == payload['email']
    path = f'/api/recursos/{identifier}'
    payload['email'] = 'ana@equipo.com'
    assert mutate(client, 'PUT', path, payload).status_code == 200
    assert client.get(path).json()['email'] == payload['email']
    payload['email'] = 'invalido'
    response = mutate(client, 'PUT', path, payload)
    assert response.status_code == 400
    assert 'email' in response.json()['error']['message']
    assert client.get(path).json()['email'] == 'ana@equipo.com'
    payload['email'] = ''
    assert mutate(client, 'PUT', path, payload).json()['email'] is None
