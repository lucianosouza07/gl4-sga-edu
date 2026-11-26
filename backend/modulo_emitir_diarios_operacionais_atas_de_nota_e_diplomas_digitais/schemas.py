"""Schemas Pydantic v2, enums de domínio e validadores do módulo SGA-25."""

from datetime import date
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PERFIL_SECRETARIA_ID = 3
PERFIL_ADMIN_ID = 5
PERFIS_OPERADORES_AUTORIZADOS: frozenset[int] = frozenset({PERFIL_SECRETARIA_ID, PERFIL_ADMIN_ID})

FREQUENCIA_MINIMA_PERCENTUAL = 75.0
MEDIA_MINIMA_APROVACAO_PADRAO = 6.0
FORMATO_ACERVO_PADRAO = "PDF_A_ASSINADO"
PRAZO_GUARDA_PADRAO = "PERMANENTE"


class TipoDocumentoEnum(str, Enum):
    """Tipos oficiais de documentos acadêmicos emitidos pelo módulo."""

    DIARIO_OPERACIONAL = "DIARIO_OPERACIONAL"
    ATA_NOTAS = "ATA_NOTAS"
    DIPLOMA_DIGITAL = "DIPLOMA_DIGITAL"


class PortariaMECEnum(str, Enum):
    """Portarias do Ministério da Educação para custódia do Acervo Acadêmico Digital."""

    PORTARIA_MEC_360_2022 = "PORTARIA_MEC_360_2022"
    PORTARIA_MEC_315_2018 = "PORTARIA_MEC_315_2018"


class StatusCustodiaEnum(str, Enum):
    """Estados de custódia e integridade no Acervo Acadêmico Digital MEC."""

    INTEGRO = "INTEGRO"
    REVOGADO = "REVOGADO"
    CORROMPIDO = "CORROMPIDO"


class SituacaoFinalTurmaEnum(str, Enum):
    """Situações finais de fechamento de discente em ata de notas finais."""

    APROVADO = "APROVADO"
    REPROVADO_NOTA = "REPROVADO_NOTA"
    REPROVADO_FALTA = "REPROVADO_FALTA"


def _normalizar_texto_opcional(valor: Optional[str], max_len: int, nome_campo: str) -> Optional[str]:
    if valor is None:
        return None
    limpo = valor.strip()
    if not limpo:
        return None
    if len(limpo) > max_len:
        raise ValueError(f"{nome_campo} deve conter no máximo {max_len} caracteres.")
    return limpo


class DiarioOperacionalEntrada(BaseModel):
    """Payload de entrada para emissão de Diário Operacional de turma."""

    model_config = ConfigDict(extra="forbid")

    turma_id: int = Field(..., gt=0, description="Identificador da turma ofertada.")
    portaria_referencia: PortariaMECEnum = Field(
        default=PortariaMECEnum.PORTARIA_MEC_360_2022,
        description="Portaria MEC de referência para custódia no acervo.",
    )
    observacoes: Optional[str] = Field(
        default=None,
        description="Observações institucionais opcionais (máximo 500 caracteres).",
    )

    @field_validator("observacoes")
    @classmethod
    def validar_observacoes(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto_opcional(valor, 500, "Observações")


class AtaNotasEntrada(BaseModel):
    """Payload de entrada para emissão de Ata de Notas Finais de turma."""

    model_config = ConfigDict(extra="forbid")

    turma_id: int = Field(..., gt=0, description="Identificador da turma ofertada.")
    media_minima_aprovacao: float = Field(
        default=MEDIA_MINIMA_APROVACAO_PADRAO,
        ge=0.0,
        le=10.0,
        description="Nota mínima na escala de 0.00 a 10.00 para aprovação.",
    )
    portaria_referencia: PortariaMECEnum = Field(
        default=PortariaMECEnum.PORTARIA_MEC_360_2022,
        description="Portaria MEC de referência para custódia no acervo.",
    )
    observacoes: Optional[str] = Field(
        default=None,
        description="Observações institucionais opcionais (máximo 500 caracteres).",
    )

    @field_validator("observacoes")
    @classmethod
    def validar_observacoes(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto_opcional(valor, 500, "Observações")


class DiplomaDigitalEntrada(BaseModel):
    """Payload de entrada para emissão de Diploma Digital de conclusão de curso."""

    model_config = ConfigDict(extra="forbid")

    aluno_matricula: int = Field(..., gt=0, description="Matrícula do estudante concluinte.")
    data_conclusao: date = Field(..., description="Data de conclusão do curso (YYYY-MM-DD).")
    data_colacao_grau: date = Field(..., description="Data de colação de grau (YYYY-MM-DD).")
    numero_registro: Optional[str] = Field(
        default=None,
        description="Número oficial de registro institucional (3 a 60 caracteres; autogerado se omitido).",
    )
    livro_registro: Optional[str] = Field(default=None, description="Livro de registro (até 60 caracteres).")
    folha_registro: Optional[str] = Field(default=None, description="Folha de registro (até 60 caracteres).")
    carga_horaria_integralizada: Optional[int] = Field(
        default=None,
        gt=0,
        description="Carga horária integralizada pelo estudante (padrão: carga horária total do curso).",
    )
    portaria_referencia: PortariaMECEnum = Field(
        default=PortariaMECEnum.PORTARIA_MEC_360_2022,
        description="Portaria MEC de referência para custódia no acervo.",
    )
    instituicao_terceira: bool = Field(
        default=False,
        description="Indica diploma de instituição terceira (fora do escopo da versão inicial).",
    )
    registrar_blockchain: bool = Field(
        default=False,
        description="Indica solicitação de registro em blockchain (fora do escopo da versão inicial).",
    )
    observacoes: Optional[str] = Field(
        default=None,
        description="Observações institucionais opcionais (máximo 500 caracteres).",
    )

    @field_validator("data_conclusao", "data_colacao_grau")
    @classmethod
    def validar_data_nao_futura(cls, valor: date) -> date:
        if valor > date.today():
            raise ValueError("Data de conclusão e data de colação de grau não podem ser futuras.")
        return valor

    @field_validator("numero_registro")
    @classmethod
    def validar_numero_registro(cls, valor: Optional[str]) -> Optional[str]:
        limpo = _normalizar_texto_opcional(valor, 60, "Número de registro")
        if limpo is not None and len(limpo) < 3:
            raise ValueError("Número de registro deve conter entre 3 e 60 caracteres.")
        return limpo

    @field_validator("livro_registro")
    @classmethod
    def validar_livro_registro(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto_opcional(valor, 60, "Livro de registro")

    @field_validator("folha_registro")
    @classmethod
    def validar_folha_registro(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto_opcional(valor, 60, "Folha de registro")

    @field_validator("observacoes")
    @classmethod
    def validar_observacoes(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto_opcional(valor, 500, "Observações")

    @model_validator(mode="after")
    def validar_ordem_datas(self) -> "DiplomaDigitalEntrada":
        if self.data_colacao_grau < self.data_conclusao:
            raise ValueError("A data de colação de grau não pode ser anterior à data de conclusão.")
        return self


class RevogacaoDocumentoEntrada(BaseModel):
    """Payload de entrada para revogação/invalidação formal de documento emitido."""

    model_config = ConfigDict(extra="forbid")

    motivo: str = Field(..., description="Justificativa obrigatória da revogação (5 a 500 caracteres).")

    @field_validator("motivo")
    @classmethod
    def validar_motivo(cls, valor: str) -> str:
        limpo = valor.strip()
        if len(limpo) < 5 or len(limpo) > 500:
            raise ValueError("O motivo da revogação deve conter entre 5 e 500 caracteres úteis.")
        return limpo


class AcervoDigitalMECResposta(BaseModel):
    """Metadados regulatórios de custódia 1:1 no Acervo Acadêmico Digital MEC."""

    id_acervo: int
    documento_id: int
    portaria_referencia: str
    formato_arquivo: str
    assinatura_icp_brasil: str
    carimbo_tempo: str
    prazo_guarda: str
    status_custodia: str


class DocumentoAcademicoResposta(BaseModel):
    """Representação completa do documento acadêmico emitido e sua custódia MEC."""

    id_documento: int
    tipo_documento: str
    aluno_matricula: Optional[int] = None
    turma_id: Optional[int] = None
    curso_id: Optional[int] = None
    numero_registro: Optional[str] = None
    codigo_verificacao: str
    hash_sha256: str
    url_validacao_qrcode: str
    emitido_em: str
    emitido_por_usuario_id: Optional[int] = None
    valido: bool
    motivo_revogacao: Optional[str] = None
    revogado_em: Optional[str] = None
    conteudo: dict[str, Any]
    acervo_mec: AcervoDigitalMECResposta


class DocumentoAcademicoResumo(BaseModel):
    """Representação resumida para listagem administrativa de documentos."""

    id_documento: int
    tipo_documento: str
    aluno_matricula: Optional[int] = None
    turma_id: Optional[int] = None
    curso_id: Optional[int] = None
    numero_registro: Optional[str] = None
    codigo_verificacao: str
    hash_sha256: str
    url_validacao_qrcode: str
    emitido_em: str
    emitido_por_usuario_id: Optional[int] = None
    valido: bool
    motivo_revogacao: Optional[str] = None
    revogado_em: Optional[str] = None
    portaria_referencia: str
    prazo_guarda: str
    status_custodia: str


class CustodiaPublicaResumo(BaseModel):
    """Metadados públicos essenciais da custódia regulatória MEC."""

    portaria_referencia: str
    formato_arquivo: str
    carimbo_tempo: str
    prazo_guarda: str
    status_custodia: str


class ValidacaoPublicaResposta(BaseModel):
    """Resposta minimizada (LGPD) para consulta pública via código verificador ou QR Code."""

    autentico: bool
    status_validacao: str
    codigo_verificacao: str
    tipo_documento: str
    emitido_em: str
    hash_sha256: str
    resumo_publico: dict[str, Any]
    custodia_mec: CustodiaPublicaResumo
    motivo_revogacao: Optional[str] = None
    revogado_em: Optional[str] = None


class VerificacaoIntegridadeResposta(BaseModel):
    """Resultado da conferência criptográfica de integridade no Acervo Digital MEC."""

    id_documento: int
    codigo_verificacao: str
    integro: bool
    hash_armazenado: str
    hash_recalculado: str
    assinatura_valida: bool
    status_custodia: str
    verificado_em: str


class EventoAuditoriaResposta(BaseModel):
    """Evento registrado na trilha de auditoria institucional (LogAuditoriaSistema)."""

    id_auditoria: int
    usuario_id: Optional[int] = None
    entidade_afetada: str
    id_registro_afetado: Optional[str] = None
    acao: str
    dados_anteriores: Optional[str] = None
    dados_novos: Optional[str] = None
    ip_origem: str
    data_hora: str
