from sqlalchemy import text

from tests.conftest import login, mutate, post, project_data, upload


def task(name, start, end, hours):
    return dict(
        tarea_nombre=name,
        fecha_inicio=start,
        fecha_fin=end,
        horas_requeridas=hours,
        porcentaje_avance=0,
        recurso_id=None,
    )


def test_derived_plan_updates_after_every_task_change(client):
    login(client)
    p = post(client, '/api/proyectos', project_data()).json()
    assert p['horas_requeridas'] == 0 and p['fecha_inicio'] is None and p['fecha_fin'] is None
    key = p['proyecto_id']
    url = f'/api/proyectos/{key}/tareas'
    first = post(client, url, task('Primera', '2026-10-02', '2026-10-04', 30)).json()
    second = post(client, url, task('Segunda', '2026-10-01', '2026-10-10', 50)).json()

    def plan():
        return client.get(f'/api/proyectos/{key}').json()['proyecto']

    assert (plan()['fecha_inicio'], plan()['fecha_fin'], plan()['horas_requeridas']) == (
        '2026-10-01',
        '2026-10-10',
        80,
    )
    assert (
        mutate(
            client,
            'PUT',
            f'/api/tareas/{second["tarea_id"]}',
            task('Segunda', '2026-10-05', '2026-10-06', 15),
        ).status_code
        == 200
    )
    assert (plan()['fecha_inicio'], plan()['fecha_fin'], plan()['horas_requeridas']) == (
        '2026-10-02',
        '2026-10-06',
        45,
    )
    assert mutate(client, 'DELETE', f'/api/tareas/{first["tarea_id"]}').status_code == 204
    assert (plan()['fecha_inicio'], plan()['fecha_fin'], plan()['horas_requeridas']) == (
        '2026-10-05',
        '2026-10-06',
        15,
    )
    assert mutate(client, 'DELETE', f'/api/tareas/{second["tarea_id"]}').status_code == 204
    assert plan()['fecha_inicio'] is None and plan()['fecha_fin'] is None and plan()['horas_requeridas'] == 0
    assert client.get(f'/api/proyectos/{key}/reporte').status_code == 200


def test_hours_required_positive_and_project_fields_read_only(client):
    login(client)
    for hours in (None, 0, -1, 'nan', True):
        assert (
            post(
                client, '/api/proyectos/1/tareas', task('Mal', '2026-10-01', '2026-10-02', hours)
            ).status_code
            == 400
        )
    for field, value in [
        ('horas_requeridas', 100),
        ('fecha_inicio', '2026-01-01'),
        ('fecha_fin', '2027-01-01'),
    ]:
        assert post(client, '/api/proyectos', project_data() | {field: value}).status_code == 400
        assert mutate(client, 'PUT', '/api/proyectos/1', project_data() | {field: value}).status_code == 400


def test_bulk_tasks_update_plan(client):
    login(client)
    key = post(client, '/api/proyectos', project_data()).json()['proyecto_id']
    csv = (
        'proyecto_id,tarea_nombre,fecha_inicio,fecha_fin,horas_requeridas\n'
        f'{key},A,2026-10-01,2026-10-03,30\n{key},B,2026-10-02,2026-10-05,20\n'
    )
    assert upload(client, 'tareas', 't.csv', csv, confirmar=True).json()['creadas'] == 2
    plan = client.get(f'/api/proyectos/{key}').json()
    assert plan['proyecto']['horas_requeridas'] == 50
    assert plan['proyecto']['fecha_inicio'] == '2026-10-01'
    assert plan['proyecto']['fecha_fin'] == '2026-10-05'
    assert len(plan['tareas']) == 2


def test_trigger_updates_plan_for_direct_imports(client, seeded):
    login(client)
    with seeded.state.engine.begin() as db:
        db.execute(
            text(
                'INSERT INTO tarea (proyecto_id,tarea_nombre,fecha_inicio,fecha_fin,horas_requeridas) '
                "VALUES (1,'Importada','2026-10-01','2026-10-02',12)"
            )
        )
    assert client.get('/api/proyectos/1').json()['proyecto']['horas_requeridas'] == 12
