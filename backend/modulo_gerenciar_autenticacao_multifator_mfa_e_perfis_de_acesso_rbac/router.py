"""Endpoints FastAPI para MFA (setup, ativação, status, desafio) e governança RBAC."""

from typing import Any, Optional
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .repository import MfaRbacRepository
from .schemas import (
    AuditoriaItemResponse,
    MfaActivateRequest,
    MfaActivateResponse,
    MfaAdminResetResponse,
    MfaChallengeRequest,
    MfaChallengeResponse,
    MfaDeactivateRequest,
    MfaSetupResponse,
    MfaStatusResponse,
    PerfilResponse,
    SimpleMessageResponse,
    UsuarioPerfilUpdateRequest,
    UsuarioRbacResponse,
)
from .security import (
    gerar_token_desafio_mfa,
    gerar_token_sessao,
    require_admin,
    require_authenticated_user,
    verificar_senha,
)
from .service import MfaRbacService

mfa_router = APIRouter(prefix="/api/mfa", tags=["MFA"])
auth_mfa_router = APIRouter(prefix="/api/auth", tags=["Autenticação e Desafio MFA"])
rbac_router = APIRouter(prefix="/api/rbac", tags=["Governança RBAC"])


def _obter_servico(request: Request) -> MfaRbacService:
    servico = getattr(request.app.state, "service", None)
    if servico is None:
        repo = getattr(request.app.state, "repo", None) or MfaRbacRepository()
        servico = MfaRbacService(repo)
        request.app.state.service = servico
    return servico


# --- Endpoints MFA (Titular) ---

@mfa_router.post(
    "/setup",
    response_model=MfaSetupResponse,
    summary="Iniciar configuração de MFA para a conta logada",
)
def iniciar_setup_mfa(
    request: Request,
    auth_user: dict[str, Any] = Depends(require_authenticated_user),
):
    service = _obter_servico(request)
    usuario_id = int(auth_user["sub"])
    return service.iniciar_setup_mfa(usuario_id=usuario_id, request=request)


@mfa_router.post(
    "/activate",
    response_model=MfaActivateResponse,
    summary="Confirmar primeiro código e ativar MFA",
)
def ativar_mfa(
    payload: MfaActivateRequest,
    request: Request,
    auth_user: dict[str, Any] = Depends(require_authenticated_user),
):
    service = _obter_servico(request)
    usuario_id = int(auth_user["sub"])
    return service.ativar_mfa(usuario_id=usuario_id, codigo=payload.codigo, request=request)


@mfa_router.get(
    "/status",
    response_model=MfaStatusResponse,
    summary="Consultar situação do MFA da conta",
)
def consultar_status_mfa(
    request: Request,
    auth_user: dict[str, Any] = Depends(require_authenticated_user),
):
    service = _obter_servico(request)
    usuario_id = int(auth_user["sub"])
    return service.consultar_status_mfa(usuario_id=usuario_id)


@mfa_router.post(
    "/deactivate",
    response_model=SimpleMessageResponse,
    summary="Desativar voluntariamente o MFA da conta",
)
def desativar_mfa(
    payload: MfaDeactivateRequest,
    request: Request,
    auth_user: dict[str, Any] = Depends(require_authenticated_user),
):
    service = _obter_servico(request)
    usuario_id = int(auth_user["sub"])
    return service.desativar_mfa_usuario(
        usuario_id=usuario_id,
        senha=payload.senha,
        codigo=payload.codigo,
        request=request,
    )


# --- Endpoints de Login e Desafio MFA ---

class LoginRequest(BaseModel):
    login: str
    senha: str


@auth_mfa_router.post(
    "/login",
    operation_id="login_com_desafio_mfa",
    summary="Login inicial com suporte a desafio MFA",
)
def login_com_desafio_mfa(payload: LoginRequest, request: Request):
    """Valida credenciais primárias; se MFA ativo emite challenge_token, senão emite token Bearer."""
    repo: MfaRbacRepository = getattr(request.app.state, "repo", None) or MfaRbacRepository()
    usuario = repo.buscar_usuario_por_login(payload.login)
    if not usuario or int(usuario.get("statusCONTA", 0)) != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou conta inativa.",
        )

    if not verificar_senha(payload.senha, str(usuario.get("senha_hash", ""))):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou conta inativa.",
        )

    usuario_id = int(usuario["id_usuario"])
    login_user = str(usuario["login"])
    perfil_id = int(usuario["perfil_RBAC"])

    if usuario.get("tokenMFA"):
        challenge_token = gerar_token_desafio_mfa(usuario_id=usuario_id, login=login_user, exp_segundos=300)
        return {
            "status": "mfa_required",
            "challenge_token": challenge_token,
            "mensagem": "Autenticação de segundo fator necessária.",
        }

    access_token = gerar_token_sessao(usuario_id=usuario_id, login=login_user, perfil_id=perfil_id)
    return {
        "status": "authenticated",
        "access_token": access_token,
        "token_type": "bearer",
        "perfil_RBAC": perfil_id,
        "usuario_id": usuario_id,
        "login": login_user,
    }


@auth_mfa_router.post(
    "/mfa/challenge",
    response_model=MfaChallengeResponse,
    summary="Responder ao desafio de segundo fator",
)
def responder_desafio_mfa(payload: MfaChallengeRequest, request: Request):
    service = _obter_servico(request)
    return service.processar_desafio_mfa(
        challenge_token=payload.challenge_token,
        codigo=payload.codigo,
        request=request,
    )


# --- Endpoints de Governança RBAC (Admin Apenas) ---

@rbac_router.get(
    "/perfis",
    response_model=list[PerfilResponse],
    summary="Listar catálogo institucional dos 5 perfis RBAC",
)
def listar_perfis(
    request: Request,
    _: dict[str, Any] = Depends(require_admin),
):
    service = _obter_servico(request)
    return service.listar_perfis()


@rbac_router.get(
    "/usuarios/{usuario_id}",
    response_model=UsuarioRbacResponse,
    summary="Consultar dados de perfil e situação de MFA de um usuário",
)
def consultar_usuario(
    usuario_id: int,
    request: Request,
    _: dict[str, Any] = Depends(require_admin),
):
    service = _obter_servico(request)
    return service.consultar_usuario_rbac(usuario_id=usuario_id)


@rbac_router.put(
    "/usuarios/{usuario_id}/perfil",
    response_model=UsuarioRbacResponse,
    summary="Alterar perfil de acesso de um usuário (com salvaguarda do último Admin)",
)
def alterar_perfil(
    usuario_id: int,
    payload: UsuarioPerfilUpdateRequest,
    request: Request,
    admin_auth: dict[str, Any] = Depends(require_admin),
):
    service = _obter_servico(request)
    admin_id = int(admin_auth["sub"])
    return service.alterar_perfil_usuario(
        usuario_id=usuario_id,
        novo_perfil_id=payload.novo_perfil_id,
        admin_executor_id=admin_id,
        request=request,
    )


@rbac_router.post(
    "/usuarios/{usuario_id}/mfa/reset",
    response_model=MfaAdminResetResponse,
    summary="Redefinição emergencial de MFA para usuário sem dispositivo",
)
def redefinir_mfa(
    usuario_id: int,
    request: Request,
    admin_auth: dict[str, Any] = Depends(require_admin),
):
    service = _obter_servico(request)
    admin_id = int(admin_auth["sub"])
    return service.redefinir_mfa_admin(
        usuario_id=usuario_id,
        admin_executor_id=admin_id,
        request=request,
    )


@rbac_router.get(
    "/auditoria",
    response_model=list[AuditoriaItemResponse],
    summary="Consultar trilha de auditoria para ações de MFA e RBAC",
)
def listar_auditoria(
    request: Request,
    usuario_id: Optional[int] = Query(None, description="Filtrar por autor"),
    acao: Optional[str] = Query(None, description="Filtrar por ação"),
    limite: int = Query(50, ge=1, le=200, description="Máximo de registros"),
    _: dict[str, Any] = Depends(require_admin),
):
    service = _obter_servico(request)
    return service.consultar_auditoria(usuario_id=usuario_id, acao=acao, limite=limite)


def criar_app(repo: Optional[MfaRbacRepository] = None) -> FastAPI:
    """Cria e configura aplicação FastAPI standalone com roteadores registrados."""
    app_instance = FastAPI(
        title="SGA-Edu - MFA & RBAC API",
        version="1.0.0",
        description="Módulo de Gerenciamento de MFA e Governança RBAC",
    )
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    repository = repo or MfaRbacRepository()
    app_instance.state.repo = repository
    app_instance.state.service = MfaRbacService(repository)

    app_instance.include_router(mfa_router)
    app_instance.include_router(auth_mfa_router)
    app_instance.include_router(rbac_router)

    return app_instance


app = criar_app()
