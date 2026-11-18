"""Testes da User Story 2: Listagem, filtros, consulta por matrícula, atualização e status (SGA-15)."""

from fastapi.testclient import TestClient
from modulo_cadastrar_alunos.repository import AlunoRepository
from .conftest import gerar_cpf_valido


def test_listagem_alfabetica_filtros_e_consulta_por_matricula(
    client: TestClient,
    repo: AlunoRepository,
    secretaria_headers: dict[str, str],
) -> None:
    curso_2 = repo.inserir_curso_seed(codigo_mec="MEC-PED-2026", nome="Licenciatura em Pedagogia")

    alunos_seed = [
        {
            "nome": "Carlos Eduardo Souza",
            "cpf": gerar_cpf_valido("201202203"),
            "email": "carlos.souza@uneb.br",
            "curso_id": 1,
            "login": "carlos.souza",
            "senha_inicial": "SenhaForte@2026",
        },
        {
            "nome": "Ana Beatriz Lima",
            "cpf": gerar_cpf_valido("301302303"),
            "email": "ana.lima@uneb.br",
            "curso_id": curso_2,
            "login": "ana.lima",
            "senha_inicial": "SenhaForte@2026",
        },
        {
            "nome": "Bruno Henrique Alves",
            "cpf": gerar_cpf_valido("401402403"),
            "email": "bruno.alves@uneb.br",
            "curso_id": 1,
            "login": "bruno.alves",
            "senha_inicial": "SenhaForte@2026",
        },
    ]

    criados = []
    for item in alunos_seed:
        r = client.post("/api/alunos", json=item, headers=secretaria_headers)
        assert r.status_code == 201
        criados.append(r.json())

    # Listagem padrão em ordem alfabética
    r_lista = client.get("/api/alunos", headers=secretaria_headers)
    assert r_lista.status_code == 200
    nomes = [a["nome"] for a in r_lista.json()]
    assert nomes == ["Ana Beatriz Lima", "Bruno Henrique Alves", "Carlos Eduardo Souza"]

    # Filtro por curso_id
    r_curso = client.get(f"/api/alunos?curso_id={curso_2}", headers=secretaria_headers)
    assert r_curso.status_code == 200
    assert len(r_curso.json()) == 1
    assert r_curso.json()[0]["nome"] == "Ana Beatriz Lima"

    # Filtro por busca textual
    r_busca = client.get("/api/alunos?busca=bruno.alves", headers=secretaria_headers)
    assert r_busca.status_code == 200
    assert len(r_busca.json()) == 1
    assert r_busca.json()[0]["nome"] == "Bruno Henrique Alves"

    # Consulta individual por matrícula
    mat_ana = criados[1]["matricula"]
    r_detalhe = client.get(f"/api/alunos/{mat_ana}", headers=secretaria_headers)
    assert r_detalhe.status_code == 200
    assert r_detalhe.json()["email"] == "ana.lima@uneb.br"

    # Consulta por matrícula inexistente -> 404
    r_404 = client.get("/api/alunos/99999999", headers=secretaria_headers)
    assert r_404.status_code == 404


def test_atualizacao_cadastral_academica_e_alteracao_status_conta(
    client: TestClient,
    secretaria_headers: dict[str, str],
) -> None:
    cpf_1 = gerar_cpf_valido("501502503")
    cpf_2 = gerar_cpf_valido("601602603")

    r1 = client.post(
        "/api/alunos",
        json={
            "nome": "Fernanda Dias",
            "cpf": cpf_1,
            "email": "fernanda.dias@uneb.br",
            "telefone": "71988881111",
            "data_nascimento": "2003-08-20",
            "curso_id": 1,
            "login": "fernanda.dias",
            "senha_inicial": "SenhaForte@2026",
        },
        headers=secretaria_headers,
    )
    assert r1.status_code == 201
    mat_1 = r1.json()["matricula"]

    r2 = client.post(
        "/api/alunos",
        json={
            "nome": "Gabriel Moreira",
            "cpf": cpf_2,
            "email": "gabriel.moreira@uneb.br",
            "login": "gabriel.moreira",
            "senha_inicial": "SenhaForte@2026",
        },
        headers=secretaria_headers,
    )
    assert r2.status_code == 201

    # Atualização válida de dados cadastrais e situação acadêmica
    r_upd = client.put(
        f"/api/alunos/{mat_1}",
        json={
            "nome": "Fernanda Dias Santos",
            "cpf": cpf_1,
            "email": "fernanda.santos@uneb.br",
            "telefone": "71977772222",
            "data_nascimento": "2003-08-20",
            "curso_id": 1,
            "login": "fernanda.santos",
            "status_academico": "TRANCADO",
        },
        headers=secretaria_headers,
    )
    assert r_upd.status_code == 200, r_upd.text
    atualizado = r_upd.json()
    assert atualizado["nome"] == "Fernanda Dias Santos"
    assert atualizado["email"] == "fernanda.santos@uneb.br"
    assert atualizado["login"] == "fernanda.santos"
    assert atualizado["status_academico"] == "TRANCADO"

    # Filtro por status_academico=TRANCADO
    r_trancados = client.get("/api/alunos?status_academico=TRANCADO", headers=secretaria_headers)
    assert r_trancados.status_code == 200
    assert len(r_trancados.json()) == 1
    assert r_trancados.json()[0]["matricula"] == mat_1

    # Tentativa de atualizar com e-mail já pertencente a outro aluno -> 409 Conflict
    r_conflito = client.put(
        f"/api/alunos/{mat_1}",
        json={
            "nome": "Fernanda Dias Santos",
            "cpf": cpf_1,
            "email": "gabriel.moreira@uneb.br",
            "login": "fernanda.santos",
            "status_academico": "TRANCADO",
        },
        headers=secretaria_headers,
    )
    assert r_conflito.status_code == 409

    # Inativação e reativação da conta de acesso (PATCH /api/alunos/{matricula}/status)
    r_inativar = client.patch(
        f"/api/alunos/{mat_1}/status",
        json={"ativo": False},
        headers=secretaria_headers,
    )
    assert r_inativar.status_code == 200
    assert r_inativar.json()["ativo"] is False

    r_inativos = client.get("/api/alunos?ativo=false", headers=secretaria_headers)
    assert r_inativos.status_code == 200
    assert len(r_inativos.json()) == 1
    assert r_inativos.json()[0]["matricula"] == mat_1

    r_reativar = client.patch(
        f"/api/alunos/{mat_1}/status",
        json={"ativo": True},
        headers=secretaria_headers,
    )
    assert r_reativar.status_code == 200
    assert r_reativar.json()["ativo"] is True
