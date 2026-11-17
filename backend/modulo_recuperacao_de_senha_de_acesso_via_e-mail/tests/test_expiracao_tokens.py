"""Testes da User Story 3: Invalidação e expiração de tokens de recuperação."""

from datetime import datetime, timedelta, timezone
from models import Database
from rate_limiter import solicitacao_rate_limiter


def test_token_expirado_rejeitado(client, mock_email):
    """Garante recusa de token cujo tempo atual ultrapassou 30 minutos."""
    solicitacao_rate_limiter.reset()
    mock_email.limpar()
    resp = client.post("/api/v1/auth/recuperar-senha/solicitar", json={"email": "professor.valido@sga.edu.br"})
    assert resp.status_code == 200

    token = mock_email.mensagens_enviadas[0].token

    # Simula passagem de tempo alterando a data de expiração para o passado
    for t in Database.tokens.values():
        t.expira_em = datetime.now(timezone.utc) - timedelta(minutes=1)

    # Tentativa de validação deve falhar
    resp_val = client.get(f"/api/v1/auth/recuperar-senha/validar-token?token={token}")
    assert resp_val.status_code == 400
    assert "inválido, expirou ou já foi utilizado" in resp_val.json()["detail"]

    # Tentativa de redefinição deve falhar
    payload = {
        "token": token,
        "nova_senha": "NovaSenhaForte@2026",
        "confirmacao_senha": "NovaSenhaForte@2026",
    }
    resp_red = client.post("/api/v1/auth/recuperar-senha/redefinir", json=payload)
    assert resp_red.status_code == 400


def test_invalida_token_anterior_quando_novo_solicitado(client, mock_email):
    """Garante que solicitar nova recuperação invalida automaticamente tokens pendentes anteriores."""
    solicitacao_rate_limiter.reset()
    mock_email.limpar()

    # Primeira solicitação
    resp1 = client.post("/api/v1/auth/recuperar-senha/solicitar", json={"email": "professor.valido@sga.edu.br"})
    assert resp1.status_code == 200
    token1 = mock_email.mensagens_enviadas[0].token

    # Segunda solicitação para a mesma conta
    resp2 = client.post("/api/v1/auth/recuperar-senha/solicitar", json={"email": "professor.valido@sga.edu.br"})
    assert resp2.status_code == 200
    token2 = mock_email.mensagens_enviadas[1].token

    assert token1 != token2

    # Token 1 deve ter sido revogado
    resp_val1 = client.get(f"/api/v1/auth/recuperar-senha/validar-token?token={token1}")
    assert resp_val1.status_code == 400

    # Token 2 deve permanecer válido
    resp_val2 = client.get(f"/api/v1/auth/recuperar-senha/validar-token?token={token2}")
    assert resp_val2.status_code == 200
    assert resp_val2.json()["valido"] is True
