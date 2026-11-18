"""Testes da US1: cadastro conjunto atômico, validações de domínio e conflitos."""

import pytest

from security import verify_password


def _cpf_valido(base9: str) -> str:
    """Gera CPF matematicamente válido (módulo 11) a partir de 9 dígitos."""
    def _dig(parcial: str, peso: int) -> str:
        soma = sum(int(ch) * (peso - i) for i, ch in enumerate(parcial))
        resto = (soma * 10) % 11
        return "0" if resto == 10 else str(resto)

    d1 = _dig(base9, 10)
    d2 = _dig(base9 + d1, 11)
    return base9 + d1 + d2


@pytest.mark.parametrize(
    ("perfil", "perfil_id_esperado", "base_cpf", "login", "setor", "cargo"),
    [
        ("Secretaria", 3, "529982247", "Maria.Sec@UNEB.br", "Secretaria Acadêmica", "Secretária Geral"),
        ("Financeiro", 4, "111444777", "joao.fin@uneb.br", "Tesouraria", None),
        ("Admin", 5, "390533447", "admin.novo@uneb.br", "TI e Governança", "   "),
    ],
)
def test_cadastrar_funcionario_para_cada_perfil_administrativo(
    client, repo, headers_para, perfil, perfil_id_esperado, base_cpf, login, setor, cargo
):
    cpf_digitos = _cpf_valido(base_cpf)
    cpf_mascarado = f" {cpf_digitos[:3]}.{cpf_digitos[3:6]}.{cpf_digitos[6:9]}-{cpf_digitos[9:]} "
    payload = {
        "nome": "  Servidor Teste  ",
        "cpf": cpf_mascarado,
        "login": f"  {login}  ",
        "senha_inicial": "Provisoria@2026",
        "setor": f"  {setor}  ",
        "cargo": cargo,
        "perfil": perfil,
    }

    resp = client.post("/api/funcionarios-administrativos", json=payload, headers=headers_para("admin"))
    assert resp.status_code == 201, resp.text
    corpo = resp.json()

    assert corpo["id_funcionario"] >= 1
    assert corpo["usuario_id"] >= 1
    assert corpo["nome"] == "Servidor Teste"
    assert corpo["cpf"] == cpf_digitos
    assert corpo["login"] == login.strip().lower()
    assert corpo["setor"] == setor.strip()
    assert corpo["cargo"] == (cargo.strip() if cargo and cargo.strip() else None)
    assert corpo["perfil"] == perfil
    assert corpo["perfil_id"] == perfil_id_esperado
    assert corpo["ativo"] is True
    assert corpo["senha_provisoria"] is True

    usuario = repo.buscar_usuario_por_id(corpo["usuario_id"])
    assert usuario is not None
    assert usuario["perfil_RBAC"] == perfil_id_esperado
    assert usuario["statusCONTA"] == 1
    assert usuario["senha_hash"] != "Provisoria@2026"
    assert verify_password("Provisoria@2026", usuario["senha_hash"])

    logs = repo.conn.execute(
        "SELECT * FROM LogAuditoriaSistema WHERE acao = 'CRIAR' AND id_registro_afetado = ?",
        (str(corpo["id_funcionario"]),),
    ).fetchall()
    assert len(logs) == 1
    assert logs[0]["entidade_afetada"] == "FuncionarioAdministrativo"


def test_cadastro_bloqueia_cpf_duplicado_e_nao_deixa_usuario_orfao(client, repo, headers_para):
    cpf_dup = _cpf_valido("482910374")
    primeiro = {
        "nome": "Ana Paula",
        "cpf": cpf_dup,
        "login": "ana.paula@uneb.br",
        "senha_inicial": "SenhaSegura@1",
        "setor": "Secretaria",
        "perfil": "Secretaria",
    }
    assert client.post("/api/funcionarios-administrativos", json=primeiro, headers=headers_para("admin")).status_code == 201

    total_usuarios_antes = repo.conn.execute("SELECT COUNT(*) FROM Usuario").fetchone()[0]
    total_func_antes = repo.conn.execute("SELECT COUNT(*) FROM FuncionarioAdministrativo").fetchone()[0]

    segundo = {
        "nome": "Ana Duplicada",
        "cpf": f"{cpf_dup[:3]}.{cpf_dup[3:6]}.{cpf_dup[6:9]}-{cpf_dup[9:]}",
        "login": "ana.outra@uneb.br",
        "senha_inicial": "SenhaSegura@2",
        "setor": "Financeiro",
        "perfil": "Financeiro",
    }
    resp = client.post("/api/funcionarios-administrativos", json=segundo, headers=headers_para("admin"))
    assert resp.status_code == 409
    assert "CPF" in resp.json()["detail"]

    assert repo.conn.execute("SELECT COUNT(*) FROM Usuario").fetchone()[0] == total_usuarios_antes
    assert repo.conn.execute("SELECT COUNT(*) FROM FuncionarioAdministrativo").fetchone()[0] == total_func_antes


def test_cadastro_bloqueia_login_duplicado_com_conta_preexistente_sem_registro_parcial(
    client, repo, headers_para, seed_atores
):
    total_usuarios_antes = repo.conn.execute("SELECT COUNT(*) FROM Usuario").fetchone()[0]
    total_func_antes = repo.conn.execute("SELECT COUNT(*) FROM FuncionarioAdministrativo").fetchone()[0]

    payload = {
        "nome": "Conflito Login",
        "cpf": _cpf_valido("739182645"),
        "login": str(seed_atores["secretaria"]["login"]),
        "senha_inicial": "SenhaSegura@1",
        "setor": "Secretaria",
        "perfil": "Secretaria",
    }
    resp = client.post("/api/funcionarios-administrativos", json=payload, headers=headers_para("admin"))
    assert resp.status_code == 409
    assert "login" in resp.json()["detail"].lower()

    assert repo.conn.execute("SELECT COUNT(*) FROM Usuario").fetchone()[0] == total_usuarios_antes
    assert repo.conn.execute("SELECT COUNT(*) FROM FuncionarioAdministrativo").fetchone()[0] == total_func_antes


@pytest.mark.parametrize(
    ("campo", "valor_invalido"),
    [
        ("nome", "  ab  "),
        ("cpf", "11111111111"),
        ("cpf", "52998224720"),
        ("cpf", "12345"),
        ("login", "login com espaco"),
        ("login", "ab"),
        ("senha_inicial", "1234567"),
        ("senha_inicial", "        "),
        ("setor", " "),
        ("cargo", "A"),
        ("perfil", "Aluno"),
        ("perfil", "Professor"),
    ],
)
def test_cadastro_rejeita_campos_e_perfis_invalidos(client, headers_para, campo, valor_invalido):
    payload = {
        "nome": "Servidor Válido",
        "cpf": _cpf_valido("618293045"),
        "login": "servidor.valido@uneb.br",
        "senha_inicial": "SenhaForte@2026",
        "setor": "Financeiro",
        "cargo": "Analista",
        "perfil": "Financeiro",
    }
    payload[campo] = valor_invalido
    resp = client.post("/api/funcionarios-administrativos", json=payload, headers=headers_para("admin"))
    assert resp.status_code == 422
