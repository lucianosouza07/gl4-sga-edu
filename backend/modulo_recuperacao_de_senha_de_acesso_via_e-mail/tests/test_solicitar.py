"""Testes da User Story 1: Solicitação de recuperação de senha e proteção anti-enumeração."""

import pytest
from models import Database
from rate_limiter import solicitacao_rate_limiter


def test_solicitar_recuperacao_email_valido(client, mock_email):
    """Garante que e-mail válido existente recebe 200 OK neutro e despacha token por e-mail."""
    solicitacao_rate_limiter.reset()
    payload = {"email": "professor.valido@sga.edu.br"}
    response = client.post("/api/v1/auth/recuperar-senha/solicitar", json=payload)

    assert response.status_code == 200
    dados = response.json()
    assert "Se os dados informados corresponderem a uma conta ativa" in dados["mensagem"]

    # Verifica se a mensagem foi enfileirada no mock de e-mail
    assert len(mock_email.mensagens_enviadas) == 1
    msg = mock_email.mensagens_enviadas[0]
    assert msg.destinatario == "professor.valido@sga.edu.br"
    assert len(msg.token) >= 32

    # Verifica se o hash do token foi persistido na base
    assert len(Database.tokens) == 1


def test_solicitar_recuperacao_email_inexistente_anti_enumeracao(client, mock_email):
    """Garante resposta neutra idêntica para e-mail não cadastrado, sem envio de e-mail."""
    solicitacao_rate_limiter.reset()
    payload = {"email": "desconhecido.inexistente@sga.edu.br"}
    response = client.post("/api/v1/auth/recuperar-senha/solicitar", json=payload)

    assert response.status_code == 200
    dados = response.json()
    # Mensagem exatamente idêntica à do e-mail válido
    assert "Se os dados informados corresponderem a uma conta ativa" in dados["mensagem"]

    # Nenhum e-mail externo é despachado
    assert len(mock_email.mensagens_enviadas) == 0


def test_solicitar_recuperacao_email_invalido(client):
    """Valida rejeição de formato de e-mail malformado."""
    solicitacao_rate_limiter.reset()
    payload = {"email": "formato-invalido-sem-arroba"}
    response = client.post("/api/v1/auth/recuperar-senha/solicitar", json=payload)

    assert response.status_code == 422


def test_solicitar_recuperacao_rate_limit(client):
    """Garante bloqueio 429 Too Many Requests quando limite de tentativas por IP/e-mail é atingido."""
    solicitacao_rate_limiter.reset()
    payload = {"email": "professor.valido@sga.edu.br"}

    for _ in range(5):
        resp = client.post("/api/v1/auth/recuperar-senha/solicitar", json=payload)
        assert resp.status_code == 200

    # Sexta tentativa consecutiva deve ser bloqueada
    resp_bloqueada = client.post("/api/v1/auth/recuperar-senha/solicitar", json=payload)
    assert resp_bloqueada.status_code == 429
    assert "Muitas solicitações recentes" in resp_bloqueada.json()["detail"]
    solicitacao_rate_limiter.reset()
