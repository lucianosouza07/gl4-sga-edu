"""Serviço de auditoria e conformidade LGPD para MFA e governança RBAC."""

import json
from typing import Any, Mapping, Optional
from fastapi import Request

CAMPOS_SENSIVEIS = frozenset({
    "senha",
    "senha_inicial",
    "senha_hash",
    "password",
    "token",
    "token_sessao",
    "tokenmfa",
    "secret",
    "segredo",
    "codigo",
    "challenge_token",
    "backup_codes",
})


def extrair_ip_cliente(request: Optional[Request]) -> str:
    """Extrai o endereço IP do solicitante considerando proxies reversos."""
    if request is None:
        return "127.0.0.1"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client and request.client.host else "127.0.0.1"


def _sanitizar_valor(valor: Any) -> Any:
    if isinstance(valor, Mapping):
        return {
            str(chave): _sanitizar_valor(item)
            for chave, item in valor.items()
            if str(chave).lower() not in CAMPOS_SENSIVEIS
        }
    if isinstance(valor, list):
        return [_sanitizar_valor(item) for item in valor]
    return valor


def sanitizar_snapshot(dados: Optional[Mapping[str, Any]]) -> Optional[str]:
    """Remove campos sensíveis e credenciais, serializando o snapshot em JSON ordenado."""
    if dados is None:
        return None
    limpo = _sanitizar_valor(dados)
    return json.dumps(limpo, ensure_ascii=False, sort_keys=True)


def registrar_evento_auditoria(
    repo: Any,
    acao: str,
    usuario_id: Optional[int],
    id_registro_afetado: Optional[int | str],
    entidade_afetada: str = "Usuario",
    dados_anteriores: Optional[Mapping[str, Any]] = None,
    dados_novos: Optional[Mapping[str, Any]] = None,
    request: Optional[Request] = None,
    ip_origem: Optional[str] = None,
) -> dict[str, Any]:
    """Grava de forma imutável e higienizada um evento na trilha de auditoria."""
    ip_final = ip_origem or extrair_ip_cliente(request)
    snapshot_ant = sanitizar_snapshot(dados_anteriores)
    snapshot_nov = sanitizar_snapshot(dados_novos)

    return repo.registrar_auditoria(
        usuario_id=usuario_id,
        entidade_afetada=entidade_afetada,
        id_registro_afetado=str(id_registro_afetado) if id_registro_afetado is not None else None,
        acao=acao,
        dados_anteriores=snapshot_ant,
        dados_novos=snapshot_nov,
        ip_origem=ip_final,
    )
