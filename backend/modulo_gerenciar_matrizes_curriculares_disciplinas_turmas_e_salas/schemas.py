import re
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class StatusMatriz(str, Enum):
    em_elaboracao = "em_elaboracao"
    vigente = "vigente"
    encerrada = "encerrada"


class TipoDependencia(str, Enum):
    pre_requisito = "pre_requisito"
    correquisito = "correquisito"


class TipoSala(str, Enum):
    teorica = "teorica"
    laboratorio_informatica = "laboratorio_informatica"
    laboratorio_especifico = "laboratorio_especifico"
    auditorio = "auditorio"


class StatusSala(str, Enum):
    disponivel = "disponivel"
    manutencao = "manutencao"
    inativa = "inativa"


class TurnoTurma(str, Enum):
    matutino = "matutino"
    vespertino = "vespertino"
    noturno = "noturno"
    integral = "integral"


class StatusTurma(str, Enum):
    planejada = "planejada"
    aberta = "aberta"
    em_andamento = "em_andamento"
    concluida = "concluida"
    cancelada = "cancelada"


class DiaSemana(str, Enum):
    segunda = "segunda"
    terca = "terca"
    quarta = "quarta"
    quinta = "quinta"
    sexta = "sexta"
    sabado = "sabado"


# ---------------------------------------------------------------------------
# Schemas: Matrizes Curriculares e Disciplinas (US1)
# ---------------------------------------------------------------------------

class MatrizEntrada(BaseModel):
    codigo: str = Field(min_length=3, max_length=20)
    curso: str = Field(min_length=3, max_length=120)
    vigencia_ano: int = Field(ge=2000)
    vigencia_semestre: int = Field(ge=1, le=2)
    carga_horaria_total: int = Field(ge=0)
    status: StatusMatriz = StatusMatriz.em_elaboracao

    @field_validator("codigo", "curso")
    @classmethod
    def normalizar_strings(cls, v: str) -> str:
        return v.strip()


class Matriz(MatrizEntrada):
    id: int


class DisciplinaEntrada(BaseModel):
    codigo: str = Field(min_length=2, max_length=20)
    nome: str = Field(min_length=3, max_length=120)
    periodo_recomendado: int = Field(ge=1)
    carga_horaria_teorica: int = Field(ge=0)
    carga_horaria_pratica: int = Field(ge=0)
    creditos: int = Field(ge=1)
    ementa: Optional[str] = ""

    @field_validator("codigo", "nome")
    @classmethod
    def normalizar_strings(cls, v: str) -> str:
        return v.strip()


class Disciplina(DisciplinaEntrada):
    id: int
    matriz_id: int
    carga_horaria_total: int
    status: str = "ativa"


# ---------------------------------------------------------------------------
# Schemas: Dependências Curriculares (US2)
# ---------------------------------------------------------------------------

class DependenciaEntrada(BaseModel):
    disciplina_id: int
    disciplina_requisito_id: int
    tipo: TipoDependencia = TipoDependencia.pre_requisito

    @model_validator(mode="after")
    def validar_nao_auto_dependente(self):
        if self.disciplina_id == self.disciplina_requisito_id:
            raise ValueError("Uma disciplina não pode ser dependente de si mesma.")
        return self


class Dependencia(DependenciaEntrada):
    id: int
    matriz_id: int


class MatrizDetalhe(Matriz):
    disciplinas: List[Disciplina] = []
    dependencias: List[Dependencia] = []


# ---------------------------------------------------------------------------
# Schemas: Salas e Espaços Físicos (US3)
# ---------------------------------------------------------------------------

class SalaEntrada(BaseModel):
    codigo: str = Field(min_length=2, max_length=20)
    bloco: str = Field(min_length=1, max_length=50)
    andar: int
    capacidade_maxima: int = Field(ge=1)
    tipo: TipoSala = TipoSala.teorica
    status: StatusSala = StatusSala.disponivel

    @field_validator("codigo", "bloco")
    @classmethod
    def normalizar_strings(cls, v: str) -> str:
        return v.strip()


class Sala(SalaEntrada):
    id: int


# ---------------------------------------------------------------------------
# Schemas: Turmas e Alocações de Horário (US4)
# ---------------------------------------------------------------------------

class TurmaEntrada(BaseModel):
    codigo: str = Field(min_length=3, max_length=30)
    disciplina_id: int
    periodo_letivo: str = Field(min_length=4, max_length=10)
    turno: TurnoTurma = TurnoTurma.matutino
    vagas_ofertadas: int = Field(ge=1)
    professor_id: Optional[int] = None
    status: StatusTurma = StatusTurma.planejada

    @field_validator("codigo", "periodo_letivo")
    @classmethod
    def normalizar_strings(cls, v: str) -> str:
        return v.strip()


class Turma(TurmaEntrada):
    id: int


class AlocacaoEntrada(BaseModel):
    sala_id: int
    dia_semana: DiaSemana
    horario_inicio: str
    horario_fim: str

    @field_validator("horario_inicio", "horario_fim")
    @classmethod
    def validar_formato_hora(cls, v: str) -> str:
        v = v.strip()
        if not re.fullmatch(r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", v):
            raise ValueError("Horário deve estar no formato HH:MM (ex: 08:00, 19:30).")
        return v

    @model_validator(mode="after")
    def validar_ordem_horarios(self):
        if self.horario_inicio >= self.horario_fim:
            raise ValueError("horario_inicio deve ser anterior a horario_fim.")
        return self


class Alocacao(AlocacaoEntrada):
    id: int
    turma_id: int


class TurmaDetalhe(Turma):
    alocacoes: List[Alocacao] = []


class OcupacaoSala(BaseModel):
    sala: Sala
    periodo_letivo: str
    alocacoes: List[Alocacao] = []
