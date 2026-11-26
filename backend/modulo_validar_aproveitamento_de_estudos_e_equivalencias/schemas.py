"""Schemas Pydantic v2, enums de domínio e validadores do módulo SGA-26."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PERFIL_SECRETARIA_ID = 3
PERFIL_ADMIN_ID = 5
PERFIS_OPERADORES_AUTORIZADOS: frozenset[int] = frozenset({PERFIL_SECRETARIA_ID, PERFIL_ADMIN_ID})

NOTA_MINIMA_APROVACAO = 6.0
PERCENTUAL_MINIMO_CARGA_HORARIA = 75.0


class ModalidadeAproveitamentoEnum(str, Enum):
    """Modalidades oficiais de aproveitamento de estudos."""

    EQUIVALENCIA_INTERNA = "EQUIVALENCIA_INTERNA"
    ESTUDOS_EXTERNOS = "ESTUDOS_EXTERNOS"


class StatusSolicitacaoEnum(str, Enum):
    """Estados de tramitação de um protocolo de aproveitamento de estudos."""

    EM_ANALISE = "EM_ANALISE"
    DEFERIDO = "DEFERIDO"
    INDEFERIDO = "INDEFERIDO"


class DecisaoDeliberacaoEnum(str, Enum):
    """Decisões possíveis no ato de deliberação formal."""

    DEFERIDO = "DEFERIDO"
    INDEFERIDO = "INDEFERIDO"


class OrigemAtendimentoPreRequisitoEnum(str, Enum):
    """Origem do cumprimento de um pré-requisito curricular pelo estudante."""

    APROVADO_TURMA = "APROVADO_TURMA"
    DISPENSA_APROVEITAMENTO = "DISPENSA_APROVEITAMENTO"
    PENDENTE = "PENDENTE"


def _normalizar_texto_opcional(valor: Optional[str], max_len: int, nome_campo: str) -> Optional[str]:
    if valor is None:
        return None
    limpo = valor.strip()
    if not limpo:
        return None
    if len(limpo) > max_len:
        raise ValueError(f"{nome_campo} deve conter no máximo {max_len} caracteres.")
    return limpo


# ---------------------------------------------------------------------------
# US1: Equivalências de Disciplinas
# ---------------------------------------------------------------------------


class EquivalenciaEntrada(BaseModel):
    """Payload para cadastro de nova regra direcional de equivalência entre disciplinas."""

    model_config = ConfigDict(extra="forbid")

    disciplina_origem_id: int = Field(..., gt=0, description="ID da disciplina cursada na origem.")
    disciplina_equivalente_id: int = Field(..., gt=0, description="ID da disciplina equivalente/alvo.")
    portaria_aprovacao: Optional[str] = Field(
        default=None,
        description="Portaria institucional de aprovação (máximo 60 caracteres).",
    )

    @field_validator("portaria_aprovacao")
    @classmethod
    def validar_portaria(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto_opcional(valor, 60, "Portaria de aprovação")

    @model_validator(mode="after")
    def validar_nao_auto_equivalente(self) -> "EquivalenciaEntrada":
        if self.disciplina_origem_id == self.disciplina_equivalente_id:
            raise ValueError("Uma disciplina não pode ser cadastrada como equivalente a si mesma.")
        return self


class EquivalenciaAtualizacao(BaseModel):
    """Payload para atualização de portaria institucional e/ou status de vigência."""

    model_config = ConfigDict(extra="forbid")

    portaria_aprovacao: Optional[str] = Field(
        default=None,
        description="Nova portaria institucional (máximo 60 caracteres).",
    )
    ativa: Optional[bool] = Field(
        default=None,
        description="Define se a regra de equivalência está vigente.",
    )

    @field_validator("portaria_aprovacao")
    @classmethod
    def validar_portaria(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto_opcional(valor, 60, "Portaria de aprovação")

    @model_validator(mode="after")
    def validar_ao_menos_um_campo(self) -> "EquivalenciaAtualizacao":
        if self.portaria_aprovacao is None and self.ativa is None:
            raise ValueError("Informe ao menos um campo para atualização (portaria_aprovacao ou ativa).")
        return self


class EquivalenciaResposta(BaseModel):
    """Representação completa de uma regra de equivalência entre disciplinas."""

    id_equivalencia: int
    disciplina_origem_id: int
    disciplina_origem_codigo: str
    disciplina_origem_nome: str
    disciplina_origem_carga_horaria: int
    disciplina_equivalente_id: int
    disciplina_equivalente_codigo: str
    disciplina_equivalente_nome: str
    disciplina_equivalente_carga_horaria: int
    portaria_aprovacao: Optional[str] = None
    ativa: bool


# ---------------------------------------------------------------------------
# US2: Protocolos e Pré-Validação de Aproveitamento
# ---------------------------------------------------------------------------


class SolicitacaoAproveitamentoEntrada(BaseModel):
    """Payload para abertura de protocolo de aproveitamento (interno ou externo)."""

    model_config = ConfigDict(extra="forbid")

    aluno_matricula: int = Field(..., gt=0, description="Matrícula do estudante.")
    disciplina_alvo_id: int = Field(..., gt=0, description="ID da disciplina alvo na matriz.")
    modalidade: ModalidadeAproveitamentoEnum = Field(..., description="Modalidade do aproveitamento.")

    # Modalidade EQUIVALENCIA_INTERNA
    disciplina_origem_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="ID da disciplina interna cursada (obrigatório em EQUIVALENCIA_INTERNA).",
    )

    # Modalidade ESTUDOS_EXTERNOS
    instituicao_origem: Optional[str] = Field(
        default=None,
        description="Nome da instituição externa de origem (máximo 150 caracteres).",
    )
    disciplina_externa_nome: Optional[str] = Field(
        default=None,
        description="Nome da disciplina cursada externamente (máximo 150 caracteres).",
    )
    carga_horaria_cursada: Optional[int] = Field(
        default=None,
        gt=0,
        description="Carga horária cursada (obrigatória em ESTUDOS_EXTERNOS).",
    )
    nota_obtida: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Nota obtida na escala de 0.00 a 10.00 (obrigatória em ESTUDOS_EXTERNOS).",
    )
    ementa_resumo: Optional[str] = Field(
        default=None,
        description="Resumo da ementa cursada (obrigatório em ESTUDOS_EXTERNOS, 10 a 2000 chars).",
    )
    documentacao_comprobatoria: Optional[str] = Field(
        default=None,
        description="Referência da documentação comprobatória (máximo 255 caracteres).",
    )

    @field_validator("instituicao_origem")
    @classmethod
    def validar_instituicao(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto_opcional(valor, 150, "Instituição de origem")

    @field_validator("disciplina_externa_nome")
    @classmethod
    def validar_disciplina_externa(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto_opcional(valor, 150, "Nome da disciplina externa")

    @field_validator("ementa_resumo")
    @classmethod
    def validar_ementa(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto_opcional(valor, 2000, "Resumo da ementa")

    @field_validator("documentacao_comprobatoria")
    @classmethod
    def validar_doc(cls, valor: Optional[str]) -> Optional[str]:
        return _normalizar_texto_opcional(valor, 255, "Documentação comprobatória")

    @model_validator(mode="after")
    def validar_campos_por_modalidade(self) -> "SolicitacaoAproveitamentoEntrada":
        if self.modalidade == ModalidadeAproveitamentoEnum.EQUIVALENCIA_INTERNA:
            if self.disciplina_origem_id is None:
                raise ValueError("disciplina_origem_id é obrigatório na modalidade EQUIVALENCIA_INTERNA.")
            if self.disciplina_origem_id == self.disciplina_alvo_id:
                raise ValueError("A disciplina de origem não pode ser igual à disciplina alvo.")
        else:
            faltantes: list[str] = []
            if not self.instituicao_origem:
                faltantes.append("instituicao_origem")
            if not self.disciplina_externa_nome:
                faltantes.append("disciplina_externa_nome")
            if self.carga_horaria_cursada is None:
                faltantes.append("carga_horaria_cursada")
            if self.nota_obtida is None:
                faltantes.append("nota_obtida")
            if not self.ementa_resumo or len(self.ementa_resumo) < 10:
                faltantes.append("ementa_resumo (mínimo 10 caracteres)")
            if faltantes:
                raise ValueError(
                    f"Campos obrigatórios ausentes ou inválidos para ESTUDOS_EXTERNOS: {', '.join(faltantes)}."
                )
        return self


class DiagnosticoPreValidacao(BaseModel):
    """Diagnóstico objetivo de pré-validação de elegibilidade acadêmica."""

    elegivel: bool
    nota_aprovada: bool
    carga_horaria_compativel: bool
    percentual_carga_horaria: float
    equivalencia_ativa_encontrada: Optional[bool] = None
    aprovacao_interna_comprovada: Optional[bool] = None
    pendencias: list[str] = Field(default_factory=list)


class SolicitacaoAproveitamentoResposta(BaseModel):
    """Representação completa de um protocolo de aproveitamento de estudos."""

    id_solicitacao: int
    protocolo: str
    aluno_matricula: int
    aluno_nome: str
    disciplina_alvo_id: int
    disciplina_alvo_codigo: str
    disciplina_alvo_nome: str
    disciplina_alvo_carga_horaria: int
    modalidade: str
    disciplina_origem_id: Optional[int] = None
    disciplina_origem_codigo: Optional[str] = None
    disciplina_origem_nome: Optional[str] = None
    equivalencia_id: Optional[int] = None
    instituicao_origem: Optional[str] = None
    disciplina_externa_nome: Optional[str] = None
    carga_horaria_cursada: int
    nota_obtida: float
    ementa_resumo: Optional[str] = None
    documentacao_comprobatoria: Optional[str] = None
    pre_validacao: DiagnosticoPreValidacao
    status_solicitacao: str
    parecer_tecnico: Optional[str] = None
    aberto_por_usuario_id: Optional[int] = None
    deliberado_por_usuario_id: Optional[int] = None
    aberto_em: str
    deliberado_em: Optional[str] = None


# ---------------------------------------------------------------------------
# US3: Deliberação, Dispensas e Pré-Requisitos
# ---------------------------------------------------------------------------


class DeliberacaoAproveitamentoEntrada(BaseModel):
    """Payload para deliberação formal (deferimento ou indeferimento) com parecer obrigatório."""

    model_config = ConfigDict(extra="forbid")

    decisao: DecisaoDeliberacaoEnum = Field(..., description="Decisão final: DEFERIDO ou INDEFERIDO.")
    parecer_tecnico: str = Field(..., description="Parecer técnico justificativo (5 a 1000 caracteres úteis).")

    @field_validator("parecer_tecnico")
    @classmethod
    def validar_parecer(cls, valor: str) -> str:
        limpo = valor.strip()
        if len(limpo) < 5 or len(limpo) > 1000:
            raise ValueError("O parecer técnico deve conter entre 5 e 1000 caracteres úteis.")
        return limpo


class DispensaDisciplinaResposta(BaseModel):
    """Registro consolidado de dispensa de disciplina após deferimento."""

    id_dispensa: int
    aluno_matricula: int
    disciplina_id: int
    disciplina_codigo: str
    disciplina_nome: str
    solicitacao_id: int
    protocolo: str
    modalidade: str
    nota_aproveitada: float
    carga_horaria_aproveitada: int
    reconhecido_em: str


class DeliberacaoResposta(BaseModel):
    """Retorno unificado da deliberação (protocolo atualizado + dispensa se deferido)."""

    solicitacao: SolicitacaoAproveitamentoResposta
    dispensa: Optional[DispensaDisciplinaResposta] = None


class ResumoDispensasAlunoResposta(BaseModel):
    """Visão consolidada das disciplinas aproveitadas/dispensadas de um estudante."""

    aluno_matricula: int
    aluno_nome: str
    total_disciplinas_dispensadas: int
    carga_horaria_total_aproveitada: int
    dispensas: list[DispensaDisciplinaResposta]


class ItemPreRequisitoStatus(BaseModel):
    """Situação individual de cumprimento de um pré-requisito curricular."""

    requisito_disciplina_id: int
    codigo: str
    nome: str
    atendido: bool
    origem_atendimento: OrigemAtendimentoPreRequisitoEnum


class VerificacaoPreRequisitosResposta(BaseModel):
    """Resultado consolidado de atendimento de pré-requisitos considerando aprovações e dispensas."""

    aluno_matricula: int
    disciplina_id: int
    disciplina_codigo: str
    disciplina_nome: str
    apto_para_matricula: bool
    requisitos: list[ItemPreRequisitoStatus]


# ---------------------------------------------------------------------------
# US4: Auditoria LGPD
# ---------------------------------------------------------------------------


class EventoAuditoriaResposta(BaseModel):
    """Evento imutável registrado na trilha de auditoria institucional."""

    id_auditoria: int
    usuario_id: Optional[int] = None
    entidade_afetada: str
    id_registro_afetado: Optional[str] = None
    acao: str
    dados_anteriores: Optional[str] = None
    dados_novos: Optional[str] = None
    ip_origem: str
    data_hora: str
