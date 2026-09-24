from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..errors import APIError
from ..models import Recurso, Sesion
from ..queries import get_or_404
from ..schemas import RecursoIn, UsuarioOut
from ..security import hash_password
from ..sessions import DB, protected, require_admin

router = APIRouter(
    prefix='/api/recursos', tags=['recursos'], dependencies=[*protected, Depends(require_admin)]
)


def is_last_admin(db: Session, item: Recurso) -> bool:
    # Row locks serialize concurrent demotions/deletions, so two requests can't remove the last two admins.
    admins = db.scalars(select(Recurso.recurso_id).where(Recurso.es_admin).with_for_update()).all()
    return item.es_admin and len(admins) <= 1


@router.get('', response_model=list[UsuarioOut])
def index(db: DB):
    return db.scalars(select(Recurso).order_by(func.lower(Recurso.recurso_nombre))).all()


@router.get('/{identifier}', response_model=UsuarioOut)
def detail(identifier: int, db: DB):
    return get_or_404(db, Recurso, identifier)


@router.post('', status_code=201, response_model=UsuarioOut)
def create(data: RecursoIn, db: DB):
    if len(data.password) < 8:
        raise APIError('La contraseña debe tener al menos 8 caracteres.')
    item = Recurso(
        recurso_nombre=data.recurso_nombre,
        email=data.email,
        es_admin=data.es_admin,
        password=hash_password(data.password),
        debe_cambiar_password=True,
    )
    db.add(item)
    db.commit()
    return item


@router.put('/{identifier}', response_model=UsuarioOut)
def update(identifier: int, data: RecursoIn, db: DB):
    item = get_or_404(db, Recurso, identifier)
    if data.password and len(data.password) < 8:
        raise APIError('La contraseña debe tener al menos 8 caracteres.')
    if not data.es_admin and is_last_admin(db, item):
        raise APIError('Debe quedar al menos un administrador.', 409, 'last_admin')
    item.recurso_nombre = data.recurso_nombre
    item.email = data.email
    item.es_admin = data.es_admin
    if data.password:
        # A reset password must be replaced at next login; existing sessions are closed.
        item.password = hash_password(data.password)
        item.debe_cambiar_password = True
        db.execute(delete(Sesion).where(Sesion.recurso_id == identifier))
    db.commit()
    return item


@router.delete('/{identifier}', status_code=204)
def remove(identifier: int, db: DB):
    item = get_or_404(db, Recurso, identifier)
    if is_last_admin(db, item):
        raise APIError('No se puede eliminar al último administrador.', 409, 'last_admin')
    db.delete(item)
    db.commit()
    return Response(status_code=204)
