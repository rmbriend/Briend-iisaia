from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .common import admin_required, dates, delete, number, record, reference, required, save
from .db import get_db

bp = Blueprint('projects', __name__, url_prefix='/proyectos')
STATUSES = ('pendiente', 'en curso', 'pausado', 'finalizado')


@bp.get('')
def index():
    status = request.args.get('estado', '')
    owner = request.args.get('responsable', '')
    rows = get_db().execute('''SELECT p.*, r.recurso_nombre, COALESCE(c.total,0) AS consumidas
        FROM proyecto p JOIN recurso r ON r.recurso_id=p.owner_id
        LEFT JOIN (SELECT proyecto_id,SUM(horas_consumidas) AS total FROM consumo GROUP BY proyecto_id) c
        ON c.proyecto_id=p.proyecto_id
        WHERE (?='' OR p.proyect_status=?) AND (?='' OR p.owner_id=?)
        ORDER BY p.proyecto_id DESC''', (status, status, owner, owner)).fetchall()
    return render_template('projects.html', projects=rows, statuses=STATUSES,
                           resources=get_db().execute('SELECT * FROM recurso ORDER BY recurso_nombre').fetchall())


@bp.get('/<int:identifier>')
def detail(identifier):
    project = record('proyecto', 'proyecto_id', identifier)
    rows = get_db().execute('''SELECT c.*,r.recurso_nombre,l.rol_descripcion FROM consumo c
        JOIN recurso r USING(recurso_id) JOIN rol l USING(rol_id)
        WHERE proyecto_id=? ORDER BY fecha_inicio DESC,consumo_id DESC''', (identifier,)).fetchall()
    by_resource, by_role = {}, {}
    for row in rows:
        by_resource[row['recurso_nombre']] = by_resource.get(row['recurso_nombre'], 0) + row['horas_consumidas']
        by_role[row['rol_descripcion']] = by_role.get(row['rol_descripcion'], 0) + row['horas_consumidas']
    return render_template('project_detail.html', project=project, consumptions=rows,
                           total=sum(row['horas_consumidas'] for row in rows),
                           owner=record('recurso', 'recurso_id', project['owner_id']),
                           by_resource=by_resource, by_role=by_role)


@bp.route('/nuevo', methods=['GET', 'POST'])
@bp.route('/<int:identifier>/editar', methods=['GET', 'POST'])
def edit(identifier=None):
    project = record('proyecto', 'proyecto_id', identifier) if identifier else None
    if not g.user['es_admin'] and (project is None or project['owner_id'] != g.user['recurso_id']):
        abort(403, 'Solo el responsable o un administrador puede editar este proyecto.')
    if request.method == 'POST':
        try:
            start, end = dates()
            owner = reference('owner_id', 'recurso', 'recurso_id') if g.user['es_admin'] else project['owner_id']
            status = required('proyect_status')
            if status not in STATUSES:
                raise ValueError('Seleccioná un estado válido.')
            values = (required('proyecto_nombre'), start, end, number('horas_requeridas'), owner,
                      status, number('porcentaje_avance', maximum=100, strict=False))
            if project:
                ok = save('''UPDATE proyecto SET proyecto_nombre=?,fecha_inicio=?,fecha_fin=?,horas_requeridas=?,
                    owner_id=?,proyect_status=?,porcentaje_avance=? WHERE proyecto_id=?''', values + (identifier,))
            else:
                ok = save('''INSERT INTO proyecto (proyecto_nombre,fecha_inicio,fecha_fin,horas_requeridas,
                    owner_id,proyect_status,porcentaje_avance) VALUES (?,?,?,?,?,?,?)''', values)
            if ok:
                flash('Proyecto guardado.', 'success')
                return redirect(url_for('projects.index'))
        except ValueError as error:
            flash(str(error), 'danger')
    return render_template('project_form.html', item=project, statuses=STATUSES,
                           resources=get_db().execute('SELECT * FROM recurso ORDER BY recurso_nombre').fetchall())


@bp.post('/<int:identifier>/eliminar')
def remove(identifier):
    admin_required()
    record('proyecto', 'proyecto_id', identifier)
    delete('proyecto', 'proyecto_id', identifier)
    return redirect(url_for('projects.index'))
