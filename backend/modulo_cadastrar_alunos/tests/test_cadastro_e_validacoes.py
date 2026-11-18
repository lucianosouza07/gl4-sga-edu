"""Testes da User Story 1: Cadastro oficial de novo aluno, matrícula e validações (SGA-15)."""

from fastapi.testclient import TestClient
from modulo_cadastrar_alunos.repository import AlunoRepository
from modulo_cadastrar_alunos.security import verify_password
from .conftest import gerar_cpf_valido


def test_cadastro_aluno_com_matricula_automatica_por_secretaria(
    client: TestClient,
    repo: AlunoRepository,
    secretaria_headers: dict[str, str],
) -> None:
    cpf_valido = gerar_cpf_valido("529982247")
    payload = {
        "nome": "  Mariana Costa Oliveira  ",
        "cpf": f"{cpf_valido[:3]}.{cpf_valido[3:6]}.{cpf_valido[6:9]}-{cpf_valido[9:]}",
        "email": "  Mariana.Oliveira@UNEB.br  ",
        "telefone": "(71) 99888-7766",
        "data_nascimento": "2004-05-14",
        "curso_id": 1,
        "login": "  Mariana.Oliveira@UNEB.br  ",
        "senha_inicial": "Uneb@2026Forte",
    }

    resp = client.post("/api/alunos", json=payload, headers=secretaria_headers)
    assert resp.status_code == 201, resp.text
    dados = resp.json()

    assert dados["matricula"] >= 20260001
    assert dados["nome"] == "Mariana Costa Oliveira"
    assert dados["cpf"] == cpf_valido
    assert dados["email"] == "mariana.oliveira@uneb.br"
    assert dados["telefone"] == "71998887766"
    assert dados["data_nascimento"] == "2004-05-14"
    assert dados["curso_id"] == 1
    assert dados["curso_nome"] == "Sistemas de Informação"
    assert dados["status_academico"] == "ATIVO"
    assert dados["ira"] == 0.0
    assert dados["login"] == "mariana.oliveira@uneb.br"
    assert dados["perfil_id"] == 1
    assert dados["perfil"] == "Aluno"
    assert dados["ativo"] is True
    assert dados["senha_provisoria"] is True
    assert "senha" not in dados
    assert "senha_hash" not in dados
    assert "senha_inicial" not in dados

    usuario_db = repo.buscar_usuario_por_id(dados["usuario_id"])
    assert usuario_db is not None
    assert usuario_db["perfil_RBAC"] == 1
    assert usuario_db["statusCONTA"] == 1
    assert verify_password("Uneb@2026Forte", usuario_db["senha_hash"]) is True


def test_cadastro_aluno_com_matricula_explicita_por_admin(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    cpf_valido = gerar_cpf_valido("123456789")
    payload = {
        "matricula": 20269999,
        "nome": "Lucas Mendes Rocha",
        "cpf": cpf_valido,
        "email": "lucas.rocha@uneb.br",
        "login": "lucas.rocha",
        "senha_inicial": "SenhaInicial@123",
    }

    resp = client.post("/api/alunos", json=payload, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    dados = resp.json()

    assert dados["matricula"] == 20269999
    assert dados["curso_id"] is None
    assert dados["curso_nome"] is None
    assert dados["telefone"] is None
    assert dados["data_nascimento"] is None
    assert dados["status_academico"] == "ATIVO"
    assert dados["ira"] == 0.0
    assert dados["perfil"] == "Aluno"


def test_duplicidade_cpf_email_login_matricula_faz_rollback_sem_usuario_orfao(
    client: TestClient,
    repo: AlunoRepository,
    secretaria_headers: dict[str, str],
) -> None:
    cpf_1 = gerar_cpf_valido("111222333")
    cpf_2 = gerar_cpf_valido("444555666")

    base = {
        "matricula": 20260100,
        "nome": "Aluno Base",
        "cpf": cpf_1,
        "email": "aluno.base@uneb.br",
        "login": "aluno.base",
        "senha_inicial": "SenhaValida@2026",
    }
    r1 = client.post("/api/alunos", json=base, headers=secretaria_headers)
    assert r1.status_code == 201

    # 1. Conflito de matrícula
    r_mat = client.post(
        "/api/alunos",
        json={
            **base,
            "cpf": cpf_2,
            "email": "outro1@uneb.br",
            "login": "outro1.login",
        },
        headers=secretaria_headers,
    )
    assert r_mat.status_code == 409
    assert "matrícula" in r_mat.json()["detail"].lower()
    assert repo.buscar_usuario_por_login("outro1.login") is None

    # 2. Conflito de CPF
    r_cpf = client.post(
        "/api/alunos",
        json={
            **base,
            "matricula": 20260101,
            "email": "outro2@uneb.br",
            "login": "outro2.login",
        },
        headers=secretaria_headers,
    )
    assert r_cpf.status_code == 409
    assert "cpf" in r_cpf.json()["detail"].lower()
    assert repo.buscar_usuario_por_login("outro2.login") is None

    # 3. Conflito de e-mail
    r_email = client.post(
        "/api/alunos",
        json={
            **base,
            "matricula": 20260102,
            "cpf": cpf_2,
            "login": "outro3.login",
        },
        headers=secretaria_headers,
    )
    assert r_email.status_code == 409
    assert "e-mail" in r_email.json()["detail"].lower()
    assert repo.buscar_usuario_por_login("outro3.login") is None

    # 4. Conflito de login
    r_login = client.post(
        "/api/alunos",
        json={
            **base,
            "matricula": 20260103,
            "cpf": cpf_2,
            "email": "outro4@uneb.br",
        },
        headers=secretaria_headers,
    )
    assert r_login.status_code == 409
    assert "login" in r_login.json()["detail"].lower()


def test_validacoes_campos_invalidos_e_curso_inexistente(
    client: TestClient,
    secretaria_headers: dict[str, str],
) -> None:
    cpf_valido = gerar_cpf_valido("777888999")
    base = {
        "nome": "Estudante Teste",
        "cpf": cpf_valido,
        "email": "estudante.teste@uneb.br",
        "login": "estudante.teste",
        "senha_inicial": "SenhaValida@2026",
    }

    # CPF com sequência repetida
    r_rep = client.post(
        "/api/alunos",
        json={**base, "cpf": "111.111.111-11"},
        headers=secretaria_headers,
    )
    assert r_rep.status_code == 422

    # CPF com dígito verificador incorreto
    cpf_dv_errado = cpf_valido[:-1] + ("0" if cpf_valido[-1] != "0" else "1")
    r_dv = client.post(
        "/api/alunos",
        json={**base, "cpf": cpf_dv_errado},
        headers=secretaria_headers,
    )
    assert r_dv.status_code == 422

    # E-mail inválido
    r_email = client.post(
        "/api/alunos",
        json={**base, "email": "email-invalido-sem-arroba"},
        headers=secretaria_headers,
    )
    assert r_email.status_code == 422

    # Data de nascimento futura
    r_data = client.post(
        "/api/alunos",
        json={**base, "data_nascimento": "2099-01-01"},
        headers=secretaria_headers,
    )
    assert r_data.status_code == 422

    # Telefone com quantidade inválida de dígitos
    r_tel = client.post(
        "/api/alunos",
        json={**base, "telefone": "71999"},
        headers=secretaria_headers,
    )
    assert r_tel.status_code == 422

    # Senha apenas com espaços
    r_senha = client.post(
        "/api/alunos",
        json={**base, "senha_inicial": "        "},
        headers=secretaria_headers,
    )
    assert r_senha.status_code == 422

    # Curso inexistente -> 404 Not Found
    r_curso = client.post(
        "/api/alunos",
        json={**base, "curso_id": 9999},
        headers=secretaria_headers,
    )
    assert r_curso.status_code == 404
    assert "curso" in r_curso.json()["detail"].lower()
