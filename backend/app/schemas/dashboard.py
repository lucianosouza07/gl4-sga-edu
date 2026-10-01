import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


PeriodoDashboard = Literal["3", "6", "ano"]


class PeriodoDashboardResponse(BaseModel):
    chave: PeriodoDashboard
    inicio: date
    fim: date


class TotaisDashboard(BaseModel):
    alunos: int
    ativos: int
    inativos: int
    novas_matriculas: int


class MatriculasPorMes(BaseModel):
    mes: str
    total: int
    parcial: bool


class AlunosPorStatus(BaseModel):
    status: str
    total: int


class CadastroRecente(BaseModel):
    id: uuid.UUID
    nome_completo: str
    matricula: str
    status: str
    criado_em: datetime


class DashboardResponse(BaseModel):
    gerado_em: datetime
    ano: int
    semestre: int
    periodo: PeriodoDashboardResponse
    totais: TotaisDashboard
    matriculas_por_mes: list[MatriculasPorMes]
    alunos_por_status: list[AlunosPorStatus]
    ultimos_cadastros: list[CadastroRecente]
