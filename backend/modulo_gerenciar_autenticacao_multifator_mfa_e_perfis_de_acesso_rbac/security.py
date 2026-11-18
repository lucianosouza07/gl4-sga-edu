"""Utilitários de segurança, criptografia, tokens de sessão e desafio efêmero."""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Optional
import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SECRET_KEY: str = os.getenv("SGA_JWT_SECRET", "sga-edu-mfa-rbac-secret-key-2026")
bearer_scheme = HTTPBearer(auto_error=False)


def _pre_hash_senha(senha: str) -> bytes:
    """Aplica digest SHA-256 para normalizar senhas sem exceder limite de 72 bytes do bcrypt."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest().encode("ascii")


def hash_senha(senha: str) -> str:
    """Gera hash bcrypt com salt de 12 rounds."""
    digest = _pre_hash_senha(senha)
    return bcrypt.hashpw(digest, bcrypt.gensalt(rounds=12)).decode("ascii")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica senha contra o hash bcrypt."""
    try:
        digest = _pre_hash_senha(senha)
        return bcrypt.checkpw(digest, senha_hash.encode("ascii"))
    except Exception:
        return False


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    padding = (4 - len(s) % 4) % 4
    return base64.urlsafe_b64decode((s + "=" * padding).encode("ascii"))


def gerar_token_assinado(payload: dict[str, Any], exp_segundos: int = 86400) -> str:
    """Gera token JWT-compatível compacto assinado com HMAC-SHA256."""
    header = {"alg": "HS256", "typ": "JWT"}
    body = dict(payload)
    body["exp"] = int(time.time()) + exp_segundos
    body["iat"] = int(time.time())

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

    sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decodificar_token_assinado(token: str) -> dict[str, Any]:
    """Valida assinatura e expiração de token HMAC-SHA256, retornando o payload."""
    partes = token.strip().split(".")
    if len(partes) != 3:
        raise ValueError("Token com formato inválido.")

    header_b64, payload_b64, sig_b64 = partes
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    sig_esperada = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_fornecida = _b64url_decode(sig_b64)

    if not hmac.compare_digest(sig_esperada, sig_fornecida):
        raise ValueError("Assinatura do token inválida.")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("Token expirado.")

    return payload


def gerar_token_sessao(usuario_id: int, login: str, perfil_id: int, exp_segundos: int = 86400) -> str:
    """Gera token de sessão institucional Bearer."""
    return gerar_token_assinado(
        {
            "sub": usuario_id,
            "login": login,
            "perfil_RBAC": perfil_id,
            "tipo": "sessao",
        },
        exp_segundos=exp_segundos,
    )


def gerar_token_desafio_mfa(usuario_id: int, login: str, exp_segundos: int = 300) -> str:
    """Gera token temporário efêmero para resposta ao desafio de segundo fator (TTL 5 min)."""
    return gerar_token_assinado(
        {
            "sub": usuario_id,
            "login": login,
            "tipo": "desafio_mfa",
            "jti": base64.b16encode(os.urandom(8)).decode("ascii"),
        },
        exp_segundos=exp_segundos,
    )


def decodificar_token_desafio_mfa(token: str) -> dict[str, Any]:
    """Decodifica e valida um token de desafio MFA."""
    payload = decodificar_token_assinado(token)
    if payload.get("tipo") != "desafio_mfa":
        raise ValueError("Tipo de token inválido para desafio MFA.")
    return payload


async def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Extrai e valida o token Bearer do cabeçalho Authorization."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação obrigatória ou token inválido.",
        )
    try:
        payload = decodificar_token_assinado(credentials.credentials)
        if payload.get("tipo") != "sessao":
            raise ValueError("Token não é de sessão.")
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação obrigatória ou token inválido.",
        )


async def require_authenticated_user(
    request: Request,
    payload: dict[str, Any] = Depends(get_current_user_payload),
) -> dict[str, Any]:
    """Exige usuário autenticado ativo no banco de dados."""
    repo = getattr(request.app.state, "repo", None)
    usuario_id = int(payload.get("sub", 0))

    if repo:
        usuario = repo.buscar_usuario_por_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário associado ao token não encontrado.",
            )
        if int(usuario.get("statusCONTA", 0)) != 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conta de usuário inativa.",
            )
        payload["perfil_RBAC"] = int(usuario.get("perfil_RBAC", payload.get("perfil_RBAC", 0)))
        payload["mfa_ativo"] = bool(usuario.get("tokenMFA"))

    return payload


async def require_admin(
    payload: dict[str, Any] = Depends(require_authenticated_user),
) -> dict[str, Any]:
    """Exige que o usuário autenticado possua perfil Admin (id_perfil == 5)."""
    perfil = int(payload.get("perfil_RBAC", 0))
    if perfil != 5:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao perfil Admin.",
        )
    return payload
