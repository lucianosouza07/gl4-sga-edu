"""Serviço criptográfico para código verificador, SHA-256 canônico, QR Code e assinatura ICP-Brasil."""

import hashlib
import hmac
import json
import os
import secrets
from typing import Any

_DEFAULT_ICP_SECRET = "sga-edu-icp-brasil-institutional-key-2026"
_DEFAULT_QRCODE_BASE_URL = "https://sga-edu.institucional.edu.br/api/documentos/validar"

PREFIXOS_CODIGO: dict[str, str] = {
    "DIARIO_OPERACIONAL": "SGA-DIA",
    "ATA_NOTAS": "SGA-ATA",
    "DIPLOMA_DIGITAL": "SGA-DIP",
}


def _obter_segredo_icp() -> bytes:
    segredo = os.getenv("SGA_ICP_BRASIL_SECRET") or _DEFAULT_ICP_SECRET
    return segredo.encode("utf-8")


def serializar_conteudo_canonico(conteudo: dict[str, Any]) -> str:
    """Serializa o conteúdo consolidado de forma determinística para cálculo de hash SHA-256."""
    return json.dumps(conteudo, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def calcular_hash_sha256(conteudo_ou_json: dict[str, Any] | str) -> str:
    """Calcula resumo criptográfico SHA-256 (64 caracteres hexadecimais)."""
    texto = (
        conteudo_ou_json
        if isinstance(conteudo_ou_json, str)
        else serializar_conteudo_canonico(conteudo_ou_json)
    )
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def gerar_codigo_verificacao(tipo_documento: str) -> str:
    """Gera código verificador institucional único com entropia criptográfica."""
    prefixo = PREFIXOS_CODIGO.get(tipo_documento, "SGA-DOC")
    sufixo = secrets.token_hex(8).upper()
    return f"{prefixo}-{sufixo}"


def gerar_url_validacao_qrcode(codigo_verificacao: str) -> str:
    """Compõe o endereço institucional de validação pública para incorporação em QR Code."""
    base_url = (os.getenv("SGA_VALIDACAO_BASE_URL") or _DEFAULT_QRCODE_BASE_URL).rstrip("/")
    return f"{base_url}/{codigo_verificacao}"


def gerar_assinatura_icp_brasil(
    hash_sha256: str,
    carimbo_tempo: str,
    portaria_referencia: str,
    codigo_verificacao: str,
) -> str:
    """Gera assinatura institucional determinística de 128 hex chars (HMAC-SHA512)."""
    mensagem = f"{hash_sha256}|{carimbo_tempo}|{portaria_referencia}|{codigo_verificacao}"
    return hmac.new(_obter_segredo_icp(), mensagem.encode("utf-8"), hashlib.sha512).hexdigest()


def verificar_assinatura_icp_brasil(
    assinatura_armazenada: str,
    hash_sha256: str,
    carimbo_tempo: str,
    portaria_referencia: str,
    codigo_verificacao: str,
) -> bool:
    """Valida a assinatura institucional ICP-Brasil em tempo constante."""
    esperada = gerar_assinatura_icp_brasil(
        hash_sha256=hash_sha256,
        carimbo_tempo=carimbo_tempo,
        portaria_referencia=portaria_referencia,
        codigo_verificacao=codigo_verificacao,
    )
    return hmac.compare_digest(assinatura_armazenada, esperada)
