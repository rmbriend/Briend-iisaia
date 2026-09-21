import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from app.db import get_db, init_db


@pytest.fixture
def app(tmp_path):
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-only', 'DATABASE': str(tmp_path / 'test.sqlite')})
    with app.app_context():
        init_db()
        db = get_db()
        db.execute('UPDATE recurso SET debe_cambiar_password=0 WHERE recurso_id=1')
        for name in ('ana', 'bruno'):
            db.execute('INSERT INTO recurso (recurso_nombre,password,debe_cambiar_password) VALUES (?,?,0)',
                       (name, generate_password_hash('Personal123')))
        db.execute("INSERT INTO rol (rol_descripcion) VALUES ('Analista')")
        db.execute("""INSERT INTO proyecto (proyecto_nombre,fecha_inicio,fecha_fin,horas_requeridas,
            owner_id,proyect_status,porcentaje_avance) VALUES ('Proyecto ejemplo','2026-09-01','2026-09-30',10,2,'en curso',25)""")
        db.execute("""INSERT INTO consumo (proyecto_id,recurso_id,fecha_inicio,fecha_fin,horas_consumidas,tarea,rol_id)
            VALUES (1,2,'2026-09-02','2026-09-02',3,'Diseño',1)""")
        db.commit()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def post(client, path, data=None, **kwargs):
    client.get('/login')
    with client.session_transaction() as session:
        token = session['csrf']
    return client.post(path, data={**(data or {}), 'csrf_token': token}, **kwargs)


def login(client, name='admin', password='Proyecto1'):
    return post(client, '/login', {'recurso_nombre': name, 'password': password})


def project_data():
    return dict(proyecto_nombre='Proyecto editado', fecha_inicio='2026-09-01', fecha_fin='2026-09-30',
                horas_requeridas='10', owner_id='2', proyect_status='en curso', porcentaje_avance='25')


def consumption_data():
    return dict(proyecto_id='1', recurso_id='2', fecha_inicio='2026-10-01', fecha_fin='2026-10-02',
                horas_consumidas='12', tarea='Implementación', rol_id='1')
