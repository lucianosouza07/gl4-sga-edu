import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import event

from app.core.security import criar_token_jwt
from app.models.aluno import Aluno
from app.models.usuario import Usuario
from app.services.aluno_service import AlunoService
from app.services.dashboard_service import DashboardService


AGORA = datetime(2026, 10, 15, 15, tzinfo=timezone.utc)


def adicionar_aluno(db, numero, criado_em, status="ATIVO", usuario_ativo=True):
    usuario = Usuario(
        id=uuid.UUID(int=numero), nome=f"Aluno {numero}", email=f"aluno{numero}@teste.edu",
        senha_hash="hash-nao-utilizado", perfil="ALUNO", ativo=usuario_ativo,
    )
    aluno = Aluno(
        id=uuid.UUID(int=numero), usuario=usuario, matricula=str(202620000 + numero),
        nome_completo=usuario.nome, email=usuario.email, cpf=f"{numero:011d}",
        data_nascimento=date(2005, 1, 1), criado_em=criado_em, status=status,
    )
    db.add(aluno)
    db.commit()
    return aluno


def test_dashboard_vazio(db_session):
    resultado = DashboardService(db_session).obter_dashboard("ano", agora=AGORA)
    assert resultado.totais.model_dump() == {
        "alunos": 0, "ativos": 0, "inativos": 0, "novas_matriculas": 0,
    }
    assert resultado.ano == 2026 and resultado.semestre == 2
    assert resultado.gerado_em == AGORA
    assert resultado.periodo.inicio == date(2026, 1, 1)
    assert resultado.periodo.fim == date(2026, 10, 15)
    assert len(resultado.matriculas_por_mes) == 10
    assert all(mes.total == 0 for mes in resultado.matriculas_por_mes)
    assert [mes.parcial for mes in resultado.matriculas_por_mes] == [False] * 9 + [True]
    assert resultado.alunos_por_status == [] and resultado.ultimos_cadastros == []


def test_dashboard_conta_todos_os_registros_e_status_sem_paginacao(db_session):
    for numero in range(1, 106):
        status = ["ATIVO", "INATIVO", "TRANCADO", "FORMADO", "LEGADO"][(numero - 1) % 5]
        adicionar_aluno(db_session, numero, datetime(2026, 10, 1, 4), status, usuario_ativo=False)
    comandos = []
    def registrar(conn, cursor, statement, parameters, context, executemany):
        comandos.append(statement)
    event.listen(db_session.bind, "before_cursor_execute", registrar)
    try:
        resultado = DashboardService(db_session).obter_dashboard("ano", agora=AGORA)
    finally:
        event.remove(db_session.bind, "before_cursor_execute", registrar)
    assert resultado.totais.alunos == resultado.totais.novas_matriculas == 105
    assert resultado.totais.ativos == resultado.totais.inativos == 21
    assert {item.status: item.total for item in resultado.alunos_por_status} == {
        "ATIVO": 21, "INATIVO": 21, "TRANCADO": 21, "FORMADO": 21, "LEGADO": 21,
    }
    assert [item.id.int for item in resultado.ultimos_cadastros] == [105, 104, 103, 102]
    assert all(item.criado_em.tzinfo is not None for item in resultado.ultimos_cadastros)
    assert len(comandos) == 2  # Uma agregação e uma consulta limitada, sem N+1.


@pytest.mark.parametrize("periodo, inicio, meses", [
    ("3", date(2025, 11, 1), ["2025-11", "2025-12", "2026-01"]),
    ("6", date(2025, 8, 1), ["2025-08", "2025-09", "2025-10", "2025-11", "2025-12", "2026-01"]),
    ("ano", date(2026, 1, 1), ["2026-01"]),
])
def test_dashboard_periodos_cruzam_virada_do_ano(db_session, periodo, inicio, meses):
    resultado = DashboardService(db_session).obter_dashboard(
        periodo, agora=datetime(2026, 1, 20, 12, tzinfo=timezone.utc),
    )
    assert resultado.periodo.inicio == inicio
    assert [item.mes for item in resultado.matriculas_por_mes] == meses
    assert resultado.semestre == 1


def test_dashboard_limites_bahia_e_futuro(db_session):
    datas = [
        datetime(2026, 8, 1, 2, 59, 59),  # Julho na Bahia: fora dos três meses.
        datetime(2026, 8, 1, 3),
        datetime(2026, 9, 1, 2, 59, 59),  # Agosto na Bahia.
        datetime(2026, 9, 1, 3),
        datetime(2026, 10, 1, 2, 59, 59),  # Setembro na Bahia.
        datetime(2026, 10, 1, 3),
        datetime(2026, 10, 15, 15),       # Inclui o instante da consulta.
        datetime(2026, 10, 15, 15, 0, 1), # Futuro: não entra na série.
    ]
    for numero, criado_em in enumerate(datas, start=1):
        adicionar_aluno(db_session, numero, criado_em)
    resultado = DashboardService(db_session).obter_dashboard("3", agora=AGORA)
    assert [(mes.mes, mes.total) for mes in resultado.matriculas_por_mes] == [
        ("2026-08", 2), ("2026-09", 2), ("2026-10", 2),
    ]
    assert resultado.totais.alunos == 8 and resultado.totais.novas_matriculas == 6


def test_dashboard_periodo_nao_filtra_totais_nem_cadastros_recentes(db_session):
    adicionar_aluno(db_session, 1, datetime(2025, 1, 1, 12), "INATIVO")
    adicionar_aluno(db_session, 2, datetime(2026, 10, 2, 12))
    resultado = DashboardService(db_session).obter_dashboard("3", agora=AGORA)
    assert resultado.totais.alunos == 2 and resultado.totais.novas_matriculas == 1
    assert [item.id.int for item in resultado.ultimos_cadastros] == [2, 1]


def test_dashboard_recentes_priorizam_data_antes_do_id(db_session):
    for numero, dia in [(1, 14), (2, 13), (3, 13), (4, 12), (5, 11), (6, 10)]:
        adicionar_aluno(db_session, numero, datetime(2026, 10, dia, 12))
    resultado = DashboardService(db_session).obter_dashboard("3", agora=AGORA)
    assert [item.id.int for item in resultado.ultimos_cadastros] == [1, 3, 2, 4]


@pytest.mark.parametrize("agora, ano, semestre, ultimo_mes", [
    (datetime(2026, 1, 1, 2, 59, 59, tzinfo=timezone.utc), 2025, 2, "2025-12"),
    (datetime(2026, 1, 1, 3, tzinfo=timezone.utc), 2026, 1, "2026-01"),
    (datetime(2026, 7, 1, 2, 59, 59, tzinfo=timezone.utc), 2026, 1, "2026-06"),
    (datetime(2026, 7, 1, 3, tzinfo=timezone.utc), 2026, 2, "2026-07"),
])
def test_dashboard_calendario_civil_bahia(db_session, agora, ano, semestre, ultimo_mes):
    resultado = DashboardService(db_session).obter_dashboard("ano", agora=agora)
    assert (resultado.ano, resultado.semestre) == (ano, semestre)
    assert resultado.matriculas_por_mes[-1].mes == ultimo_mes


def test_dashboard_inativacao_e_reativacao_nao_criam_matriculas(db_session):
    aluno = adicionar_aluno(db_session, 1, datetime(2026, 10, 1, 12))
    servico = DashboardService(db_session)
    AlunoService(db_session).inativar_aluno(aluno.id)
    inativo = servico.obter_dashboard("ano", agora=AGORA)
    assert inativo.totais.ativos == 0 and inativo.totais.inativos == 1
    assert inativo.totais.novas_matriculas == 1
    AlunoService(db_session).reativar_aluno(aluno.id)
    ativo = servico.obter_dashboard("ano", agora=AGORA)
    assert ativo.totais.ativos == 1 and ativo.totais.inativos == 0
    assert ativo.totais.novas_matriculas == 1


@pytest.mark.parametrize("headers_fixture", ["admin_headers", "secretaria_headers"])
def test_api_dashboard_perfis_autorizados(client, request, headers_fixture, db_session):
    adicionar_aluno(db_session, 99, datetime(2020, 1, 1, 12))
    resposta = client.get("/api/v1/dashboard", headers=request.getfixturevalue(headers_fixture))
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["periodo"]["chave"] == "ano"
    assert dados["totais"]["alunos"] == 1
    assert dados["gerado_em"].endswith("Z")
    assert set(dados["ultimos_cadastros"][0]) == {
        "id", "nome_completo", "matricula", "status", "criado_em",
    }
    assert dados["ultimos_cadastros"][0]["criado_em"].endswith("Z")


@pytest.mark.parametrize("perfil", ["PROFESSOR", "ALUNO"])
def test_api_dashboard_perfis_negados(client, db_session, perfil):
    usuario = Usuario(nome="Acesso restrito", email="restrito@teste.edu", senha_hash="hash", perfil=perfil)
    db_session.add(usuario)
    db_session.commit()
    token = criar_token_jwt({"sub": str(usuario.id)})
    assert client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"}).status_code == 403


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer invalido"}])
def test_api_dashboard_autenticacao_invalida(client, headers):
    assert client.get("/api/v1/dashboard", headers=headers).status_code == 401


@pytest.mark.parametrize("periodo", ["", "12", "mes", "ANO"])
def test_api_dashboard_periodo_invalido(client, admin_headers, periodo):
    assert client.get("/api/v1/dashboard", params={"periodo": periodo}, headers=admin_headers).status_code == 422


@pytest.mark.parametrize("periodo, quantidade_meses", [("3", 3), ("6", 6)])
def test_api_dashboard_periodos_validos(client, admin_headers, periodo, quantidade_meses):
    resposta = client.get("/api/v1/dashboard", params={"periodo": periodo}, headers=admin_headers)
    assert resposta.status_code == 200
    assert resposta.json()["periodo"]["chave"] == periodo
    assert len(resposta.json()["matriculas_por_mes"]) == quantidade_meses
