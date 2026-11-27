"""Testes da US3: Central de Requerimentos, Despachos e Alocação do Corpo Docente (SGA-27)."""

import sqlite3
from typing import Any
from fastapi.testclient import TestClient
import pytest

from .conftest import auth_header
from ..repository import PainelCoordenacaoRepository


def test_fila_requerimentos_despacho_atomico_imutabilidade_e_bloqueio_delete(
    client: TestClient, repo: PainelCoordenacaoRepository, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])
    req_aberto = dados_base["requerimentos"]["aberto"]
    req_deferido = dados_base["requerimentos"]["deferido"]

    # Listagem filtrada por status ABERTO
    r_list = client.get(
        "/api/coordenacao/requerimentos",
        params={"status_requerimento": "ABERTO"},
        headers=headers,
    )
    assert r_list.status_code == 200
    assert len(r_list.json()) == 1
    assert r_list.json()[0]["protocolo"] == "REQ-2026-0001"
    assert "52998224725" not in r_list.text

    # Detalhamento
    assert client.get(f"/api/coordenacao/requerimentos/{req_aberto}", headers=headers).status_code == 200
    assert client.get("/api/coordenacao/requerimentos/99999", headers=headers).status_code == 404

    # Parecer curto demais -> 422
    assert (
        client.patch(
            f"/api/coordenacao/requerimentos/{req_aberto}/despachar",
            json={"novo_status": "EM_ANALISE", "parecer": "ok"},
            headers=headers,
        ).status_code
        == 422
    )

    # Despacho ABERTO -> EM_ANALISE -> DEFERIDO
    r_analise = client.patch(
        f"/api/coordenacao/requerimentos/{req_aberto}/despachar",
        json={"novo_status": "EM_ANALISE", "parecer": "Encaminhado ao docente para conferência da prova."},
        headers=headers,
    )
    assert r_analise.status_code == 200
    assert r_analise.json()["status_requerimento"] == "EM_ANALISE"

    r_def = client.patch(
        f"/api/coordenacao/requerimentos/{req_aberto}/despachar",
        json={"novo_status": "DEFERIDO", "parecer": "Revisão deferida com ajuste registrado no diário."},
        headers=headers,
    )
    assert r_def.status_code == 200
    assert r_def.json()["status_requerimento"] == "DEFERIDO"
    assert r_def.json()["atualizado_em"] is not None

    # Tentativa de alterar requerimento já encerrado -> 409 Conflict
    r_imut = client.patch(
        f"/api/coordenacao/requerimentos/{req_deferido}/despachar",
        json={"novo_status": "INDEFERIDO", "parecer": "Tentativa indevida de reversão."},
        headers=headers,
    )
    assert r_imut.status_code == 409

    # Bloqueio de exclusão física via API (405) e trigger SQLite
    assert client.delete(f"/api/coordenacao/requerimentos/{req_aberto}", headers=headers).status_code == 405
    with pytest.raises(sqlite3.IntegrityError, match="preservacao historica"):
        repo.conn.execute("DELETE FROM RequerimentoAcademico WHERE id_requerimento = ?", (req_aberto,))


def test_relatorio_alocacao_docentes_exclui_canceladas_e_protege_dados_lgpd(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["admin"])

    r = client.get(
        "/api/coordenacao/docentes/alocacao",
        params={"curso_id": dados_base["curso_si"], "periodo_letivo_id": dados_base["periodo_atual"]},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    por_nome = {d["nome"]: d for d in r.json()}

    # Prof. Alex: t1 (60h, 2 alunos) + t3 (60h, 0 alunos); t_cancel NÃO conta!
    assert por_nome["Prof. Alex Coelho"]["total_turmas"] == 2
    assert por_nome["Prof. Alex Coelho"]["carga_horaria_total"] == 120
    assert por_nome["Prof. Alex Coelho"]["total_alunos_atendidos"] == 2

    # Profa. Ana: t2 (60h) + t4 (60h) + t5 (60h) = 3 turmas, 180h
    assert por_nome["Profa. Ana Rocha"]["total_turmas"] == 3
    assert por_nome["Profa. Ana Rocha"]["carga_horaria_total"] == 180

    # Minimização LGPD: sem CPF, e-mail ou telefone de professores
    texto = r.text.lower()
    for sensivel in ("11122233344", "alex@sga.edu.br", "71977776666"):
        assert sensivel not in texto
