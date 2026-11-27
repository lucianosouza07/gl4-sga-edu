"""Tokens Bearer HMAC-SHA256 e guardião RBAC Secretaria/Admin para o módulo SGA-27."""

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    from .repository import PainelCoordenacaoRepository, get_repository
    from .schemas import PERFIS_OPERADORES_AUTORIZADOS
except ImportError:
    from repository import PainelCoordenacaoRepository, get_repository
    from schemas import PERFIS_OPERADORES_AUTORIZADOS

_EPHEMERAL_SECRET = secrets.token_hex(32)
_bearer_scheme = HTTPBearer(auto_error=False)


def _obter_segredo_sessao() -> bytes:
    segredo = os.getenv("SGA_SESSION_SECRET") or _EPHEMERAL_SECRET
    return segredo.encode("utf-8")


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(texto: str) -> bytes:
    padding = "=" * (-len(texto) % 4)
    return base64.urlsafe_b64decode((texto + padding).encode("ascii"))


def criar_token_sessao(usuario_id: int, perfil_id: int, ttl_segundos: int = 3600) -> str:
    """Emite token Bearer assinado via HMAC-SHA256 com validade explícita."""
    payload = {
        "uid": int(usuario_id),
        "pid": int(perfil_id),
        "exp": int(time.time()) + ttl_segundos,
    }
    corpo = _b64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    assinatura = hmac.new(_obter_segredo_sessao(), corpo.encode("ascii"), hashlib.sha256).digest()
    return f"{corpo}.{_b64url_encode(assinatura)}"


def decodificar_token_sessao(token: str) -> Optional[dict[str, Any]]:
    """Valida assinatura HMAC-SHA256 e expiração do token, retornando o payload ou None."""
    try:
        corpo, assinatura_b64 = token.strip().split(".", 1)
        esperada = hmac.new(_obter_segredo_sessao(), corpo.encode("ascii"), hashlib.sha256).digest()
        recebida = _b64url_decode(assinatura_b64)
        if not hmac.compare_digest(esperada, recebida):
            return None
        payload = json.loads(_b64url_decode(corpo).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


@dataclass(frozen=True)
class OperadorAutenticado:
    """Operador verificado no momento da requisição administrativa."""

    usuario_id: int
    login: str
    perfil_id: int
    perfil_nome: str
    status_conta: int


def require_secretaria_ou_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    repo: PainelCoordenacaoRepository = Depends(get_repository),
) -> OperadorAutenticado:
    """Dependência FastAPI que exige sessão válida e perfil ativo de Secretaria ou Admin."""
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação obrigatória ou token inválido.",
        )

    payload = decodificar_token_sessao(credentials.credentials)
    if not payload or "uid" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação obrigatória ou token inválido.",
        )

    usuario = repo.buscar_usuario_por_id(int(payload["uid"]))
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação obrigatória ou token inválido.",
        )

    if int(usuario["statusCONTA"]) != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta de usuário inativa ou suspensa.",
        )

    if int(usuario["perfil_RBAC"]) not in PERFIS_OPERADORES_AUTORIZADOS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito aos perfis Secretaria e Admin.",
        )

    return OperadorAutenticado(
        usuario_id=int(usuario["id_usuario"]),
        login=str(usuario["login"]),
        perfil_id=int(usuario["perfil_RBAC"]),
        perfil_nome=str(usuario["nome_perfil"]),
        status_conta=int(usuario["statusCONTA"]),
    )
