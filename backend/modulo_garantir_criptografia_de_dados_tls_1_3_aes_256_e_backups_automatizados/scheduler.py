"""Agendador e rotina periódica de salvaguarda automatizada e ciclo de retenção."""

from typing import Dict, Any

try:
    from .backup_service import BackupService
    from .restore_service import RestoreService
    from .retention_service import RetentionService
    from .audit_service import registrar_auditoria
except (ImportError, ValueError):
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.backup_service import BackupService
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.restore_service import RestoreService
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.retention_service import RetentionService
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.audit_service import registrar_auditoria


def execute_scheduled_cycle() -> Dict[str, Any]:
    """Executa o ciclo diário completo de backup, validação de integridade e expurgo de retenção."""
    # 1. Executa backup completo do banco de dados
    backup = BackupService.execute_backup(
        tipo="COMPLETO",
        operador="SISTEMA_SCHEDULER",
        observacoes="Execução programada pelo ciclo diário de salvaguarda",
    )

    # 2. Valida imediatamente o hash SHA-256 do volume recém-criado
    validacao = RestoreService.validate_integrity(backup.id_backup, operador="SISTEMA_SCHEDULER")

    # 3. Executa o ciclo de retenção para descartar cópias que excederam o prazo
    expurgo = RetentionService.purge_expired(operador="SISTEMA_SCHEDULER")

    return {
        "status": "SUCESSO",
        "backup_id": backup.id_backup,
        "arquivo": backup.nome_arquivo,
        "integridade_confirmada": validacao["integridade_preservada"],
        "quantidade_expurgada": expurgo["quantidade_expurgada"],
        "copias_ativas_preservadas": expurgo["copias_preservadas"],
    }
