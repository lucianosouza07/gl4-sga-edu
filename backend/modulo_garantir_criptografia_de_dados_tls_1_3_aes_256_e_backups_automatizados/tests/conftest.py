"""Fixtures de teste para o módulo de Criptografia e Backups Automatizados."""

import os
import sys
import shutil
from pathlib import Path

# Adiciona o diretório src/backend ao sys.path para permitir importações de pacote
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Configuração de chave mestra de teste (32 bytes)
TEST_MASTER_KEY = "sga_edu_test_master_key_32bytes!"
os.environ["CRYPTO_MASTER_KEY"] = TEST_MASTER_KEY

import pytest
from fastapi.testclient import TestClient

from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.models import (
    Database, BackupRegistro, PoliticaRetencaoBackup, LogAuditoriaBackup
)
from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.router import app


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """Configura diretório de armazenamento e reseta a base de dados em memória."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    os.environ["BACKUP_STORAGE_DIR"] = str(backup_dir)

    Database.reset()
    yield Database
    Database.reset()

    # Limpeza de diretório temporário após testes
    if backup_dir.exists():
        shutil.rmtree(str(backup_dir), ignore_errors=True)


@pytest.fixture
def client():
    """Cliente de teste FastAPI para requisições HTTP locais."""
    with TestClient(app) as test_client:
        yield test_client
