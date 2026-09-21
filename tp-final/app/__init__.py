import os
import secrets
import sqlite3
from pathlib import Path

from flask import Flask, abort, g, jsonify, request, session
from werkzeug.exceptions import HTTPException

from .db import close_db, get_db, init_command
from .common import APIError


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True, static_folder=None)
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
        if request.endpoint is None:
            return  # Let Flask return JSON 404/405 through the error handler.
        if session.get('user_id'):
            g.user = get_db().execute('SELECT * FROM recurso WHERE recurso_id=?',
                                      (session['user_id'],)).fetchone()
            if g.user is None:
                session.clear()
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        if request.endpoint not in ('auth.login', 'auth.current_session'):
            if g.user is None:
                raise APIError('Iniciá sesión para continuar.', 401, 'unauthorized')
            if g.user['debe_cambiar_password'] and request.endpoint not in ('auth.password', 'auth.logout'):
                raise APIError('Debés cambiar tu contraseña inicial.', 403, 'password_change_required')
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            token = request.headers.get('X-CSRF-Token', '')
            if not secrets.compare_digest(token, session['csrf']):
                raise APIError('La sesión del formulario venció. Recargá la página.', 400, 'csrf_invalid')
            if not request.is_json:
                abort(415, 'Enviá un cuerpo JSON con Content-Type: application/json.')
            g.data = request.get_json()
            if not isinstance(g.data, dict):
                abort(400, 'El cuerpo JSON debe ser un objeto.')

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(APIError)
    def api_error(error):
        return jsonify(error={'code': error.code, 'message': str(error)}), error.status

    @app.errorhandler(ValueError)
    def validation_error(error):
        return jsonify(error={'code': 'validation_error', 'message': str(error)}), 400

    @app.errorhandler(sqlite3.IntegrityError)
    def integrity_error(error):
        get_db().rollback()
        return jsonify(error={'code': 'conflict', 'message':
            'No se puede completar: el nombre ya existe o el registro tiene referencias asociadas.'}), 409

    @app.errorhandler(HTTPException)
    def http_error(error):
        response = error.get_response()
        message = 'Error interno del servidor.' if error.code == 500 else error.description
        response.data = app.json.dumps({'error': {'code': f'http_{error.code}', 'message': message}})
        response.content_type = 'application/json'
        return response

    return app
