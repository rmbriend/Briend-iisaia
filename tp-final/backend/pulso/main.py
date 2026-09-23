from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import Settings, get_settings
from .db import make_engine, make_sessionmaker


class APIError(Exception):
    """Business/validation error rendered with the uniform `{"error": {...}}` contract."""

    def __init__(self, message: str, status: int = 400, code: str = 'validation_error'):
        super().__init__(message)
        self.status = status
        self.code = code


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({'error': {'code': code, 'message': message}}, status_code=status)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title='Pulso API',
        version='0.2.0',
        docs_url='/api/docs',
        redoc_url=None,
        openapi_url='/api/openapi.json',
    )
    app.state.settings = settings
    app.state.engine = make_engine(settings.database_url)
    app.state.sessionmaker = make_sessionmaker(app.state.engine)

    @app.middleware('http')
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        if request.url.path.startswith('/api/') and request.url.path != '/api/docs':
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(APIError)
    async def api_error(_: Request, error: APIError):
        return error_response(error.status, error.code, str(error))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, error: RequestValidationError):
        first = error.errors()[0] if error.errors() else {}
        return error_response(400, 'validation_error', first.get('msg', 'Datos inválidos.'))

    @app.exception_handler(IntegrityError)
    async def integrity_error(_: Request, __: IntegrityError):
        return error_response(
            409,
            'conflict',
            'No se puede completar: el nombre ya existe o el registro tiene referencias asociadas.',
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, error: StarletteHTTPException):
        message = 'Error interno del servidor.' if error.status_code >= 500 else str(error.detail)
        return error_response(error.status_code, f'http_{error.status_code}', message)

    @app.get('/api/health', tags=['sistema'])
    def health() -> dict[str, str]:
        with app.state.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        return {'status': 'ok'}

    return app
