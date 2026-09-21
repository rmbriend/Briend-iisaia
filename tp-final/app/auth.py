import secrets
from flask import Blueprint, g, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash
from .common import APIError, public_user, text
from .db import get_db

bp = Blueprint('auth', __name__, url_prefix='/api')
DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(24))


def session_payload():
    return jsonify(user=public_user(g.user) if g.user else None, csrf_token=session['csrf'])


@bp.get('/session')
def current_session():
    return session_payload()


@bp.post('/login')
def login():
    name = text('recurso_nombre')
    password = text('password', strip=False)
    user = get_db().execute('SELECT * FROM recurso WHERE recurso_nombre=?', (name,)).fetchone()
    valid = check_password_hash(user['password'] if user else DUMMY_HASH, password)
    if not user or not valid:
        raise APIError('Usuario o contraseña incorrectos.', 401, 'invalid_credentials')
    session.clear()
    session['user_id'] = user['recurso_id']
    session['csrf'] = secrets.token_urlsafe(32)
    g.user = user
    return session_payload()


@bp.post('/logout')
def logout():
    session.clear()
    session['csrf'] = secrets.token_urlsafe(32)
    g.user = None
    return session_payload()


@bp.put('/password')
def password():
    actual = text('actual', strip=False)
    new = text('password', strip=False)
    confirmation = text('confirmacion', strip=False)
    if not check_password_hash(g.user['password'], actual):
        raise ValueError('La contraseña actual es incorrecta.')
    if len(new) < 8 or new != confirmation:
        raise ValueError('La nueva contraseña debe tener al menos 8 caracteres y coincidir con la confirmación.')
    if check_password_hash(g.user['password'], new):
        raise ValueError('Elegí una contraseña diferente de la actual.')
    db = get_db()
    db.execute('UPDATE recurso SET password=?,debe_cambiar_password=0 WHERE recurso_id=?',
               (generate_password_hash(new), g.user['recurso_id']))
    db.commit()
    session['csrf'] = secrets.token_urlsafe(32)
    g.user = db.execute('SELECT * FROM recurso WHERE recurso_id=?', (g.user['recurso_id'],)).fetchone()
    return session_payload()
