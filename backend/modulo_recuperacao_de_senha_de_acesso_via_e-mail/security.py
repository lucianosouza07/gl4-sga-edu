"""Utilitários de segurança e criptografia para o fluxo de recuperação de senhas."""

import hashlib
import secrets
import bcrypt


def generate_secure_token(nbytes: int = 32) -> str:
    """Gera um token criptograficamente seguro e opaco (URL-safe)."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """Calcula o hash SHA-256 do token em formato hexadecimal (64 caracteres)."""
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """Gera o hash bcrypt com salt automático e work factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica a correspondência entre senha em texto puro e hash bcrypt."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False
