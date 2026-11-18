"""Testes de autorização estrita (RBAC Admin) e sigilo de credenciais."""

import pytest


PAYLOAD_VALIDO = {
    "nome": "Carla Ribeiro",
    "cpf": "52998224725",
    "login": "carla.ribeiro@uneb.br",
    "senha_inicial": "SenhaSegura@2026",
    "setor": "Secretaria Acadêmica",
    "cargo": "Coordenadora",
    "perfil": "Secretaria",
}


def test_rejeita_cadastro_sem_token_ou_token_invalido(client):
    assert client.post("/api/funcionarios-administrativos", json=PAYLOAD_VALIDO).status_code == 401
    assert (
        client.post(
            "/api/funcionarios-administrativos",
            json=PAYLOAD_VALIDO,
            headers={"Authorization": "Bearer token-adulterado"},
        ).status_code
        == 401
    )


@pytest.mark.parametrize("ator", ["aluno", "professor", "secretaria", "financeiro", "admin_inativo"])
def test_rejeita_cadastro_para_perfis_nao_admin_e_admin_inativo(client, headers_para, ator):
    resp = client.post("/api/funcionarios-administrativos", json=PAYLOAD_VALIDO, headers=headers_para(ator))
    assert resp.status_code == 403


def test_resposta_e_auditoria_de_cadastro_nunca_expoem_senhas_ou_hashes(client, repo, headers_para):
    resp = client.post(
        "/api/funcionarios-administrativos",
        json=PAYLOAD_VALIDO,
        headers=headers_para("admin"),
    )
    assert resp.status_code == 201
    texto_resposta = resp.text.lower()
    assert "senha_hash" not in texto_resposta
    assert "senha_inicial" not in texto_resposta
    assert "senhasegura@2026" not in texto_resposta

    logs = repo.conn.execute("SELECT dados_anteriores, dados_novos FROM LogAuditoriaSistema").fetchall()
    assert len(logs) == 1
    conteudo_log = f"{logs[0]['dados_anteriores']} {logs[0]['dados_novos']}".lower()
    assert "senha_hash" not in conteudo_log
    assert "senha_inicial" not in conteudo_log
    assert "senhasegura@2026" not in conteudo_log


def test_integracao_entrypoint_principal_e_paridade_openapi(client):
    import sys
    from pathlib import Path

    backend_root = Path(__file__).resolve().parents[2]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from modulo_34_cadastrar_professor.main import app as integrated_app
    from router import app as standalone_app

    caminhos_integrados = integrated_app.openapi()["paths"]
    assert set(caminhos_integrados["/api/funcionarios-administrativos"].keys()) >= {"get", "post"}
    assert set(caminhos_integrados["/api/funcionarios-administrativos/auditoria"].keys()) >= {"get"}
    assert set(caminhos_integrados["/api/funcionarios-administrativos/{funcionario_id}"].keys()) >= {"get", "put", "delete"}
    assert set(caminhos_integrados["/api/funcionarios-administrativos/{funcionario_id}/status"].keys()) >= {"patch"}

    openapi = standalone_app.openapi()
    paths = openapi["paths"]
    assert set(paths["/api/funcionarios-administrativos"].keys()) >= {"get", "post"}
    assert set(paths["/api/funcionarios-administrativos/auditoria"].keys()) >= {"get"}
    assert set(paths["/api/funcionarios-administrativos/{funcionario_id}"].keys()) >= {"get", "put", "delete"}
    assert set(paths["/api/funcionarios-administrativos/{funcionario_id}/status"].keys()) >= {"patch"}
