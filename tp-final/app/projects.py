from flask import Blueprint, abort, g, jsonify, request
from .common import admin_required, dates, delete, number, record, reference, text, save, rows_json
from .db import get_db

bp = Blueprint('projects', __name__, url_prefix='/api')
STATUSES = ('pendiente', 'en curso', 'pausado', 'finalizado')
PROJECT_QUERY = """SELECT p.*,r.recurso_nombre AS responsable,
    COALESCE(c.total,0) AS horas_consumidas
    FROM proyecto p JOIN recurso r ON r.recurso_id=p.owner_id
    LEFT JOIN (SELECT proyecto_id,SUM(horas_consumidas) AS total FROM consumo GROUP BY proyecto_id) c
    ON c.proyecto_id=p.proyecto_id"""


def project_json(row):
    data = dict(row)
    data['saldo'] = data['horas_requeridas'] - data['horas_consumidas']
    data['exceso'] = max(-data['saldo'], 0)
    data['porcentaje_consumo'] = data['horas_consumidas'] / data['horas_requeridas'] * 100
    return data


@bp.get('/catalogos')
def catalogs():
    db = get_db()
    return jsonify(estados=STATUSES,
        recursos=rows_json(db.execute('SELECT recurso_id,recurso_nombre FROM recurso ORDER BY recurso_nombre')),
        roles=rows_json(db.execute('SELECT * FROM rol ORDER BY rol_descripcion')))


@bp.get('/proyectos')
def index():
    status, owner = request.args.get('estado', ''), request.args.get('responsable', '')
    rows = get_db().execute(PROJECT_QUERY + """ WHERE (?='' OR p.proyect_status=?)
        AND (?='' OR p.owner_id=?) ORDER BY p.proyecto_id DESC""", (status, status, owner, owner))
    return jsonify([project_json(row) for row in rows])


@bp.get('/proyectos/<int:identifier>')
def detail(identifier):
    record('proyecto', 'proyecto_id', identifier)
    db = get_db()
    project = project_json(db.execute(PROJECT_QUERY + ' WHERE p.proyecto_id=?', (identifier,)).fetchone())
    rows = rows_json(db.execute("""SELECT c.*,r.recurso_nombre,l.rol_descripcion FROM consumo c
        JOIN recurso r USING(recurso_id) JOIN rol l USING(rol_id)
        WHERE proyecto_id=? ORDER BY fecha_inicio DESC,consumo_id DESC""", (identifier,)))
    by_resource, by_role = {}, {}
    for row in rows:
        name, role = row['recurso_nombre'], row['rol_descripcion']
        by_resource[name] = by_resource.get(name, 0) + row['horas_consumidas']
        by_role[role] = by_role.get(role, 0) + row['horas_consumidas']
    return jsonify(proyecto=project, consumos=rows, por_recurso=by_resource, por_rol=by_role)


@bp.post('/proyectos')
@bp.put('/proyectos/<int:identifier>')
def edit(identifier=None):
    project = record('proyecto', 'proyecto_id', identifier) if identifier else None
    if not g.user['es_admin'] and (project is None or project['owner_id'] != g.user['recurso_id']):
        abort(403, 'Solo el responsable o un administrador puede editar este proyecto.')
    start, end = dates()
    owner = reference('owner_id', 'recurso', 'recurso_id') if g.user['es_admin'] else project['owner_id']
    status = text('proyect_status')
    if status not in STATUSES:
        raise ValueError('Seleccioná un estado válido.')
    values = (text('proyecto_nombre'), start, end, number('horas_requeridas'), owner,
              status, number('porcentaje_avance', maximum=100, strict=False))
    if project:
        save("""UPDATE proyecto SET proyecto_nombre=?,fecha_inicio=?,fecha_fin=?,horas_requeridas=?,
            owner_id=?,proyect_status=?,porcentaje_avance=? WHERE proyecto_id=?""", values + (identifier,))
    else:
        identifier = save("""INSERT INTO proyecto (proyecto_nombre,fecha_inicio,fecha_fin,horas_requeridas,
            owner_id,proyect_status,porcentaje_avance) VALUES (?,?,?,?,?,?,?)""", values)
    return jsonify(dict(record('proyecto', 'proyecto_id', identifier))), 200 if project else 201


@bp.delete('/proyectos/<int:identifier>')
def remove(identifier):
    admin_required()
    record('proyecto', 'proyecto_id', identifier)
    delete('proyecto', 'proyecto_id', identifier)
    return '', 204
