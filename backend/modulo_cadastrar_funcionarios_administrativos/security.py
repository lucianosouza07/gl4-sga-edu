"""Utilitários criptográficos, tokens de sessão Bearer e guardião RBAC Admin."""

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Optional
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    from .repository import FuncionarioAdminRepository, get_repository
    from .schemas import PERFIL_ADMIN_ID
except ImportError:
    from repository import FuncionarioAdminRepository, get_repository
    from schemas import PERFIL_ADMIN_ID

_EPHEMERAL_SECRET = secrets.token_hex(32)
_bearer_scheme = HTTPBearer(auto_error=False)


def _obter_segredo_sessao() -> bytes:
    segredo = os.getenv("SGA_SESSION_SECRET") or _EPHEMERAL_SECRET
    return segredo.encode("utf-8")


def _pre_hash_bcrypt(senha: str) -> bytes:
    """Normaliza senha via SHA-256 hex (64 bytes) para suportar até 128 chars no bcrypt 5.0."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest().encode("utf-8")


def hash_password(senha: str, rounds: int = 12) -> str:
    """Gera hash bcrypt seguro sem expor a senha em texto claro."""
    sal = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(_pre_hash_bcrypt(senha), sal).decode("utf-8")


def verify_password(senha_plana: str, senha_hash: str) -> bool:
    """Verifica senha em texto claro contra hash bcrypt."""
    try:
        return bcrypt.checkpw(_pre_hash_bcrypt(senha_plana), senha_hash.encode("utf-8"))
    except Exception:
        return False


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
    """Representa o operador verificado no momento da requisição."""

    usuario_id: int
    login: str
    perfil_id: int
    perfil_nome: str
    status_conta: int


def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    repo: FuncionarioAdminRepository = Depends(get_repository),
) -> OperadorAutenticado:
    """Dependência FastAPI que exige sessão válida e perfil estritamente Admin ativo."""
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

    if int(usuario["perfil_RBAC"]) != PERFIL_ADMIN_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao perfil Admin.",
        )

    return OperadorAutenticado(
        usuario_id=int(usuario["id_usuario"]),
        login=str(usuario["login"]),
        perfil_id=int(usuario["perfil_RBAC"]),
        perfil_nome=str(usuario["nome_perfil"]),
        status_conta=int(usuario["statusCONTA"]),
    )
