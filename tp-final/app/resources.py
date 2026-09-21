from flask import Blueprint, g, jsonify
from werkzeug.security import generate_password_hash
from .common import APIError, admin_required, delete, record, text, public_user
from .db import get_db

bp = Blueprint('resources', __name__, url_prefix='/api/recursos')


@bp.before_request
def protect():
    admin_required()


def last_admin(db, item):
    return item['es_admin'] and db.execute('SELECT COUNT(*) FROM recurso WHERE es_admin=1').fetchone()[0] <= 1


@bp.get('')
def index():
    return jsonify([public_user(row) for row in get_db().execute('SELECT * FROM recurso ORDER BY recurso_nombre')])


@bp.get('/<int:identifier>')
def detail(identifier):
    return jsonify(public_user(record('recurso', 'recurso_id', identifier)))


@bp.post('')
@bp.put('/<int:identifier>')
def edit(identifier=None):
    item = record('recurso', 'recurso_id', identifier) if identifier else None
    name = text('recurso_nombre')
    raw_admin = g.data.get('es_admin', False)
    if not isinstance(raw_admin, (bool, int)) or raw_admin not in (0, 1):
        raise ValueError('es_admin debe ser un booleano.')
    admin = int(raw_admin)
    password = text('password', optional=bool(item), strip=False)
    if (not item or password) and len(password) < 8:
        raise ValueError('La contraseña debe tener al menos 8 caracteres.')
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    if item:
        current = record('recurso', 'recurso_id', identifier)
        if not admin and last_admin(db, current):
            db.rollback()
            raise APIError('Debe quedar al menos un administrador.', 409, 'last_admin')
        db.execute('UPDATE recurso SET recurso_nombre=?,es_admin=? WHERE recurso_id=?', (name, admin, identifier))
        if password:
            db.execute('UPDATE recurso SET password=?,debe_cambiar_password=1 WHERE recurso_id=?',
                       (generate_password_hash(password), identifier))
    else:
        identifier = db.execute('INSERT INTO recurso (recurso_nombre,password,es_admin) VALUES (?,?,?)',
                                (name, generate_password_hash(password), admin)).lastrowid
    db.commit()
    return jsonify(public_user(record('recurso', 'recurso_id', identifier))), 200 if item else 201


@bp.delete('/<int:identifier>')
def remove(identifier):
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    item = record('recurso', 'recurso_id', identifier)
    if last_admin(db, item):
        db.rollback()
        raise APIError('No se puede eliminar al último administrador.', 409, 'last_admin')
    delete('recurso', 'recurso_id', identifier)
    return '', 204
