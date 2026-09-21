import sqlite3
import pytest
from werkzeug.security import check_password_hash
from app import create_app
from app.db import get_db, init_db
from conftest import consumption_data, login, mutate, post, project_data


def test_login_csrf_logout(client):
    assert client.get('/api/proyectos').status_code == 401
    session = client.get('/api/session').json
    assert session['user'] is None and session['csrf_token']
    assert client.post('/api/login', json={'recurso_nombre':'admin','password':'Proyecto1'}).status_code == 400
    assert login(client, password='incorrecta').status_code == 401
    result = login(client)
    assert result.status_code == 200 and result.json['user']['es_admin'] == 1
    assert result.json['csrf_token'] != session['csrf_token']
    assert client.get('/api/proyectos').status_code == 200
    assert post(client, '/api/logout').json['user'] is None
    assert client.get('/api/proyectos').status_code == 401


def test_initialization_password_and_existing_database(tmp_path):
    config = {'TESTING':True,'SECRET_KEY':'test','DATABASE':str(tmp_path/'existing.sqlite')}
    app = create_app(config)
    assert app.test_cli_runner().invoke(args=['init-db']).exit_code == 0
    client = app.test_client()
    assert login(client).json['user']['debe_cambiar_password'] == 1
    blocked = client.get('/api/roles')
    assert blocked.status_code == 403 and blocked.json['error']['code'] == 'password_change_required'
    assert post(client, '/api/roles', {'rol_descripcion':'No permitido'}).status_code == 403
    for data in [dict(actual='wrong',password='Distinta123',confirmacion='Distinta123'),
                 dict(actual='Proyecto1',password='Proyecto1',confirmacion='Proyecto1'),
                 dict(actual='Proyecto1',password='short',confirmacion='short'),
                 dict(actual='Proyecto1',password='Distinta123',confirmacion='Otra123')]:
        assert mutate(client,'PUT','/api/password',data).status_code == 400
    result = mutate(client,'PUT','/api/password',dict(actual='Proyecto1',password='Distinta123',confirmacion='Distinta123'))
    assert result.status_code == 200 and result.json['user']['debe_cambiar_password'] == 0
    with app.app_context():
        before = dict(get_db().execute('SELECT * FROM recurso').fetchone())
        assert check_password_hash(before['password'],'Distinta123')
        init_db()
        assert dict(get_db().execute('SELECT * FROM recurso').fetchone()) == before
    restarted = create_app(config).test_client()
    assert login(restarted,password='Distinta123').status_code == 200


@pytest.mark.parametrize('path',['/api/recursos','/api/roles','/api/recursos/1','/api/roles/1'])
def test_admin_read_permissions(client,path):
    login(client,'bruno','Personal123')
    assert client.get(path).status_code == 403
    # Non-sensitive catalogs remain available to register hours and filter projects.
    assert client.get('/api/catalogos').status_code == 200


@pytest.mark.parametrize('method,path',[
    ('POST','/api/proyectos'),('POST','/api/recursos'),('POST','/api/roles'),
    ('PUT','/api/proyectos/1'),('PUT','/api/consumos/1'),('PUT','/api/recursos/2'),('PUT','/api/roles/1'),
    ('DELETE','/api/proyectos/1'),('DELETE','/api/consumos/1'),('DELETE','/api/recursos/2'),('DELETE','/api/roles/1')])
def test_direct_mutation_permissions(client,method,path):
    login(client,'bruno','Personal123')
    assert mutate(client,method,path,consumption_data()).status_code == 403


def test_owner_cannot_reassign_project(client,app):
    login(client,'ana','Personal123')
    data=project_data()
    data.update(owner_id=3,porcentaje_avance=70)
    assert mutate(client,'PUT','/api/proyectos/1',data).status_code == 200
    with app.app_context():
        p=get_db().execute('SELECT * FROM proyecto').fetchone()
        assert p['owner_id']==2 and p['porcentaje_avance']==70


def test_consumption_owner_totals_and_manual_progress(client,app):
    login(client,'bruno','Personal123')
    result=post(client,'/api/consumos',consumption_data())
    assert result.status_code==201 and result.json['recurso_id']==3
    detail=client.get('/api/proyectos/1').json
    p=detail['proyecto']
    assert p['horas_consumidas']==15 and p['porcentaje_consumo']==150
    assert p['saldo']==-5 and p['exceso']==5 and p['porcentaje_avance']==25
    assert detail['por_recurso']=={'ana':3,'bruno':12} and detail['por_rol']=={'Analista':15}
    data=consumption_data()
    data['horas_consumidas']=5
    assert mutate(client,'PUT','/api/consumos/2',data).status_code==200
    assert client.get('/api/proyectos/1').json['proyecto']['horas_consumidas']==8
    assert mutate(client,'DELETE','/api/consumos/2').status_code==204
    assert client.get('/api/proyectos/1').json['proyecto']['horas_consumidas']==3
    assert client.get('/api/proyectos/1').json['proyecto']['porcentaje_avance']==25


@pytest.mark.parametrize('name,value',[
    ('horas_requeridas',0),('horas_requeridas',-1),('horas_requeridas','nan'),('horas_requeridas','inf'),
    ('horas_requeridas',True),('horas_requeridas',[]),('porcentaje_avance',-1),('porcentaje_avance',101),
    ('porcentaje_avance','nan'),('fecha_fin','2026-08-01'),('fecha_inicio','2026-02-30'),
    ('owner_id',999),('owner_id',2.5),('owner_id',True),('proyecto_nombre','  '),
    ('proyecto_nombre',None),('proyecto_nombre',{}),('proyect_status','inventado')])
def test_project_validation(client,app,name,value):
    login(client)
    data=project_data()
    data[name]=value
    response=mutate(client,'PUT','/api/proyectos/1',data)
    assert response.status_code==400 and response.is_json
    with app.app_context():
        assert get_db().execute('SELECT proyecto_nombre FROM proyecto').fetchone()[0]=='Proyecto ejemplo'


@pytest.mark.parametrize('value',[0,100])
def test_progress_boundaries(client,value):
    login(client)
    data=project_data()
    data['porcentaje_avance']=value
    response=mutate(client,'PUT','/api/proyectos/1',data)
    assert response.status_code==200 and response.json['porcentaje_avance']==value


@pytest.mark.parametrize('name,value',[
    ('horas_consumidas',0),('horas_consumidas',-2),('horas_consumidas','nan'),
    ('fecha_fin','2026-01-01'),('fecha_inicio','bad'),('proyecto_id',999),
    ('recurso_id',999),('rol_id',999),('tarea',' '),('tarea',[])])
def test_consumption_validation(client,app,name,value):
    login(client)
    data=consumption_data()
    data[name]=value
    assert post(client,'/api/consumos',data).status_code==400
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM consumo').fetchone()[0]==1


@pytest.mark.parametrize('path', ['/api/proyectos/1','/api/recursos/2','/api/roles/1'])
def test_referenced_deletion_blocked(client,path):
    login(client)
    response=mutate(client,'DELETE',path)
    assert response.status_code==409 and response.json['error']['code']=='conflict'
    assert client.get(path).status_code==200


def test_last_admin_duplicates_and_boolean_validation(client):
    login(client)
    assert mutate(client,'DELETE','/api/recursos/1').json['error']['code']=='last_admin'
    assert mutate(client,'PUT','/api/recursos/1',{'recurso_nombre':'admin','es_admin':False}).status_code==409
    assert post(client,'/api/recursos',{'recurso_nombre':'ANA','password':'Personal123'}).status_code==409
    assert post(client,'/api/roles',{'rol_descripcion':'Analista'}).status_code==409
    assert mutate(client,'PUT','/api/recursos/2',{'recurso_nombre':'ana','es_admin':'false'}).status_code==400
    assert client.get('/api/recursos/1').json['es_admin']==1


def test_admin_crud_and_reset(client,app):
    login(client)
    assert post(client,'/api/recursos',{'recurso_nombre':'nuevo','password':'Inicial123'}).status_code==201
    result=mutate(client,'PUT','/api/recursos/4',{'recurso_nombre':'renombrado','password':'Reinicio123'})
    assert result.status_code==200 and result.json['debe_cambiar_password']==1
    with app.app_context():
        row=get_db().execute('SELECT * FROM recurso WHERE recurso_id=4').fetchone()
        assert check_password_hash(row['password'],'Reinicio123')
    assert post(client,'/api/roles',{'rol_descripcion':'Diseñador'}).status_code==201
    assert mutate(client,'PUT','/api/roles/2',{'rol_descripcion':'Desarrollador'}).status_code==200
    assert post(client,'/api/proyectos',project_data()).status_code==201
    assert mutate(client,'DELETE','/api/proyectos/2').status_code==204
    assert mutate(client,'DELETE','/api/roles/2').status_code==204
    assert mutate(client,'DELETE','/api/recursos/4').status_code==204
    assert client.get('/api/recursos/4').status_code==404


def test_filters_read_views_and_api_only(client):
    login(client)
    for path in ['/api/proyectos','/api/proyectos/1','/api/consumos','/api/consumos/1',
                 '/api/roles','/api/roles/1','/api/recursos','/api/recursos/1','/api/catalogos','/api/session']:
        response=client.get(path)
        assert response.status_code==200 and response.is_json, path
    assert len(client.get('/api/proyectos?estado=en+curso&responsable=2').json)==1
    assert client.get('/api/proyectos?estado=finalizado').json==[]
    assert client.get('/api/proyectos?responsable=3').json==[]
    assert client.get('/api/proyectos/999').status_code==404
    assert client.get('/api/logout').status_code==405
    assert client.get('/api/unknown').is_json
    assert client.get('/proyectos').status_code==404  # No server-rendered pages.


def test_foreign_keys(app):
    with app.app_context():
        db=get_db()
        assert db.execute('PRAGMA foreign_keys').fetchone()[0]==1
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('DELETE FROM rol WHERE rol_id=1')
        db.rollback()


def test_deleted_account_id_is_not_reused(client):
    login(client)
    first=post(client,'/api/recursos',{'recurso_nombre':'temporal','password':'Inicial123'}).json
    mutate(client,'DELETE','/api/recursos/'+str(first['recurso_id']))
    second=post(client,'/api/recursos',{'recurso_nombre':'distinto','password':'Inicial123'}).json
    assert second['recurso_id']>first['recurso_id']


def test_password_hashes_never_exposed(client,app):
    login(client)
    with app.app_context():
        hashes=[row[0] for row in get_db().execute('SELECT password FROM recurso')]
    for path in ['/api/session','/api/recursos','/api/recursos/1','/api/catalogos','/api/proyectos/1']:
        response=client.get(path)
        body=response.get_data(as_text=True)
        assert all(value not in body for value in hashes)
        assert '"password"' not in body


@pytest.mark.parametrize('method,path',[('POST','/api/roles'),('PUT','/api/proyectos/1'),('DELETE','/api/consumos/1')])
def test_csrf_all_mutation_methods(client,method,path):
    login(client)
    response=client.open(path,method=method,json={})
    assert response.status_code==400 and response.json['error']['code']=='csrf_invalid'


@pytest.mark.parametrize('payload',[[],None,'text',123])
def test_non_object_json(client,payload):
    login(client)
    token=client.get('/api/session').json['csrf_token']
    import json
    response=client.post('/api/roles',data=json.dumps(payload),content_type='application/json',headers={'X-CSRF-Token':token})
    assert response.status_code==400 and response.is_json


def test_invalid_json_and_content_type(client):
    login(client)
    token=client.get('/api/session').json['csrf_token']
    headers={'X-CSRF-Token':token}
    assert client.post('/api/roles',data='{bad',content_type='application/json',headers=headers).status_code==400
    assert client.post('/api/roles',data={'rol_descripcion':'X'},headers=headers).status_code==415
