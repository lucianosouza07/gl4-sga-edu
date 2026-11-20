"""Testes unitários e de integração para o ciclo de vida do consentimento LGPD (US1)."""

import pytest


def test_obter_termo_vigente_publico(client):
    """Garante que a rota de termos vigentes seja acessível e retorne a versão corrente com finalidades."""
    resp = client.get("/api/lgpd/termos/vigente")
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["versao"] == "v1.0"
    assert len(dados["finalidades"]) >= 2
    finalidade_academica = next(f for f in dados["finalidades"] if f["codigo"] == "TRATAMENTO_ACADEMICO")
    assert finalidade_academica["obrigatoria"] is True


def test_status_consentimento_sem_aceite_previo(client, aluno_headers):
    """Valida que um usuário sem aceite prévio reporte possui_aceite_vigente = False."""
    resp = client.get("/api/lgpd/consentimentos/status", headers=aluno_headers)
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["possui_aceite_vigente"] is False
    assert dados["consentimentos_ativos"] == []


def test_aceite_consentimento_com_sucesso(client, aluno_headers):
    """Testa o aceite formal de consentimento com finalidades obrigatória e opcional."""
    payload = {
        "versao_termo": "v1.0",
        "finalidades": ["TRATAMENTO_ACADEMICO", "COMUNICACAO_INSTITUCIONAL"],
    }
    resp = client.post(
        "/api/lgpd/consentimentos/aceitar",
        headers={**aluno_headers, "X-Forwarded-For": "189.40.10.25"},
        json=payload,
    )
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["versao_termo"] == "v1.0"
    assert dados["total_aceites_gravados"] == 2

    # Verifica status após o aceite
    status_resp = client.get("/api/lgpd/consentimentos/status", headers=aluno_headers)
    assert status_resp.status_code == 200
    status_dados = status_resp.json()
    assert status_dados["possui_aceite_vigente"] is True
    assert "TRATAMENTO_ACADEMICO" in status_dados["consentimentos_ativos"]
    assert "COMUNICACAO_INSTITUCIONAL" in status_dados["consentimentos_ativos"]


def test_rejeicao_aceite_versao_invalida(client, aluno_headers):
    """Valida que o aceite de uma versão que não seja a vigente seja rejeitado."""
    payload = {
        "versao_termo": "v99.0",
        "finalidades": ["TRATAMENTO_ACADEMICO"],
    }
    resp = client.post("/api/lgpd/consentimentos/aceitar", headers=aluno_headers, json=payload)
    assert resp.status_code == 400
    assert "Versão do termo inválida" in resp.json()["detail"]


def test_rejeicao_aceite_sem_finalidade_obrigatoria(client, aluno_headers):
    """Garante que o aceite seja recusado se a finalidade essencial/obrigatória for omitida."""
    payload = {
        "versao_termo": "v1.0",
        "finalidades": ["COMUNICACAO_INSTITUCIONAL"],
    }
    resp = client.post("/api/lgpd/consentimentos/aceitar", headers=aluno_headers, json=payload)
    assert resp.status_code == 400
    assert "finalidades obrigatórias não foram aceitas" in resp.json()["detail"]


def test_revogacao_finalidade_opcional_sucesso(client, aluno_headers):
    """Valida que uma finalidade opcional previamente aceita possa ser revogada com sucesso."""
    # 1. Primeiro aceita
    client.post(
        "/api/lgpd/consentimentos/aceitar",
        headers=aluno_headers,
        json={"versao_termo": "v1.0", "finalidades": ["TRATAMENTO_ACADEMICO", "COMUNICACAO_INSTITUCIONAL"]},
    )

    # 2. Em seguida revoga a opcional
    resp_revog = client.post(
        "/api/lgpd/consentimentos/revogar",
        headers={**aluno_headers, "X-Real-IP": "201.55.10.4"},
        json={"versao_termo": "v1.0", "finalidade": "COMUNICACAO_INSTITUCIONAL"},
    )
    assert resp_revog.status_code == 200
    dados_revog = resp_revog.json()
    assert dados_revog["finalidade"] == "COMUNICACAO_INSTITUCIONAL"
    assert "data_revogacao" in dados_revog

    # 3. Status deve manter apenas a finalidade obrigatória ativa
    status_resp = client.get("/api/lgpd/consentimentos/status", headers=aluno_headers)
    assert "COMUNICACAO_INSTITUCIONAL" not in status_resp.json()["consentimentos_ativos"]
    assert "TRATAMENTO_ACADEMICO" in status_resp.json()["consentimentos_ativos"]
    assert status_resp.json()["possui_aceite_vigente"] is True


def test_rejeicao_revogacao_finalidade_obrigatoria(client, aluno_headers):
    """Impede que o titular revogue finalidades essenciais vinculadas a obrigações legais."""
    client.post(
        "/api/lgpd/consentimentos/aceitar",
        headers=aluno_headers,
        json={"versao_termo": "v1.0", "finalidades": ["TRATAMENTO_ACADEMICO"]},
    )
    resp = client.post(
        "/api/lgpd/consentimentos/revogar",
        headers=aluno_headers,
        json={"versao_termo": "v1.0", "finalidade": "TRATAMENTO_ACADEMICO"},
    )
    assert resp.status_code == 400
    assert "Finalidades obrigatórias" in resp.json()["detail"]
