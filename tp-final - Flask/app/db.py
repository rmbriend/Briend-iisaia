import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'))
    # Seed only an empty installation; never recreate a renamed initial account.
    if db.execute('SELECT COUNT(*) FROM recurso').fetchone()[0] == 0:
        db.execute('INSERT INTO recurso (recurso_nombre,password,es_admin) VALUES (?,?,1)',
                   ('admin', generate_password_hash('Proyecto1')))
    db.commit()


@click.command('init-db')
@with_appcontext
def init_command():
    init_db()
    click.echo('Base inicializada. En instalaciones nuevas: admin / Proyecto1.')
