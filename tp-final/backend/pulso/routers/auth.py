from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import delete, func, select

from ..errors import APIError
from ..models import Recurso, Sesion
from ..schemas import LoginIn, PasswordIn, SesionOut
from ..security import hash_password, verify_password
from ..sessions import DB, State, User, guard, start_session

router = APIRouter(prefix='/api', tags=['sesión'])


def payload(user: Recurso | None, csrf: str) -> dict:
    return {'user': user, 'csrf_token': csrf}


@router.get('/session', response_model=SesionOut)
def current_session(request: Request, response: Response, db: DB, state: State):
    row = state.row or start_session(db, response, request, None)
    return payload(state.user, row.csrf)


@router.post('/login', response_model=SesionOut, dependencies=[Depends(guard(require_user=False))])
def login(data: LoginIn, request: Request, response: Response, db: DB):
    user = db.scalar(select(Recurso).where(func.lower(Recurso.recurso_nombre) == data.recurso_nombre.lower()))
    valid, new_hash = verify_password(data.password, user.password if user else None)
    if not user or not valid:
        raise APIError('Usuario o contraseña incorrectos.', 401, 'invalid_credentials')
    if new_hash:
        user.password = new_hash
    row = start_session(db, response, request, user)
    return payload(user, row.csrf)


@router.post('/logout', response_model=SesionOut, dependencies=[Depends(guard(allow_pending=True))])
def logout(request: Request, response: Response, db: DB):
    row = start_session(db, response, request, None)
    return payload(None, row.csrf)


@router.put('/password', response_model=SesionOut, dependencies=[Depends(guard(allow_pending=True))])
def change_password(data: PasswordIn, request: Request, response: Response, db: DB, user: User):
    if not data.actual or not verify_password(data.actual, user.password)[0]:
        raise APIError('La contraseña actual es incorrecta.')
    if len(data.password) < 8 or data.password != data.confirmacion:
        raise APIError(
            'La nueva contraseña debe tener al menos 8 caracteres y coincidir con la confirmación.'
        )
    if verify_password(data.password, user.password)[0]:
        raise APIError('Elegí una contraseña diferente de la actual.')
    user.password = hash_password(data.password)
    user.debe_cambiar_password = False
    # Sign out every other browser of this user; this one gets a fresh token and CSRF.
    db.execute(delete(Sesion).where(Sesion.recurso_id == user.recurso_id))
    row = start_session(db, response, request, user)
    return payload(user, row.csrf)
