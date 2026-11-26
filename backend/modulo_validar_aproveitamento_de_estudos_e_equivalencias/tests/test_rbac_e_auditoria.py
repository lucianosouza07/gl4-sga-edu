"""Testes da US4: Governança de Acesso RBAC e Trilha de Auditoria LGPD (SGA-26)."""

from typing import Any
from fastapi.testclient import TestClient

from .conftest import auth_header


def test_rbac_bloqueia_anonimos_tokens_invalidos_perfis_sem_permissao_e_conta_inativa(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    d = dados_base["disciplinas"]
    rotas = [
        ("POST", "/api/aproveitamentos/equivalencias", {"disciplina_origem_id": d["origem_60h"], "disciplina_equivalente_id": d["alvo_60h"]}),
        ("GET", "/api/aproveitamentos/equivalencias", None),
        ("GET", "/api/aproveitamentos/equivalencias/1", None),
        ("PATCH", "/api/aproveitamentos/equivalencias/1", {"ativa": False}),
        ("POST", "/api/aproveitamentos/solicitacoes", {"aluno_matricula": dados_base["mat_ativo"], "disciplina_alvo_id": d["alvo_60h"], "modalidade": "EQUIVALENCIA_INTERNA", "disciplina_origem_id": d["origem_60h"]}),
        ("GET", "/api/aproveitamentos/solicitacoes", None),
        ("GET", "/api/aproveitamentos/solicitacoes/1", None),
        ("PATCH", "/api/aproveitamentos/solicitacoes/1/deliberar", {"decisao": "INDEFERIDO", "parecer_tecnico": "Parecer de teste válido."}),
        ("DELETE", "/api/aproveitamentos/solicitacoes/1", None),
        ("GET", f"/api/aproveitamentos/alunos/{dados_base['mat_ativo']}/dispensas", None),
        ("GET", f"/api/aproveitamentos/alunos/{dados_base['mat_ativo']}/disciplinas/{d['avancada']}/pre-requisitos", None),
        ("GET", "/api/aproveitamentos/auditoria", None),
    ]

    for metodo, url, payload in rotas:
        assert client.request(metodo, url, json=payload).status_code == 401
        assert client.request(metodo, url, json=payload, headers=auth_header("invalido.token")).status_code == 401
        assert client.request(metodo, url, json=payload, headers=auth_header(dados_base["tokens"]["expirado"])).status_code == 401

        for perfil in ("aluno", "professor", "financeiro", "inativo"):
            resp = client.request(metodo, url, json=payload, headers=auth_header(dados_base["tokens"][perfil]))
            assert resp.status_code == 403, f"{metodo} {url} deveria retornar 403 para {perfil}"


def test_trilha_auditoria_registra_todas_operacoes_com_higienizacao_lgpd(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    d = dados_base["disciplinas"]
    headers_sec = {
        **auth_header(dados_base["tokens"]["secretaria"]),
        "X-Forwarded-For": "203.0.113.88, 10.0.0.2",
    }
    headers_admin = {
        **auth_header(dados_base["tokens"]["admin"]),
        "X-Forwarded-For": "198.51.100.99",
    }

    # 1. Criar equivalência (Secretaria)
    eq = client.post(
        "/api/aproveitamentos/equivalencias",
        json={"disciplina_origem_id": d["origem_60h"], "disciplina_equivalente_id": d["alvo_60h"], "portaria_aprovacao": "Portaria 10/2026"},
        headers=headers_sec,
    ).json()

    # 2. Protocolar solicitação (Secretaria)
    sol = client.post(
        "/api/aproveitamentos/solicitacoes",
        json={
            "aluno_matricula": dados_base["mat_ativo"],
            "disciplina_alvo_id": d["alvo_60h"],
            "modalidade": "EQUIVALENCIA_INTERNA",
            "disciplina_origem_id": d["origem_60h"],
        },
        headers=headers_sec,
    ).json()

    # 3. Deferir solicitação -> cria SolicitacaoAproveitamento DEFERIDO + DispensaDisciplina CONSOLIDAR_DISPENSA (Admin)
    client.patch(
        f"/api/aproveitamentos/solicitacoes/{sol['id_solicitacao']}/deliberar",
        json={"decisao": "DEFERIDO", "parecer_tecnico": "Aprovado pelo colegiado do curso."},
        headers=headers_admin,
    )

    # Consultar trilha geral
    r_aud = client.get("/api/aproveitamentos/auditoria", headers=headers_admin)
    assert r_aud.status_code == 200
    eventos = r_aud.json()
    assert len(eventos) == 4
    assert [(e["entidade_afetada"], e["acao"]) for e in eventos] == [
        ("DispensaDisciplina", "CONSOLIDAR_DISPENSA"),
        ("SolicitacaoAproveitamento", "DEFERIDO"),
        ("SolicitacaoAproveitamento", "PROTOCOLAR"),
        ("EquivalenciaDisciplina", "CRIAR"),
    ]
    assert eventos[0]["ip_origem"] == "198.51.100.99"
    assert eventos[0]["usuario_id"] == dados_base["usuarios"]["admin"]
    assert eventos[3]["ip_origem"] == "203.0.113.88"
    assert eventos[3]["usuario_id"] == dados_base["usuarios"]["secretaria"]

    # Filtro por entidade e registro
    r_eq_aud = client.get(
        "/api/aproveitamentos/auditoria",
        params={"entidade_afetada": "EquivalenciaDisciplina", "id_registro_afetado": str(eq["id_equivalencia"])},
        headers=headers_admin,
    )
    assert r_eq_aud.status_code == 200
    assert len(r_eq_aud.json()) == 1

    # Nenhum dado pessoal sensível LGPD nos snapshots de auditoria
    aud_texto = r_aud.text.lower()
    for sensivel in ("52998224725", "lucas.pereira@sga.edu.br", "71988887777", "2003-04-15", "hash_fake", "senha"):
        assert sensivel not in aud_texto
