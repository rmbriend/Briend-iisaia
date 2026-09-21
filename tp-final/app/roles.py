from flask import Blueprint, flash, redirect, render_template, request, url_for

from .common import admin_required, delete, record, required, save
from .db import get_db

bp = Blueprint('roles', __name__, url_prefix='/roles')


@bp.before_request
def protect():
    admin_required()


@bp.get('')
def index():
    return render_template('roles.html', roles=get_db().execute('SELECT * FROM rol ORDER BY rol_descripcion').fetchall())


@bp.route('/nuevo', methods=['GET', 'POST'])
@bp.route('/<int:identifier>/editar', methods=['GET', 'POST'])
def edit(identifier=None):
    item = record('rol', 'rol_id', identifier) if identifier else None
    if request.method == 'POST':
        try:
            name = required('rol_descripcion')
            ok = save('UPDATE rol SET rol_descripcion=? WHERE rol_id=?', (name, identifier)) if item else save(
                'INSERT INTO rol (rol_descripcion) VALUES (?)', (name,))
            if ok:
                flash('Rol guardado.', 'success')
                return redirect(url_for('roles.index'))
        except ValueError as error:
            flash(str(error), 'danger')
    return render_template('role_form.html', item=item)


@bp.post('/<int:identifier>/eliminar')
def remove(identifier):
    record('rol', 'rol_id', identifier)
    delete('rol', 'rol_id', identifier)
    return redirect(url_for('roles.index'))
