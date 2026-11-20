"""Serviço de registro de auditoria e conformidade para Criptografia e Backups."""

from typing import Optional
from fastapi import Request

try:
    from .models import Database, LogAuditoriaBackup
except (ImportError, ValueError):
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.models import Database, LogAuditoriaBackup


def extrair_ip_cliente(request: Optional[Request] = None) -> str:
    """Extrai o endereço IP real do cliente considerando cabeçalhos de proxy reverso."""
    if request is None:
        return "127.0.0.1"

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


def registrar_auditoria(
    acao: str,
    status_resultado: str,
    operador: str = "SISTEMA",
    request: Optional[Request] = None,
    backup_id: Optional[int] = None,
    detalhes: Optional[str] = None,
) -> LogAuditoriaBackup:
    """Registra um evento estruturado de auditoria na base de governança."""
    ip_origem = extrair_ip_cliente(request)
    return Database.add_log(
        acao=acao,
        status_resultado=status_resultado,
        operador=operador,
        ip_origem=ip_origem,
        backup_id=backup_id,
        detalhes=detalhes,
    )
