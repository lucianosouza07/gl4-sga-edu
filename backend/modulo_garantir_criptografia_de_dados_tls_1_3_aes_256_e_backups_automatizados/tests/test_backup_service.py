"""Testes unitários e de integração para o serviço e endpoints de Backups Automatizados."""

from pathlib import Path
import pytest
from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.backup_service import BackupService
from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.models import Database


def test_execute_backup_success():
    """Valida a extração, compactação, cifragem e registro de um backup no storage."""
    backup = BackupService.execute_backup(tipo="MANUAL", operador="OPERADOR_TESTE")

    assert backup.id_backup > 0
    assert backup.tipo_backup == "MANUAL"
    assert backup.algoritmo_cifragem == "AES-256-GCM"
    assert backup.status == "CONCLUIDO"
    assert backup.tamanho_original_bytes > 0
    assert backup.tamanho_cifrado_bytes > 0
    assert len(backup.checksum_sha256) == 64

    storage_dir = BackupService.get_storage_dir()
    caminho_fisico = storage_dir / backup.nome_arquivo
    assert caminho_fisico.exists()
    assert caminho_fisico.stat().st_size == backup.tamanho_cifrado_bytes


def test_execute_backup_invalid_type():
    """Valida que tipos de backup não autorizados são rejeitados."""
    with pytest.raises(ValueError, match="Tipo de backup inválido"):
        BackupService.execute_backup(tipo="INVALIDO")


def test_api_executar_backup(client):
    """Valida o endpoint POST /api/v1/backups/executar retornando HTTP 202 Accepted."""
    resp = client.post("/api/v1/backups/executar", json={"tipo": "COMPLETO", "observacoes": "Backup diário agendado"})
    assert resp.status_code == 202
    data = resp.json()

    assert data["id_backup"] > 0
    assert data["tipo_backup"] == "COMPLETO"
    assert data["status"] == "CONCLUIDO"
    assert len(data["checksum_sha256"]) == 64


def test_api_listar_e_obter_backups(client):
    """Valida a listagem e recuperação detalhada de backups via API."""
    # Cria dois backups para teste
    BackupService.execute_backup(tipo="MANUAL")
    BackupService.execute_backup(tipo="INCREMENTAL")

    resp_list = client.get("/api/v1/backups")
    assert resp_list.status_code == 200
    backups = resp_list.json()
    assert len(backups) >= 2

    # Consulta por ID
    primeiro_id = backups[0]["id_backup"]
    resp_get = client.get(f"/api/v1/backups/{primeiro_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["id_backup"] == primeiro_id

    # Consulta ID inexistente
    resp_404 = client.get("/api/v1/backups/999999")
    assert resp_404.status_code == 404
