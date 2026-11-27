"""Endpoints REST FastAPI para o painel administrativo da coordenação (SGA-27)."""

from typing import Optional
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status

try:
    from .audit_service import extrair_ip_origem
    from .repository import PainelCoordenacaoRepository, get_repository
    from .schemas import (
        AlocacaoDocenteResposta,
        DespachoRequerimentoEntrada,
        DiagnosticoConflitosOfertaResposta,
        EventoAuditoriaResposta,
        OfertaTurmaItemResposta,
        PainelResumoResposta,
        RelatorioEvasaoResposta,
        RequerimentoCoordenacaoResposta,
        StatusRequerimentoEnum,
    )
    from .security import OperadorAutenticado, require_secretaria_ou_admin
    from .service import PainelCoordenacaoService
except ImportError:
    from audit_service import extrair_ip_origem
    from repository import PainelCoordenacaoRepository, get_repository
    from schemas import (
        AlocacaoDocenteResposta,
        DespachoRequerimentoEntrada,
        DiagnosticoConflitosOfertaResposta,
        EventoAuditoriaResposta,
        OfertaTurmaItemResposta,
        PainelResumoResposta,
        RelatorioEvasaoResposta,
        RequerimentoCoordenacaoResposta,
        StatusRequerimentoEnum,
    )
    from security import OperadorAutenticado, require_secretaria_ou_admin
    from service import PainelCoordenacaoService

router = APIRouter(
    prefix="/api/coordenacao",
    tags=["Painel Administrativo para Coordenação (SGA-27)"],
)


def get_service(repo: PainelCoordenacaoRepository = Depends(get_repository)) -> PainelCoordenacaoService:
    return PainelCoordenacaoService(repo)


# ---------------------------------------------------------------------------
# US1: Painel de KPIs e Relatório de Evasão
# ---------------------------------------------------------------------------


@router.get(
    "/painel/resumo",
    response_model=PainelResumoResposta,
    status_code=status.HTTP_200_OK,
)
def obter_resumo_painel(
    curso_id: Optional[int] = Query(default=None, gt=0),
    periodo_letivo_id: Optional[int] = Query(default=None, gt=0),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: PainelCoordenacaoService = Depends(get_service),
) -> PainelResumoResposta:
    return PainelResumoResposta(
        **service.obter_resumo_painel(curso_id=curso_id, periodo_letivo_id=periodo_letivo_id)
    )


@router.get(
    "/relatorios/evasao",
    response_model=RelatorioEvasaoResposta,
    status_code=status.HTTP_200_OK,
)
def obter_relatorio_evasao(
    curso_id: Optional[int] = Query(default=None, gt=0),
    periodo_letivo_id: Optional[int] = Query(default=None, gt=0),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: PainelCoordenacaoService = Depends(get_service),
) -> RelatorioEvasaoResposta:
    return RelatorioEvasaoResposta(
        **service.obter_relatorio_evasao(curso_id=curso_id, periodo_letivo_id=periodo_letivo_id)
    )


# ---------------------------------------------------------------------------
# US2: Oferta de Turmas e Diagnóstico de Conflitos
# ---------------------------------------------------------------------------


@router.get(
    "/oferta/turmas",
    response_model=list[OfertaTurmaItemResposta],
    status_code=status.HTTP_200_OK,
)
def listar_oferta_turmas(
    periodo_letivo_id: Optional[int] = Query(default=None, gt=0),
    curso_id: Optional[int] = Query(default=None, gt=0),
    turno: Optional[str] = Query(default=None),
    status_turma: Optional[str] = Query(default=None),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: PainelCoordenacaoService = Depends(get_service),
) -> list[OfertaTurmaItemResposta]:
    itens = service.listar_oferta_turmas(
        periodo_letivo_id=periodo_letivo_id,
        curso_id=curso_id,
        turno=turno,
        status_turma=status_turma,
    )
    return [OfertaTurmaItemResposta(**item) for item in itens]


@router.get(
    "/oferta/conflitos",
    response_model=DiagnosticoConflitosOfertaResposta,
    status_code=status.HTTP_200_OK,
)
def diagnosticar_conflitos_oferta(
    periodo_letivo_id: int = Query(..., gt=0),
    curso_id: Optional[int] = Query(default=None, gt=0),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: PainelCoordenacaoService = Depends(get_service),
) -> DiagnosticoConflitosOfertaResposta:
    return DiagnosticoConflitosOfertaResposta(
        **service.diagnosticar_conflitos_oferta(
            periodo_letivo_id=periodo_letivo_id, curso_id=curso_id
        )
    )


# ---------------------------------------------------------------------------
# US3: Central de Requerimentos e Corpo Docente
# ---------------------------------------------------------------------------


@router.get(
    "/requerimentos",
    response_model=list[RequerimentoCoordenacaoResposta],
    status_code=status.HTTP_200_OK,
)
def listar_requerimentos(
    curso_id: Optional[int] = Query(default=None, gt=0),
    periodo_letivo_id: Optional[int] = Query(default=None, gt=0),
    tipo_requerimento: Optional[str] = Query(default=None),
    aluno_matricula: Optional[int] = Query(default=None, gt=0),
    status_requerimento: Optional[StatusRequerimentoEnum] = Query(default=None),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: PainelCoordenacaoService = Depends(get_service),
) -> list[RequerimentoCoordenacaoResposta]:
    itens = service.listar_requerimentos(
        curso_id=curso_id,
        periodo_letivo_id=periodo_letivo_id,
        tipo_requerimento=tipo_requerimento,
        aluno_matricula=aluno_matricula,
        status_requerimento=status_requerimento.value if status_requerimento else None,
    )
    return [RequerimentoCoordenacaoResposta(**item) for item in itens]


@router.get(
    "/requerimentos/{id_requerimento}",
    response_model=RequerimentoCoordenacaoResposta,
    status_code=status.HTTP_200_OK,
)
def obter_requerimento(
    id_requerimento: int,
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: PainelCoordenacaoService = Depends(get_service),
) -> RequerimentoCoordenacaoResposta:
    return RequerimentoCoordenacaoResposta(**service.obter_requerimento(id_requerimento))


@router.patch(
    "/requerimentos/{id_requerimento}/despachar",
    response_model=RequerimentoCoordenacaoResposta,
    status_code=status.HTTP_200_OK,
)
def despachar_requerimento(
    id_requerimento: int,
    entrada: DespachoRequerimentoEntrada,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: PainelCoordenacaoService = Depends(get_service),
) -> RequerimentoCoordenacaoResposta:
    resultado = service.despachar_requerimento(
        id_requerimento=id_requerimento,
        entrada=entrada,
        operador=operador,
        ip_origem=extrair_ip_origem(request),
    )
    return RequerimentoCoordenacaoResposta(**resultado)


@router.delete(
    "/requerimentos/{id_requerimento}",
    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
)
def bloquear_exclusao_requerimento(
    id_requerimento: int,
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
) -> None:
    """Impede exclusão física de requerimentos acadêmicos para preservação histórica."""
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail=(
            f"Exclusão física do requerimento {id_requerimento} é proibida para preservação "
            f"histórica institucional."
        ),
    )


@router.get(
    "/docentes/alocacao",
    response_model=list[AlocacaoDocenteResposta],
    status_code=status.HTTP_200_OK,
)
def listar_alocacao_docentes(
    departamento: Optional[str] = Query(default=None),
    curso_id: Optional[int] = Query(default=None, gt=0),
    periodo_letivo_id: Optional[int] = Query(default=None, gt=0),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: PainelCoordenacaoService = Depends(get_service),
) -> list[AlocacaoDocenteResposta]:
    itens = service.listar_alocacao_docentes(
        departamento=departamento,
        curso_id=curso_id,
        periodo_letivo_id=periodo_letivo_id,
    )
    return [AlocacaoDocenteResposta(**item) for item in itens]


# ---------------------------------------------------------------------------
# US4: Auditoria LGPD
# ---------------------------------------------------------------------------


@router.get(
    "/auditoria",
    response_model=list[EventoAuditoriaResposta],
    status_code=status.HTTP_200_OK,
)
def listar_auditoria(
    id_registro_afetado: Optional[str] = Query(default=None),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: PainelCoordenacaoService = Depends(get_service),
) -> list[EventoAuditoriaResposta]:
    eventos = service.listar_auditoria(id_registro_afetado=id_registro_afetado)
    return [EventoAuditoriaResposta(**ev) for ev in eventos]


app = FastAPI(
    title="SGA-Edu | Módulo Painel Administrativo para Coordenação (SGA-27)",
    version="1.0.0",
)
app.include_router(router)


@app.get("/")
def raiz() -> dict[str, str]:
    return {
        "status": "Módulo SGA-27 operacional",
        "prefixo": "/api/coordenacao",
        "docs": "/docs",
    }
