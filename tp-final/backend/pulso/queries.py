from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from .errors import APIError, not_found
from .models import Base, Consumo, Proyecto, Recurso, Rol


def get_or_404[M: Base](db: Session, model: type[M], identifier: int) -> M:
    row = db.get(model, identifier)
    if row is None:
        raise not_found()
    return row


def reference(db: Session, model: type[Base], identifier: int | None) -> int:
    """Validate a foreign key sent by the client (400, not 404, like the Flask version)."""
    if identifier is None:
        raise APIError('Seleccioná una referencia válida.')
    if db.get(model, identifier) is None:
        raise APIError('El recurso, proyecto o rol seleccionado no existe.')
    return identifier


def columns(row: Base) -> dict:
    return {column.key: getattr(row, column.key) for column in row.__table__.columns}


def projects_query() -> Select:
    consumed = (
        select(Consumo.proyecto_id, func.sum(Consumo.horas_consumidas).label('total'))
        .group_by(Consumo.proyecto_id)
        .subquery()
    )
    return (
        select(
            Proyecto,
            Recurso.recurso_nombre.label('responsable'),
            func.coalesce(consumed.c.total, 0).label('horas_consumidas'),
        )
        .join(Recurso, Recurso.recurso_id == Proyecto.owner_id)
        .outerjoin(consumed, consumed.c.proyecto_id == Proyecto.proyecto_id)
    )


def project_summary(project: Proyecto, responsable: str, consumed: float) -> dict:
    data = columns(project)
    saldo = project.horas_requeridas - consumed
    data.update(
        responsable=responsable,
        horas_consumidas=consumed,
        saldo=saldo,
        exceso=max(-saldo, 0),
        porcentaje_consumo=consumed / project.horas_requeridas * 100,
    )
    return data


def consumptions_query() -> Select:
    return (
        select(Consumo, Proyecto.proyecto_nombre, Recurso.recurso_nombre, Rol.rol_descripcion)
        .join(Proyecto, Proyecto.proyecto_id == Consumo.proyecto_id)
        .join(Recurso, Recurso.recurso_id == Consumo.recurso_id)
        .join(Rol, Rol.rol_id == Consumo.rol_id)
        .order_by(Consumo.fecha_inicio.desc(), Consumo.consumo_id.desc())
    )


def consumption_row(consumo: Consumo, proyecto: str, recurso: str, rol: str) -> dict:
    return columns(consumo) | {'proyecto_nombre': proyecto, 'recurso_nombre': recurso, 'rol_descripcion': rol}
