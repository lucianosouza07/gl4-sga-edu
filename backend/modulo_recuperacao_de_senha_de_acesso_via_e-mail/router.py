"""Rotas e ponto de entrada da API FastAPI para recuperação de senhas."""

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

try:
    from .schemas import (
        ErroResponse,
        RedefinirSenhaRequest,
        RedefinirSenhaResponse,
        SolicitarRecuperacaoRequest,
        SolicitarRecuperacaoResponse,
        ValidarTokenResponse,
    )
    from .service import PasswordRecoveryService
    from .email_service import EmailServiceInterface, get_email_service
    from .audit_service import extrair_ip_cliente, registrar_evento_auditoria
    from .rate_limiter import solicitacao_rate_limiter
except (ImportError, ValueError):
    from schemas import (
        ErroResponse,
        RedefinirSenhaRequest,
        RedefinirSenhaResponse,
        SolicitarRecuperacaoRequest,
        SolicitarRecuperacaoResponse,
        ValidarTokenResponse,
    )
    from service import PasswordRecoveryService
    from email_service import EmailServiceInterface, get_email_service
    from audit_service import extrair_ip_cliente, registrar_evento_auditoria
    from rate_limiter import solicitacao_rate_limiter


router = APIRouter(prefix="/api/v1/auth/recuperar-senha", tags=["Recuperação de Senha"])


@router.post(
    "/solicitar",
    response_model=SolicitarRecuperacaoResponse,
    status_code=status.HTTP_200_OK,
    responses={
        429: {"model": ErroResponse, "description": "Taxa de requisições excedida"},
    },
)
def solicitar_recuperacao(
    payload: SolicitarRecuperacaoRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    email_service: EmailServiceInterface = Depends(get_email_service),
):
    ip = extrair_ip_cliente(request)
    chave_limite = f"{ip}:{payload.email}"

    if not solicitacao_rate_limiter.is_allowed(chave_limite):
        registrar_evento_auditoria(
            request=request,
            acao="RATE_LIMIT_EXCEDIDO",
            status_resultado="BLOQUEADO",
            detalhes=f"Limite de requisições excedido para {payload.email}",
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas solicitações recentes. Por favor, aguarde alguns instantes antes de tentar novamente.",
        )

    # Processamento assíncrono em background task para retorno imediato
    def tarefa_despacho():
        sucesso, user_id = PasswordRecoveryService.processar_solicitacao(
            email=payload.email,
            ip_solicitacao=ip,
            email_service=email_service,
        )
        registrar_evento_auditoria(
            request=request,
            acao="SOLICITACAO_RECUPERACAO",
            status_resultado="SUCESSO",
            usuario_id=user_id,
            detalhes=f"Solicitação processada para e-mail {payload.email}",
        )

    background_tasks.add_task(tarefa_despacho)
    return SolicitarRecuperacaoResponse()


@router.get(
    "/validar-token",
    response_model=ValidarTokenResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErroResponse, "description": "Token inválido ou expirado"}},
)
def validar_token(
    request: Request,
    token: str = Query(..., min_length=32, description="Token recebido via link de e-mail"),
):
    valido, mensagem, token_reg = PasswordRecoveryService.validar_token(token)
    user_id = token_reg.usuario_id if token_reg else None

    if not valido:
        registrar_evento_auditoria(
            request=request,
            acao="VALIDACAO_TOKEN",
            status_resultado="FALHA",
            usuario_id=user_id,
            detalhes="Tentativa com token inválido, expirado ou revogado",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=mensagem)

    registrar_evento_auditoria(
        request=request,
        acao="VALIDACAO_TOKEN",
        status_resultado="SUCESSO",
        usuario_id=user_id,
        detalhes="Token validado com sucesso",
    )
    return ValidarTokenResponse(valido=True, mensagem=mensagem)


@router.post(
    "/redefinir",
    response_model=RedefinirSenhaResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErroResponse, "description": "Falha na validação do token ou política de senha"},
    },
)
def redefinir_senha(
    payload: RedefinirSenhaRequest,
    request: Request,
):
    ip = extrair_ip_cliente(request)
    sucesso, mensagem, user_id = PasswordRecoveryService.redefinir_senha(
        token_bruto=payload.token,
        nova_senha=payload.nova_senha,
        ip_utilizacao=ip,
    )

    if not sucesso:
        registrar_evento_auditoria(
            request=request,
            acao="REDEFINICAO_SENHA",
            status_resultado="FALHA",
            usuario_id=user_id,
            detalhes=mensagem,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=mensagem)

    registrar_evento_auditoria(
        request=request,
        acao="REDEFINICAO_SENHA",
        status_resultado="SUCESSO",
        usuario_id=user_id,
        detalhes="Senha redefinida com sucesso e sessões revogadas",
    )
    return RedefinirSenhaResponse(sucesso=True, mensagem=mensagem)


# Inicialização da aplicação FastAPI modular
app = FastAPI(
    title="SGA-EDU - Módulo de Recuperação de Senha",
    description="Endpoints REST para autoatendimento de redefinição de senhas de acesso via e-mail.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
