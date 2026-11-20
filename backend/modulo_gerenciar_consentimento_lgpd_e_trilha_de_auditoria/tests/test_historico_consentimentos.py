"""Testes unitários e de integração para histórico de consentimentos e autodeterminação do titular (US4)."""


def test_titular_consulta_proprio_historico(client, aluno_headers):
    """Garante que o titular consulte todo o seu histórico de manifestações."""
    # Aceita duas finalidades
    client.post(
        "/api/lgpd/consentimentos/aceitar",
        headers={**aluno_headers, "X-Forwarded-For": "189.1.2.3"},
        json={"versao_termo": "v1.0", "finalidades": ["TRATAMENTO_ACADEMICO", "COMUNICACAO_INSTITUCIONAL"]},
    )
    # Revoga uma finalidade opcional
    client.post(
        "/api/lgpd/consentimentos/revogar",
        headers={**aluno_headers, "X-Forwarded-For": "189.1.2.4"},
        json={"versao_termo": "v1.0", "finalidade": "COMUNICACAO_INSTITUCIONAL"},
    )

    resp = client.get("/api/lgpd/consentimentos/historico", headers=aluno_headers)
    assert resp.status_code == 200
    historico = resp.json()

    assert len(historico) == 2
    item_revogado = next(i for i in historico if i["finalidade"] == "COMUNICACAO_INSTITUCIONAL")
    assert item_revogado["aceito"] is False
    assert item_revogado["data_revogacao"] is not None

    item_ativo = next(i for i in historico if i["finalidade"] == "TRATAMENTO_ACADEMICO")
    assert item_ativo["aceito"] is True
    assert item_ativo["data_revogacao"] is None


def test_isolamento_multitenancy_historico(client, aluno_headers, aluno2_headers):
    """Garante que um titular veja estritamente seus próprios registros de consentimento."""
    # Aluno 1 aceita
    client.post(
        "/api/lgpd/consentimentos/aceitar",
        headers=aluno_headers,
        json={"versao_termo": "v1.0", "finalidades": ["TRATAMENTO_ACADEMICO"]},
    )
    # Aluno 2 aceita
    client.post(
        "/api/lgpd/consentimentos/aceitar",
        headers=aluno2_headers,
        json={"versao_termo": "v1.0", "finalidades": ["TRATAMENTO_ACADEMICO", "SERVICOS_BIBLIOTECA_VIRTUAL"]},
    )

    # Consulta do Aluno 1
    resp1 = client.get("/api/lgpd/consentimentos/historico", headers=aluno_headers)
    assert resp1.status_code == 200
    hist1 = resp1.json()
    assert len(hist1) == 1
    assert all(i["usuario_id"] == 3 for i in hist1)

    # Consulta do Aluno 2
    resp2 = client.get("/api/lgpd/consentimentos/historico", headers=aluno2_headers)
    assert resp2.status_code == 200
    hist2 = resp2.json()
    assert len(hist2) == 2
    assert all(i["usuario_id"] == 4 for i in hist2)
