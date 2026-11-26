"""Testes da US3: Validação Pública (LGPD), Listagem, Integridade MEC, Revogação e Guarda Permanente."""

import sqlite3
from typing import Any
from fastapi.testclient import TestClient
import pytest

from .conftest import auth_header
from ..repository import DocumentoRepository


def test_validacao_publica_sem_autenticacao_e_minimizacao_lgpd(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])

    # Emitir diploma e ata
    doc_dip = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_formado"],
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": "2026-11-20",
        },
        headers=headers,
    ).json()

    doc_ata = client.post(
        "/api/documentos/atas-notas",
        json={"turma_id": dados_base["turma_consolidada_id"]},
        headers=headers,
    ).json()

    # Consulta pública SEM header Authorization
    r_pub_dip = client.get(f"/api/documentos/validar/{doc_dip['codigo_verificacao']}")
    assert r_pub_dip.status_code == 200
    pub_dip = r_pub_dip.json()
    assert pub_dip["autentico"] is True
    assert pub_dip["status_validacao"] == "VALIDO"
    assert pub_dip["tipo_documento"] == "DIPLOMA_DIGITAL"
    assert pub_dip["resumo_publico"]["titular_nome"] == "Ana Clara Souza"
    assert pub_dip["resumo_publico"]["curso_nome"] == "Sistemas de Informação"
    assert pub_dip["custodia_mec"]["prazo_guarda"] == "PERMANENTE"

    # Garantir ausência absoluta de dados sensíveis LGPD na resposta pública
    texto_pub = r_pub_dip.text.lower()
    for sensivel in ("52998224725", "ana.clara@sga.edu.br", "71999990000", "2002-05-10", "emitido_por_usuario_id"):
        assert sensivel not in texto_pub

    # Consulta pública de ata de notas
    r_pub_ata = client.get(f"/api/documentos/validar/{doc_ata['codigo_verificacao']}")
    assert r_pub_ata.status_code == 200
    pub_ata = r_pub_ata.json()
    assert pub_ata["autentico"] is True
    assert pub_ata["resumo_publico"]["codigo_turma"] == "SI-20262-A"
    assert pub_ata["resumo_publico"]["aprovados"] == 1
    assert pub_ata["resumo_publico"]["reprovados_falta"] == 1
    assert "Ana Clara Souza" not in r_pub_ata.text

    # Código inexistente -> 404
    r_404 = client.get("/api/documentos/validar/SGA-DIP-INEXISTENTE000")
    assert r_404.status_code == 404


def test_listagem_filtrada_e_detalhamento_administrativo(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])

    d1 = client.post(
        "/api/documentos/diarios-operacionais",
        json={"turma_id": dados_base["turma_consolidada_id"]},
        headers=headers,
    ).json()
    d2 = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_formado"],
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": "2026-11-20",
        },
        headers=headers,
    ).json()

    # Listagem geral ordenada por id DESC
    r_all = client.get("/api/documentos", headers=headers)
    assert r_all.status_code == 200
    itens = r_all.json()
    assert [i["id_documento"] for i in itens] == [d2["id_documento"], d1["id_documento"]]

    # Filtro por tipo e período letivo
    r_diarios = client.get(
        "/api/documentos",
        params={"tipo_documento": "DIARIO_OPERACIONAL", "periodo_letivo_codigo": "2026.2"},
        headers=headers,
    )
    assert r_diarios.status_code == 200
    assert len(r_diarios.json()) == 1
    assert r_diarios.json()[0]["id_documento"] == d1["id_documento"]

    # Filtro por matrícula
    r_mat = client.get(
        "/api/documentos",
        params={"aluno_matricula": dados_base["mat_formado"]},
        headers=headers,
    )
    assert r_mat.status_code == 200
    assert len(r_mat.json()) == 1
    assert r_mat.json()[0]["id_documento"] == d2["id_documento"]

    # Detalhamento
    r_det = client.get(f"/api/documentos/{d2['id_documento']}", headers=headers)
    assert r_det.status_code == 200
    assert r_det.json()["codigo_verificacao"] == d2["codigo_verificacao"]

    assert client.get("/api/documentos/99999", headers=headers).status_code == 404


def test_verificacao_integridade_detecta_adulteracao_no_acervo_mec(
    client: TestClient, repo: DocumentoRepository, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["admin"])
    doc = client.post(
        "/api/documentos/atas-notas",
        json={"turma_id": dados_base["turma_consolidada_id"]},
        headers=headers,
    ).json()

    # 1. Documento íntegro
    r_ok = client.post(f"/api/documentos/{doc['id_documento']}/verificar-integridade", headers=headers)
    assert r_ok.status_code == 200
    body_ok = r_ok.json()
    assert body_ok["integro"] is True
    assert body_ok["assinatura_valida"] is True
    assert body_ok["hash_armazenado"] == body_ok["hash_recalculado"]
    assert body_ok["status_custodia"] == "INTEGRO"

    # 2. Simular adulteração direta em conteudo_json no banco
    repo.conn.execute(
        "UPDATE DocumentoAcademico SET conteudo_json = ? WHERE id_documento = ?",
        ('{"adulterado":true}', doc["id_documento"]),
    )
    repo.conn.commit()

    r_corrupt = client.post(f"/api/documentos/{doc['id_documento']}/verificar-integridade", headers=headers)
    assert r_corrupt.status_code == 200
    body_corrupt = r_corrupt.json()
    assert body_corrupt["integro"] is False
    assert body_corrupt["hash_armazenado"] != body_corrupt["hash_recalculado"]
    assert body_corrupt["status_custodia"] == "CORROMPIDO"

    # Validação pública também sinaliza CORROMPIDO
    r_pub = client.get(f"/api/documentos/validar/{doc['codigo_verificacao']}")
    assert r_pub.status_code == 200
    assert r_pub.json()["autentico"] is False
    assert r_pub.json()["status_validacao"] == "CORROMPIDO"


def test_revogacao_com_justificativa_e_bloqueio_de_exclusao_fisica(
    client: TestClient, repo: DocumentoRepository, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])
    doc = client.post(
        "/api/documentos/diarios-operacionais",
        json={"turma_id": dados_base["turma_consolidada_id"]},
        headers=headers,
    ).json()

    # Bloqueio de exclusão física via API -> 405 Method Not Allowed
    r_del = client.delete(f"/api/documentos/{doc['id_documento']}", headers=headers)
    assert r_del.status_code == 405
    assert "guarda permanente" in r_del.json()["detail"].lower()

    # Bloqueio de exclusão física no SGBD via trigger BEFORE DELETE
    with pytest.raises(sqlite3.IntegrityError, match="guarda permanente"):
        repo.conn.execute("DELETE FROM AcervoDigitalMEC WHERE documento_id = ?", (doc["id_documento"],))
    with pytest.raises(sqlite3.IntegrityError, match="guarda permanente"):
        repo.conn.execute("DELETE FROM DocumentoAcademico WHERE id_documento = ?", (doc["id_documento"],))

    # Motivo curto demais -> 422
    r_curto = client.patch(
        f"/api/documentos/{doc['id_documento']}/revogar",
        json={"motivo": "abc"},
        headers=headers,
    )
    assert r_curto.status_code == 422

    # Revogação válida -> 200 OK
    r_rev = client.patch(
        f"/api/documentos/{doc['id_documento']}/revogar",
        json={"motivo": "Erro material identificado na consolidação de faltas"},
        headers=headers,
    )
    assert r_rev.status_code == 200
    rev = r_rev.json()
    assert rev["valido"] is False
    assert rev["motivo_revogacao"] == "Erro material identificado na consolidação de faltas"
    assert rev["revogado_em"] is not None
    assert rev["acervo_mec"]["status_custodia"] == "REVOGADO"

    # Validação pública agora retorna REVOGADO
    r_pub = client.get(f"/api/documentos/validar/{doc['codigo_verificacao']}")
    assert r_pub.status_code == 200
    assert r_pub.json()["autentico"] is False
    assert r_pub.json()["status_validacao"] == "REVOGADO"
    assert r_pub.json()["motivo_revogacao"] == "Erro material identificado na consolidação de faltas"

    # Segunda revogação -> 409 Conflict
    r_rev2 = client.patch(
        f"/api/documentos/{doc['id_documento']}/revogar",
        json={"motivo": "Tentativa duplicada de revogação"},
        headers=headers,
    )
    assert r_rev2.status_code == 409
