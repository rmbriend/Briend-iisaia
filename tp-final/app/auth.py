import secrets

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint('auth', __name__)
DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(24))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = get_db().execute('SELECT * FROM recurso WHERE recurso_nombre=?',
                                (request.form.get('recurso_nombre', '').strip(),)).fetchone()
        valid = check_password_hash(user['password'] if user else DUMMY_HASH,
                                    request.form.get('password', ''))
        if user and valid:
            session.clear()
            session['user_id'] = user['recurso_id']
            session['csrf'] = secrets.token_urlsafe(32)
            return redirect(url_for('auth.password' if user['debe_cambiar_password'] else 'projects.index'))
        flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')


@bp.post('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@bp.route('/password', methods=['GET', 'POST'])
def password():
    if request.method == 'POST':
        new = request.form.get('password', '')
        if not check_password_hash(g.user['password'], request.form.get('actual', '')):
            flash('La contraseña actual es incorrecta.', 'danger')
        elif len(new) < 8 or new != request.form.get('confirmacion'):
            flash('La nueva contraseña debe tener al menos 8 caracteres y coincidir con la confirmación.', 'danger')
        elif check_password_hash(g.user['password'], new):
            flash('Elegí una contraseña diferente de la actual.', 'danger')
        else:
            db = get_db()
            db.execute('UPDATE recurso SET password=?, debe_cambiar_password=0 WHERE recurso_id=?',
                       (generate_password_hash(new), g.user['recurso_id']))
            db.commit()
            session['csrf'] = secrets.token_urlsafe(32)
            flash('Contraseña actualizada.', 'success')
            return redirect(url_for('projects.index'))
    return render_template('password.html')
