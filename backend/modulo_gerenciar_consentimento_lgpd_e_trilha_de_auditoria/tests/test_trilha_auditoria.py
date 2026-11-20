"""Testes unitários e de integração para a trilha imutável de auditoria e higienização de senhas (US2)."""

import json
import pytest
from ..audit_service import sanitize_audit_payload


def test_sanitizacao_chaves_sensiveis_e_senhas():
    """Valida que credenciais, senhas e chaves sejam mascaradas para [REDACTED]."""
    payload_bruto = {
        "usuario": "aluno@sga.edu.br",
        "senha": "MinhaSenhaSuperSecreta123!",
        "confirmar_password": "MinhaSenhaSuperSecreta123!",
        "token": "jwt_token_12345",
        "chave_mfa": "JBSWY3DPEHPK3PXP",
        "dados_cadastrais": {
            "nome": "João Silva",
            "password_hash": "$2b$12$e...",
            "cartao_credito": "4111111111111111",
        },
    }

    resultado_str = sanitize_audit_payload(payload_bruto)
    assert resultado_str is not None
    dados_limpos = json.loads(resultado_str)

    assert dados_limpos["senha"] == "[REDACTED]"
    assert dados_limpos["confirmar_password"] == "[REDACTED]"
    assert dados_limpos["token"] == "[REDACTED]"
    assert dados_limpos["chave_mfa"] == "[REDACTED]"
    assert dados_limpos["dados_cadastrais"]["password_hash"] == "[REDACTED]"
    assert dados_limpos["dados_cadastrais"]["cartao_credito"] == "[REDACTED]"
    assert dados_limpos["usuario"] == "aluno@sga.edu.br"
    assert dados_limpos["dados_cadastrais"]["nome"] == "João Silva"


def test_geracao_automatica_auditoria_no_aceite(client, aluno_headers, repo):
    """Garante que a ação de aceite gere automaticamente entrada de auditoria na base."""
    client.post(
        "/api/lgpd/consentimentos/aceitar",
        headers={**aluno_headers, "X-Forwarded-For": "177.16.20.100"},
        json={"versao_termo": "v1.0", "finalidades": ["TRATAMENTO_ACADEMICO"]},
    )

    total, logs = repo.consultar_logs_auditoria(usuario_id=3, entidade_afetada="TermoConsentimentoLGPD")
    assert total >= 1
    ultimo_log = logs[0]
    assert ultimo_log["acao"] == "CRIACAO"
    assert ultimo_log["ip_origem"] == "177.16.20.100"
    assert "TRATAMENTO_ACADEMICO" in ultimo_log["dados_novos"]


def test_geracao_automatica_auditoria_na_revogacao(client, aluno_headers, repo):
    """Garante que a revogação de consentimento seja devidamente auditada."""
    client.post(
        "/api/lgpd/consentimentos/aceitar",
        headers=aluno_headers,
        json={"versao_termo": "v1.0", "finalidades": ["TRATAMENTO_ACADEMICO", "COMUNICACAO_INSTITUCIONAL"]},
    )
    client.post(
        "/api/lgpd/consentimentos/revogar",
        headers={**aluno_headers, "X-Forwarded-For": "177.16.20.101"},
        json={"versao_termo": "v1.0", "finalidade": "COMUNICACAO_INSTITUCIONAL"},
    )

    total, logs = repo.consultar_logs_auditoria(usuario_id=3, acao="REVOGACAO_LGPD")
    assert total >= 1
    log_revog = logs[0]
    assert log_revog["ip_origem"] == "177.16.20.101"
    assert "COMUNICACAO_INSTITUCIONAL" in log_revog["dados_novos"]


def test_imutabilidade_da_trilha_de_auditoria(repo):
    """Confirma que métodos de alteração ou exclusão direta na trilha disparam exceção."""
    with pytest.raises(RuntimeError) as exc_update:
        repo.atualizar_log_auditoria(1)
    assert "proibidas na trilha imutável" in str(exc_update.value)

    with pytest.raises(RuntimeError) as exc_delete:
        repo.excluir_log_auditoria(1)
    assert "proibidas na trilha imutável" in str(exc_delete.value)
