"""Testes unitários e de integração para validação de integridade e simulação de restauração."""

import pytest
from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.backup_service import BackupService
from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.restore_service import RestoreService
from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.models import Database


def test_validate_integrity_success(client):
    """Valida a confirmação bem-sucedida de hash SHA-256 em volume íntegro."""
    backup = BackupService.execute_backup(tipo="MANUAL")

    # Validação via serviço
    resultado = RestoreService.validate_integrity(backup.id_backup)
    assert resultado["integridade_preservada"] is True
    assert resultado["checksum_esperado"] == backup.checksum_sha256
    assert resultado["checksum_calculado"] == backup.checksum_sha256

    # Validação via endpoint da API
    resp = client.post(f"/api/v1/backups/{backup.id_backup}/validar-integridade")
    assert resp.status_code == 200
    assert resp.json()["integridade_preservada"] is True


def test_validate_integrity_corrupted_file(client):
    """Valida que adulteração no arquivo físico é detectada retornando 409 Conflict."""
    backup = BackupService.execute_backup(tipo="MANUAL")
    storage_dir = BackupService.get_storage_dir()
    caminho_arquivo = storage_dir / backup.nome_arquivo

    # Corrompe um byte do arquivo físico
    with open(caminho_arquivo, "r+b") as f:
        f.seek(15)
        byte_atual = f.read(1)[0]
        f.seek(15)
        f.write(bytes([byte_atual ^ 0xFF]))

    resp = client.post(f"/api/v1/backups/{backup.id_backup}/validar-integridade")
    assert resp.status_code == 409
    assert "Discrepância de integridade detectada" in resp.json()["detail"]

    backup_atualizado = Database.get_backup(backup.id_backup)
    assert backup_atualizado.status_integridade == "CORROMPIDO"


def test_simulate_restore_success(client):
    """Valida a rotina de simulação de restauração em sandbox atestando RTO regulatório."""
    backup = BackupService.execute_backup(tipo="COMPLETO")

    # Validação via serviço
    resultado = RestoreService.simulate_restore(backup.id_backup)
    assert resultado["sucesso"] is True
    assert resultado["dentro_do_rto"] is True
    assert resultado["duracao_segundos"] < 3600.0
    assert resultado["tabelas_restauradas"] >= 3

    # Validação via API
    resp = client.post(f"/api/v1/backups/{backup.id_backup}/simular-restauracao")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sucesso"] is True
    assert data["dentro_do_rto"] is True


def test_simulate_restore_nonexistent(client):
    """Valida erro 404 para backup inexistente na simulação de restauração."""
    resp = client.post("/api/v1/backups/88888/simular-restauracao")
    assert resp.status_code == 404
