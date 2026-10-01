from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.models.aluno import Aluno, StatusAluno
from app.schemas.dashboard import (
    AlunosPorStatus, CadastroRecente, DashboardResponse, MatriculasPorMes,
    PeriodoDashboard, PeriodoDashboardResponse, TotaisDashboard,
)


FUSO_INSTITUICAO = ZoneInfo("America/Bahia")


def _utc(instante: datetime) -> datetime:
    # Os DateTime legados sem fuso são persistidos em UTC.
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=timezone.utc)
    return instante.astimezone(timezone.utc)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def obter_dashboard(
        self, periodo: PeriodoDashboard = "ano", *, agora: datetime | None = None,
    ) -> DashboardResponse:
        agora_utc = _utc(agora or datetime.now(timezone.utc))
        agora_local = agora_utc.astimezone(FUSO_INSTITUICAO)
        quantidade_meses = agora_local.month if periodo == "ano" else int(periodo)
        indice_atual = agora_local.year * 12 + agora_local.month - 1
        inicios = []
        for indice in range(indice_atual - quantidade_meses + 1, indice_atual + 2):
            ano, mes = divmod(indice, 12)
            inicios.append(datetime(ano, mes + 1, 1, tzinfo=FUSO_INSTITUICAO))

        agora_banco = agora_utc.replace(tzinfo=None)
        contagens_mensais = [
            func.sum(case((and_(
                Aluno.criado_em >= _utc(inicio).replace(tzinfo=None),
                Aluno.criado_em < _utc(fim).replace(tzinfo=None),
                Aluno.criado_em <= agora_banco,
            ), 1), else_=0))
            for inicio, fim in zip(inicios, inicios[1:])
        ]
        # COUNT e CASE agrupados por status são portáveis entre SQLite/PostgreSQL.
        # Totais e série vêm da mesma consulta, sem materializar a lista de alunos.
        grupos = self.db.query(
            Aluno.status, func.count(Aluno.id), *contagens_mensais,
        ).group_by(Aluno.status).order_by(Aluno.status).all()
        por_status = {grupo[0]: grupo[1] for grupo in grupos}
        serie = [
            MatriculasPorMes(
                mes=inicio.strftime("%Y-%m"),
                total=sum(grupo[indice + 2] for grupo in grupos),
                parcial=indice == quantidade_meses - 1,
            )
            for indice, inicio in enumerate(inicios[:-1])
        ]
        recentes = self.db.query(
            Aluno.id, Aluno.nome_completo, Aluno.matricula, Aluno.status, Aluno.criado_em,
        ).order_by(Aluno.criado_em.desc(), Aluno.id.desc()).limit(4).all()

        return DashboardResponse(
            gerado_em=agora_utc,
            ano=agora_local.year,
            semestre=1 if agora_local.month <= 6 else 2,
            periodo=PeriodoDashboardResponse(
                chave=periodo, inicio=inicios[0].date(), fim=agora_local.date(),
            ),
            totais=TotaisDashboard(
                alunos=sum(por_status.values()),
                ativos=por_status.get(StatusAluno.ATIVO.value, 0),
                inativos=por_status.get(StatusAluno.INATIVO.value, 0),
                novas_matriculas=sum(mes.total for mes in serie),
            ),
            matriculas_por_mes=serie,
            alunos_por_status=[
                AlunosPorStatus(status=status, total=total)
                for status, total in por_status.items()
            ],
            ultimos_cadastros=[
                CadastroRecente(
                    id=aluno.id, nome_completo=aluno.nome_completo,
                    matricula=aluno.matricula, status=aluno.status,
                    criado_em=_utc(aluno.criado_em),
                )
                for aluno in recentes
            ],
        )
