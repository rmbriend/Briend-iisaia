import sqlite3
import pytest
from werkzeug.security import check_password_hash
from app import create_app
from app.db import get_db, init_db
from conftest import consumption_data, login, post, project_data


def test_login_csrf_logout(client):
    assert client.get('/proyectos').status_code == 302
    assert client.post('/login', data={'recurso_nombre': 'admin', 'password': 'Proyecto1'}).status_code == 400
    assert 'incorrectos' in login(client, password='incorrecta').get_data(as_text=True)
    assert login(client).status_code == 302
    assert client.get('/proyectos').status_code == 200
    assert post(client, '/logout').status_code == 302
    assert client.get('/proyectos').status_code == 302


def test_initialization_and_mandatory_password(tmp_path):
    config = {'TESTING': True, 'SECRET_KEY': 'test', 'DATABASE': str(tmp_path / 'fresh.sqlite')}
    app = create_app(config)
    assert app.test_cli_runner().invoke(args=['init-db']).exit_code == 0
    client = app.test_client()
    assert login(client).location.endswith('/password')
    assert client.get('/roles').location.endswith('/password')
    assert post(client, '/roles/nuevo', {'rol_descripcion': 'No permitido'}).location.endswith('/password')
    for data in [dict(actual='wrong', password='Distinta123', confirmacion='Distinta123'),
                 dict(actual='Proyecto1', password='Proyecto1', confirmacion='Proyecto1'),
                 dict(actual='Proyecto1', password='short', confirmacion='short'),
                 dict(actual='Proyecto1', password='Distinta123', confirmacion='Otra123')]:
        assert post(client, '/password', data).status_code == 200
    assert post(client, '/password', dict(actual='Proyecto1', password='Distinta123', confirmacion='Distinta123')).status_code == 302
    with app.app_context():
        before = dict(get_db().execute('SELECT * FROM recurso').fetchone())
        assert before['password'] != 'Distinta123'
        assert check_password_hash(before['password'], 'Distinta123')
        init_db()
        assert dict(get_db().execute('SELECT * FROM recurso').fetchone()) == before
    restarted = create_app(config).test_client()
    assert login(restarted, password='Distinta123').location.endswith('/proyectos')


@pytest.mark.parametrize('path', ['/recursos', '/roles', '/recursos/nuevo', '/roles/nuevo', '/proyectos/nuevo', '/consumos/1/editar'])
def test_ordinary_user_permissions(client, path):
    login(client, 'bruno', 'Personal123')
    assert client.get(path).status_code == 403


@pytest.mark.parametrize('path', ['/recursos/2/eliminar', '/roles/1/eliminar', '/proyectos/1/eliminar', '/consumos/1/eliminar', '/proyectos/1/editar', '/consumos/1/editar', '/recursos/nuevo', '/roles/nuevo'])
def test_direct_post_permissions(client, path):
    login(client, 'bruno', 'Personal123')
    assert post(client, path, consumption_data()).status_code == 403


def test_owner_cannot_reassign_project(client, app):
    login(client, 'ana', 'Personal123')
    data = project_data()
    data.update(owner_id='3', porcentaje_avance='70')
    assert post(client, '/proyectos/1/editar', data).status_code == 302
    with app.app_context():
        project = get_db().execute('SELECT * FROM proyecto').fetchone()
        assert project['owner_id'] == 2 and project['porcentaje_avance'] == 70


def test_consumption_owner_totals_and_manual_progress(client, app):
    login(client, 'bruno', 'Personal123')
    assert post(client, '/consumos/nuevo', consumption_data()).status_code == 302
    with app.app_context():
        assert get_db().execute('SELECT recurso_id FROM consumo WHERE consumo_id=2').fetchone()[0] == 3
        assert get_db().execute('SELECT SUM(horas_consumidas) FROM consumo').fetchone()[0] == 15
        assert get_db().execute('SELECT porcentaje_avance FROM proyecto').fetchone()[0] == 25
    html = client.get('/proyectos/1').get_data(as_text=True)
    assert '150.0 %' in html and '25 %' in html and '-5 / 5' in html
    data = consumption_data()
    data['horas_consumidas'] = '5'
    assert post(client, '/consumos/2/editar', data).status_code == 302
    assert '80.0 %' in client.get('/proyectos/1').get_data(as_text=True)
    assert post(client, '/consumos/2/eliminar').status_code == 302
    assert '30.0 %' in client.get('/proyectos/1').get_data(as_text=True)


@pytest.mark.parametrize('name,value', [('horas_requeridas','0'), ('horas_requeridas','-1'), ('horas_requeridas','nan'),
    ('horas_requeridas','inf'), ('porcentaje_avance','-1'), ('porcentaje_avance','101'), ('porcentaje_avance','nan'),
    ('fecha_fin','2026-08-01'), ('fecha_inicio','2026-02-30'), ('owner_id','999'), ('proyecto_nombre','  '), ('proyect_status','inventado')])
def test_project_validation(client, app, name, value):
    login(client)
    data = project_data()
    data[name] = value
    assert post(client, '/proyectos/1/editar', data).status_code == 200
    with app.app_context():
        assert get_db().execute('SELECT proyecto_nombre FROM proyecto').fetchone()[0] == 'Proyecto ejemplo'


@pytest.mark.parametrize('value', ['0', '100'])
def test_valid_progress_boundaries(client, app, value):
    login(client)
    data = project_data()
    data['porcentaje_avance'] = value
    assert post(client, '/proyectos/1/editar', data).status_code == 302
    with app.app_context():
        assert get_db().execute('SELECT porcentaje_avance FROM proyecto').fetchone()[0] == float(value)


@pytest.mark.parametrize('name,value', [('horas_consumidas','0'), ('horas_consumidas','-2'), ('horas_consumidas','nan'),
    ('fecha_fin','2026-01-01'), ('fecha_inicio','bad'), ('proyecto_id','999'), ('recurso_id','999'), ('rol_id','999'), ('tarea',' ')])
def test_consumption_validation(client, app, name, value):
    login(client)
    data = consumption_data()
    data[name] = value
    assert post(client, '/consumos/nuevo', data).status_code == 200
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM consumo').fetchone()[0] == 1


@pytest.mark.parametrize('path,table', [('/proyectos/1/eliminar','proyecto'), ('/recursos/2/eliminar','recurso'), ('/roles/1/eliminar','rol')])
def test_referenced_deletion_blocked(client, app, path, table):
    login(client)
    assert 'asociados' in post(client, path, follow_redirects=True).get_data(as_text=True)
    with app.app_context():
        assert get_db().execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] > 0


def test_last_admin_and_duplicate_names(client, app):
    login(client)
    assert 'último administrador' in post(client, '/recursos/1/eliminar', follow_redirects=True).get_data(as_text=True)
    assert 'al menos un administrador' in post(client, '/recursos/1/editar', {'recurso_nombre':'admin'}).get_data(as_text=True)
    assert 'Ya existe' in post(client, '/recursos/nuevo', {'recurso_nombre':'ANA', 'password':'Personal123'}).get_data(as_text=True)
    assert 'ya existe' in post(client, '/roles/nuevo', {'rol_descripcion':'Analista'}).get_data(as_text=True)
    with app.app_context():
        assert get_db().execute('SELECT es_admin FROM recurso WHERE recurso_id=1').fetchone()[0] == 1


def test_admin_crud_and_reset(client, app):
    login(client)
    assert post(client, '/recursos/nuevo', {'recurso_nombre':'nuevo', 'password':'Inicial123'}).status_code == 302
    assert post(client, '/recursos/4/editar', {'recurso_nombre':'renombrado', 'password':'Reinicio123'}).status_code == 302
    with app.app_context():
        row = get_db().execute('SELECT * FROM recurso WHERE recurso_id=4').fetchone()
        assert check_password_hash(row['password'], 'Reinicio123') and row['debe_cambiar_password'] == 1
    assert post(client, '/roles/nuevo', {'rol_descripcion':'Diseñador'}).status_code == 302
    assert post(client, '/roles/2/editar', {'rol_descripcion':'Desarrollador'}).status_code == 302
    assert post(client, '/proyectos/nuevo', project_data()).status_code == 302
    assert post(client, '/proyectos/2/eliminar').status_code == 302
    assert post(client, '/roles/2/eliminar').status_code == 302
    assert post(client, '/recursos/4/eliminar').status_code == 302
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM proyecto').fetchone()[0] == 1
        assert get_db().execute('SELECT COUNT(*) FROM rol').fetchone()[0] == 1
        assert get_db().execute('SELECT COUNT(*) FROM recurso').fetchone()[0] == 3


def test_filters_read_views_and_methods(client):
    login(client)
    for path in ['/proyectos','/proyectos/1','/consumos','/roles','/recursos','/password',
                 '/proyectos/nuevo','/proyectos/1/editar','/consumos/nuevo','/consumos/1/editar',
                 '/roles/nuevo','/roles/1/editar','/recursos/nuevo','/recursos/1/editar']:
        assert client.get(path).status_code == 200, path
    assert 'Proyecto ejemplo' in client.get('/proyectos?estado=en+curso&responsable=2').get_data(as_text=True)
    assert 'No hay proyectos' in client.get('/proyectos?estado=finalizado').get_data(as_text=True)
    assert 'No hay proyectos' in client.get('/proyectos?responsable=3').get_data(as_text=True)
    assert client.get('/proyectos/999').status_code == 404
    assert client.get('/proyectos/1/eliminar').status_code == 405
    assert client.get('/logout').status_code == 405


def test_foreign_keys_and_escaping(app, client):
    with app.app_context():
        db = get_db()
        assert db.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('DELETE FROM rol WHERE rol_id=1')
        db.rollback()
    login(client)
    data = project_data()
    data['proyecto_nombre'] = '<script>alert(1)</script>'
    post(client, '/proyectos/1/editar', data)
    html = client.get('/proyectos').get_data(as_text=True)
    assert '<script>alert(1)</script>' not in html and '&lt;script&gt;' in html


def test_deleted_account_id_is_not_reused(client, app):
    login(client)
    post(client, '/recursos/nuevo', {'recurso_nombre': 'temporal', 'password': 'Inicial123'})
    post(client, '/recursos/4/eliminar')
    post(client, '/recursos/nuevo', {'recurso_nombre': 'distinto', 'password': 'Inicial123'})
    with app.app_context():
        row = get_db().execute("SELECT recurso_id FROM recurso WHERE recurso_nombre='distinto'").fetchone()
        assert row[0] > 4  # A deleted user's session cannot become another account.
