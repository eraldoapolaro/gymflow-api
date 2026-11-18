"""GymFlow API entrypoint: FastAPI app, CORS, malformed JSON middleware, and routers."""

import json

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.exceptions import (
    BadRequestException,
    ConflictException,
    EntityNotFoundException,
    ForbiddenException,
    InvalidUUIDException,
    UnauthorizedException,
    bad_request_exception_handler,
    build_api_error_response,
    conflict_exception_handler,
    entity_not_found_exception_handler,
    forbidden_exception_handler,
    generic_exception_handler,
    invalid_uuid_exception_handler,
    request_validation_exception_handler,
    starlette_http_exception_handler,
    unauthorized_exception_handler,
)
from api.routers import auth, executions, students, workouts

app = FastAPI(
    title="GymFlow API",
    version="1.0.0",
    description="API de gestão de treinos e acompanhamento físico para Personal Trainers e Alunos",
)

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Middleware: Intercept Malformed JSON Payloads
# ---------------------------------------------------------------------------
@app.middleware("http")
async def intercept_malformed_json_middleware(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.body()
            if body:
                try:
                    json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return build_api_error_response(
                        status_code=400,
                        type_uri="https://api.gymflow.dev/errors/bad-request",
                        title="Requisição Malformada",
                        detail="O corpo da requisição não é um JSON sintaticamente válido.",
                        instance=request.url.path,
                    )
            # Re-supply receive channel so route handlers can read the body
            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            request._receive = receive

    return await call_next(request)


# ---------------------------------------------------------------------------
# Exception Handlers Registration (RFC 9457 Strict Compliance)
# ---------------------------------------------------------------------------
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(EntityNotFoundException, entity_not_found_exception_handler)
app.add_exception_handler(UnauthorizedException, unauthorized_exception_handler)
app.add_exception_handler(ForbiddenException, forbidden_exception_handler)
app.add_exception_handler(BadRequestException, bad_request_exception_handler)
app.add_exception_handler(InvalidUUIDException, invalid_uuid_exception_handler)
app.add_exception_handler(ConflictException, conflict_exception_handler)
app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ---------------------------------------------------------------------------
# Root Redirect to Swagger Documentation
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/docs")


# ---------------------------------------------------------------------------
# Include Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(workouts.router)
app.include_router(executions.router)
