"""Custom domain exceptions and RFC 9457 Problem Details error handlers."""

from typing import Any, Dict, List, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------
class GymFlowBaseException(Exception):
    """Base class for all application domain exceptions."""

    def __init__(self, detail: str, invalid_params: Optional[List[Dict[str, str]]] = None):
        super().__init__(detail)
        self.detail = detail
        self.invalid_params = invalid_params


class EntityNotFoundException(GymFlowBaseException):
    """Raised when an entity is not found in storage."""

    def __init__(self, entity_name: str, entity_id: str):
        detail = f"{entity_name} com identificador '{entity_id}' não foi encontrado(a)."
        super().__init__(detail=detail)
        self.entity_name = entity_name
        self.entity_id = entity_id


class InvalidUUIDException(GymFlowBaseException):
    """Raised when a provided path or query UUID parameter is malformed."""

    def __init__(self, param_name: str, value: str):
        detail = f"O parâmetro '{param_name}' com valor '{value}' não é um UUID válido."
        super().__init__(detail=detail)
        self.param_name = param_name
        self.value = value


class BadRequestException(GymFlowBaseException):
    """Raised for general bad request scenarios (HTTP 400)."""

    def __init__(self, detail: str, invalid_params: Optional[List[Dict[str, str]]] = None):
        super().__init__(detail=detail, invalid_params=invalid_params)


class UnauthorizedException(GymFlowBaseException):
    """Raised when authentication fails or is missing (HTTP 401)."""

    def __init__(self, detail: str = "Credenciais inválidas ou token ausente/expirado."):
        super().__init__(detail=detail)


class ForbiddenException(GymFlowBaseException):
    """Raised when an authenticated user has insufficient permissions (HTTP 403)."""

    def __init__(self, detail: str = "Acesso negado para o perfil do usuário."):
        super().__init__(detail=detail)


class ConflictException(GymFlowBaseException):
    """Raised for resource state conflicts, such as duplicate unique keys (HTTP 409)."""

    def __init__(self, detail: str, invalid_params: Optional[List[Dict[str, str]]] = None):
        super().__init__(detail=detail, invalid_params=invalid_params)


# ---------------------------------------------------------------------------
# RFC 9457 Factory Helper
# ---------------------------------------------------------------------------
def build_api_error_response(
    status_code: int,
    type_uri: str,
    title: str,
    detail: str,
    instance: str,
    invalid_params: Optional[List[Dict[str, str]]] = None,
) -> JSONResponse:
    """Build a standard RFC 9457 Problem Details response."""
    payload: Dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
    }
    if invalid_params is not None:
        payload["invalidParams"] = invalid_params

    return JSONResponse(
        status_code=status_code,
        content=payload,
        media_type="application/problem+json",
    )


# ---------------------------------------------------------------------------
# Global Exception Handlers
# ---------------------------------------------------------------------------
async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI/Pydantic validation errors (HTTP 422)."""
    invalid_params: List[Dict[str, str]] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        # Filter out "body" from loc prefix for cleaner param names
        loc_parts = [str(p) for p in loc if p != "body"]
        param_name = ".".join(loc_parts) if loc_parts else "body"
        msg = err.get("msg", "Campo inválido")
        invalid_params.append({"name": param_name, "reason": msg})

    return build_api_error_response(
        status_code=422,
        type_uri="https://api.gymflow.dev/errors/validation-error",
        title="Erro de Validação Semântica",
        detail="Um ou mais campos da requisição falharam na validação.",
        instance=request.url.path,
        invalid_params=invalid_params,
    )


async def entity_not_found_exception_handler(request: Request, exc: EntityNotFoundException) -> JSONResponse:
    """Handle 404 EntityNotFoundException."""
    return build_api_error_response(
        status_code=404,
        type_uri="https://api.gymflow.dev/errors/not-found",
        title="Recurso Inexistente",
        detail=exc.detail,
        instance=request.url.path,
    )


async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
    """Handle 401 UnauthorizedException."""
    return build_api_error_response(
        status_code=401,
        type_uri="https://api.gymflow.dev/errors/unauthorized",
        title="Não Autorizado",
        detail=exc.detail,
        instance=request.url.path,
    )


async def forbidden_exception_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
    """Handle 403 ForbiddenException."""
    return build_api_error_response(
        status_code=403,
        type_uri="https://api.gymflow.dev/errors/forbidden",
        title="Acesso Proibido",
        detail=exc.detail,
        instance=request.url.path,
    )


async def bad_request_exception_handler(request: Request, exc: BadRequestException) -> JSONResponse:
    """Handle 400 BadRequestException."""
    return build_api_error_response(
        status_code=400,
        type_uri="https://api.gymflow.dev/errors/bad-request",
        title="Requisição Inválida",
        detail=exc.detail,
        instance=request.url.path,
        invalid_params=exc.invalid_params,
    )


async def invalid_uuid_exception_handler(request: Request, exc: InvalidUUIDException) -> JSONResponse:
    """Handle 400 InvalidUUIDException."""
    return build_api_error_response(
        status_code=400,
        type_uri="https://api.gymflow.dev/errors/bad-request",
        title="Requisição Inválida",
        detail=exc.detail,
        instance=request.url.path,
    )


async def conflict_exception_handler(request: Request, exc: ConflictException) -> JSONResponse:
    """Handle 409 ConflictException."""
    return build_api_error_response(
        status_code=409,
        type_uri="https://api.gymflow.dev/errors/conflict",
        title="Conflito de Estado",
        detail=exc.detail,
        instance=request.url.path,
        invalid_params=exc.invalid_params,
    )


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Intercept Starlette/FastAPI default HTTPExceptions and format strictly as RFC 9457."""
    titles = {
        400: "Requisição Inválida",
        401: "Não Autorizado",
        403: "Acesso Proibido",
        404: "Recurso Inexistente",
        405: "Método Não Permitido",
        409: "Conflito de Estado",
        422: "Erro de Validação Semântica",
        500: "Erro Interno do Servidor",
    }
    type_slugs = {
        400: "bad-request",
        401: "unauthorized",
        403: "forbidden",
        404: "not-found",
        405: "method-not-allowed",
        409: "conflict",
        422: "validation-error",
        500: "internal-server-error",
    }
    title = titles.get(exc.status_code, "Erro na Requisição")
    slug = type_slugs.get(exc.status_code, "http-error")
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    return build_api_error_response(
        status_code=exc.status_code,
        type_uri=f"https://api.gymflow.dev/errors/{slug}",
        title=title,
        detail=detail,
        instance=request.url.path,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all unhandled exceptions and format strictly as RFC 9457 (HTTP 500)."""
    return build_api_error_response(
        status_code=500,
        type_uri="https://api.gymflow.dev/errors/internal-server-error",
        title="Erro Interno do Servidor",
        detail="Ocorreu um erro interno inesperado no servidor.",
        instance=request.url.path,
    )
