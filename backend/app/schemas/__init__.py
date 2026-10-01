from app.schemas.auth import LoginRequest, UsuarioResponse, TokenResponse
from app.schemas.aluno import AlunoCreate, AlunoUpdate, AlunoResponse
from app.schemas.paginacao import PaginaResponse

__all__ = [
    "LoginRequest",
    "UsuarioResponse",
    "TokenResponse",
    "AlunoCreate",
    "AlunoUpdate",
    "AlunoResponse",
    "PaginaResponse",
]
