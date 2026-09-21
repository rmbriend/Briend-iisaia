import os
import secrets
from pathlib import Path

from flask import Flask, abort, g, redirect, render_template, request, session, url_for

from .db import close_db, get_db, init_command


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        DATABASE=str(Path(app.instance_path) / 'proyectos.sqlite'),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE') == '1',
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config['SECRET_KEY']:
        raise RuntimeError('Configurá la variable de entorno SECRET_KEY antes de iniciar Flask.')
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_command)

    from . import auth, projects, resources, roles, consumptions
    for module in (auth, projects, resources, roles, consumptions):
        app.register_blueprint(module.bp)

    @app.before_request
    def protect_request():
        g.user = None
        if session.get('user_id'):
            g.user = get_db().execute('SELECT * FROM recurso WHERE recurso_id=?',
                                      (session['user_id'],)).fetchone()
            if g.user is None:
                session.clear()
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        if request.method == 'POST':
            token = request.form.get('csrf_token', '')
            if not secrets.compare_digest(token, session['csrf']):
                abort(400, 'El formulario venció. Recargá la página e intentá nuevamente.')
        if request.endpoint in ('static', 'auth.login'):
            return
        if g.user is None:
            return redirect(url_for('auth.login'))
        if g.user['debe_cambiar_password'] and request.endpoint not in ('auth.password', 'auth.logout'):
            return redirect(url_for('auth.password'))

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        if request.endpoint != 'static':
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def error_page(error):
        return render_template('error.html', error=error), error.code

    @app.get('/')
    def index():
        return redirect(url_for('projects.index'))

    return app
