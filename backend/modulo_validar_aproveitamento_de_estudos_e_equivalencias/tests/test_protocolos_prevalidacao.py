"""Testes da US2: Protocolo e Pré-Validação de Solicitações de Aproveitamento (SGA-26)."""

from typing import Any
from fastapi.testclient import TestClient

from .conftest import auth_header


def test_abrir_protocolo_equivalencia_interna_elegivel_e_com_pendencias(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])
    d = dados_base["disciplinas"]

    # Cadastrar equivalência ativa SI101 (60h) -> SI201 (60h)
    eq = client.post(
        "/api/aproveitamentos/equivalencias",
        json={
            "disciplina_origem_id": d["origem_60h"],
            "disciplina_equivalente_id": d["alvo_60h"],
            "portaria_aprovacao": "Portaria 01/2026",
        },
        headers=headers,
    ).json()

    # 1. Lucas (aprovado em SI101 com 8.5, 60h) -> pré-validação elegível = True
    r_ok = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_ativo"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "EQUIVALENCIA_INTERNA",
            "disciplina_origem_id": d["origem_60h"],
            "documentacao_comprobatoria": "Histórico interno 2026.1",
        },
        headers=headers,
    )
    assert r_ok.status_code == 201, r_ok.text
    sol = r_ok.json()
    assert sol["protocolo"].startswith("APR-")
    assert sol["status_solicitacao"] == "EM_ANALISE"
    assert sol["equivalencia_id"] == eq["id_equivalencia"]
    assert sol["nota_obtida"] == 8.5
    assert sol["carga_horaria_cursada"] == 60
    assert sol["pre_validacao"]["elegivel"] is True
    assert sol["pre_validacao"]["equivalencia_ativa_encontrada"] is True
    assert sol["pre_validacao"]["aprovacao_interna_comprovada"] is True
    assert sol["pre_validacao"]["percentual_carga_horaria"] == 100.0
    assert sol["pre_validacao"]["pendencias"] == []

    # 2. Pedro (sem aprovação em SI101) -> protocolo aberto com elegivel = False e pendências
    r_pend = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_sem_aprovacao"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "EQUIVALENCIA_INTERNA",
            "disciplina_origem_id": d["origem_60h"],
        },
        headers=headers,
    )
    assert r_pend.status_code == 201
    sol_pend = r_pend.json()
    assert sol_pend["pre_validacao"]["elegivel"] is False
    assert sol_pend["pre_validacao"]["aprovacao_interna_comprovada"] is False
    assert len(sol_pend["pre_validacao"]["pendencias"]) >= 1


def test_abrir_protocolo_estudos_externos_elegivel_e_inelegivel(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])
    d = dados_base["disciplinas"]

    # 1. Estudos externos elegível (CH 45h = 75% de 60h, nota 7.0)
    r_ok = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_ativo"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "ESTUDOS_EXTERNOS",
            "instituicao_origem": "UFBA",
            "disciplina_externa_nome": "Introdução à Programação",
            "carga_horaria_cursada": 45,
            "nota_obtida": 7.0,
            "ementa_resumo": "Variáveis, controle de fluxo, funções, ponteiros e arquivos.",
        },
        headers=headers,
    )
    assert r_ok.status_code == 201, r_ok.text
    sol = r_ok.json()
    assert sol["pre_validacao"]["elegivel"] is True
    assert sol["pre_validacao"]["percentual_carga_horaria"] == 75.0
    assert sol["pre_validacao"]["nota_aprovada"] is True

    # 2. Estudos externos com nota < 6.00 e CH < 75% (30h = 50%) -> elegivel = False
    r_ineleg = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_sem_aprovacao"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "ESTUDOS_EXTERNOS",
            "instituicao_origem": "Instituição Externa",
            "disciplina_externa_nome": "Programação Básica",
            "carga_horaria_cursada": 30,
            "nota_obtida": 5.5,
            "ementa_resumo": "Conteúdo introdutório básico de algoritmos.",
        },
        headers=headers,
    )
    assert r_ineleg.status_code == 201
    pv = r_ineleg.json()["pre_validacao"]
    assert pv["elegivel"] is False
    assert pv["nota_aprovada"] is False
    assert pv["carga_horaria_compativel"] is False
    assert len(pv["pendencias"]) == 2


def test_bloqueios_abertura_protocolo_e_listagem_filtrada(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["admin"])
    d = dados_base["disciplinas"]

    # Aluno inexistente -> 404
    assert (
        client.post(
            "/api/aproveitamentos/solicitacoes",
            json={
                "aluno_matricula": 99999999,
                "disciplina_alvo_id": d["alvo_60h"],
                "modalidade": "EQUIVALENCIA_INTERNA",
                "disciplina_origem_id": d["origem_60h"],
            },
            headers=headers,
        ).status_code
        == 404
    )

    # Aluno TRANCADO -> 422
    r_tranc = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_trancado"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "EQUIVALENCIA_INTERNA",
            "disciplina_origem_id": d["origem_60h"],
        },
        headers=headers,
    )
    assert r_tranc.status_code == 422
    assert "TRANCADO" in r_tranc.json()["detail"]

    # Nota fora de 0.00..10.00 -> 422
    r_nota = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_ativo"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "ESTUDOS_EXTERNOS",
            "instituicao_origem": "UFBA",
            "disciplina_externa_nome": "Algoritmos",
            "carga_horaria_cursada": 60,
            "nota_obtida": 10.5,
            "ementa_resumo": "Conteúdo completo de algoritmos e estruturas.",
        },
        headers=headers,
    )
    assert r_nota.status_code == 422

    # Disciplina alvo já aprovada pelo aluno (SI202) -> 409
    r_ja_aprov = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_ativo"],
            "disciplina_alvo_id": d["alvo_ja_aprovada"],
            "modalidade": "EQUIVALENCIA_INTERNA",
            "disciplina_origem_id": d["origem_60h"],
        },
        headers=headers,
    )
    assert r_ja_aprov.status_code == 409

    # Protocolo duplicado EM_ANALISE -> 409
    payload = {
        "aluno_matricula": dados_base["mat_ativo"],
        "disciplina_alvo_id": d["alvo_60h"],
        "modalidade": "EQUIVALENCIA_INTERNA",
        "disciplina_origem_id": d["origem_60h"],
    }
    r1 = client.post("/api/aproveitamentos/solicitacoes", json=payload, headers=headers)
    assert r1.status_code == 201
    r2 = client.post("/api/aproveitamentos/solicitacoes", json=payload, headers=headers)
    assert r2.status_code == 409

    # Listagem filtrada e detalhamento
    r_list = client.get(
        "/api/aproveitamentos/solicitacoes",
        params={"aluno_matricula": dados_base["mat_ativo"], "status_solicitacao": "EM_ANALISE"},
        headers=headers,
    )
    assert r_list.status_code == 200
    assert len(r_list.json()) == 1
    sol_id = r1.json()["id_solicitacao"]
    assert client.get(f"/api/aproveitamentos/solicitacoes/{sol_id}", headers=headers).status_code == 200
    assert client.get("/api/aproveitamentos/solicitacoes/99999", headers=headers).status_code == 404
