"""
Modelos Pydantic para Autenticação e RBAC (SGA-EDU)
Módulo 30 - src/backend/modulo_30_autenticacao_rbac/models.py
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=255, description="Matrícula ou usuário institucional")
    senha: str = Field(..., min_length=4, max_length=128, description="Senha de acesso")

    @field_validator("login")
    @classmethod
    def validar_e_sanitizar_login(cls, valor: str) -> str:
        limpo = valor.strip()
        if not limpo:
            raise ValueError("O login ou matrícula não pode estar vazio.")
        return limpo

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("A senha não pode estar vazia.")
        return valor


class UsuarioInfo(BaseModel):
    id: int
    login: str
    nome: str
    perfil_id: int
    perfil_nome: str
    perfil_slug: str
    status_conta: int


class LoginResponse(BaseModel):
    sucesso: bool
    mensagem: str
    usuario: Optional[UsuarioInfo] = None
    token_sessao: Optional[str] = None


class RecuperarSenhaRequest(BaseModel):
    identificador: str = Field(..., min_length=3, max_length=255, description="E-mail ou CPF")

    @field_validator("identificador")
    @classmethod
    def sanitizar_identificador(cls, valor: str) -> str:
        limpo = valor.strip()
        if not limpo:
            raise ValueError("Informe um e-mail institucional ou CPF válido.")
        return limpo


class RecuperarSenhaResponse(BaseModel):
    sucesso: bool
    mensagem: str
    expira_em_minutos: int = 30
