"""Authentication Router: user registration, login, and profile inspection."""

from fastapi import APIRouter, Depends, status

from api.database import create_user, get_user_by_email
from api.dependencies import get_current_user
from api.exceptions import BadRequestException, UnauthorizedException
from api.schemas import AuthTokenResponse, LoginRequestDTO, RegisterUserDTO, UserResponse
from api.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário (Personal ou Aluno)",
)
async def register(dto: RegisterUserDTO) -> UserResponse:
    existing = get_user_by_email(dto.email)
    if existing:
        raise BadRequestException(
            detail=f"O e-mail '{dto.email}' já está em uso.",
            invalid_params=[{"name": "email", "reason": "E-mail já cadastrado no sistema."}],
        )

    hashed_pwd = hash_password(dto.password)
    new_user = create_user(dto, hashed_pwd)
    return UserResponse.model_validate(new_user)


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Autenticação e obtenção de token JWT",
)
async def login(dto: LoginRequestDTO) -> AuthTokenResponse:
    user = get_user_by_email(dto.email)
    if not user or not verify_password(dto.password, user["password"]):
        raise UnauthorizedException("Credenciais inválidas: e-mail ou senha incorretos.")

    token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar dados do usuário autenticado",
)
async def get_me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
