"""Modelos Pydantic v2 para validação e transporte do módulo MFA e governança RBAC."""

import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

PERFIL_ID_PARA_NOME: dict[int, str] = {
    1: "Aluno",
    2: "Professor",
    3: "Secretaria",
    4: "Financeiro",
    5: "Admin",
}

PERFIL_NOME_PARA_ID: dict[str, int] = {
    nome: id_perfil for id_perfil, nome in PERFIL_ID_PARA_NOME.items()
}


class MfaSetupResponse(BaseModel):
    """Resposta com dados de aprovisionamento provisório de MFA."""
    model_config = ConfigDict(extra="forbid")

    secret: str = Field(..., description="Segredo Base32 de 160 bits para pareamento")
    otpauth_uri: str = Field(..., description="URI formatada para importação no autenticador")
    validade_segundos: int = Field(600, description="Tempo limite em segundos para confirmar o código")


class MfaActivateRequest(BaseModel):
    """Payload de submissão do primeiro código para ativação definitiva de MFA."""
    model_config = ConfigDict(extra="forbid")

    codigo: str = Field(..., description="Código numérico de 6 dígitos gerado pelo autenticador")

    @field_validator("codigo")
    @classmethod
    def validar_codigo_totp(cls, valor: str) -> str:
        limpo = valor.strip()
        if not re.match(r"^\d{6}$", limpo):
            raise ValueError("O código de verificação deve conter exatamente 6 dígitos numéricos.")
        return limpo


class MfaActivateResponse(BaseModel):
    """Resposta com confirmação de ativação e lote de códigos de contingência."""
    model_config = ConfigDict(extra="forbid")

    mfa_ativo: bool = Field(True, description="Indicador de MFA ativado na conta")
    backup_codes: list[str] = Field(..., description="Lote de 8 códigos de contingência descartáveis")


class MfaStatusResponse(BaseModel):
    """Consulta de situação do MFA da conta."""
    model_config = ConfigDict(extra="forbid")

    mfa_ativo: bool = Field(..., description="Se a conta possui MFA ativo")
    token_mfa_configurado: bool = Field(..., description="Se o token TOTP já foi gravado")


class MfaDeactivateRequest(BaseModel):
    """Payload de desativação voluntária do MFA pelo próprio usuário."""
    model_config = ConfigDict(extra="forbid")

    senha: str = Field(..., min_length=8, description="Senha primária atual do usuário")
    codigo: str = Field(..., min_length=6, description="Código TOTP atual ou código de recuperação")

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, valor: str) -> str:
        if not valor or len(valor.strip()) < 8:
            raise ValueError("A senha deve possuir no mínimo 8 caracteres.")
        return valor

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo(cls, valor: str) -> str:
        limpo = valor.strip()
        if not limpo:
            raise ValueError("O código de verificação não pode estar em branco.")
        return limpo


class MfaChallengeRequest(BaseModel):
    """Payload de resposta ao desafio de segundo fator durante o fluxo de login."""
    model_config = ConfigDict(extra="forbid")

    challenge_token: str = Field(..., min_length=10, description="Token temporário assinado do desafio de login")
    codigo: str = Field(..., min_length=6, description="Código numérico TOTP de 6 dígitos ou código de recuperação")

    @field_validator("challenge_token", "codigo")
    @classmethod
    def validar_nao_vazio(cls, valor: str) -> str:
        limpo = valor.strip()
        if not limpo:
            raise ValueError("Campo obrigatório não pode estar vazio.")
        return limpo


class MfaChallengeResponse(BaseModel):
    """Resposta de autenticação completa após validação de segundo fator."""
    model_config = ConfigDict(extra="forbid")

    access_token: str = Field(..., description="Token Bearer da sessão institucional")
    token_type: str = Field("bearer", description="Tipo do token de autenticação")
    perfil_RBAC: int = Field(..., description="Identificador do perfil atribuído")
    usuario_id: int = Field(..., description="Identificador único do usuário")
    login: str = Field(..., description="Identificador de acesso institucional")


class PerfilResponse(BaseModel):
    """Representação de um perfil institucional do catálogo RBAC."""
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id_perfil: int
    nome_perfil: str
    descricao: Optional[str] = None


class UsuarioRbacResponse(BaseModel):
    """Visualização governada de conta de usuário com perfil RBAC e status de MFA."""
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id_usuario: int
    login: str
    perfil_RBAC: int
    nome_perfil: str
    statusCONTA: int
    mfa_ativo: bool
    criado_em: Optional[str] = None


class UsuarioPerfilUpdateRequest(BaseModel):
    """Payload para atualização de perfil institucional por um operador Admin."""
    model_config = ConfigDict(extra="forbid")

    novo_perfil_id: int = Field(..., ge=1, le=5, description="Identificador do novo perfil (1 a 5)")


class MfaAdminResetResponse(BaseModel):
    """Confirmação de redefinição emergencial de MFA executada pelo Admin."""
    model_config = ConfigDict(extra="forbid")

    mensagem: str
    mfa_ativo: bool = False


class SimpleMessageResponse(BaseModel):
    """Mensagem simples de confirmação de operação."""
    model_config = ConfigDict(extra="forbid")

    mensagem: str


class AuditoriaItemResponse(BaseModel):
    """Item individual da trilha de auditoria do sistema."""
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id_auditoria: int
    usuario_id: Optional[int] = None
    entidade_afetada: str
    id_registro_afetado: Optional[str] = None
    acao: str
    dados_anteriores: Optional[str] = None
    dados_novos: Optional[str] = None
    ip_origem: str
    data_hora: str


class ErrorDetail(BaseModel):
    """Mensagem de erro padronizada."""
    model_config = ConfigDict(extra="forbid")

    detail: str
