"""Roteadores FastAPI para Consentimento LGPD e Trilha de Auditoria."""

from typing import Any, Optional
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

from .audit_service import AuditService
from .repository import LgpdAuditRepository
from .schemas import (
    AceiteConsentimentoRequest,
    AceiteConsentimentoResponse,
    AuditoriaConsultaResponse,
    ConsentimentoItemResponse,
    ConsentimentoStatusResponse,
    LogAuditoriaItemResponse,
    RevogacaoConsentimentoRequest,
    RevogacaoConsentimentoResponse,
    TermoVigenteResponse,
)
from .security import extract_client_ip, require_admin, require_authenticated_user
from .service import ConsentimentoService

lgpd_router = APIRouter(prefix="/api/lgpd", tags=["LGPD e Consentimento"])
auditoria_router = APIRouter(prefix="/api/auditoria", tags=["Trilha de Auditoria"])


def _obter_repositorio(request: Request) -> LgpdAuditRepository:
    repo = getattr(request.app.state, "repo", None)
    if repo is None:
        repo = LgpdAuditRepository()
        request.app.state.repo = repo
    return repo


def _obter_audit_service(request: Request) -> AuditService:
    audit_service = getattr(request.app.state, "audit_service", None)
    if audit_service is None:
        repo = _obter_repositorio(request)
        audit_service = AuditService(repo)
        request.app.state.audit_service = audit_service
    return audit_service


def _obter_consentimento_service(request: Request) -> ConsentimentoService:
    service = getattr(request.app.state, "consentimento_service", None)
    if service is None:
        repo = _obter_repositorio(request)
        audit_service = _obter_audit_service(request)
        service = ConsentimentoService(repo, audit_service)
        request.app.state.consentimento_service = service
    return service


# ==============================================================================
# Endpoints LGPD e Consentimento
# ==============================================================================

@lgpd_router.get(
    "/termos/vigente",
    response_model=TermoVigenteResponse,
    summary="Consultar termos de privacidade e consentimento vigentes",
)
def obter_termo_vigente(request: Request):
    service = _obter_consentimento_service(request)
    return service.obter_termo_vigente()


@lgpd_router.get(
    "/consentimentos/status",
    response_model=ConsentimentoStatusResponse,
    summary="Consultar status de conformidade LGPD do usuário logado",
)
def consultar_status_consentimento(
    request: Request,
    auth_user: dict[str, Any] = Depends(require_authenticated_user),
):
    service = _obter_consentimento_service(request)
    usuario_id = int(auth_user["sub"])
    return service.consultar_status_usuario(usuario_id)


@lgpd_router.post(
    "/consentimentos/aceitar",
    response_model=AceiteConsentimentoResponse,
    summary="Registrar aceite formal do termo de consentimento",
)
def aceitar_consentimento(
    request: Request,
    body: AceiteConsentimentoRequest,
    auth_user: dict[str, Any] = Depends(require_authenticated_user),
):
    service = _obter_consentimento_service(request)
    usuario_id = int(auth_user["sub"])
    ip_origem = extract_client_ip(request)
    return service.aceitar_consentimento(usuario_id, body, ip_origem)


@lgpd_router.post(
    "/consentimentos/revogar",
    response_model=RevogacaoConsentimentoResponse,
    summary="Revogar consentimento para finalidade específica",
)
def revogar_consentimento(
    request: Request,
    body: RevogacaoConsentimentoRequest,
    auth_user: dict[str, Any] = Depends(require_authenticated_user),
):
    service = _obter_consentimento_service(request)
    usuario_id = int(auth_user["sub"])
    ip_origem = extract_client_ip(request)
    return service.revogar_consentimento(usuario_id, body, ip_origem)


@lgpd_router.get(
    "/consentimentos/historico",
    response_model=list[ConsentimentoItemResponse],
    summary="Consultar histórico de consentimentos do titular (Art. 18 LGPD)",
)
def listar_historico_consentimentos(
    request: Request,
    auth_user: dict[str, Any] = Depends(require_authenticated_user),
):
    service = _obter_consentimento_service(request)
    usuario_id = int(auth_user["sub"])
    return service.listar_historico_titular(usuario_id)


# ==============================================================================
# Endpoints Trilha de Auditoria (Admin)
# ==============================================================================

@auditoria_router.get(
    "",
    response_model=AuditoriaConsultaResponse,
    summary="Consultar trilha geral de auditoria com paginação e filtros",
)
def consultar_auditoria(
    request: Request,
    usuario_id: Optional[int] = Query(None),
    entidade_afetada: Optional[str] = Query(None),
    acao: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    limite: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin_user: dict[str, Any] = Depends(require_admin),
):
    audit_service = _obter_audit_service(request)
    total, itens = audit_service.consultar_auditoria(
        usuario_id=usuario_id,
        entidade_afetada=entidade_afetada,
        acao=acao,
        data_inicio=data_inicio,
        data_fim=data_fim,
        limite=limite,
        offset=offset,
    )
    return AuditoriaConsultaResponse(
        total=total,
        limite=limite,
        offset=offset,
        itens=itens,
    )


@auditoria_router.get(
    "/{id_auditoria}",
    response_model=LogAuditoriaItemResponse,
    summary="Detalhes de um registro específico de auditoria",
)
def detalhe_auditoria(
    id_auditoria: int,
    request: Request,
    admin_user: dict[str, Any] = Depends(require_admin),
):
    audit_service = _obter_audit_service(request)
    item = audit_service.buscar_detalhe_por_id(id_auditoria)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro de auditoria com id {id_auditoria} não encontrado.",
        )
    return item


# ==============================================================================
# Factory de Aplicação FastAPI
# ==============================================================================

def criar_app(repo: Optional[LgpdAuditRepository] = None) -> FastAPI:
    app = FastAPI(
        title="SGA-Edu | Consentimento LGPD & Auditoria",
        version="1.0.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    repositorio = repo or LgpdAuditRepository()
    audit_service = AuditService(repositorio)
    consentimento_service = ConsentimentoService(repositorio, audit_service)

    app.state.repo = repositorio
    app.state.audit_service = audit_service
    app.state.consentimento_service = consentimento_service

    app.include_router(lgpd_router)
    app.include_router(auditoria_router)

    return app
