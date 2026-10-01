import uuid
from typing import Callable, Sequence
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.usuario import Usuario, PerfilUsuario
from app.core.security import decodificar_token_jwt

# Define o esquema de autenticação OAuth2 Bearer apontando para o endpoint de login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependência que valida o token JWT recebido no Header Authorization: Bearer <token>.
    Retorna a instância do Usuario autenticado ou lança HTTP 401.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado. Token de acesso Bearer não informado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decodificar_token_jwt(token)
        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo ou inexistente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario


def require_roles(perfis_permitidos: Sequence[PerfilUsuario | str]) -> Callable:
    """
    Fábrica de dependências para Controle de Acesso Baseado em Perfis (RBAC).
    Garante que apenas usuários com os perfis especificados acessem o endpoint.
    Lança HTTP 403 Forbidden caso contrário.
    """
    valores_permitidos = {
        p.value if isinstance(p, PerfilUsuario) else str(p)
        for p in perfis_permitidos
    }

    def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.perfil not in valores_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso não autorizado para o perfil deste usuário."
            )
        return current_user

    return role_checker
