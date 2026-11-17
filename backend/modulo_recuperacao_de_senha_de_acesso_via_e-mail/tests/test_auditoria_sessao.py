"""Testes da User Story 4: Revogação de sessões e persistência de trilha de auditoria."""

from models import Database
from rate_limiter import solicitacao_rate_limiter


def test_revogacao_sessoes_incrementa_token_versao(client, mock_email):
    """Garante que a versão do token é incrementada, invalidando sessões ativas prévias."""
    solicitacao_rate_limiter.reset()
    mock_email.limpar()

    usuario_antes = Database.buscar_usuario_por_email("professor.valido@sga.edu.br")
    versao_inicial = usuario_antes.token_versao

    resp_solic = client.post("/api/v1/auth/recuperar-senha/solicitar", json={"email": "professor.valido@sga.edu.br"})
    assert resp_solic.status_code == 200
    token = mock_email.mensagens_enviadas[0].token

    payload = {
        "token": token,
        "nova_senha": "NovaSenhaSessao@2026",
        "confirmacao_senha": "NovaSenhaSessao@2026",
    }
    resp_red = client.post("/api/v1/auth/recuperar-senha/redefinir", json=payload)
    assert resp_red.status_code == 200

    usuario_depois = Database.buscar_usuario_por_email("professor.valido@sga.edu.br")
    assert usuario_depois.token_versao == versao_inicial + 1


def test_trilha_auditoria_registrada(client, mock_email):
    """Garante que todos os eventos relevantes do fluxo são registrados na auditoria."""
    solicitacao_rate_limiter.reset()
    mock_email.limpar()
    Database.auditoria.clear()

    # 1. Solicitação
    client.post("/api/v1/auth/recuperar-senha/solicitar", json={"email": "professor.valido@sga.edu.br"})
    token = mock_email.mensagens_enviadas[0].token

    # 2. Validação
    client.get(f"/api/v1/auth/recuperar-senha/validar-token?token={token}")

    # 3. Redefinição
    payload = {
        "token": token,
        "nova_senha": "NovaSenhaAudit@2026",
        "confirmacao_senha": "NovaSenhaAudit@2026",
    }
    client.post("/api/v1/auth/recuperar-senha/redefinir", json=payload)

    acoes_registradas = [log.acao for log in Database.auditoria]
    assert "SOLICITACAO_RECUPERACAO" in acoes_registradas
    assert "VALIDACAO_TOKEN" in acoes_registradas
    assert "REDEFINICAO_SENHA" in acoes_registradas

    for log in Database.auditoria:
        assert log.data_hora is not None
        assert log.ip_origem != ""
        assert log.status_resultado in ("SUCESSO", "FALHA", "BLOQUEADO")
