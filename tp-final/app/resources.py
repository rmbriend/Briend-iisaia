from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from .common import admin_required, delete, record, required
from .db import get_db
import sqlite3

bp = Blueprint('resources', __name__, url_prefix='/recursos')


@bp.before_request
def protect():
    admin_required()


def last_admin(db, item):
    return item['es_admin'] and db.execute('SELECT COUNT(*) FROM recurso WHERE es_admin=1').fetchone()[0] <= 1


@bp.get('')
def index():
    return render_template('resources.html', resources=get_db().execute('SELECT * FROM recurso ORDER BY recurso_nombre').fetchall())


@bp.route('/nuevo', methods=['GET', 'POST'])
@bp.route('/<int:identifier>/editar', methods=['GET', 'POST'])
def edit(identifier=None):
    item = record('recurso', 'recurso_id', identifier) if identifier else None
    if request.method == 'POST':
        db = get_db()
        try:
            name = required('recurso_nombre')
            admin = int(request.form.get('es_admin') == '1')
            password = request.form.get('password', '')
            if (not item or password) and len(password) < 8:
                raise ValueError('La contraseña debe tener al menos 8 caracteres.')
            db.execute('BEGIN IMMEDIATE')
            if item:
                current = record('recurso', 'recurso_id', identifier)
                if not admin and last_admin(db, current):
                    raise ValueError('Debe quedar al menos un administrador.')
                db.execute('UPDATE recurso SET recurso_nombre=?,es_admin=? WHERE recurso_id=?', (name, admin, identifier))
                if password:
                    db.execute('UPDATE recurso SET password=?,debe_cambiar_password=1 WHERE recurso_id=?',
                               (generate_password_hash(password), identifier))
            else:
                db.execute('INSERT INTO recurso (recurso_nombre,password,es_admin) VALUES (?,?,?)',
                           (name, generate_password_hash(password), admin))
            db.commit()
            flash('Recurso guardado.', 'success')
            return redirect(url_for('resources.index'))
        except (ValueError, sqlite3.IntegrityError) as error:
            db.rollback()
            flash(str(error) if isinstance(error, ValueError) else 'Ya existe un usuario con ese nombre.', 'danger')
    return render_template('resource_form.html', item=item)


@bp.post('/<int:identifier>/eliminar')
def remove(identifier):
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    item = record('recurso', 'recurso_id', identifier)
    if last_admin(db, item):
        db.rollback()
        flash('No se puede eliminar al último administrador.', 'danger')
    else:
        delete('recurso', 'recurso_id', identifier)
    return redirect(url_for('resources.index'))
