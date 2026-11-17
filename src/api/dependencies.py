"""Authentication and RBAC dependency injection."""

from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.database import get_user_by_id
from api.exceptions import ForbiddenException, UnauthorizedException
from api.security import decode_access_token

oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
) -> dict:
    """Retrieve and validate the authenticated user from the Bearer JWT token."""
    if credentials is None or not credentials.credentials:
        raise UnauthorizedException("Token de acesso ausente ou não informado.")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise UnauthorizedException("Token de acesso inválido ou expirado.")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token de acesso com payload inválido.")

    user = get_user_by_id(user_id)
    if not user:
        raise UnauthorizedException("Usuário associado ao token não encontrado.")

    return user


async def require_personal(current_user: dict = Depends(get_current_user)) -> dict:
    """Ensure the authenticated user possesses the PERSONAL role."""
    if current_user.get("role") != "PERSONAL":
        raise ForbiddenException("Acesso negado: operação restrita a Personal Trainers.")
    return current_user


async def require_student(current_user: dict = Depends(get_current_user)) -> dict:
    """Ensure the authenticated user possesses the STUDENT role."""
    if current_user.get("role") != "STUDENT":
        raise ForbiddenException("Acesso negado: operação restrita a Alunos.")
    return current_user
