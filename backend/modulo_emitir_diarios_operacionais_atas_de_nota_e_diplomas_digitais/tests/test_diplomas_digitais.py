"""Testes da US2: Emissão e Custódia de Diplomas Digitais (SGA-25)."""

from datetime import date, timedelta
from typing import Any
from fastapi.testclient import TestClient

from .conftest import auth_header


def test_emitir_diploma_digital_sucesso_registro_manual_e_automatico(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])
    resp = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_formado"],
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": "2026-11-20",
            "numero_registro": "DIP-2026-REG-01",
            "livro_registro": "Livro 01",
            "folha_registro": "Folha 12",
            "observacoes": "Colação de grau regular",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert body["tipo_documento"] == "DIPLOMA_DIGITAL"
    assert body["aluno_matricula"] == dados_base["mat_formado"]
    assert body["curso_id"] == dados_base["curso_id"]
    assert body["numero_registro"] == "DIP-2026-REG-01"
    assert body["codigo_verificacao"].startswith("SGA-DIP-")
    assert body["valido"] is True

    conteudo = body["conteudo"]
    assert conteudo["diplomado"]["nome"] == "Ana Clara Souza"
    assert conteudo["curso"]["codigo_mec"] == "MEC-SI-2026"
    assert conteudo["curso"]["grau_academico"] == "Bacharelado"
    assert conteudo["curso"]["carga_horaria_integralizada"] == 3000
    assert conteudo["expedicao"]["numero_registro"] == "DIP-2026-REG-01"
    assert "cpf" not in conteudo["diplomado"]
    assert "email" not in conteudo["diplomado"]

    assert body["acervo_mec"]["formato_arquivo"] == "PDF_A_ASSINADO"
    assert body["acervo_mec"]["prazo_guarda"] == "PERMANENTE"
    assert body["acervo_mec"]["status_custodia"] == "INTEGRO"


def test_bloquear_diploma_duplicado_e_permitir_reemissao_apos_revogacao(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])
    payload = {
        "aluno_matricula": dados_base["mat_formado"],
        "data_conclusao": "2026-11-10",
        "data_colacao_grau": "2026-11-20",
    }

    r1 = client.post("/api/documentos/diplomas", json=payload, headers=headers)
    assert r1.status_code == 201
    doc1 = r1.json()
    assert doc1["numero_registro"].startswith("DIP-2026-")

    # Segunda emissão ativa para o mesmo aluno/curso -> 409 Conflict
    r2 = client.post("/api/documentos/diplomas", json=payload, headers=headers)
    assert r2.status_code == 409
    assert "Já existe um diploma digital válido" in r2.json()["detail"]

    # Revogar o primeiro diploma
    r_rev = client.patch(
        f"/api/documentos/{doc1['id_documento']}/revogar",
        json={"motivo": "Retificação de grafia do nome civil"},
        headers=headers,
    )
    assert r_rev.status_code == 200
    assert r_rev.json()["valido"] is False

    # Reemissão substituta após revogação -> 201 Created com novo código e novo registro
    r3 = client.post("/api/documentos/diplomas", json=payload, headers=headers)
    assert r3.status_code == 201
    doc2 = r3.json()
    assert doc2["id_documento"] != doc1["id_documento"]
    assert doc2["codigo_verificacao"] != doc1["codigo_verificacao"]
    assert doc2["numero_registro"] != doc1["numero_registro"]


def test_rejeitar_diploma_para_estudantes_inelegiveis_e_aluno_inexistente(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])

    # Aluno inexistente -> 404
    r_404 = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": 99999999,
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": "2026-11-20",
        },
        headers=headers,
    )
    assert r_404.status_code == 404

    # Aluno ATIVO -> 422
    r_ativo = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_ativo"],
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": "2026-11-20",
        },
        headers=headers,
    )
    assert r_ativo.status_code == 422
    assert "ATIVO" in r_ativo.json()["detail"]

    # Aluno TRANCADO -> 422
    r_trancado = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_faltoso"],
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": "2026-11-20",
        },
        headers=headers,
    )
    assert r_trancado.status_code == 422
    assert "TRANCADO" in r_trancado.json()["detail"]

    # Aluno FORMADO mas sem curso vinculado -> 422
    r_sem_curso = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_sem_curso"],
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": "2026-11-20",
        },
        headers=headers,
    )
    assert r_sem_curso.status_code == 422
    assert "nenhum curso" in r_sem_curso.json()["detail"]

    # Carga horária integralizada inferior à do curso (3000h) -> 422
    r_ch = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_formado"],
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": "2026-11-20",
            "carga_horaria_integralizada": 2400,
        },
        headers=headers,
    )
    assert r_ch.status_code == 422
    assert "Carga horária integralizada" in r_ch.json()["detail"]


def test_rejeitar_diploma_datas_invalidas_e_fora_de_escopo_terceiros_blockchain(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["admin"])

    # Data de colação anterior à conclusão -> 422
    r_ordem = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_formado"],
            "data_conclusao": "2026-11-20",
            "data_colacao_grau": "2026-11-10",
        },
        headers=headers,
    )
    assert r_ordem.status_code == 422

    # Data futura -> 422
    amanha = (date.today() + timedelta(days=1)).isoformat()
    r_futura = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_formado"],
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": amanha,
        },
        headers=headers,
    )
    assert r_futura.status_code == 422

    # Instituição terceira -> 422
    r_terceira = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_formado"],
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": "2026-11-20",
            "instituicao_terceira": True,
        },
        headers=headers,
    )
    assert r_terceira.status_code == 422
    assert "fora do escopo" in r_terceira.json()["detail"]

    # Blockchain -> 422
    r_chain = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_formado"],
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": "2026-11-20",
            "registrar_blockchain": True,
        },
        headers=headers,
    )
    assert r_chain.status_code == 422
    assert "blockchain" in r_chain.json()["detail"]
