from flask import Blueprint, abort, g, jsonify
from .common import dates, delete, number, record, reference, text, save, rows_json
from .db import get_db

bp = Blueprint('consumptions', __name__, url_prefix='/api/consumos')


def authorize(item):
    if item and not g.user['es_admin'] and item['recurso_id'] != g.user['recurso_id']:
        abort(403, 'Solo podés modificar tus propios consumos.')


@bp.get('')
def index():
    return jsonify(rows_json(get_db().execute("""SELECT c.*,p.proyecto_nombre,r.recurso_nombre,l.rol_descripcion
        FROM consumo c JOIN proyecto p USING(proyecto_id) JOIN recurso r USING(recurso_id)
        JOIN rol l USING(rol_id) ORDER BY c.fecha_inicio DESC,c.consumo_id DESC""")))


@bp.get('/<int:identifier>')
def detail(identifier):
    return jsonify(dict(record('consumo', 'consumo_id', identifier)))


@bp.post('')
@bp.put('/<int:identifier>')
def edit(identifier=None):
    item = record('consumo', 'consumo_id', identifier) if identifier else None
    authorize(item)
    start, end = dates()
    resource = reference('recurso_id', 'recurso', 'recurso_id') if g.user['es_admin'] else g.user['recurso_id']
    values = (reference('proyecto_id', 'proyecto', 'proyecto_id'), resource, start, end,
              number('horas_consumidas'), text('tarea'), reference('rol_id', 'rol', 'rol_id'))
    if item:
        save("""UPDATE consumo SET proyecto_id=?,recurso_id=?,fecha_inicio=?,fecha_fin=?,
            horas_consumidas=?,tarea=?,rol_id=? WHERE consumo_id=?""", values + (identifier,))
    else:
        identifier = save("""INSERT INTO consumo (proyecto_id,recurso_id,fecha_inicio,fecha_fin,horas_consumidas,
            tarea,rol_id) VALUES (?,?,?,?,?,?,?)""", values)
    return jsonify(dict(record('consumo', 'consumo_id', identifier))), 200 if item else 201


@bp.delete('/<int:identifier>')
def remove(identifier):
    item = record('consumo', 'consumo_id', identifier)
    authorize(item)
    delete('consumo', 'consumo_id', identifier)
    return '', 204
