"""Schemas Pydantic e validadores de domínio para cadastro e gestão de alunos (SGA-15)."""

from datetime import date
from enum import Enum
import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

PERFIL_ALUNO_ID = 1
PERFIL_ALUNO_NOME = "Aluno"
PERFIL_SECRETARIA_ID = 3
PERFIL_ADMIN_ID = 5
PERFIS_OPERADORES_AUTORIZADOS: frozenset[int] = frozenset({
    PERFIL_SECRETARIA_ID,
    PERFIL_ADMIN_ID,
})

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class StatusAcademicoEnum(str, Enum):
    """Situações acadêmicas possíveis de um estudante no SGA-Edu."""

    ATIVO = "ATIVO"
    TRANCADO = "TRANCADO"
    FORMADO = "FORMADO"
    TRANSFERIDO = "TRANSFERIDO"
    CANCELADO = "CANCELADO"
    JUBILADO = "JUBILADO"


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


def normalizar_e_validar_email(valor: str) -> str:
    """Normaliza e-mail para minúsculas e valida formato e comprimento máximo de 120 caracteres."""
    limpo = limpar_texto_obrigatorio(valor, 5, 120, "E-mail").lower()
    if not EMAIL_REGEX.match(limpo):
        raise ValueError("E-mail em formato inválido.")
    return limpo


def normalizar_e_validar_telefone(valor: Optional[str]) -> Optional[str]:
    """Normaliza telefone opcional para None ou 10..11 dígitos numéricos."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError("Telefone inválido.")
    limpo = valor.strip()
    if not limpo:
        return None
    digitos = re.sub(r"\D", "", limpo)
    if len(digitos) not in (10, 11):
        raise ValueError("Telefone deve conter 10 ou 11 dígitos numéricos.")
    return digitos


def normalizar_e_validar_data_nascimento(valor: Optional[str]) -> Optional[str]:
    """Valida data de nascimento opcional no formato ISO YYYY-MM-DD (não futura, ano >= 1900)."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError("Data de nascimento inválida.")
    limpo = valor.strip()
    if not limpo:
        return None
    try:
        dt = date.fromisoformat(limpo)
    except ValueError as exc:
        raise ValueError("Data de nascimento deve estar no formato YYYY-MM-DD.") from exc
    if dt.year < 1900:
        raise ValueError("Data de nascimento inválida: ano anterior a 1900.")
    if dt > date.today():
        raise ValueError("Data de nascimento não pode ser uma data futura.")
    return dt.isoformat()


def normalizar_e_validar_login(valor: str) -> str:
    """Normaliza login (3..255 caracteres), proíbe espaços internos e aplica lowercase em e-mail."""
    limpo = limpar_texto_obrigatorio(valor, 3, 255, "Login")
    if re.search(r"\s", limpo):
        raise ValueError("Login não pode conter espaços internos.")
    return limpo.lower() if "@" in limpo else limpo


class _AlunoCamposBase(BaseModel):
    """Campos cadastrais compartilhados entre criação e atualização de aluno."""

    nome: str
    cpf: str
    email: str
    telefone: Optional[str] = None
    data_nascimento: Optional[str] = None
    curso_id: Optional[int] = None
    login: str

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        return limpar_texto_obrigatorio(valor, 3, 120, "Nome")

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        return normalizar_e_validar_cpf(valor)

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: str) -> str:
        return normalizar_e_validar_email(valor)

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, valor: Optional[str]) -> Optional[str]:
        return normalizar_e_validar_telefone(valor)

    @field_validator("data_nascimento")
    @classmethod
    def validar_data_nascimento(cls, valor: Optional[str]) -> Optional[str]:
        return normalizar_e_validar_data_nascimento(valor)

    @field_validator("curso_id")
    @classmethod
    def validar_curso_id(cls, valor: Optional[int]) -> Optional[int]:
        if valor is not None and valor <= 0:
            raise ValueError("Identificador do curso deve ser um inteiro positivo.")
        return valor

    @field_validator("login")
    @classmethod
    def validar_login(cls, valor: str) -> str:
        return normalizar_e_validar_login(valor)


class AlunoCreate(_AlunoCamposBase):
    """Payload de entrada para cadastro conjunto de aluno e conta de acesso discente."""

    matricula: Optional[int] = None
    senha_inicial: str = Field(..., min_length=8, max_length=128)

    @field_validator("matricula")
    @classmethod
    def validar_matricula(cls, valor: Optional[int]) -> Optional[int]:
        if valor is not None and valor <= 0:
            raise ValueError("Número de matrícula deve ser um inteiro positivo.")
        return valor

    @field_validator("senha_inicial")
    @classmethod
    def validar_senha_inicial(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("A senha inicial não pode ser composta apenas por espaços.")
        return valor


class AlunoUpdate(_AlunoCamposBase):
    """Payload de entrada para atualização cadastral e acadêmica do aluno."""

    status_academico: StatusAcademicoEnum = StatusAcademicoEnum.ATIVO


class AlunoStatusUpdate(BaseModel):
    """Payload de entrada para ativar ou inativar a conta de acesso do aluno."""

    ativo: bool


class AlunoResponse(BaseModel):
    """Representação pública e segura do aluno cadastrado sem exposição de senha."""

    model_config = ConfigDict(from_attributes=True)

    matricula: int
    usuario_id: int
    nome: str
    cpf: str
    email: str
    telefone: Optional[str] = None
    data_nascimento: Optional[str] = None
    curso_id: Optional[int] = None
    curso_nome: Optional[str] = None
    status_academico: StatusAcademicoEnum
    ira: float
    login: str
    perfil_id: int
    perfil: str
    ativo: bool
    senha_provisoria: bool
    criado_em: Optional[str] = None


class AuditoriaEventoResponse(BaseModel):
    """Evento registrado na trilha de auditoria do módulo de alunos."""

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
