from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select

from ..models import Rol
from ..queries import get_or_404
from ..schemas import RolIn, RolOut
from ..sessions import DB, protected, require_admin

router = APIRouter(prefix='/api/roles', tags=['roles'], dependencies=[*protected, Depends(require_admin)])


@router.get('', response_model=list[RolOut])
def index(db: DB):
    return db.scalars(select(Rol).order_by(func.lower(Rol.rol_descripcion))).all()


@router.get('/{identifier}', response_model=RolOut)
def detail(identifier: int, db: DB):
    return get_or_404(db, Rol, identifier)


def save(item: Rol, data: RolIn, db: DB) -> Rol:
    item.rol_descripcion = data.rol_descripcion
    db.add(item)
    db.commit()
    return item


@router.post('', status_code=201, response_model=RolOut)
def create(data: RolIn, db: DB):
    return save(Rol(), data, db)


@router.put('/{identifier}', response_model=RolOut)
def update(identifier: int, data: RolIn, db: DB):
    return save(get_or_404(db, Rol, identifier), data, db)


@router.delete('/{identifier}', status_code=204)
def remove(identifier: int, db: DB):
    db.delete(get_or_404(db, Rol, identifier))
    db.commit()
    return Response(status_code=204)
