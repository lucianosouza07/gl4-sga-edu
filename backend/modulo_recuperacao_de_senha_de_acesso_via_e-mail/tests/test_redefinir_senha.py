"""Testes da User Story 2: Validação de token e redefinição de senha com complexidade."""

import pytest
from models import Database
from security import verify_password
from rate_limiter import solicitacao_rate_limiter


def _obter_token_valido(client, mock_email, email="professor.valido@sga.edu.br") -> str:
    solicitacao_rate_limiter.reset()
    mock_email.limpar()
    resp = client.post("/api/v1/auth/recuperar-senha/solicitar", json={"email": email})
    assert resp.status_code == 200
    assert len(mock_email.mensagens_enviadas) == 1
    return mock_email.mensagens_enviadas[0].token


def test_validar_token_sucesso(client, mock_email):
    """Valida token ativo e não consumido."""
    token = _obter_token_valido(client, mock_email)
    response = client.get(f"/api/v1/auth/recuperar-senha/validar-token?token={token}")

    assert response.status_code == 200
    dados = response.json()
    assert dados["valido"] is True
    assert "Token válido" in dados["mensagem"]


def test_validar_token_inexistente(client):
    """Valida rejeição de token inventado."""
    token_falso = "a" * 32
    response = client.get(f"/api/v1/auth/recuperar-senha/validar-token?token={token_falso}")

    assert response.status_code == 400
    assert "inválido, expirou ou já foi utilizado" in response.json()["detail"]


def test_redefinir_senha_sucesso(client, mock_email):
    """Garante troca de senha com sucesso atendendo aos requisitos de complexidade."""
    token = _obter_token_valido(client, mock_email)

    payload = {
        "token": token,
        "nova_senha": "NovaSenhaForte@2026",
        "confirmacao_senha": "NovaSenhaForte@2026",
    }
    response = client.post("/api/v1/auth/recuperar-senha/redefinir", json=payload)

    assert response.status_code == 200
    assert response.json()["sucesso"] is True

    # Verifica se a senha do usuário foi de fato atualizada no banco
    usuario = Database.buscar_usuario_por_email("professor.valido@sga.edu.br")
    assert verify_password("NovaSenhaForte@2026", usuario.senha_hash) is True
    assert verify_password("SenhaAntiga@123", usuario.senha_hash) is False

    # Nova tentativa com o mesmo token deve ser rejeitada
    resp_reuso = client.post("/api/v1/auth/recuperar-senha/redefinir", json=payload)
    assert resp_reuso.status_code == 400


def test_redefinir_senha_divergente(client, mock_email):
    """Garante recusa quando confirmação não bate com a nova senha."""
    token = _obter_token_valido(client, mock_email)
    payload = {
        "token": token,
        "nova_senha": "NovaSenhaForte@2026",
        "confirmacao_senha": "OutraSenhaDiferente@2026",
    }
    response = client.post("/api/v1/auth/recuperar-senha/redefinir", json=payload)
    assert response.status_code == 422


def test_redefinir_senha_fraca_sem_especial(client, mock_email):
    """Garante recusa de senha sem caractere especial."""
    token = _obter_token_valido(client, mock_email)
    payload = {
        "token": token,
        "nova_senha": "SenhaSemEspecial123",
        "confirmacao_senha": "SenhaSemEspecial123",
    }
    response = client.post("/api/v1/auth/recuperar-senha/redefinir", json=payload)
    assert response.status_code == 422


def test_redefinir_senha_reaproveitando_antiga(client, mock_email):
    """Rejeita tentativa de usar a mesma senha atual."""
    token = _obter_token_valido(client, mock_email)
    payload = {
        "token": token,
        "nova_senha": "SenhaAntiga@123",
        "confirmacao_senha": "SenhaAntiga@123",
    }
    response = client.post("/api/v1/auth/recuperar-senha/redefinir", json=payload)
    assert response.status_code == 400
    assert "não pode ser idêntica" in response.json()["detail"]
