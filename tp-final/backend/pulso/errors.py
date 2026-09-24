from fastapi.responses import JSONResponse


class APIError(Exception):
    """Business/validation error rendered with the uniform `{"error": {...}}` contract."""

    def __init__(self, message: str, status: int = 400, code: str = 'validation_error'):
        super().__init__(message)
        self.status = status
        self.code = code


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({'error': {'code': code, 'message': message}}, status_code=status)


def not_found() -> APIError:
    return APIError('No se encontró el registro.', 404, 'http_404')


def forbidden(message: str) -> APIError:
    return APIError(message, 403, 'http_403')
