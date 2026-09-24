from typing import Annotated

from fastapi import APIRouter, Depends, Response

from ..errors import forbidden
from ..models import Consumo, Proyecto, Recurso, Rol
from ..queries import columns, consumption_row, consumptions_query, get_or_404, reference
from ..schemas import ConsumoIn, ConsumoListado, ConsumoOut
from ..sessions import DB, User, protected

router = APIRouter(prefix='/api/consumos', tags=['consumos'], dependencies=protected)


@router.get('', response_model=list[ConsumoListado])
def index(db: DB):
    return [consumption_row(*row) for row in db.execute(consumptions_query())]


@router.get('/{identifier}', response_model=ConsumoOut)
def detail(identifier: int, db: DB):
    return columns(get_or_404(db, Consumo, identifier))


def own_consumption(identifier: int, db: DB, user: User) -> Consumo:
    """Loaded before the body is validated, so permission errors win over validation errors."""
    item = get_or_404(db, Consumo, identifier)
    if not user.es_admin and item.recurso_id != user.recurso_id:
        raise forbidden('Solo podés modificar tus propios consumos.')
    return item


Own = Annotated[Consumo, Depends(own_consumption)]


def apply(item: Consumo, data: ConsumoIn, db: DB, user: User) -> Consumo:
    resource = reference(db, Recurso, data.recurso_id) if user.es_admin else user.recurso_id
    item.proyecto_id = reference(db, Proyecto, data.proyecto_id)
    item.rol_id = reference(db, Rol, data.rol_id)
    item.recurso_id = resource
    for key in ('fecha_inicio', 'fecha_fin', 'horas_consumidas', 'tarea'):
        setattr(item, key, getattr(data, key))
    db.add(item)
    db.commit()
    return item


@router.post('', status_code=201, response_model=ConsumoOut)
def create(data: ConsumoIn, db: DB, user: User):
    return apply(Consumo(), data, db, user)


@router.put('/{identifier}', response_model=ConsumoOut)
def update(item: Own, data: ConsumoIn, db: DB, user: User):
    return apply(item, data, db, user)


@router.delete('/{identifier}', status_code=204)
def remove(item: Own, db: DB):
    db.delete(item)
    db.commit()
    return Response(status_code=204)
