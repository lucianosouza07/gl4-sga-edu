"""Endpoints REST FastAPI para validação de aproveitamento de estudos e equivalências (SGA-26)."""

from typing import Optional
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status

try:
    from .audit_service import extrair_ip_origem
    from .repository import AproveitamentoRepository, get_repository
    from .schemas import (
        DeliberacaoAproveitamentoEntrada,
        DeliberacaoResposta,
        EquivalenciaAtualizacao,
        EquivalenciaEntrada,
        EquivalenciaResposta,
        EventoAuditoriaResposta,
        ModalidadeAproveitamentoEnum,
        ResumoDispensasAlunoResposta,
        SolicitacaoAproveitamentoEntrada,
        SolicitacaoAproveitamentoResposta,
        StatusSolicitacaoEnum,
        VerificacaoPreRequisitosResposta,
    )
    from .security import OperadorAutenticado, require_secretaria_ou_admin
    from .service import AproveitamentoService
except ImportError:
    from audit_service import extrair_ip_origem
    from repository import AproveitamentoRepository, get_repository
    from schemas import (
        DeliberacaoAproveitamentoEntrada,
        DeliberacaoResposta,
        EquivalenciaAtualizacao,
        EquivalenciaEntrada,
        EquivalenciaResposta,
        EventoAuditoriaResposta,
        ModalidadeAproveitamentoEnum,
        ResumoDispensasAlunoResposta,
        SolicitacaoAproveitamentoEntrada,
        SolicitacaoAproveitamentoResposta,
        StatusSolicitacaoEnum,
        VerificacaoPreRequisitosResposta,
    )
    from security import OperadorAutenticado, require_secretaria_ou_admin
    from service import AproveitamentoService

router = APIRouter(
    prefix="/api/aproveitamentos",
    tags=["Aproveitamento de Estudos e Equivalências (SGA-26)"],
)


def get_service(repo: AproveitamentoRepository = Depends(get_repository)) -> AproveitamentoService:
    return AproveitamentoService(repo)


# ---------------------------------------------------------------------------
# US1: Equivalências de Disciplinas
# ---------------------------------------------------------------------------


@router.post(
    "/equivalencias",
    response_model=EquivalenciaResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_equivalencia(
    entrada: EquivalenciaEntrada,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: AproveitamentoService = Depends(get_service),
) -> EquivalenciaResposta:
    resultado = service.criar_equivalencia(entrada, operador, extrair_ip_origem(request))
    return EquivalenciaResposta(**resultado)


@router.get(
    "/equivalencias",
    response_model=list[EquivalenciaResposta],
    status_code=status.HTTP_200_OK,
)
def listar_equivalencias(
    disciplina_origem_id: Optional[int] = Query(default=None, gt=0),
    disciplina_equivalente_id: Optional[int] = Query(default=None, gt=0),
    ativa: Optional[bool] = Query(default=None),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: AproveitamentoService = Depends(get_service),
) -> list[EquivalenciaResposta]:
    itens = service.listar_equivalencias(
        disciplina_origem_id=disciplina_origem_id,
        disciplina_equivalente_id=disciplina_equivalente_id,
        ativa=ativa,
    )
    return [EquivalenciaResposta(**item) for item in itens]


@router.get(
    "/equivalencias/{id_equivalencia}",
    response_model=EquivalenciaResposta,
    status_code=status.HTTP_200_OK,
)
def obter_equivalencia(
    id_equivalencia: int,
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: AproveitamentoService = Depends(get_service),
) -> EquivalenciaResposta:
    return EquivalenciaResposta(**service.obter_equivalencia(id_equivalencia))


@router.patch(
    "/equivalencias/{id_equivalencia}",
    response_model=EquivalenciaResposta,
    status_code=status.HTTP_200_OK,
)
def atualizar_equivalencia(
    id_equivalencia: int,
    entrada: EquivalenciaAtualizacao,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: AproveitamentoService = Depends(get_service),
) -> EquivalenciaResposta:
    resultado = service.atualizar_equivalencia(id_equivalencia, entrada, operador, extrair_ip_origem(request))
    return EquivalenciaResposta(**resultado)


# ---------------------------------------------------------------------------
# US2 & US3: Solicitações, Deliberação, Dispensas e Pré-Requisitos
# ---------------------------------------------------------------------------


@router.post(
    "/solicitacoes",
    response_model=SolicitacaoAproveitamentoResposta,
    status_code=status.HTTP_201_CREATED,
)
def abrir_solicitacao(
    entrada: SolicitacaoAproveitamentoEntrada,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: AproveitamentoService = Depends(get_service),
) -> SolicitacaoAproveitamentoResposta:
    resultado = service.abrir_solicitacao(entrada, operador, extrair_ip_origem(request))
    return SolicitacaoAproveitamentoResposta(**resultado)


@router.get(
    "/solicitacoes",
    response_model=list[SolicitacaoAproveitamentoResposta],
    status_code=status.HTTP_200_OK,
)
def listar_solicitacoes(
    aluno_matricula: Optional[int] = Query(default=None, gt=0),
    disciplina_alvo_id: Optional[int] = Query(default=None, gt=0),
    modalidade: Optional[ModalidadeAproveitamentoEnum] = Query(default=None),
    status_solicitacao: Optional[StatusSolicitacaoEnum] = Query(default=None),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: AproveitamentoService = Depends(get_service),
) -> list[SolicitacaoAproveitamentoResposta]:
    itens = service.listar_solicitacoes(
        aluno_matricula=aluno_matricula,
        disciplina_alvo_id=disciplina_alvo_id,
        modalidade=modalidade.value if modalidade else None,
        status_solicitacao=status_solicitacao.value if status_solicitacao else None,
    )
    return [SolicitacaoAproveitamentoResposta(**item) for item in itens]


@router.get(
    "/solicitacoes/{id_solicitacao}",
    response_model=SolicitacaoAproveitamentoResposta,
    status_code=status.HTTP_200_OK,
)
def obter_solicitacao(
    id_solicitacao: int,
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: AproveitamentoService = Depends(get_service),
) -> SolicitacaoAproveitamentoResposta:
    return SolicitacaoAproveitamentoResposta(**service.obter_solicitacao(id_solicitacao))


@router.patch(
    "/solicitacoes/{id_solicitacao}/deliberar",
    response_model=DeliberacaoResposta,
    status_code=status.HTTP_200_OK,
)
def deliberar_solicitacao(
    id_solicitacao: int,
    entrada: DeliberacaoAproveitamentoEntrada,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: AproveitamentoService = Depends(get_service),
) -> DeliberacaoResposta:
    resultado = service.deliberar_solicitacao(id_solicitacao, entrada, operador, extrair_ip_origem(request))
    return DeliberacaoResposta(**resultado)


@router.delete(
    "/solicitacoes/{id_solicitacao}",
    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
)
def bloquear_exclusao_solicitacao(
    id_solicitacao: int,
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
) -> None:
    """Impede exclusão física de protocolos e deliberações para preservação histórica."""
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail=(
            f"Exclusão física da solicitação {id_solicitacao} é proibida para preservação "
            f"histórica de deliberações e dispensas acadêmicas."
        ),
    )


@router.get(
    "/alunos/{aluno_matricula}/dispensas",
    response_model=ResumoDispensasAlunoResposta,
    status_code=status.HTTP_200_OK,
)
def listar_dispensas_aluno(
    aluno_matricula: int,
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: AproveitamentoService = Depends(get_service),
) -> ResumoDispensasAlunoResposta:
    return ResumoDispensasAlunoResposta(**service.listar_dispensas_aluno(aluno_matricula))


@router.get(
    "/alunos/{aluno_matricula}/disciplinas/{disciplina_id}/pre-requisitos",
    response_model=VerificacaoPreRequisitosResposta,
    status_code=status.HTTP_200_OK,
)
def verificar_pre_requisitos(
    aluno_matricula: int,
    disciplina_id: int,
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: AproveitamentoService = Depends(get_service),
) -> VerificacaoPreRequisitosResposta:
    return VerificacaoPreRequisitosResposta(
        **service.verificar_pre_requisitos_aluno(aluno_matricula, disciplina_id)
    )


# ---------------------------------------------------------------------------
# US4: Auditoria LGPD
# ---------------------------------------------------------------------------


@router.get(
    "/auditoria",
    response_model=list[EventoAuditoriaResposta],
    status_code=status.HTTP_200_OK,
)
def listar_auditoria(
    entidade_afetada: Optional[str] = Query(default=None),
    id_registro_afetado: Optional[str] = Query(default=None),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    service: AproveitamentoService = Depends(get_service),
) -> list[EventoAuditoriaResposta]:
    eventos = service.listar_auditoria(
        entidade_afetada=entidade_afetada,
        id_registro_afetado=id_registro_afetado,
    )
    return [EventoAuditoriaResposta(**ev) for ev in eventos]


app = FastAPI(
    title="SGA-Edu | Módulo Aproveitamento de Estudos e Equivalências (SGA-26)",
    version="1.0.0",
)
app.include_router(router)


@app.get("/")
def raiz() -> dict[str, str]:
    return {
        "status": "Módulo SGA-26 operacional",
        "prefixo": "/api/aproveitamentos",
        "docs": "/docs",
    }
