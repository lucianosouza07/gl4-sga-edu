"""Testes automatizados para a User Story 2 (Desafio MFA no Login, Replay Attack e Backup Codes)."""

import pytest
from ..security import gerar_token_desafio_mfa
from ..totp_service import calcular_codigo_totp


def test_login_usuario_sem_mfa(client):
    """Contas sem MFA recebem token Bearer diretamente na autenticação primária."""
    resp = client.post(
        "/api/auth/login",
        json={"login": "prof@sga.edu.br", "senha": "SenhaForte#2026"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "authenticated"
    assert "access_token" in data
    assert data["perfil_RBAC"] == 2
    assert data["usuario_id"] == 3


def test_login_usuario_com_mfa_gera_desafio(client, prof_headers):
    """Contas com MFA ativo recebem status mfa_required e challenge_token temporário."""
    # 1. Ativa MFA no professor
    setup_resp = client.post("/api/mfa/setup", headers=prof_headers)
    segredo = setup_resp.json()["secret"]
    codigo = calcular_codigo_totp(segredo)
    client.post("/api/mfa/activate", json={"codigo": codigo}, headers=prof_headers)

    # 2. Realiza login primário
    login_resp = client.post(
        "/api/auth/login",
        json={"login": "prof@sga.edu.br", "senha": "SenhaForte#2026"},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert data["status"] == "mfa_required"
    assert "challenge_token" in data
    assert "access_token" not in data


def test_desafio_mfa_sucesso_totp_e_anti_replay(client, prof_headers):
    """US2: Validação de TOTP no desafio emite token de sessão e bloqueia replay attack."""
    setup_resp = client.post("/api/mfa/setup", headers=prof_headers)
    segredo = setup_resp.json()["secret"]
    codigo_ativacao = calcular_codigo_totp(segredo)
    client.post("/api/mfa/activate", json={"codigo": codigo_ativacao}, headers=prof_headers)

    # Login primário gera desafio
    login_resp = client.post(
        "/api/auth/login",
        json={"login": "prof@sga.edu.br", "senha": "SenhaForte#2026"},
    )
    challenge_token = login_resp.json()["challenge_token"]

    codigo_atual = calcular_codigo_totp(segredo)
    challenge_resp = client.post(
        "/api/auth/mfa/challenge",
        json={"challenge_token": challenge_token, "codigo": codigo_atual},
    )
    assert challenge_resp.status_code == 200
    data = challenge_resp.json()
    assert "access_token" in data
    assert data["perfil_RBAC"] == 2
    assert data["login"] == "prof@sga.edu.br"

    # Tentativa de Replay Attack: reutilizar o mesmo código na mesma janela temporal
    # Gera um novo desafio para o mesmo usuário
    login_resp2 = client.post(
        "/api/auth/login",
        json={"login": "prof@sga.edu.br", "senha": "SenhaForte#2026"},
    )
    challenge_token2 = login_resp2.json()["challenge_token"]

    replay_resp = client.post(
        "/api/auth/mfa/challenge",
        json={"challenge_token": challenge_token2, "codigo": codigo_atual},
    )
    assert replay_resp.status_code == 400
    assert "já utilizado nesta janela temporal" in replay_resp.json()["detail"]


def test_desafio_mfa_sucesso_com_backup_code_descartavel(client, prof_headers):
    """US2: Validação com código de contingência emite sessão e invalida o código consumido."""
    setup_resp = client.post("/api/mfa/setup", headers=prof_headers)
    segredo = setup_resp.json()["secret"]
    codigo_ativacao = calcular_codigo_totp(segredo)
    act_resp = client.post("/api/mfa/activate", json={"codigo": codigo_ativacao}, headers=prof_headers)
    backup_codes = act_resp.json()["backup_codes"]
    cod1 = backup_codes[0]

    login_resp = client.post(
        "/api/auth/login",
        json={"login": "prof@sga.edu.br", "senha": "SenhaForte#2026"},
    )
    challenge_token = login_resp.json()["challenge_token"]

    # Consumo válido do código de recuperação
    resp1 = client.post(
        "/api/auth/mfa/challenge",
        json={"challenge_token": challenge_token, "codigo": cod1},
    )
    assert resp1.status_code == 200
    assert "access_token" in resp1.json()

    # Tentativa de reutilizar o mesmo código de recuperação em outro login
    login_resp2 = client.post(
        "/api/auth/login",
        json={"login": "prof@sga.edu.br", "senha": "SenhaForte#2026"},
    )
    challenge_token2 = login_resp2.json()["challenge_token"]

    resp2 = client.post(
        "/api/auth/mfa/challenge",
        json={"challenge_token": challenge_token2, "codigo": cod1},
    )
    assert resp2.status_code == 400
    assert "Código de segundo fator incorreto ou inválido" in resp2.json()["detail"]


def test_desafio_mfa_limite_forca_bruta_5_tentativas(client, prof_headers):
    """Edge Case: Bloqueio do desafio após 5 tentativas consecutivas incorretas."""
    setup_resp = client.post("/api/mfa/setup", headers=prof_headers)
    segredo = setup_resp.json()["secret"]
    codigo_ativacao = calcular_codigo_totp(segredo)
    client.post("/api/mfa/activate", json={"codigo": codigo_ativacao}, headers=prof_headers)

    login_resp = client.post(
        "/api/auth/login",
        json={"login": "prof@sga.edu.br", "senha": "SenhaForte#2026"},
    )
    challenge_token = login_resp.json()["challenge_token"]

    # 4 erros consecutivos
    for i in range(1, 5):
        err_resp = client.post(
            "/api/auth/mfa/challenge",
            json={"challenge_token": challenge_token, "codigo": f"00000{i}"},
        )
        assert err_resp.status_code == 400
        assert f"Tentativas restantes: {5 - i}" in err_resp.json()["detail"]

    # 5º erro -> esgota tentativas
    err_5 = client.post(
        "/api/auth/mfa/challenge",
        json={"challenge_token": challenge_token, "codigo": "000005"},
    )
    assert err_5.status_code == 400
    assert "Tentativas restantes: 0" in err_5.json()["detail"]

    # 6ª tentativa mesmo com código correto deve ser bloqueada
    codigo_correto = calcular_codigo_totp(segredo)
    bloqueado = client.post(
        "/api/auth/mfa/challenge",
        json={"challenge_token": challenge_token, "codigo": codigo_correto},
    )
    assert bloqueado.status_code == 400
    assert "Limite de tentativas excedido" in bloqueado.json()["detail"]


def test_desafio_mfa_token_invalido_ou_expirado(client):
    """Rejeita challenge_token forjado ou corrompido."""
    resp = client.post(
        "/api/auth/mfa/challenge",
        json={"challenge_token": "token.invalido.falso", "codigo": "123456"},
    )
    assert resp.status_code == 401
    assert "Token de desafio inválido ou expirado" in resp.json()["detail"]
