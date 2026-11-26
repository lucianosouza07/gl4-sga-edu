"""Serviço de sanitização LGPD para trilha de auditoria e extração de IP (SGA-25)."""

import json
from typing import Any, Optional
from fastapi import Request

CAMPOS_SENSIVEIS_LGPD: frozenset[str] = frozenset(
    {
        "cpf",
        "email",
        "telefone",
        "data_nascimento",
        "login",
        "senha",
        "senha_inicial",
        "senha_hash",
        "token",
        "tokenmfa",
        "token_mfa",
        "authorization",
    }
)


def extrair_ip_origem(request: Optional[Request]) -> str:
    """Extrai o endereço IP de origem da requisição respeitando X-Forwarded-For."""
    if request is None:
        return "127.0.0.1"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        primeiro_ip = forwarded.split(",")[0].strip()
        if primeiro_ip:
            return primeiro_ip[:45]
    if request.client and request.client.host:
        return str(request.client.host)[:45]
    return "127.0.0.1"


def _sanitizar_recursivo(objeto: Any) -> Any:
    if isinstance(objeto, dict):
        limpo: dict[str, Any] = {}
        for chave, valor in objeto.items():
            if str(chave).lower() in CAMPOS_SENSIVEIS_LGPD:
                continue
            limpo[chave] = _sanitizar_recursivo(valor)
        return limpo
    if isinstance(objeto, list):
        return [_sanitizar_recursivo(item) for item in objeto]
    return objeto


def sanitizar_snapshot_documento(dados: dict[str, Any]) -> dict[str, Any]:
    """Remove recursivamente dados pessoais sensíveis e credenciais antes de gravar auditoria."""
    resultado = _sanitizar_recursivo(dados)
    assert isinstance(resultado, dict)
    return resultado


def serializar_snapshot_auditoria(dados: Optional[dict[str, Any]]) -> Optional[str]:
    """Serializa snapshot higienizado para armazenamento em LogAuditoriaSistema."""
    if dados is None:
        return None
    higienizado = sanitizar_snapshot_documento(dados)
    return json.dumps(higienizado, ensure_ascii=False, sort_keys=True)
