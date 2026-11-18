"""Testes unitários para o motor TOTP (RFC 6238) e códigos de recuperação."""

import pytest
from ..totp_service import (
    calcular_codigo_totp,
    decodificar_segredo_base32,
    gerar_codigos_recuperacao,
    gerar_segredo_base32,
    gerar_uri_otpauth,
    hash_codigo_recuperacao,
    normalizar_codigo_recuperacao,
    validar_codigo_totp,
)


def test_gerar_segredo_base32():
    segredo = gerar_segredo_base32()
    assert isinstance(segredo, str)
    assert len(segredo) == 32
    # Deve decodificar sem erros
    decodificado = decodificar_segredo_base32(segredo)
    assert len(decodificado) == 20


def test_rfc6238_vetores_oficiais():
    """Valida contra os vetores oficiais do RFC 6238 (Apêndice B - SHA1, 6 dígitos).

    Chave ASCII: '12345678901234567890'
    Chave Base32: 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'
    """
    segredo_rfc_base32 = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"

    # Time = 59s -> step 1 -> RFC SHA1 8-digit: 94287082 -> 6-digit: 287082
    c1 = calcular_codigo_totp(segredo_rfc_base32, timestamp=59)
    assert c1 == "287082"

    # Time = 1111111109s -> step 37037036 -> RFC SHA1 8-digit: 07081804 -> 6-digit: 081804
    c2 = calcular_codigo_totp(segredo_rfc_base32, timestamp=1111111109)
    assert c2 == "081804"

    # Time = 1111111111s -> step 37037037 -> RFC SHA1 8-digit: 14050471 -> 6-digit: 050471
    c3 = calcular_codigo_totp(segredo_rfc_base32, timestamp=1111111111)
    assert c3 == "050471"

    # Time = 1234567890s -> step 41152263 -> RFC SHA1 8-digit: 89005924 -> 6-digit: 005924
    c4 = calcular_codigo_totp(segredo_rfc_base32, timestamp=1234567890)
    assert c4 == "005924"

    # Time = 2000000000s -> step 66666666 -> RFC SHA1 8-digit: 69279037 -> 6-digit: 279037
    c5 = calcular_codigo_totp(segredo_rfc_base32, timestamp=2000000000)
    assert c5 == "279037"


def test_validar_codigo_totp_com_drift():
    segredo = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"
    tempo_base = 1000000.0

    codigo_atual = calcular_codigo_totp(segredo, timestamp=tempo_base)
    valido, passo = validar_codigo_totp(segredo, codigo_atual, timestamp=tempo_base)
    assert valido is True
    assert passo == int(tempo_base // 30)

    # Código da janela anterior (tempo - 30s) com drift=1 deve ser aceito
    codigo_anterior = calcular_codigo_totp(segredo, timestamp=tempo_base - 30)
    valido_ant, passo_ant = validar_codigo_totp(segredo, codigo_anterior, drift_passos=1, timestamp=tempo_base)
    assert valido_ant is True
    assert passo_ant == int((tempo_base - 30) // 30)

    # Código da janela posterior (tempo + 30s) com drift=1 deve ser aceito
    codigo_posterior = calcular_codigo_totp(segredo, timestamp=tempo_base + 30)
    valido_pos, passo_pos = validar_codigo_totp(segredo, codigo_posterior, drift_passos=1, timestamp=tempo_base)
    assert valido_pos is True
    assert passo_pos == int((tempo_base + 30) // 30)

    # Código fora do drift (tempo - 60s) deve ser rejeitado
    codigo_muito_antigo = calcular_codigo_totp(segredo, timestamp=tempo_base - 60)
    valido_fora, _ = validar_codigo_totp(segredo, codigo_muito_antigo, drift_passos=1, timestamp=tempo_base)
    assert valido_fora is False


def test_gerar_uri_otpauth():
    uri = gerar_uri_otpauth(
        login="admin@sga.edu.br",
        segredo="JBSWY3DPEHPK3PXP",
        emissor="SGA-Edu",
    )
    assert uri.startswith("otpauth://totp/SGA-Edu%3Aadmin%40sga.edu.br?")
    assert "secret=JBSWY3DPEHPK3PXP" in uri
    assert "issuer=SGA-Edu" in uri
    assert "digits=6" in uri
    assert "period=30" in uri


def test_codigos_recuperacao():
    codigos = gerar_codigos_recuperacao(8)
    assert len(codigos) == 8
    assert len(set(codigos)) == 8  # Todos únicos

    codigo = codigos[0]
    assert len(codigo) == 9  # Formato 4-4 (XXXX-XXXX)
    norm = normalizar_codigo_recuperacao(codigo)
    assert len(norm) == 8
    h1 = hash_codigo_recuperacao(codigo)
    h2 = hash_codigo_recuperacao(norm)
    assert h1 == h2
    assert len(h1) == 64
