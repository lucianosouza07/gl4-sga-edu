"""Implementação pura de TOTP (RFC 6238 / RFC 4226) com zero dependências externas.

Suporta:
- Geração de segredo Base32 seguro (RFC 4648)
- Geração de URI padronizada otpauth://
- Cálculo de código TOTP de 6 dígitos decimais com HMAC-SHA1
- Validação com tolerância a drift de relógio (±1 intervalo de 30s)
- Geração e hash de códigos de recuperação (backup codes) descartáveis
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import Optional
import urllib.parse


def gerar_segredo_base32(num_bytes: int = 20) -> str:
    """Gera um segredo aleatório criptográfico codificado em Base32 (160 bits por padrão)."""
    bytes_aleatorios = secrets.token_bytes(num_bytes)
    base32_str = base64.b32encode(bytes_aleatorios).decode("ascii")
    return base32_str.replace("=", "").strip().upper()


def decodificar_segredo_base32(segredo: str) -> bytes:
    """Decodifica um segredo Base32, tolerando variações de padding e minúsculas."""
    segredo_limpo = segredo.strip().replace(" ", "").upper()
    padding_faltante = (8 - len(segredo_limpo) % 8) % 8
    if padding_faltante != 0:
        segredo_limpo += "=" * padding_faltante
    return base64.b32decode(segredo_limpo.encode("ascii"), casefold=True)


def gerar_uri_otpauth(
    login: str,
    segredo: str,
    emissor: str = "SGA-Edu",
    digitos: int = 6,
    periodo: int = 30,
) -> str:
    """Gera a URI segura no formato otpauth://totp para pareamento com apps autenticadores."""
    label = f"{emissor}:{login}"
    params = {
        "secret": segredo.strip().upper(),
        "issuer": emissor,
        "algorithm": "SHA1",
        "digits": str(digitos),
        "period": str(periodo),
    }
    query_str = urllib.parse.urlencode(params)
    label_encoded = urllib.parse.quote(label)
    return f"otpauth://totp/{label_encoded}?{query_str}"


def calcular_codigo_totp(
    segredo: str,
    passo_tempo: Optional[int] = None,
    timestamp: Optional[float] = None,
    periodo: int = 30,
    digitos: int = 6,
) -> str:
    """Calcula o código numérico TOTP para o passo temporal especificado."""
    if passo_tempo is None:
        ts = time.time() if timestamp is None else timestamp
        passo_tempo = int(ts // periodo)

    chave_bytes = decodificar_segredo_base32(segredo)
    msg_counter = struct.pack(">Q", passo_tempo)

    hmac_digest = hmac.new(chave_bytes, msg_counter, hashlib.sha1).digest()
    offset = hmac_digest[-1] & 0x0F
    code_int = struct.unpack(">I", hmac_digest[offset : offset + 4])[0] & 0x7FFFFFFF
    codigo_num = code_int % (10**digitos)
    return f"{codigo_num:0{digitos}d}"


def validar_codigo_totp(
    segredo: str,
    codigo_submetido: str,
    drift_passos: int = 1,
    timestamp: Optional[float] = None,
    periodo: int = 30,
    digitos: int = 6,
) -> tuple[bool, Optional[int]]:
    """Valida um código TOTP contra o segredo, considerando desvios de relógio (drift).

    Retorna uma tupla (valido: bool, passo_tempo_validado: Optional[int]).
    """
    codigo_limpo = codigo_submetido.strip()
    if len(codigo_limpo) != digitos or not codigo_limpo.isdigit():
        return False, None

    ts = time.time() if timestamp is None else timestamp
    passo_atual = int(ts // periodo)

    for offset in range(-drift_passos, drift_passos + 1):
        passo_candidato = passo_atual + offset
        try:
            codigo_esperado = calcular_codigo_totp(
                segredo=segredo,
                passo_tempo=passo_candidato,
                periodo=periodo,
                digitos=digitos,
            )
            if hmac.compare_digest(codigo_limpo, codigo_esperado):
                return True, passo_candidato
        except Exception:
            continue

    return False, None


def gerar_codigos_recuperacao(quantidade: int = 8) -> list[str]:
    """Gera um lote de códigos de recuperação alfanuméricos descartáveis formatados (ex: A1B2-C3D4)."""
    codigos: list[str] = []
    alfabeto = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # Base32 humana sem caracteres ambíguos (0, 1, I, O)
    for _ in range(quantidade):
        parte1 = "".join(secrets.choice(alfabeto) for _ in range(4))
        parte2 = "".join(secrets.choice(alfabeto) for _ in range(4))
        codigos.append(f"{parte1}-{parte2}")
    return codigos


def normalizar_codigo_recuperacao(codigo: str) -> str:
    """Normaliza o código de contingência removendo traços, espaços e convertendo para maiúsculas."""
    return codigo.strip().replace("-", "").replace(" ", "").upper()


def hash_codigo_recuperacao(codigo: str) -> str:
    """Gera o hash SHA-256 do código de recuperação normalizado para armazenamento seguro."""
    codigo_norm = normalizar_codigo_recuperacao(codigo)
    return hashlib.sha256(codigo_norm.encode("utf-8")).hexdigest()
