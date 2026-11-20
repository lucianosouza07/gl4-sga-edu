"""Testes unitários e de integração para a política de retenção e expurgo de backups."""

from datetime import datetime, timedelta, timezone
import pytest
from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.backup_service import BackupService
from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.retention_service import RetentionService
from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.models import Database


def test_get_and_update_policy(client):
    """Valida a consulta e atualização da política de retenção via API."""
    resp_get = client.get("/api/v1/backups/politica-retencao")
    assert resp_get.status_code == 200
    assert resp_get.json()["dias_retencao_diario"] == 30

    # Atualiza política
    resp_put = client.put(
        "/api/v1/backups/politica-retencao",
        json={"dias_retencao_diario": 45, "copias_minimas_seguranca": 8},
    )
    assert resp_put.status_code == 200
    data = resp_put.json()
    assert data["dias_retencao_diario"] == 45
    assert data["copias_minimas_seguranca"] == 8


def test_purge_expired_enforces_minimum_copies(client):
    """Valida que o expurgo remove arquivos expirados mas preserva incondicionalmente as cópias mínimas."""
    # Configura retenção para 15 dias e mínimo de 7 cópias
    RetentionService.update_policy(dias_retencao_diario=15, copias_minimas_seguranca=7)

    # Cria 10 backups
    backups_criados = []
    for i in range(10):
        b = BackupService.execute_backup(tipo="MANUAL")
        backups_criados.append(b)

    # Força data defasada (30 dias atrás) para os 6 backups mais antigos
    agora = datetime.now(timezone.utc)
    for b in backups_criados[:6]:
        b.criado_em = agora - timedelta(days=30)
        b.expira_em = agora - timedelta(days=15)
        Database.update_backup(b)

    # Executa o expurgo: dos 6 vencidos, apenas 3 podem ser removidos pois 7 devem ser preservados
    resultado = RetentionService.purge_expired()

    assert resultado["quantidade_expurgada"] == 3
    assert resultado["copias_preservadas"] == 7

    # Testa chamada via API de expurgo
    resp = client.post("/api/v1/backups/expurgo")
    assert resp.status_code == 200
    assert resp.json()["copias_preservadas"] == 7
