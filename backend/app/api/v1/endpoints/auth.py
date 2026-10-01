from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, UsuarioResponse
from app.services.auth_service import AuthService
from app.core.exceptions import CredenciaisInvalidasError
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login flexível por E-mail ou Matrícula"
)
def login(dados: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Autentica o usuário com identificador flexível (e-mail institucional ou matrícula) e senha.
    Retorna o token Bearer JWT e os dados do usuário.
    """
    auth_service = AuthService(db)
    try:
        return auth_service.autenticar_e_gerar_token(dados.identificador, dados.senha)
    except CredenciaisInvalidasError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=erro.mensagem,
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/me",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Dados do usuário logado"
)
def obter_usuario_logado(
    current_user: Usuario = Depends(get_current_user)
) -> UsuarioResponse:
    """
    Retorna os dados cadastrais e perfil de autorização do usuário logado via token JWT.
    """
    return UsuarioResponse.model_validate(current_user)
