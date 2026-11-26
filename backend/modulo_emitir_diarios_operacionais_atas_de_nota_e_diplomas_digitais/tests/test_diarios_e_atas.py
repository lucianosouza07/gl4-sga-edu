"""Testes da US1: Emissão de Diários Operacionais e Atas de Notas Finais (SGA-25)."""

import sqlite3
from typing import Any
from fastapi.testclient import TestClient
import pytest

from .conftest import auth_header
from ..repository import DocumentoRepository


def test_emitir_diario_operacional_sucesso(client: TestClient, dados_base: dict[str, Any]) -> None:
    resp = client.post(
        "/api/documentos/diarios-operacionais",
        json={
            "turma_id": dados_base["turma_consolidada_id"],
            "portaria_referencia": "PORTARIA_MEC_360_2022",
            "observacoes": "Diário parcial conferido pela secretaria",
        },
        headers=auth_header(dados_base["tokens"]["secretaria"]),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert body["tipo_documento"] == "DIARIO_OPERACIONAL"
    assert body["turma_id"] == dados_base["turma_consolidada_id"]
    assert body["aluno_matricula"] is None
    assert body["valido"] is True
    assert body["codigo_verificacao"].startswith("SGA-DIA-")
    assert len(body["hash_sha256"]) == 64
    assert body["codigo_verificacao"] in body["url_validacao_qrcode"]

    conteudo = body["conteudo"]
    assert conteudo["turma"]["codigo_turma"] == "SI-20262-A"
    assert conteudo["disciplina"]["codigo"] == "SI401"
    assert conteudo["periodo_letivo"]["codigo"] == "2026.2"
    assert conteudo["professor"]["nome"] == "Prof. Alex Coelho"
    assert conteudo["resumo"]["total_matriculados"] == 3
    assert conteudo["resumo"]["total_em_alerta_infrequencia"] == 1

    registros_por_mat = {r["matricula"]: r for r in conteudo["registros"]}
    assert registros_por_mat[dados_base["mat_formado"]]["media_calculada"] == 8.67
    assert registros_por_mat[dados_base["mat_formado"]]["percentual_frequencia"] == 90.0
    assert registros_por_mat[dados_base["mat_formado"]]["alerta_infrequencia"] is False
    assert registros_por_mat[dados_base["mat_faltoso"]]["percentual_frequencia"] == 70.0
    assert registros_por_mat[dados_base["mat_faltoso"]]["alerta_infrequencia"] is True

    acervo = body["acervo_mec"]
    assert acervo["documento_id"] == body["id_documento"]
    assert acervo["portaria_referencia"] == "PORTARIA_MEC_360_2022"
    assert acervo["formato_arquivo"] == "PDF_A_ASSINADO"
    assert acervo["prazo_guarda"] == "PERMANENTE"
    assert acervo["status_custodia"] == "INTEGRO"
    assert len(acervo["assinatura_icp_brasil"]) == 128


def test_emitir_diario_operacional_permite_turma_com_media_pendente(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    resp = client.post(
        "/api/documentos/diarios-operacionais",
        json={"turma_id": dados_base["turma_pendente_id"]},
        headers=auth_header(dados_base["tokens"]["secretaria"]),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["conteudo"]["registros"][0]["media_calculada"] is None


def test_emitir_ata_notas_finais_aplica_regras_media_e_25_porcento_faltas(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    resp = client.post(
        "/api/documentos/atas-notas",
        json={
            "turma_id": dados_base["turma_consolidada_id"],
            "media_minima_aprovacao": 6.0,
            "portaria_referencia": "PORTARIA_MEC_315_2018",
            "observacoes": "Ata oficial de encerramento",
        },
        headers=auth_header(dados_base["tokens"]["admin"]),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert body["tipo_documento"] == "ATA_NOTAS"
    assert body["codigo_verificacao"].startswith("SGA-ATA-")
    assert body["acervo_mec"]["portaria_referencia"] == "PORTARIA_MEC_315_2018"

    resumo = body["conteudo"]["resumo"]
    assert resumo["total_matriculados"] == 3
    assert resumo["aprovados"] == 1
    assert resumo["reprovados_nota"] == 1
    assert resumo["reprovados_falta"] == 1

    por_mat = {r["matricula"]: r for r in body["conteudo"]["resultados"]}
    assert por_mat[dados_base["mat_formado"]]["situacao_final"] == "APROVADO"
    assert por_mat[dados_base["mat_ativo"]]["situacao_final"] == "REPROVADO_NOTA"
    # Carla tem média 9.00, mas frequência 70.0% (30% faltas >= 25%) -> REPROVADO_FALTA
    assert por_mat[dados_base["mat_faltoso"]]["media_final"] == 9.0
    assert por_mat[dados_base["mat_faltoso"]]["percentual_frequencia"] == 70.0
    assert por_mat[dados_base["mat_faltoso"]]["situacao_final"] == "REPROVADO_FALTA"


def test_rejeitar_emissao_turma_inexistente_e_turma_vazia(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])

    r_404_diario = client.post("/api/documentos/diarios-operacionais", json={"turma_id": 9999}, headers=headers)
    assert r_404_diario.status_code == 404

    r_404_ata = client.post("/api/documentos/atas-notas", json={"turma_id": 9999}, headers=headers)
    assert r_404_ata.status_code == 404

    r_vazia_diario = client.post(
        "/api/documentos/diarios-operacionais",
        json={"turma_id": dados_base["turma_vazia_id"]},
        headers=headers,
    )
    assert r_vazia_diario.status_code == 422

    r_vazia_ata = client.post(
        "/api/documentos/atas-notas",
        json={"turma_id": dados_base["turma_vazia_id"]},
        headers=headers,
    )
    assert r_vazia_ata.status_code == 422


def test_rejeitar_ata_notas_com_pendencia_de_media_ou_nota_fora_da_faixa(
    client: TestClient, repo: DocumentoRepository, dados_base: dict[str, Any]
) -> None:
    headers = auth_header(dados_base["tokens"]["secretaria"])

    # Turma 3 tem aluno sem avaliações e sem media_final -> 422
    r_pend = client.post(
        "/api/documentos/atas-notas",
        json={"turma_id": dados_base["turma_pendente_id"]},
        headers=headers,
    )
    assert r_pend.status_code == 422
    assert "Pendência de fechamento" in r_pend.json()["detail"]

    # Forçar media_final inválida (> 10.00) diretamente no banco para testar defesa em profundidade
    repo.conn.execute(
        "UPDATE MatriculaTurma SET media_final = 11.5 WHERE turma_id = ?",
        (dados_base["turma_pendente_id"],),
    )
    repo.conn.commit()

    r_faixa = client.post(
        "/api/documentos/atas-notas",
        json={"turma_id": dados_base["turma_pendente_id"]},
        headers=headers,
    )
    assert r_faixa.status_code == 422
    assert "0.00 a 10.00" in r_faixa.json()["detail"]


def test_rollback_atomico_em_falha_de_custodia_mec(repo: DocumentoRepository, dados_base: dict[str, Any]) -> None:
    """Falha ao inserir AcervoDigitalMEC (portaria inválida) deve desfazer DocumentoAcademico e auditoria."""
    with pytest.raises(sqlite3.IntegrityError):
        repo.criar_documento_com_acervo_e_auditoria(
            tipo_documento="DIARIO_OPERACIONAL",
            aluno_matricula=None,
            turma_id=dados_base["turma_consolidada_id"],
            curso_id=None,
            numero_registro=None,
            codigo_verificacao="SGA-DIA-ROLLBACK000001",
            hash_sha256="a" * 64,
            url_validacao_qrcode="https://sga-edu.institucional.edu.br/api/documentos/validar/SGA-DIA-ROLLBACK000001",
            conteudo_json="{}",
            emitido_por_usuario_id=dados_base["usuarios"]["secretaria"],
            emitido_em="2026-11-26T12:00:00+00:00",
            portaria_referencia="PORTARIA_INVALIDA",
            formato_arquivo="PDF_A_ASSINADO",
            assinatura_icp_brasil="b" * 128,
            carimbo_tempo="2026-11-26T12:00:00+00:00",
            prazo_guarda="PERMANENTE",
            ip_origem="127.0.0.1",
            dados_novos_auditoria_json="{}",
        )

    assert repo.conn.execute("SELECT COUNT(*) FROM DocumentoAcademico").fetchone()[0] == 0
    assert repo.conn.execute("SELECT COUNT(*) FROM AcervoDigitalMEC").fetchone()[0] == 0
    assert repo.conn.execute("SELECT COUNT(*) FROM LogAuditoriaSistema").fetchone()[0] == 0
    assert repo.buscar_documento_por_codigo("SGA-DIA-ROLLBACK000001") is None
    assert repo.listar_documentos() == []
    assert repo.listar_auditoria() == []
