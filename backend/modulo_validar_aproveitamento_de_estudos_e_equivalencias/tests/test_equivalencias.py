"""Testes da US1: Cadastro e Gestão de Regras de Equivalência entre Disciplinas (SGA-26)."""

from typing import Any
from fastapi.testclient import TestClient

from .conftest import auth_header


def test_cadastrar_listar_detalhar_e_atualizar_equivalencia(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])
    d = dados_base["disciplinas"]

    r_create = client.post(
        "/api/aproveitamentos/equivalencias",
        json={
            "disciplina_origem_id": d["origem_60h"],
            "disciplina_equivalente_id": d["alvo_60h"],
            "portaria_aprovacao": "Portaria COL-SI 014/2026",
        },
        headers=headers,
    )
    assert r_create.status_code == 201, r_create.text
    eq = r_create.json()
    assert eq["disciplina_origem_codigo"] == "SI101"
    assert eq["disciplina_equivalente_codigo"] == "SI201"
    assert eq["portaria_aprovacao"] == "Portaria COL-SI 014/2026"
    assert eq["ativa"] is True

    # Direcionalidade: cadastrar o sentido inverso (B -> A) é permitido como regra separada
    r_inv = client.post(
        "/api/aproveitamentos/equivalencias",
        json={
            "disciplina_origem_id": d["alvo_60h"],
            "disciplina_equivalente_id": d["origem_60h"],
            "portaria_aprovacao": "Portaria COL-SI 015/2026",
        },
        headers=headers,
    )
    assert r_inv.status_code == 201

    # Listagem filtrada
    r_list = client.get(
        "/api/aproveitamentos/equivalencias",
        params={"disciplina_origem_id": d["origem_60h"], "ativa": True},
        headers=headers,
    )
    assert r_list.status_code == 200
    assert len(r_list.json()) == 1
    assert r_list.json()[0]["id_equivalencia"] == eq["id_equivalencia"]

    # Detalhamento
    r_det = client.get(f"/api/aproveitamentos/equivalencias/{eq['id_equivalencia']}", headers=headers)
    assert r_det.status_code == 200
    assert r_det.json()["portaria_aprovacao"] == "Portaria COL-SI 014/2026"

    # Atualização de portaria e inativação
    r_upd = client.patch(
        f"/api/aproveitamentos/equivalencias/{eq['id_equivalencia']}",
        json={"portaria_aprovacao": "Portaria COL-SI 099/2026", "ativa": False},
        headers=headers,
    )
    assert r_upd.status_code == 200
    assert r_upd.json()["portaria_aprovacao"] == "Portaria COL-SI 099/2026"
    assert r_upd.json()["ativa"] is False


def test_bloquear_auto_equivalencia_duplicidade_e_disciplina_inexistente(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["admin"])
    d = dados_base["disciplinas"]

    # Auto-equivalência -> 422
    r_auto = client.post(
        "/api/aproveitamentos/equivalencias",
        json={"disciplina_origem_id": d["alvo_60h"], "disciplina_equivalente_id": d["alvo_60h"]},
        headers=headers,
    )
    assert r_auto.status_code == 422

    # Disciplina inexistente -> 404
    r_404 = client.post(
        "/api/aproveitamentos/equivalencias",
        json={"disciplina_origem_id": 9999, "disciplina_equivalente_id": d["alvo_60h"]},
        headers=headers,
    )
    assert r_404.status_code == 404

    # Cadastro válido seguido de duplicidade -> 409
    r_ok = client.post(
        "/api/aproveitamentos/equivalencias",
        json={"disciplina_origem_id": d["origem_60h"], "disciplina_equivalente_id": d["alvo_60h"]},
        headers=headers,
    )
    assert r_ok.status_code == 201

    r_dup = client.post(
        "/api/aproveitamentos/equivalencias",
        json={"disciplina_origem_id": d["origem_60h"], "disciplina_equivalente_id": d["alvo_60h"]},
        headers=headers,
    )
    assert r_dup.status_code == 409
    assert "Já existe uma regra" in r_dup.json()["detail"]

    # Atualização vazia -> 422; ID inexistente -> 404
    assert (
        client.patch(f"/api/aproveitamentos/equivalencias/{r_ok.json()['id_equivalencia']}", json={}, headers=headers).status_code
        == 422
    )
    assert client.get("/api/aproveitamentos/equivalencias/9999", headers=headers).status_code == 404
