import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from tests.conftest import SERVER_URL, alembic_config


def test_migration_preserves_estimates_and_concurrent_task_writes():
    name = 'pulso_plan_' + uuid.uuid4().hex[:8]
    admin = create_engine(SERVER_URL, isolation_level='AUTOCOMMIT')
    with admin.connect() as db:
        db.execute(text(f'CREATE DATABASE {name}'))
    url = make_url(SERVER_URL).set(database=name).render_as_string(hide_password=False)
    engine = create_engine(url)
    try:
        config = alembic_config(url)
        command.upgrade(config, '0005')
        with engine.begin() as db:
            db.execute(text("INSERT INTO recurso (recurso_nombre,password) VALUES ('owner','test-hash')"))
            db.execute(
                text("""INSERT INTO proyecto (proyecto_nombre,fecha_inicio,fecha_fin,horas_requeridas,
                owner_id,proyect_status,porcentaje_avance) VALUES
                ('Con tareas','2026-10-01','2026-10-31',100,1,'En curso',25),
                ('Sin tareas','2026-10-01','2026-10-10',40,1,'Pendiente',0)""")
            )
            db.execute(
                text("""INSERT INTO tarea (proyecto_id,tarea_nombre,fecha_inicio,fecha_fin) VALUES
                (1,'A','2026-10-02','2026-10-03'),(1,'B','2026-10-05','2026-10-07')""")
            )
        command.upgrade(config, 'head')
        command.upgrade(config, 'head')
        with engine.connect() as db:
            hours = db.execute(text('SELECT horas_requeridas FROM tarea ORDER BY tarea_id')).scalars().all()
            assert hours == pytest.approx([40, 60, 40])
            projects = db.execute(
                text('SELECT fecha_inicio,fecha_fin,horas_requeridas FROM proyecto ORDER BY proyecto_id')
            ).all()
            assert [str(v) for v in projects[0][:2]] == ['2026-10-02', '2026-10-07']
            assert projects[0][2] == pytest.approx(100)
            assert [str(v) for v in projects[1][:2]] == ['2026-10-01', '2026-10-10']

        def insert(index):
            with engine.begin() as db:
                db.execute(
                    text("""INSERT INTO tarea
                    (proyecto_id,tarea_nombre,fecha_inicio,fecha_fin,horas_requeridas)
                    VALUES (1,:name,'2026-09-01','2026-11-01',5)"""),
                    {'name': f'Concurrente {index}'},
                )

        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(insert, range(8)))
        with engine.connect() as db:
            assert db.scalar(
                text('SELECT horas_requeridas FROM proyecto WHERE proyecto_id=1')
            ) == pytest.approx(140)
    finally:
        engine.dispose()
        with admin.connect() as db:
            db.execute(text(f'DROP DATABASE IF EXISTS {name} WITH (FORCE)'))
        admin.dispose()
