"""Testes unitários e de integração para imposição de TLS 1.3 e endpoint de diagnóstico."""

import ssl
import pytest
from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.tls_config import (
    create_tls13_context,
    validar_conformidade_tls,
)


def test_tls13_context_configuration():
    """Valida que o contexto SSL do servidor impõe estritamente o protocolo TLS 1.3."""
    context = create_tls13_context()
    assert context.minimum_version == ssl.TLSVersion.TLSv1_3
    assert context.maximum_version == ssl.TLSVersion.TLSv1_3


def test_validar_conformidade_tls():
    """Valida a função de checagem de conformidade de protocolos de rede."""
    # TLS 1.3 deve ser aprovado com conformidade integral
    valida, conformidade = validar_conformidade_tls("TLSv1.3", "TLS_AES_256_GCM_SHA384")
    assert valida is True
    assert conformidade is True

    # TLS 1.2 é versão válida porém não atende à conformidade estrita TLS 1.3
    valida_12, conformidade_12 = validar_conformidade_tls("TLSv1.2")
    assert valida_12 is True
    assert conformidade_12 is False

    # Protocolos obsoletos devem ser completamente reprovados
    valida_11, conformidade_11 = validar_conformidade_tls("TLSv1.1")
    assert valida_11 is False
    assert conformidade_11 is False

    valida_ssl, conformidade_ssl = validar_conformidade_tls("SSLv3")
    assert valida_ssl is False
    assert conformidade_ssl is False


def test_api_tls_status_endpoint(client):
    """Valida o endpoint GET /api/v1/crypto/tls-status."""
    resp = client.get("/api/v1/crypto/tls-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "protocolo_negociado" in data
    assert data["versao_tls_valida"] is True
    assert data["em_conformidade_tls13"] is True


def test_api_test_encryption_endpoint(client):
    """Valida o endpoint POST /api/v1/crypto/test-encryption."""
    payload = {"texto_plano": "Docente: Carlos Alberto - Matrícula: 10992"}
    resp = client.post("/api/v1/crypto/test-encryption", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["texto_plano_original"] == payload["texto_plano"]
    assert data["carga_cifrada"].startswith("v1:aes-256-gcm:")
    assert data["texto_decifrado"] == payload["texto_plano"]
    assert data["autenticidade_validada"] is True
    assert data["algoritmo"] == "AES-256-GCM"
