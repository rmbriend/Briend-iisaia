from flask import Blueprint, jsonify
from .common import admin_required, delete, record, text, save, rows_json
from .db import get_db

bp = Blueprint('roles', __name__, url_prefix='/api/roles')


@bp.before_request
def protect():
    admin_required()


@bp.get('')
def index():
    return jsonify(rows_json(get_db().execute('SELECT * FROM rol ORDER BY rol_descripcion')))


@bp.get('/<int:identifier>')
def detail(identifier):
    return jsonify(dict(record('rol', 'rol_id', identifier)))


@bp.post('')
@bp.put('/<int:identifier>')
def edit(identifier=None):
    item = record('rol', 'rol_id', identifier) if identifier else None
    name = text('rol_descripcion')
    if item:
        save('UPDATE rol SET rol_descripcion=? WHERE rol_id=?', (name, identifier))
    else:
        identifier = save('INSERT INTO rol (rol_descripcion) VALUES (?)', (name,))
    return jsonify(dict(record('rol', 'rol_id', identifier))), 200 if item else 201


@bp.delete('/<int:identifier>')
def remove(identifier):
    record('rol', 'rol_id', identifier)
    delete('rol', 'rol_id', identifier)
    return '', 204
