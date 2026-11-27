"""Schemas Pydantic v2, enums de domínio e constantes normativas do módulo SGA-27."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

PERFIL_SECRETARIA_ID = 3
PERFIL_ADMIN_ID = 5
PERFIS_OPERADORES_AUTORIZADOS: frozenset[int] = frozenset({PERFIL_SECRETARIA_ID, PERFIL_ADMIN_ID})

LIMIAR_FREQUENCIA_RISCO = 75.0
LIMIAR_IRA_RISCO = 6.0
STATUS_EVASAO: frozenset[str] = frozenset({"TRANCADO", "TRANSFERIDO", "CANCELADO", "JUBILADO"})
TIPOS_MOVIMENTACAO_EVASAO: tuple[str, ...] = ("TRANCAMENTO", "TRANSFERENCIA", "CANCELAMENTO", "JUBILAMENTO")


class TipoConflitoEnum(str, Enum):
    """Tipos de conflito detectados na oferta de turmas."""

    CHOQUE_SALA = "CHOQUE_SALA"
    CHOQUE_DOCENTE = "CHOQUE_DOCENTE"


class StatusRequerimentoEnum(str, Enum):
    """Situações possíveis de um requerimento acadêmico."""

    ABERTO = "ABERTO"
    EM_ANALISE = "EM_ANALISE"
    DEFERIDO = "DEFERIDO"
    INDEFERIDO = "INDEFERIDO"


class StatusDespachoEnum(str, Enum):
    """Situações de destino permitidas no despacho administrativo da coordenação."""

    EM_ANALISE = "EM_ANALISE"
    DEFERIDO = "DEFERIDO"
    INDEFERIDO = "INDEFERIDO"


# ---------------------------------------------------------------------------
# US1: KPIs e Evasão / Alertas de Risco
# ---------------------------------------------------------------------------


class PainelResumoResposta(BaseModel):
    """Indicadores gerenciais consolidados do painel da coordenação."""

    curso_id: Optional[int] = None
    curso_nome: Optional[str] = None
    periodo_letivo_id: Optional[int] = None
    periodo_letivo_codigo: Optional[str] = None
    processos_abertos: int
    matriculas_ativas_turmas: int
    trancamentos_deferidos: int
    movimentacoes_evasao_deferidas: int
    docentes_ativos_alocados: int
    total_turmas_ofertadas: int
    total_alunos_vinculados: int
    total_alunos_ativos: int
    taxa_ocupacao_media_percentual: float
    ira_medio_ativos: float
    taxa_evasao_percentual: float


class MovimentacoesPorTipoResumo(BaseModel):
    """Quantitativo de movimentações acadêmicas deferidas por categoria."""

    TRANCAMENTO: int = 0
    TRANSFERENCIA: int = 0
    CANCELAMENTO: int = 0
    JUBILAMENTO: int = 0


class AlertaRiscoAcademicoItem(BaseModel):
    """Alerta de risco acadêmico minimizado conforme LGPD (sem CPF, e-mail ou telefone)."""

    matricula: int
    nome: str
    curso_nome: Optional[str] = None
    ira: float
    menor_frequencia_percentual: Optional[float] = None
    motivos_alerta: list[str]


class RelatorioEvasaoResposta(BaseModel):
    """Relatório consolidado de evasão e estudantes em alerta de risco acadêmico."""

    curso_id: Optional[int] = None
    periodo_letivo_id: Optional[int] = None
    total_alunos_vinculados: int
    alunos_em_evasao_unicos: int
    taxa_evasao_percentual: float
    movimentacoes_por_tipo: MovimentacoesPorTipoResumo
    total_alertas_risco: int
    alertas_risco: list[AlertaRiscoAcademicoItem]


# ---------------------------------------------------------------------------
# US2: Oferta de Turmas e Diagnóstico de Conflitos
# ---------------------------------------------------------------------------


class HorarioTurmaItem(BaseModel):
    """Faixa horária semanal alocada a uma turma."""

    dia_semana: int
    hora_inicio: str
    hora_fim: str


class OfertaTurmaItemResposta(BaseModel):
    """Representação gerencial de uma turma ofertada com ocupação e pendências."""

    id_turma: int
    codigo_turma: str
    disciplina_codigo: str
    disciplina_nome: str
    carga_horaria: int
    curso_nome: str
    periodo_letivo_codigo: str
    turno: str
    status_turma: str
    professor_id: Optional[int] = None
    professor_nome: Optional[str] = None
    sala_id: Optional[int] = None
    codigo_sala: Optional[str] = None
    vagas_totais: int
    vagas_ocupadas: int
    taxa_ocupacao_percentual: float
    horarios: list[HorarioTurmaItem]
    pendencias: list[str]


class ConflitoAlocacaoItem(BaseModel):
    """Conflito de sobreposição de sala ou docente detectado entre duas turmas."""

    tipo_conflito: TipoConflitoEnum
    dia_semana: int
    intervalo_conflitante: str
    recurso_id: int
    recurso_descricao: str
    turma_a_id: int
    turma_a_codigo: str
    turma_b_id: int
    turma_b_codigo: str


class PendenciaOfertaTurmaItem(BaseModel):
    """Turma ativa que apresenta pendências operacionais de planejamento."""

    id_turma: int
    codigo_turma: str
    disciplina_nome: str
    pendencias: list[str]


class DiagnosticoConflitosOfertaResposta(BaseModel):
    """Diagnóstico completo de choques de horário/sala e pendências de um período letivo."""

    periodo_letivo_id: int
    periodo_letivo_codigo: str
    curso_id: Optional[int] = None
    total_conflitos: int
    total_choques_sala: int
    total_choques_docente: int
    conflitos: list[ConflitoAlocacaoItem]
    turmas_com_pendencias: list[PendenciaOfertaTurmaItem]


# ---------------------------------------------------------------------------
# US3: Requerimentos, Despachos e Alocação do Corpo Docente
# ---------------------------------------------------------------------------


class DespachoRequerimentoEntrada(BaseModel):
    """Payload de entrada para registro de parecer e despacho em requerimento acadêmico."""

    model_config = ConfigDict(extra="forbid")

    novo_status: StatusDespachoEnum = Field(..., description="Nova situação: EM_ANALISE, DEFERIDO ou INDEFERIDO.")
    parecer: str = Field(..., description="Parecer justificativo obrigatório (5 a 1000 caracteres úteis).")

    @field_validator("parecer")
    @classmethod
    def validar_parecer(cls, valor: str) -> str:
        limpo = valor.strip()
        if len(limpo) < 5 or len(limpo) > 1000:
            raise ValueError("O parecer deve conter entre 5 e 1000 caracteres úteis.")
        return limpo


class RequerimentoCoordenacaoResposta(BaseModel):
    """Representação de requerimento acadêmico minimizada conforme LGPD."""

    id_requerimento: int
    protocolo: str
    aluno_matricula: int
    aluno_nome: str
    curso_id: Optional[int] = None
    curso_nome: Optional[str] = None
    periodo_letivo_id: Optional[int] = None
    periodo_letivo_codigo: Optional[str] = None
    tipo_requerimento: str
    descricao: str
    status_requerimento: str
    parecer_secretaria: Optional[str] = None
    aberto_em: str
    atualizado_em: Optional[str] = None


class AlocacaoDocenteResposta(BaseModel):
    """Visão consolidada de alocação de docente minimizada conforme LGPD."""

    professor_id: int
    nome: str
    titulacao: str
    departamento: str
    area_atuacao: Optional[str] = None
    total_turmas: int
    carga_horaria_total: int
    total_alunos_atendidos: int


# ---------------------------------------------------------------------------
# US4: Auditoria LGPD
# ---------------------------------------------------------------------------


class EventoAuditoriaResposta(BaseModel):
    """Evento imutável da trilha de auditoria do painel da coordenação."""

    id_auditoria: int
    usuario_id: Optional[int] = None
    entidade_afetada: str
    id_registro_afetado: Optional[str] = None
    acao: str
    dados_anteriores: Optional[str] = None
    dados_novos: Optional[str] = None
    ip_origem: str
    data_hora: str
