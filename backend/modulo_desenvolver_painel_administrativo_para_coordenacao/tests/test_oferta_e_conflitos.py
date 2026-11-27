"""Testes da US2: Painel de Oferta de Turmas e Diagnóstico de Conflitos (SGA-27)."""

from typing import Any
from fastapi.testclient import TestClient

from .conftest import auth_header


def test_listar_oferta_turmas_com_filtros_ocupacao_e_pendencias(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])

    r = client.get(
        "/api/coordenacao/oferta/turmas",
        params={"periodo_letivo_id": dados_base["periodo_atual"], "curso_id": dados_base["curso_si"]},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    por_codigo = {item["codigo_turma"]: item for item in r.json()}

    assert por_codigo["SI101-A"]["taxa_ocupacao_percentual"] == 100.0
    assert "lotacao_esgotada" in por_codigo["SI101-A"]["pendencias"]
    assert por_codigo["SI301-PEND"]["pendencias"] == ["sem_professor", "sem_sala", "sem_horarios"]

    # Filtro por turno
    r_mat = client.get(
        "/api/coordenacao/oferta/turmas",
        params={"periodo_letivo_id": dados_base["periodo_atual"], "turno": "MATUTINO"},
        headers=headers,
    )
    assert r_mat.status_code == 200
    assert [i["codigo_turma"] for i in r_mat.json()] == ["SI301-PEND"]


def test_diagnosticar_conflitos_detecta_sala_e_docente_ignorando_contiguos_e_canceladas(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["admin"])

    r = client.get(
        "/api/coordenacao/oferta/conflitos",
        params={"periodo_letivo_id": dados_base["periodo_atual"], "curso_id": dados_base["curso_si"]},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()

    # Exatamente 2 conflitos reais:
    # 1) CHOQUE_SALA: SI101-A (19:00-20:40) vs SI201-A (20:00-21:40) na B1-101 -> 20:00-20:40
    # 2) CHOQUE_DOCENTE: SI101-A (19:00-20:40) vs SI301-A (19:30-21:10) Prof. Alex -> 19:30-20:40
    # Horários contíguos (SI201-B 19:00-20:40 vs SI101-B 20:40-22:20) e SI301-CANC (CANCELADA) NÃO geram conflito!
    assert body["total_conflitos"] == 2
    assert body["total_choques_sala"] == 1
    assert body["total_choques_docente"] == 1

    por_tipo = {c["tipo_conflito"]: c for c in body["conflitos"]}
    assert por_tipo["CHOQUE_SALA"]["intervalo_conflitante"] == "20:00-20:40"
    assert {por_tipo["CHOQUE_SALA"]["turma_a_codigo"], por_tipo["CHOQUE_SALA"]["turma_b_codigo"]} == {
        "SI101-A",
        "SI201-A",
    }
    assert por_tipo["CHOQUE_DOCENTE"]["intervalo_conflitante"] == "19:30-20:40"
    assert {por_tipo["CHOQUE_DOCENTE"]["turma_a_codigo"], por_tipo["CHOQUE_DOCENTE"]["turma_b_codigo"]} == {
        "SI101-A",
        "SI301-A",
    }

    assert len(body["turmas_com_pendencias"]) == 1
    assert body["turmas_com_pendencias"][0]["codigo_turma"] == "SI301-PEND"

    # Período limpo sem conflitos nem pendências
    r_limpo = client.get(
        "/api/coordenacao/oferta/conflitos",
        params={"periodo_letivo_id": dados_base["periodo_limpo"]},
        headers=headers,
    )
    assert r_limpo.status_code == 200
    assert r_limpo.json()["total_conflitos"] == 0
    assert r_limpo.json()["turmas_com_pendencias"] == []
