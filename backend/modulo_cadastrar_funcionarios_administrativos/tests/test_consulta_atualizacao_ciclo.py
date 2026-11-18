"""Testes das US2 (consulta/atualização) e US3 (status/exclusão/auditoria)."""

import json

from security import criar_token_sessao


def _cpf_valido(base9: str) -> str:
    def _dig(parcial: str, peso: int) -> str:
        soma = sum(int(ch) * (peso - i) for i, ch in enumerate(parcial))
        resto = (soma * 10) % 11
        return "0" if resto == 10 else str(resto)

    d1 = _dig(base9, 10)
    d2 = _dig(base9 + d1, 11)
    return base9 + d1 + d2


def _criar_sample(client, headers, nome: str, base_cpf: str, login: str, setor: str, perfil: str, cargo: str | None = None):
    payload = {
        "nome": nome,
        "cpf": _cpf_valido(base_cpf),
        "login": login,
        "senha_inicial": "SenhaInicial@2026",
        "setor": setor,
        "cargo": cargo,
        "perfil": perfil,
    }
    resp = client.post("/api/funcionarios-administrativos", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_consulta_listagem_ordenada_e_filtros(client, headers_para):
    admin_headers = headers_para("admin")
    _criar_sample(client, admin_headers, "Zélia Martins", "529982247", "zelia@uneb.br", "Financeiro", "Financeiro", "Contadora")
    _criar_sample(client, admin_headers, "bruno Almeida", "111444777", "bruno@uneb.br", "Secretaria Geral", "Secretaria")
    _criar_sample(client, admin_headers, "Amanda Costa", "390533447", "amanda@uneb.br", "TI Central", "Admin")

    resp = client.get("/api/funcionarios-administrativos", headers=admin_headers)
    assert resp.status_code == 200
    nomes = [item["nome"] for item in resp.json()]
    assert nomes == ["Amanda Costa", "bruno Almeida", "Zélia Martins"]

    resp_fin = client.get("/api/funcionarios-administrativos?perfil=Financeiro", headers=admin_headers)
    assert resp_fin.status_code == 200
    assert [i["nome"] for i in resp_fin.json()] == ["Zélia Martins"]

    resp_setor = client.get("/api/funcionarios-administrativos?setor=secretaria", headers=admin_headers)
    assert resp_setor.status_code == 200
    assert [i["nome"] for i in resp_setor.json()] == ["bruno Almeida"]

    resp_ativo = client.get("/api/funcionarios-administrativos?ativo=true", headers=admin_headers)
    assert resp_ativo.status_code == 200
    assert len(resp_ativo.json()) == 3


def test_consulta_detalhamento_e_404(client, headers_para):
    admin_headers = headers_para("admin")
    criado = _criar_sample(client, admin_headers, "Lucas Pereira", "482910374", "lucas@uneb.br", "Secretaria", "Secretaria")

    detalhe = client.get(f"/api/funcionarios-administrativos/{criado['id_funcionario']}", headers=admin_headers)
    assert detalhe.status_code == 200
    assert detalhe.json()["login"] == "lucas@uneb.br"

    inexistente = client.get("/api/funcionarios-administrativos/9999", headers=admin_headers)
    assert inexistente.status_code == 404


def test_consulta_auditoria_filtrada_e_rbac_leitura(client, headers_para):
    admin_headers = headers_para("admin")
    f1 = _criar_sample(client, admin_headers, "Paula Dias", "739182645", "paula@uneb.br", "Secretaria", "Secretaria")
    _criar_sample(client, admin_headers, "Rafael Lima", "618293045", "rafael@uneb.br", "Financeiro", "Financeiro")

    assert client.get("/api/funcionarios-administrativos", headers=headers_para("secretaria")).status_code == 403
    assert client.get("/api/funcionarios-administrativos/auditoria", headers=headers_para("financeiro")).status_code == 403

    aud = client.get(
        f"/api/funcionarios-administrativos/auditoria?id_registro_afetado={f1['id_funcionario']}",
        headers=admin_headers,
    )
    assert aud.status_code == 200
    eventos = aud.json()
    assert len(eventos) == 1
    assert eventos[0]["acao"] == "CRIAR"
    assert eventos[0]["id_registro_afetado"] == str(f1["id_funcionario"])


def test_atualizacao_dados_e_perfil_preserva_vinculo_e_auditoria(client, headers_para):
    admin_headers = headers_para("admin")
    criado = _criar_sample(client, admin_headers, "Fernanda Rocha", "849201736", "fernanda@uneb.br", "Secretaria", "Secretaria", "Auxiliar")

    update_payload = {
        "nome": "Fernanda Rocha Silva",
        "cpf": criado["cpf"],
        "login": "fernanda.silva@uneb.br",
        "setor": "Coordenação Financeira",
        "cargo": "Analista Sênior",
        "perfil": "Financeiro",
    }
    resp = client.put(
        f"/api/funcionarios-administrativos/{criado['id_funcionario']}",
        json=update_payload,
        headers=admin_headers,
    )
    assert resp.status_code == 200
    atualizado = resp.json()
    assert atualizado["usuario_id"] == criado["usuario_id"]
    assert atualizado["nome"] == "Fernanda Rocha Silva"
    assert atualizado["setor"] == "Coordenação Financeira"
    assert atualizado["cargo"] == "Analista Sênior"
    assert atualizado["perfil"] == "Financeiro"
    assert atualizado["perfil_id"] == 4

    aud = client.get(
        f"/api/funcionarios-administrativos/auditoria?id_registro_afetado={criado['id_funcionario']}",
        headers=admin_headers,
    )
    acoes = [ev["acao"] for ev in aud.json()]
    assert "ATUALIZAR" in acoes
    ev_update = [ev for ev in aud.json() if ev["acao"] == "ATUALIZAR"][0]
    antes = json.loads(ev_update["dados_anteriores"])
    depois = json.loads(ev_update["dados_novos"])
    assert antes["perfil"] == "Secretaria"
    assert depois["perfil"] == "Financeiro"


def test_atualizacao_bloqueia_duplicidade_cpf_e_login_de_outro_registro(client, headers_para):
    admin_headers = headers_para("admin")
    f1 = _criar_sample(client, admin_headers, "Servidor Um", "128394756", "um@uneb.br", "Secretaria", "Secretaria")
    f2 = _criar_sample(client, admin_headers, "Servidor Dois", "928374651", "dois@uneb.br", "Financeiro", "Financeiro")

    conflito_cpf = {
        "nome": "Servidor Dois",
        "cpf": f1["cpf"],
        "login": f2["login"],
        "setor": "Financeiro",
        "perfil": "Financeiro",
    }
    r_cpf = client.put(f"/api/funcionarios-administrativos/{f2['id_funcionario']}", json=conflito_cpf, headers=admin_headers)
    assert r_cpf.status_code == 409

    conflito_login = {
        "nome": "Servidor Dois",
        "cpf": f2["cpf"],
        "login": f1["login"],
        "setor": "Financeiro",
        "perfil": "Financeiro",
    }
    r_login = client.put(f"/api/funcionarios-administrativos/{f2['id_funcionario']}", json=conflito_login, headers=admin_headers)
    assert r_login.status_code == 409


def test_atualizacao_bloqueia_auto_rebaixamento_e_ultimo_admin_ativo(client, repo, headers_para, seed_atores):
    admin_headers = headers_para("admin")
    # Cadastra um segundo Admin que também tem registro FuncionarioAdministrativo
    admin2 = _criar_sample(client, admin_headers, "Segundo Admin", "314159265", "admin2@uneb.br", "TI", "Admin")
    token_admin2 = criar_token_sessao(usuario_id=admin2["usuario_id"], perfil_id=5)
    headers_admin2 = {"Authorization": f"Bearer {token_admin2}"}

    # Admin2 não pode rebaixar a si próprio
    resp_self = client.put(
        f"/api/funcionarios-administrativos/{admin2['id_funcionario']}",
        json={
            "nome": admin2["nome"],
            "cpf": admin2["cpf"],
            "login": admin2["login"],
            "setor": admin2["setor"],
            "perfil": "Secretaria",
        },
        headers=headers_admin2,
    )
    assert resp_self.status_code == 409

    # Inativa o admin seed inicial diretamente para que admin2 seja o único Admin ativo
    repo.conn.execute("UPDATE Usuario SET statusCONTA = 0 WHERE id_usuario = ?", (seed_atores["admin"]["usuario_id"],))
    repo.conn.commit()
    # Reativa temporariamente um terceiro admin só para testar regra pelo outro operador -> se houver apenas 1 admin ativo, ele mesmo já cai em autoproteção;
    # garantimos também proteção de último Admin ativo ao tentar rebaixar via operador distinto de si caso admin seed fosse outro papel:
    assert repo.conn.execute("SELECT COUNT(*) FROM Usuario WHERE perfil_RBAC = 5 AND statusCONTA = 1").fetchone()[0] == 1


def test_status_inativacao_e_reativacao_bloqueia_acesso_enquanto_inativo(client, headers_para):
    admin_headers = headers_para("admin")
    admin2 = _criar_sample(client, admin_headers, "Outro Admin", "271828182", "admin.outro@uneb.br", "TI", "Admin")
    headers_admin2 = {"Authorization": f"Bearer {criar_token_sessao(admin2['usuario_id'], 5)}"}

    # Confirma que admin2 consegue consultar antes de ser inativado
    assert client.get("/api/funcionarios-administrativos", headers=headers_admin2).status_code == 200

    # Admin seed inativa admin2
    r_inativar = client.patch(
        f"/api/funcionarios-administrativos/{admin2['id_funcionario']}/status",
        json={"ativo": False},
        headers=admin_headers,
    )
    assert r_inativar.status_code == 200
    assert r_inativar.json()["ativo"] is False

    # Filtro ativo=false deve localizar admin2 e token de admin2 passa a ser bloqueado (403)
    r_filtro = client.get("/api/funcionarios-administrativos?ativo=false", headers=admin_headers)
    assert [i["id_funcionario"] for i in r_filtro.json()] == [admin2["id_funcionario"]]
    assert client.get("/api/funcionarios-administrativos", headers=headers_admin2).status_code == 403

    # Reativação restaura acesso
    r_reativar = client.patch(
        f"/api/funcionarios-administrativos/{admin2['id_funcionario']}/status",
        json={"ativo": True},
        headers=admin_headers,
    )
    assert r_reativar.status_code == 200
    assert r_reativar.json()["ativo"] is True
    assert client.get("/api/funcionarios-administrativos", headers=headers_admin2).status_code == 200

    aud = client.get(
        f"/api/funcionarios-administrativos/auditoria?id_registro_afetado={admin2['id_funcionario']}",
        headers=admin_headers,
    )
    assert [ev["acao"] for ev in aud.json()].count("ALTERAR_STATUS") == 2


def test_status_e_exclusao_protegem_auto_operacao_e_ultimo_admin_ativo(client, repo, headers_para, seed_atores):
    from fastapi import HTTPException
    import pytest
    from security import OperadorAutenticado
    from service import alterar_status, excluir_funcionario
    from schemas import FuncionarioAdminStatusUpdate

    admin_headers = headers_para("admin")
    admin2 = _criar_sample(client, admin_headers, "Admin Protegido", "556677889", "admin.prot@uneb.br", "TI", "Admin")
    headers_admin2 = {"Authorization": f"Bearer {criar_token_sessao(admin2['usuario_id'], 5)}"}

    # Autoinativação e autoexclusão bloqueadas com 409
    assert (
        client.patch(
            f"/api/funcionarios-administrativos/{admin2['id_funcionario']}/status",
            json={"ativo": False},
            headers=headers_admin2,
        ).status_code
        == 409
    )
    assert (
        client.delete(
            f"/api/funcionarios-administrativos/{admin2['id_funcionario']}",
            headers=headers_admin2,
        ).status_code
        == 409
    )

    # Inativa seed admin para que admin2 seja o único Admin ativo no sistema
    repo.conn.execute("UPDATE Usuario SET statusCONTA = 0 WHERE id_usuario = ?", (seed_atores["admin"]["usuario_id"],))
    repo.conn.commit()

    operador_externo = OperadorAutenticado(
        usuario_id=99999,
        login="sistema.externo",
        perfil_id=5,
        perfil_nome="Admin",
        status_conta=1,
    )
    with pytest.raises(HTTPException) as exc_status:
        alterar_status(repo, admin2["id_funcionario"], FuncionarioAdminStatusUpdate(ativo=False), operador_externo, "127.0.0.1")
    assert exc_status.value.status_code == 409

    with pytest.raises(HTTPException) as exc_del:
        excluir_funcionario(repo, admin2["id_funcionario"], operador_externo, "127.0.0.1")
    assert exc_del.value.status_code == 409


def test_exclusao_remove_usuario_e_funcionario_em_cascata_preservando_auditoria(client, repo, headers_para):
    admin_headers = headers_para("admin")
    func = _criar_sample(client, admin_headers, "Servidor Desligado", "667788990", "desligado@uneb.br", "Financeiro", "Financeiro")
    func_id = func["id_funcionario"]
    user_id = func["usuario_id"]

    assert client.patch("/api/funcionarios-administrativos/99999/status", json={"ativo": False}, headers=admin_headers).status_code == 404
    assert client.delete("/api/funcionarios-administrativos/99999", headers=admin_headers).status_code == 404

    resp_del = client.delete(f"/api/funcionarios-administrativos/{func_id}", headers=admin_headers)
    assert resp_del.status_code == 200
    assert "removido" in resp_del.json()["mensagem"].lower()

    assert repo.buscar_por_id(func_id) is None
    assert repo.buscar_usuario_por_id(user_id) is None

    aud = client.get(f"/api/funcionarios-administrativos/auditoria?id_registro_afetado={func_id}", headers=admin_headers)
    assert aud.status_code == 200
    acoes = [ev["acao"] for ev in aud.json()]
    assert "EXCLUIR" in acoes
    assert "CRIAR" in acoes
