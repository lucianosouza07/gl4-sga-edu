import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class LoginRequest(BaseModel):
    """Payload recebido no login (identificador pode ser email ou matrícula)."""
    identificador: str = Field(..., description="E-mail ou Matrícula do usuário")
    senha: str = Field(..., min_length=4, description="Senha do usuário")


class UsuarioResponse(BaseModel):
    """Dados públicos e seguros de exibição do usuário."""
    id: uuid.UUID
    nome: str
    email: EmailStr
    perfil: str
    ativo: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Resposta contendo o token de acesso Bearer e dados do usuário."""
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse
