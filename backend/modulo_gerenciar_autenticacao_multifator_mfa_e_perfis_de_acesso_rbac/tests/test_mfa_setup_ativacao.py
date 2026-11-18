"""Testes automatizados para a User Story 1 (Ativação, Verificação e Configuração de MFA)."""

import pytest
from ..totp_service import calcular_codigo_totp


def test_mfa_setup_autenticado(client, prof_headers):
    """US1: Iniciar setup de MFA gera segredo e URI mantendo status inativo."""
    resp = client.post("/api/mfa/setup", headers=prof_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "secret" in data
    assert len(data["secret"]) == 32
    assert "otpauth_uri" in data
    assert "otpauth://totp/SGA-Edu%3Aprof%40sga.edu.br?" in data["otpauth_uri"]
    assert data["validade_segundos"] == 600

    # Status deve continuar inativo até ativação
    status_resp = client.get("/api/mfa/status", headers=prof_headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["mfa_ativo"] is False


def test_mfa_setup_nao_autenticado_e_inativo(client, inativo_headers):
    """FR-002: Rejeição com 401 sem token e 403 para conta inativa."""
    resp_no_token = client.post("/api/mfa/setup")
    assert resp_no_token.status_code == 401

    resp_inativo = client.post("/api/mfa/setup", headers=inativo_headers)
    assert resp_inativo.status_code == 403


def test_mfa_activate_sem_setup_previo(client, prof_headers):
    """Rejeita tentativa de ativação sem início prévio de configuração."""
    resp = client.post("/api/mfa/activate", json={"codigo": "123456"}, headers=prof_headers)
    assert resp.status_code == 400
    assert "Nenhuma configuração de MFA pendente" in resp.json()["detail"]


def test_mfa_activate_codigo_invalido(client, prof_headers):
    """Rejeita código TOTP que não corresponde ao segredo provisório."""
    client.post("/api/mfa/setup", headers=prof_headers)

    # 422 para formato não numérico ou tamanho errado
    resp_bad_fmt = client.post("/api/mfa/activate", json={"codigo": "abc"}, headers=prof_headers)
    assert resp_bad_fmt.status_code == 422

    # 400 para código numérico de 6 dígitos porém incorreto
    resp_bad_code = client.post("/api/mfa/activate", json={"codigo": "999999"}, headers=prof_headers)
    assert resp_bad_code.status_code == 400
    assert "Código de verificação incorreto ou expirado" in resp_bad_code.json()["detail"]


def test_mfa_activate_fluxo_completo_com_backup_codes(client, prof_headers):
    """US1: Ativação bem-sucedida com emissão de 8 códigos de recuperação e auditoria."""
    setup_resp = client.post("/api/mfa/setup", headers=prof_headers)
    segredo = setup_resp.json()["secret"]

    codigo_correto = calcular_codigo_totp(segredo)

    activate_resp = client.post("/api/mfa/activate", json={"codigo": codigo_correto}, headers=prof_headers)
    assert activate_resp.status_code == 200
    data = activate_resp.json()
    assert data["mfa_ativo"] is True
    assert len(data["backup_codes"]) == 8
    assert len(set(data["backup_codes"])) == 8

    # Status agora deve constar como ativo
    status_resp = client.get("/api/mfa/status", headers=prof_headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["mfa_ativo"] is True
    assert status_resp.json()["token_mfa_configurado"] is True


def test_mfa_deactivate_sucesso_com_totp(client, prof_headers):
    """US1: Desativação voluntária com confirmação de senha e código TOTP."""
    setup_resp = client.post("/api/mfa/setup", headers=prof_headers)
    segredo = setup_resp.json()["secret"]
    codigo_ativo = calcular_codigo_totp(segredo)
    client.post("/api/mfa/activate", json={"codigo": codigo_ativo}, headers=prof_headers)

    # Senha incorreta -> 400
    resp_senha_errada = client.post(
        "/api/mfa/deactivate",
        json={"senha": "SenhaErrada#999", "codigo": codigo_ativo},
        headers=prof_headers,
    )
    assert resp_senha_errada.status_code == 400
    assert "Senha incorreta" in resp_senha_errada.json()["detail"]

    # Código incorreto -> 400
    resp_cod_errado = client.post(
        "/api/mfa/deactivate",
        json={"senha": "SenhaForte#2026", "codigo": "000000"},
        headers=prof_headers,
    )
    assert resp_cod_errado.status_code == 400
    assert "Código de verificação incorreto ou inválido" in resp_cod_errado.json()["detail"]

    # Sucesso com senha e código TOTP correto
    resp_sucesso = client.post(
        "/api/mfa/deactivate",
        json={"senha": "SenhaForte#2026", "codigo": codigo_ativo},
        headers=prof_headers,
    )
    assert resp_sucesso.status_code == 200
    assert "MFA desativado com sucesso" in resp_sucesso.json()["mensagem"]

    # Status voltou a inativo
    status_resp = client.get("/api/mfa/status", headers=prof_headers)
    assert status_resp.json()["mfa_ativo"] is False


def test_mfa_deactivate_sucesso_com_backup_code(client, prof_headers):
    """US1: Desativação voluntária utilizando código de contingência descartável."""
    setup_resp = client.post("/api/mfa/setup", headers=prof_headers)
    segredo = setup_resp.json()["secret"]
    codigo_totp = calcular_codigo_totp(segredo)
    activate_resp = client.post("/api/mfa/activate", json={"codigo": codigo_totp}, headers=prof_headers)
    backup_codes = activate_resp.json()["backup_codes"]
    um_backup_code = backup_codes[0]

    resp_sucesso = client.post(
        "/api/mfa/deactivate",
        json={"senha": "SenhaForte#2026", "codigo": um_backup_code},
        headers=prof_headers,
    )
    assert resp_sucesso.status_code == 200
    assert "MFA desativado com sucesso" in resp_sucesso.json()["mensagem"]

    status_resp = client.get("/api/mfa/status", headers=prof_headers)
    assert status_resp.json()["mfa_ativo"] is False
