"""Testes da US3: Deliberação Formal, Dispensas, Pré-Requisitos e Imutabilidade (SGA-26)."""

import sqlite3
from typing import Any
from fastapi.testclient import TestClient
import pytest

from .conftest import auth_header
from ..repository import AproveitamentoRepository


def test_deferimento_atomico_gera_dispensa_e_libera_prerequisitos(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])
    d = dados_base["disciplinas"]

    # Antes da dispensa: Lucas tem SI202 aprovada, mas SI201 pendente -> NÃO apto para SI301
    r_pre_antes = client.get(
        f"/api/aproveitamentos/alunos/{dados_base['mat_ativo']}/disciplinas/{d['avancada']}/pre-requisitos",
        headers=headers,
    )
    assert r_pre_antes.status_code == 200
    assert r_pre_antes.json()["apto_para_matricula"] is False

    # Cadastrar equivalência ativa SI101 -> SI201 e protocolar
    client.post(
        "/api/aproveitamentos/equivalencias",
        json={"disciplina_origem_id": d["origem_60h"], "disciplina_equivalente_id": d["alvo_60h"]},
        headers=headers,
    )
    sol = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_ativo"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "EQUIVALENCIA_INTERNA",
            "disciplina_origem_id": d["origem_60h"],
        },
        headers=headers,
    ).json()

    # Deferir com parecer técnico
    r_def = client.patch(
        f"/api/aproveitamentos/solicitacoes/{sol['id_solicitacao']}/deliberar",
        json={
            "decisao": "DEFERIDO",
            "parecer_tecnico": "Equivalência vigente verificada e aprovação comprovada no histórico interno.",
        },
        headers=headers,
    )
    assert r_def.status_code == 200, r_def.text
    body = r_def.json()
    assert body["solicitacao"]["status_solicitacao"] == "DEFERIDO"
    assert body["solicitacao"]["deliberado_em"] is not None
    assert body["dispensa"] is not None
    assert body["dispensa"]["disciplina_codigo"] == "SI201"
    assert body["dispensa"]["nota_aproveitada"] == 8.5
    assert body["dispensa"]["carga_horaria_aproveitada"] == 60

    # Consultar dispensas do aluno
    r_disp = client.get(
        f"/api/aproveitamentos/alunos/{dados_base['mat_ativo']}/dispensas",
        headers=headers,
    )
    assert r_disp.status_code == 200
    assert r_disp.json()["total_disciplinas_dispensadas"] == 1
    assert r_disp.json()["carga_horaria_total_aproveitada"] == 60

    # Agora pré-requisitos de SI301 (SI201 por dispensa + SI202 por aprovação em turma) -> APTO!
    r_pre_depois = client.get(
        f"/api/aproveitamentos/alunos/{dados_base['mat_ativo']}/disciplinas/{d['avancada']}/pre-requisitos",
        headers=headers,
    )
    assert r_pre_depois.status_code == 200
    pre = r_pre_depois.json()
    assert pre["apto_para_matricula"] is True
    origens = {item["codigo"]: item["origem_atendimento"] for item in pre["requisitos"]}
    assert origens["SI201"] == "DISPENSA_APROVEITAMENTO"
    assert origens["SI202"] == "APROVADO_TURMA"

    # Novo protocolo para disciplina já dispensada -> 409 Conflict
    r_dup_disp = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_ativo"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "EQUIVALENCIA_INTERNA",
            "disciplina_origem_id": d["origem_60h"],
        },
        headers=headers,
    )
    assert r_dup_disp.status_code == 409


def test_revalidacao_bloqueia_deferimento_se_equivalencia_inativada_e_permite_indeferimento_e_reabertura(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])
    d = dados_base["disciplinas"]

    eq = client.post(
        "/api/aproveitamentos/equivalencias",
        json={"disciplina_origem_id": d["origem_60h"], "disciplina_equivalente_id": d["alvo_60h"]},
        headers=headers,
    ).json()

    sol = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_ativo"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "EQUIVALENCIA_INTERNA",
            "disciplina_origem_id": d["origem_60h"],
        },
        headers=headers,
    ).json()
    assert sol["pre_validacao"]["elegivel"] is True

    # Inativar equivalência enquanto o protocolo ainda está em análise
    client.patch(
        f"/api/aproveitamentos/equivalencias/{eq['id_equivalencia']}",
        json={"ativa": False},
        headers=headers,
    )

    # Tentativa de deferir agora deve ser bloqueada (422) pela revalidação!
    r_def_block = client.patch(
        f"/api/aproveitamentos/solicitacoes/{sol['id_solicitacao']}/deliberar",
        json={"decisao": "DEFERIDO", "parecer_tecnico": "Tentativa com equivalência revogada."},
        headers=headers,
    )
    assert r_def_block.status_code == 422
    assert "inativa" in r_def_block.json()["detail"].lower()

    # Indeferir formalmente com parecer -> 200 OK sem criar dispensa
    r_indef = client.patch(
        f"/api/aproveitamentos/solicitacoes/{sol['id_solicitacao']}/deliberar",
        json={"decisao": "INDEFERIDO", "parecer_tecnico": "Regra de equivalência suspensa por portaria."},
        headers=headers,
    )
    assert r_indef.status_code == 200
    assert r_indef.json()["solicitacao"]["status_solicitacao"] == "INDEFERIDO"
    assert r_indef.json()["dispensa"] is None

    # Tentar redeliberar protocolo já encerrado -> 409 Conflict
    r_redelib = client.patch(
        f"/api/aproveitamentos/solicitacoes/{sol['id_solicitacao']}/deliberar",
        json={"decisao": "DEFERIDO", "parecer_tecnico": "Tentativa de alterar decisão encerrada."},
        headers=headers,
    )
    assert r_redelib.status_code == 409

    # Após indeferimento, é permitido abrir NOVO protocolo para a mesma disciplina alvo
    r_novo = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_ativo"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "ESTUDOS_EXTERNOS",
            "instituicao_origem": "UFBA",
            "disciplina_externa_nome": "Algoritmos II",
            "carga_horaria_cursada": 60,
            "nota_obtida": 8.0,
            "ementa_resumo": "Algoritmos estruturados, modularização e estruturas básicas.",
        },
        headers=headers,
    )
    assert r_novo.status_code == 201
    assert r_novo.json()["protocolo"] != sol["protocolo"]


def test_bloqueio_exclusao_fisica_api_e_triggers_sqlite_e_rollback_atomico(
    client: TestClient, repo: AproveitamentoRepository, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["admin"])
    d = dados_base["disciplinas"]

    sol = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_ativo"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "ESTUDOS_EXTERNOS",
            "instituicao_origem": "UNEB",
            "disciplina_externa_nome": "Algoritmos",
            "carga_horaria_cursada": 60,
            "nota_obtida": 8.0,
            "ementa_resumo": "Estruturas de controle, funções, recursão e registros.",
        },
        headers=headers,
    ).json()

    delib = client.patch(
        f"/api/aproveitamentos/solicitacoes/{sol['id_solicitacao']}/deliberar",
        json={"decisao": "DEFERIDO", "parecer_tecnico": "Ementa e carga horária compatíveis."},
        headers=headers,
    ).json()

    # Bloqueio DELETE via API -> 405 Method Not Allowed
    r_del = client.delete(f"/api/aproveitamentos/solicitacoes/{sol['id_solicitacao']}", headers=headers)
    assert r_del.status_code == 405

    # Bloqueio DELETE via trigger SQLite em DispensaDisciplina e SolicitacaoAproveitamento encerrada
    with pytest.raises(sqlite3.IntegrityError, match="preservacao historica"):
        repo.conn.execute("DELETE FROM DispensaDisciplina WHERE id_dispensa = ?", (delib["dispensa"]["id_dispensa"],))
    with pytest.raises(sqlite3.IntegrityError, match="preservacao historica"):
        repo.conn.execute(
            "DELETE FROM SolicitacaoAproveitamento WHERE id_solicitacao = ?", (sol["id_solicitacao"],)
        )

    # Rollback atômico em falha ao inserir DispensaDisciplina (nota inválida > 10 viola CHECK)
    sol2 = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_sem_aprovacao"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "ESTUDOS_EXTERNOS",
            "instituicao_origem": "UNEB",
            "disciplina_externa_nome": "Algoritmos",
            "carga_horaria_cursada": 60,
            "nota_obtida": 8.0,
            "ementa_resumo": "Estruturas de controle, funções, recursão e registros.",
        },
        headers=headers,
    ).json()

    with pytest.raises(sqlite3.IntegrityError):
        repo.deliberar_solicitacao_atomico(
            id_solicitacao=sol2["id_solicitacao"],
            decisao="DEFERIDO",
            parecer_tecnico="Teste de rollback transacional",
            deliberado_por_usuario_id=dados_base["usuarios"]["admin"],
            deliberado_em="2026-11-26T18:00:00+00:00",
            ip_origem="127.0.0.1",
            dados_anteriores_sol_json="{}",
            dados_novos_sol_json="{}",
            criar_dispensa=True,
            aluno_matricula=dados_base["mat_sem_aprovacao"],
            disciplina_id=d["alvo_60h"],
            modalidade="ESTUDOS_EXTERNOS",
            nota_aproveitada=15.0,  # viola CHECK (0..10)
            carga_horaria_aproveitada=60,
            dados_novos_dispensa_json="{}",
        )

    sol2_recheck = repo.buscar_solicitacao_por_id(sol2["id_solicitacao"])
    assert sol2_recheck is not None
    assert sol2_recheck["status_solicitacao"] == "EM_ANALISE"
    assert repo.buscar_dispensa_por_aluno_e_disciplina(dados_base["mat_sem_aprovacao"], d["alvo_60h"]) is None
