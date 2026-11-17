"""Fixtures de teste para o módulo de Recuperação de Senha."""

import sys
from pathlib import Path

# Adiciona o diretório do módulo ao sys.path para importação direta e portabilidade
MODULO_DIR = Path(__file__).resolve().parent.parent
if str(MODULO_DIR) not in sys.path:
    sys.path.insert(0, str(MODULO_DIR))

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from router import app
from models import Database, Usuario, TokenRecuperacao, LogAuditoriaRecuperacao
from email_service import MockEmailService, get_email_service
from security import hash_password


@pytest.fixture(autouse=True)
def setup_test_db():
    """Reinicializa a base de dados em memória para isolamento entre testes."""
    Database.reset()
    # Cria usuário de teste com credenciais conhecidas
    Database.usuarios[1] = Usuario(
        id_usuario=1,
        login="prof.silva",
        email="professor.valido@sga.edu.br",
        senha_hash=hash_password("SenhaAntiga@123"),
        token_versao=1,
        statusCONTA=1,
    )
    yield Database
    Database.reset()


@pytest.fixture
def mock_email():
    """Instância isolada do mock de e-mails para checar mensagens enviadas."""
    mock_service = MockEmailService()
    app.dependency_overrides[get_email_service] = lambda: mock_service
    yield mock_service
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_email):
    """Cliente de teste FastAPI."""
    with TestClient(app) as test_client:
        yield test_client
