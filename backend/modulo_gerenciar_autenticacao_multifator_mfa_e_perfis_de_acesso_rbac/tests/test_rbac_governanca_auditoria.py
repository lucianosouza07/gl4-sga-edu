"""Testes automatizados para a User Story 3 (Governança RBAC, Redefinição MFA e Auditoria)."""

import pytest
from ..totp_service import calcular_codigo_totp


def test_listar_perfis_rbac_admin_sucesso(client, admin_headers):
    """US3: Admin consulta o catálogo completo dos 5 perfis institucionais."""
    resp = client.get("/api/rbac/perfis", headers=admin_headers)
    assert resp.status_code == 200
    perfis = resp.json()
    assert len(perfis) == 5
    nomes = [p["nome_perfil"] for p in perfis]
    assert nomes == ["Aluno", "Professor", "Secretaria", "Financeiro", "Admin"]


def test_bloqueio_rbac_nao_admin(client, prof_headers, aluno_headers, secretaria_headers):
    """FR-015: Perfis diferentes de Admin recebem 403 Forbidden ao acessar governança."""
    # Professor
    r_prof = client.get("/api/rbac/perfis", headers=prof_headers)
    assert r_prof.status_code == 403
    assert "Acesso restrito ao perfil Admin" in r_prof.json()["detail"]

    # Aluno
    r_aluno = client.put("/api/rbac/usuarios/5/perfil", json={"novo_perfil_id": 4}, headers=aluno_headers)
    assert r_aluno.status_code == 403

    # Secretaria
    r_sec = client.post("/api/rbac/usuarios/5/mfa/reset", headers=secretaria_headers)
    assert r_sec.status_code == 403

    # Visitante anônimo -> 401
    r_anon = client.get("/api/rbac/perfis")
    assert r_anon.status_code == 401


def test_consultar_usuario_rbac(client, admin_headers):
    """US3: Admin detalha dados RBAC e MFA de um usuário."""
    # Usuário existente (id=5 - Secretaria)
    resp = client.get("/api/rbac/usuarios/5", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_usuario"] == 5
    assert data["login"] == "secretaria@sga.edu.br"
    assert data["nome_perfil"] == "Secretaria"
    assert data["mfa_ativo"] is False

    # Usuário inexistente -> 404
    resp_404 = client.get("/api/rbac/usuarios/9999", headers=admin_headers)
    assert resp_404.status_code == 404


def test_alterar_perfil_usuario_e_salvaguarda_ultimo_admin(client, admin_headers):
    """US3: Alteração de perfil RBAC e proteção mandatória contra zerar administradores ativos."""
    # 1. Altera perfil da Secretaria (id=5) para Financeiro (id=4)
    resp_up = client.put("/api/rbac/usuarios/5/perfil", json={"novo_perfil_id": 4}, headers=admin_headers)
    assert resp_up.status_code == 200
    assert resp_up.json()["perfil_RBAC"] == 4
    assert resp_up.json()["nome_perfil"] == "Financeiro"

    # 2. No seed inicial existem 2 admins: id=1 e id=2.
    # Rebaixar o admin 2 para Professor (id=2) deve ser permitido porque o admin 1 ainda permanece ativo
    resp_rebaixa_admin2 = client.put("/api/rbac/usuarios/2/perfil", json={"novo_perfil_id": 2}, headers=admin_headers)
    assert resp_rebaixa_admin2.status_code == 200
    assert resp_rebaixa_admin2.json()["perfil_RBAC"] == 2

    # 3. Agora resta apenas 1 admin ativo (id=1).
    # Tentar rebaixar o único admin restante (id=1) para qualquer outro perfil deve disparar 409 Conflict
    resp_bloqueio = client.put("/api/rbac/usuarios/1/perfil", json={"novo_perfil_id": 3}, headers=admin_headers)
    assert resp_bloqueio.status_code == 409
    assert "Não é permitido alterar o perfil do único administrador ativo" in resp_bloqueio.json()["detail"]

    # 4. Perfil id inválido (fora de 1..5) -> 422
    resp_invalido = client.put("/api/rbac/usuarios/5/perfil", json={"novo_perfil_id": 99}, headers=admin_headers)
    assert resp_invalido.status_code == 422


def test_redefinicao_emergencial_mfa_admin(client, admin_headers, prof_headers):
    """US3: Admin executa reset emergencial de MFA para usuário com perda de acesso."""
    # 1. Ativa MFA no professor (id=3)
    setup_resp = client.post("/api/mfa/setup", headers=prof_headers)
    segredo = setup_resp.json()["secret"]
    codigo = calcular_codigo_totp(segredo)
    client.post("/api/mfa/activate", json={"codigo": codigo}, headers=prof_headers)

    # Status confirma MFA ativo
    st_antes = client.get("/api/mfa/status", headers=prof_headers)
    assert st_antes.json()["mfa_ativo"] is True

    # 2. Admin solicita reset emergencial de MFA do professor
    reset_resp = client.post("/api/rbac/usuarios/3/mfa/reset", headers=admin_headers)
    assert reset_resp.status_code == 200
    assert reset_resp.json()["mfa_ativo"] is False
    assert "MFA desativado com sucesso pelo administrador" in reset_resp.json()["mensagem"]

    # 3. Status agora reflete MFA desativado
    st_depois = client.get("/api/mfa/status", headers=prof_headers)
    assert st_depois.json()["mfa_ativo"] is False


def test_trilha_auditoria_mfa_rbac(client, admin_headers):
    """FR-016: Consulta de auditoria sanitizada contendo eventos das operações."""
    # Executa uma alteração de perfil para gerar evento auditado
    client.put("/api/rbac/usuarios/5/perfil", json={"novo_perfil_id": 4}, headers=admin_headers)

    resp = client.get("/api/rbac/auditoria", headers=admin_headers)
    assert resp.status_code == 200
    eventos = resp.json()
    assert isinstance(eventos, list)
    assert len(eventos) > 0

    # Verifica que nenhum snapshot contém campos sensíveis
    for ev in eventos:
        assert ev["entidade_afetada"] in ["Usuario", "Perfil", "MfaConfig"]
        for snapshot_field in ["dados_anteriores", "dados_novos"]:
            conteudo = ev.get(snapshot_field)
            if conteudo:
                assert "senha_hash" not in conteudo
                assert "tokenmfa" not in conteudo.lower()
                assert '"secret"' not in conteudo.lower()
                assert '"segredo"' not in conteudo.lower()
