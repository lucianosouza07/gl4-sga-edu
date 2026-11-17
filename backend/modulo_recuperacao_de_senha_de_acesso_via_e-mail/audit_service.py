"""Serviço de registro de eventos de auditoria e conformidade LGPD."""

from typing import Optional
from fastapi import Request

try:
    from .models import Database, LogAuditoriaRecuperacao
except (ImportError, ValueError):
    from models import Database, LogAuditoriaRecuperacao


def extrair_ip_cliente(request: Request) -> str:
    """Extrai o IP real do cliente considerando headers de proxy reverso."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"


def extrair_user_agent(request: Request) -> Optional[str]:
    return request.headers.get("user-agent")


def registrar_evento_auditoria(
    request: Request,
    acao: str,
    status_resultado: str,
    usuario_id: Optional[int] = None,
    detalhes: Optional[str] = None,
) -> LogAuditoriaRecuperacao:
    """Registra uma ocorrência imutável na trilha de auditoria do sistema."""
    ip = extrair_ip_cliente(request)
    ua = extrair_user_agent(request)
    return Database.registrar_log(
        acao=acao,
        status_resultado=status_resultado,
        ip_origem=ip,
        usuario_id=usuario_id,
        user_agent=ua,
        detalhes=detalhes,
    )
