"""Schemas Pydantic e validadores de domínio para funcionários administrativos."""

from enum import Enum
import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PerfilAdminEnum(str, Enum):
    """Perfis institucionais gerenciados por este módulo."""

    SECRETARIA = "Secretaria"
    FINANCEIRO = "Financeiro"
    ADMIN = "Admin"


PERFIL_NOME_PARA_ID: dict[str, int] = {
    PerfilAdminEnum.SECRETARIA.value: 3,
    PerfilAdminEnum.FINANCEIRO.value: 4,
    PerfilAdminEnum.ADMIN.value: 5,
}

PERFIL_ID_PARA_NOME: dict[int, str] = {v: k for k, v in PERFIL_NOME_PARA_ID.items()}
PERFIL_ADMIN_ID = PERFIL_NOME_PARA_ID[PerfilAdminEnum.ADMIN.value]


def _calcular_digito_cpf(parcial: str, peso_inicial: int) -> int:
    soma = sum(int(digito) * (peso_inicial - idx) for idx, digito in enumerate(parcial))
    resto = (soma * 10) % 11
    return 0 if resto == 10 else resto


def normalizar_e_validar_cpf(valor: str) -> str:
    """Remove pontuação, valida 11 dígitos, rejeita sequências repetidas e checa módulo 11."""
    if not isinstance(valor, str):
        raise ValueError("CPF inválido.")
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) != 11:
        raise ValueError("CPF deve conter exatamente 11 dígitos numéricos.")
    if len(set(digitos)) == 1:
        raise ValueError("CPF inválido: sequência numérica repetida não permitida.")
    d1 = _calcular_digito_cpf(digitos[:9], 10)
    d2 = _calcular_digito_cpf(digitos[:10], 11)
    if digitos[9] != str(d1) or digitos[10] != str(d2):
        raise ValueError("CPF inválido: dígitos verificadores incorretos.")
    return digitos


def limpar_texto_obrigatorio(valor: str, minimo: int, maximo: int, nome_campo: str) -> str:
    """Remove espaços nas pontas e valida comprimento do campo obrigatório."""
    if not isinstance(valor, str):
        raise ValueError(f"{nome_campo} inválido.")
    limpo = valor.strip()
    if len(limpo) < minimo or len(limpo) > maximo:
        raise ValueError(f"{nome_campo} deve conter entre {minimo} e {maximo} caracteres.")
    return limpo


def normalizar_e_validar_login(valor: str) -> str:
    """Normaliza login (3..255 caracteres), proíbe espaços internos e aplica lowercase em e-mail."""
    limpo = limpar_texto_obrigatorio(valor, 3, 255, "Login")
    if re.search(r"\s", limpo):
        raise ValueError("Login não pode conter espaços internos.")
    return limpo.lower() if "@" in limpo else limpo


def normalizar_e_validar_cargo(valor: Optional[str]) -> Optional[str]:
    """Normaliza cargo opcional para None quando vazio ou valida comprimento 2..80."""
    if valor is None:
        return None
    limpo = valor.strip()
    if not limpo:
        return None
    if len(limpo) < 2 or len(limpo) > 80:
        raise ValueError("Cargo deve conter entre 2 e 80 caracteres.")
    return limpo


class _FuncionarioAdminCamposBase(BaseModel):
    """Campos cadastrais compartilhados entre criação e atualização."""

    nome: str
    cpf: str
    login: str
    setor: str
    cargo: Optional[str] = None
    perfil: PerfilAdminEnum

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        return limpar_texto_obrigatorio(valor, 3, 120, "Nome")

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        return normalizar_e_validar_cpf(valor)

    @field_validator("login")
    @classmethod
    def validar_login(cls, valor: str) -> str:
        return normalizar_e_validar_login(valor)

    @field_validator("setor")
    @classmethod
    def validar_setor(cls, valor: str) -> str:
        return limpar_texto_obrigatorio(valor, 2, 100, "Setor")

    @field_validator("cargo")
    @classmethod
    def validar_cargo(cls, valor: Optional[str]) -> Optional[str]:
        return normalizar_e_validar_cargo(valor)


class FuncionarioAdminCreate(_FuncionarioAdminCamposBase):
    """Payload de entrada para criação conjunta de funcionário administrativo e conta."""

    senha_inicial: str = Field(..., min_length=8, max_length=128)

    @field_validator("senha_inicial")
    @classmethod
    def validar_senha_inicial(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("A senha inicial não pode ser composta apenas por espaços.")
        return valor


class FuncionarioAdminUpdate(_FuncionarioAdminCamposBase):
    """Payload de entrada para atualização cadastral e de perfil administrativo."""


class FuncionarioAdminStatusUpdate(BaseModel):
    """Payload de entrada para ativar ou inativar conta administrativa."""

    ativo: bool


class FuncionarioAdminResponse(BaseModel):
    """Representação pública segura de funcionário administrativo sem dados de senha."""

    model_config = ConfigDict(from_attributes=True)

    id_funcionario: int
    usuario_id: int
    nome: str
    cpf: str
    login: str
    setor: str
    cargo: Optional[str] = None
    perfil_id: int
    perfil: PerfilAdminEnum
    ativo: bool
    senha_provisoria: bool
    criado_em: Optional[str] = None


class AuditoriaEventoResponse(BaseModel):
    """Evento registrado na trilha de auditoria do módulo."""

    id_auditoria: int
    usuario_id: Optional[int] = None
    entidade_afetada: str
    id_registro_afetado: Optional[str] = None
    acao: str
    dados_anteriores: Optional[str] = None
    dados_novos: Optional[str] = None
    ip_origem: str
    data_hora: str


class MensagemResponse(BaseModel):
    """Resposta padrão de confirmação de operação."""

    mensagem: str
