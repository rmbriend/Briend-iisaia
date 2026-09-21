from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .common import dates, delete, number, record, reference, required, save
from .db import get_db

bp = Blueprint('consumptions', __name__, url_prefix='/consumos')


def authorize(item):
    if item and not g.user['es_admin'] and item['recurso_id'] != g.user['recurso_id']:
        abort(403, 'Solo podés modificar tus propios consumos.')


@bp.get('')
def index():
    rows = get_db().execute('''SELECT c.*,p.proyecto_nombre,r.recurso_nombre,l.rol_descripcion
        FROM consumo c JOIN proyecto p USING(proyecto_id) JOIN recurso r USING(recurso_id)
        JOIN rol l USING(rol_id) ORDER BY c.fecha_inicio DESC,c.consumo_id DESC''').fetchall()
    return render_template('consumptions.html', consumptions=rows)


@bp.route('/nuevo', methods=['GET', 'POST'])
@bp.route('/<int:identifier>/editar', methods=['GET', 'POST'])
def edit(identifier=None):
    item = record('consumo', 'consumo_id', identifier) if identifier else None
    authorize(item)
    if request.method == 'POST':
        try:
            start, end = dates()
            resource = reference('recurso_id', 'recurso', 'recurso_id') if g.user['es_admin'] else g.user['recurso_id']
            values = (reference('proyecto_id', 'proyecto', 'proyecto_id'), resource, start, end,
                      number('horas_consumidas'), required('tarea'), reference('rol_id', 'rol', 'rol_id'))
            if item:
                ok = save('''UPDATE consumo SET proyecto_id=?,recurso_id=?,fecha_inicio=?,fecha_fin=?,
                    horas_consumidas=?,tarea=?,rol_id=? WHERE consumo_id=?''', values + (identifier,))
            else:
                ok = save('''INSERT INTO consumo (proyecto_id,recurso_id,fecha_inicio,fecha_fin,horas_consumidas,
                    tarea,rol_id) VALUES (?,?,?,?,?,?,?)''', values)
            if ok:
                flash('Consumo guardado.', 'success')
                return redirect(url_for('projects.detail', identifier=values[0]))
        except ValueError as error:
            flash(str(error), 'danger')
    db = get_db()
    return render_template('consumption_form.html', item=item,
                           projects=db.execute('SELECT * FROM proyecto ORDER BY proyecto_nombre').fetchall(),
                           resources=db.execute('SELECT * FROM recurso ORDER BY recurso_nombre').fetchall(),
                           roles=db.execute('SELECT * FROM rol ORDER BY rol_descripcion').fetchall())


@bp.post('/<int:identifier>/eliminar')
def remove(identifier):
    item = record('consumo', 'consumo_id', identifier)
    authorize(item)
    delete('consumo', 'consumo_id', identifier)
    return redirect(url_for('projects.detail', identifier=item['proyecto_id']))
