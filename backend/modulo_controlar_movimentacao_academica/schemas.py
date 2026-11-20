from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class StatusDiscente(str, Enum):
    ATIVO = "ATIVO"
    TRANCADO = "TRANCADO"
    TRANSFERIDO = "TRANSFERIDO"
    CANCELADO = "CANCELADO"
    JUBILADO = "JUBILADO"


class TipoMovimentacao(str, Enum):
    TRANCAMENTO = "TRANCAMENTO"
    DESTRANCAMENTO = "DESTRANCAMENTO"
    TRANSFERENCIA_INTERNA = "TRANSFERENCIA_INTERNA"
    TRANSFERENCIA_EXTERNA_ENTRADA = "TRANSFERENCIA_EXTERNA_ENTRADA"
    TRANSFERENCIA_EXTERNA_SAIDA = "TRANSFERENCIA_EXTERNA_SAIDA"
    CANCELAMENTO_VOLUNTARIO = "CANCELAMENTO_VOLUNTARIO"
    CANCELAMENTO_COMPULSORIO = "CANCELAMENTO_COMPULSORIO"
    JUBILAMENTO = "JUBILAMENTO"


class StatusTramitacao(str, Enum):
    SOLICITADO = "SOLICITADO"
    EM_ANALISE = "EM_ANALISE"
    HOMOLOGADO = "HOMOLOGADO"
    INDEFERIDO = "INDEFERIDO"


class DiscenteCreate(BaseModel):
    matricula: str = Field(..., min_length=3, max_length=30)
    nome: str = Field(..., min_length=3, max_length=150)
    cpf: str = Field(..., min_length=11, max_length=14)
    curso_id: str = Field(..., min_length=2, max_length=50)
    nome_curso: str = Field(..., min_length=3, max_length=100)
    semestre_ingresso: str = Field(..., min_length=4, max_length=10)
    semestres_cursados: int = Field(default=0, ge=0)
    semestres_trancados: int = Field(default=0, ge=0)


class DiscenteResponse(BaseModel):
    id: str
    matricula: str
    nome: str
    cpf: str
    curso_id: str
    nome_curso: str
    semestre_ingresso: str
    status: StatusDiscente
    semestres_cursados: int
    semestres_trancados: int


class RegraCurso(BaseModel):
    curso_id: str
    nome_curso: str
    duracao_padrao_semestres: int = 8
    duracao_maxima_semestres: int = 14
    limite_semestres_trancamento: int = 4
    permite_trancamento_primeiro_semestre: bool = False
    vagas_transferencia_disponiveis: int = 10


class TrancamentoRequest(BaseModel):
    discente_id: str
    periodo_letivo: str = Field(..., min_length=4, max_length=10)
    justificativa: str = Field(..., min_length=5, max_length=500)
    operador_id: str = Field(..., min_length=2, max_length=50)
    excecao_motivo_medico: bool = False


class DestrancamentoRequest(BaseModel):
    discente_id: str
    periodo_letivo: str = Field(..., min_length=4, max_length=10)
    justificativa: str = Field(..., min_length=5, max_length=500)
    operador_id: str = Field(..., min_length=2, max_length=50)


class TransferenciaRequest(BaseModel):
    discente_id: str
    tipo_transferencia: TipoMovimentacao
    curso_destino_id: Optional[str] = None
    nome_curso_destino: Optional[str] = None
    instituicao_destino: Optional[str] = None
    periodo_letivo: str = Field(..., min_length=4, max_length=10)
    justificativa: str = Field(..., min_length=5, max_length=500)
    operador_id: str = Field(..., min_length=2, max_length=50)

    @field_validator("tipo_transferencia")
    @classmethod
    def validar_tipo_transferencia(cls, v: TipoMovimentacao) -> TipoMovimentacao:
        if v not in (TipoMovimentacao.TRANSFERENCIA_INTERNA, TipoMovimentacao.TRANSFERENCIA_EXTERNA_SAIDA):
            raise ValueError("O tipo de transferência deve ser TRANSFERENCIA_INTERNA ou TRANSFERENCIA_EXTERNA_SAIDA")
        return v


class CancelamentoRequest(BaseModel):
    discente_id: str
    tipo_cancelamento: TipoMovimentacao
    periodo_letivo: str = Field(..., min_length=4, max_length=10)
    justificativa: str = Field(..., min_length=5, max_length=500)
    operador_id: str = Field(..., min_length=2, max_length=50)

    @field_validator("tipo_cancelamento")
    @classmethod
    def validar_tipo_cancelamento(cls, v: TipoMovimentacao) -> TipoMovimentacao:
        if v not in (TipoMovimentacao.CANCELAMENTO_VOLUNTARIO, TipoMovimentacao.CANCELAMENTO_COMPULSORIO):
            raise ValueError("O tipo de cancelamento deve ser CANCELAMENTO_VOLUNTARIO ou CANCELAMENTO_COMPULSORIO")
        return v


class JubilamentoRequest(BaseModel):
    discente_id: str
    periodo_letivo: str = Field(..., min_length=4, max_length=10)
    justificativa: str = Field(..., min_length=5, max_length=500)
    operador_id: str = Field(..., min_length=2, max_length=50)


class MovimentacaoResponse(BaseModel):
    id: str
    discente_id: str
    tipo: TipoMovimentacao
    status_tramitacao: StatusTramitacao
    status_anterior: StatusDiscente
    status_novo: StatusDiscente
    periodo_letivo: str
    data_solicitacao: datetime
    data_homologacao: Optional[datetime] = None
    justificativa: str
    parecer: Optional[str] = None
    operador_id: str
    curso_origem_id: Optional[str] = None
    curso_destino_id: Optional[str] = None
    instituicao_externa: Optional[str] = None
    codigo_autenticidade: str


class CertidaoResponse(BaseModel):
    codigo_autenticidade: str
    data_emissao: datetime
    nome_discente: str
    matricula: str
    curso: str
    tipo_movimentacao: str
    periodo_letivo: str
    status_resultante: str
    texto_certidao: str


class InscricaoTurma(BaseModel):
    id: str
    discente_id: str
    turma_id: str
    periodo_letivo: str
    status: str = "ATIVA"
