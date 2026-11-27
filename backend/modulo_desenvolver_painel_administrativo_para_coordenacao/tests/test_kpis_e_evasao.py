"""Testes da US1: Painel de KPIs, Evasão e Alertas de Risco Acadêmico (SGA-27)."""

from typing import Any
from fastapi.testclient import TestClient

from .conftest import auth_header


def test_obter_resumo_painel_filtrado_e_curso_vazio_sem_divisao_por_zero(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])

    r = client.get(
        "/api/coordenacao/painel/resumo",
        params={"curso_id": dados_base["curso_si"], "periodo_letivo_id": dados_base["periodo_atual"]},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["curso_nome"] == "Sistemas de Informação"
    assert body["periodo_letivo_codigo"] == "2026.2"
    assert body["processos_abertos"] == 1
    assert body["matriculas_ativas_turmas"] == 2
    assert body["trancamentos_deferidos"] == 1
    assert body["movimentacoes_evasao_deferidas"] == 2
    assert body["docentes_ativos_alocados"] == 2
    assert body["total_turmas_ofertadas"] == 6  # exclui t_cancel
    assert body["total_alunos_vinculados"] == 4
    assert body["total_alunos_ativos"] == 2
    assert body["ira_medio_ativos"] == 6.8  # (8.8 + 4.8) / 2
    assert body["taxa_evasao_percentual"] == 50.0  # 2 evadidos únicos / 4

    # Curso vazio não deve causar erro de divisão por zero
    r_vazio = client.get(
        "/api/coordenacao/painel/resumo",
        params={"curso_id": dados_base["curso_vazio"]},
        headers=headers,
    )
    assert r_vazio.status_code == 200
    vazio = r_vazio.json()
    assert vazio["total_alunos_vinculados"] == 0
    assert vazio["taxa_ocupacao_media_percentual"] == 0.0
    assert vazio["ira_medio_ativos"] == 0.0
    assert vazio["taxa_evasao_percentual"] == 0.0

    # Filtros inexistentes -> 404
    assert client.get("/api/coordenacao/painel/resumo", params={"curso_id": 9999}, headers=headers).status_code == 404
    assert (
        client.get("/api/coordenacao/painel/resumo", params={"periodo_letivo_id": 9999}, headers=headers).status_code
        == 404
    )


def test_relatorio_evasao_e_alertas_risco_com_minimizacao_lgpd(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["admin"])

    r = client.get(
        "/api/coordenacao/relatorios/evasao",
        params={"curso_id": dados_base["curso_si"], "periodo_letivo_id": dados_base["periodo_atual"]},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_alunos_vinculados"] == 4
    assert body["alunos_em_evasao_unicos"] == 2
    assert body["taxa_evasao_percentual"] == 50.0
    assert body["movimentacoes_por_tipo"] == {
        "TRANCAMENTO": 1,
        "TRANSFERENCIA": 0,
        "CANCELAMENTO": 1,
        "JUBILAMENTO": 0,
    }
    assert body["total_alertas_risco"] == 1
    alerta = body["alertas_risco"][0]
    assert alerta["matricula"] == dados_base["alunos"]["risco"]
    assert alerta["ira"] == 4.8
    assert alerta["menor_frequencia_percentual"] == 65.0
    assert len(alerta["motivos_alerta"]) == 2

    # Minimização LGPD: sem CPF, e-mail, telefone ou data de nascimento
    texto = r.text.lower()
    for sensivel in ("15350946056", "carlos@sga.edu.br", "71999998888", "2002-07-10"):
        assert sensivel not in texto
