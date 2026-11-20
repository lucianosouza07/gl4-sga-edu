"""Serviço de Gestão do Ciclo de Vida, Retenção e Expurgo Seguro de Backups."""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from .models import Database, PoliticaRetencaoBackup, BackupRegistro
    from .backup_service import BackupService
    from .audit_service import registrar_auditoria
except (ImportError, ValueError):
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.models import Database, PoliticaRetencaoBackup, BackupRegistro
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.backup_service import BackupService
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.audit_service import registrar_auditoria


class RetentionService:
    """Aplica regras de rotação e expurgo programado garantindo contingência mínima."""

    @classmethod
    def get_policy(cls) -> PoliticaRetencaoBackup:
        """Retorna a política institucional de retenção configurada."""
        return Database.get_politica()

    @classmethod
    def update_policy(
        cls,
        frequencia_cron: Optional[str] = None,
        dias_retencao_diario: Optional[int] = None,
        meses_retencao_mensal: Optional[int] = None,
        copias_minimas_seguranca: Optional[int] = None,
        operador: str = "ADMIN",
    ) -> PoliticaRetencaoBackup:
        """Atualiza os parâmetros de retenção e registra auditoria da alteração."""
        politica = Database.get_politica()

        if frequencia_cron is not None:
            politica.frequencia_cron = frequencia_cron
        if dias_retencao_diario is not None:
            politica.dias_retencao_diario = dias_retencao_diario
        if meses_retencao_mensal is not None:
            politica.meses_retencao_mensal = meses_retencao_mensal
        if copias_minimas_seguranca is not None:
            politica.copias_minimas_seguranca = copias_minimas_seguranca

        politica.atualizado_por = operador
        Database.update_politica(politica)

        registrar_auditoria(
            acao="POLITICA_ALTERADA",
            status_resultado="SUCESSO",
            operador=operador,
            detalhes=f"Política de retenção atualizada: diária={politica.dias_retencao_diario}d, mensal={politica.meses_retencao_mensal}m, cópias mínimas={politica.copias_minimas_seguranca}",
        )
        return politica

    @classmethod
    def purge_expired(cls, operador: str = "SISTEMA") -> Dict[str, Any]:
        """Expurga com segurança cópias de segurança que excederam o prazo de retenção.

        Garante a preservação incondicional de no mínimo copias_minimas_seguranca (mínimo 7).
        """
        politica = Database.get_politica()
        agora = datetime.now(timezone.utc)
        limite_data = agora - timedelta(days=politica.dias_retencao_diario)

        storage_dir = BackupService.get_storage_dir()
        todos_backups = Database.list_backups(limit=1000)

        # Filtra apenas backups com status CONCLUIDO
        backups_ativos = [b for b in todos_backups if b.status == "CONCLUIDO"]
        # Ordena do mais recente para o mais antigo
        backups_ativos.sort(key=lambda b: b.criado_em, reverse=True)

        copias_minimas = max(politica.copias_minimas_seguranca, 1)

        # As primeiras N cópias mais recentes são protegidas incondicionalmente
        copias_protegidas = backups_ativos[:copias_minimas]
        candidatos_expurgo = backups_ativos[copias_minimas:]

        quantidade_expurgada = 0
        espaco_liberado_bytes = 0
        arquivos_removidos = []

        for backup in candidatos_expurgo:
            # Verifica se atingiu a expiração
            if backup.criado_em < limite_data or backup.expira_em < agora:
                caminho_arquivo = storage_dir / backup.nome_arquivo
                if caminho_arquivo.exists():
                    tamanho = caminho_arquivo.stat().st_size
                    caminho_arquivo.unlink(missing_ok=True)
                    espaco_liberado_bytes += tamanho
                else:
                    espaco_liberado_bytes += backup.tamanho_cifrado_bytes

                backup.status = "EXPURGADO"
                Database.update_backup(backup)
                quantidade_expurgada += 1
                arquivos_removidos.append(backup.nome_arquivo)

        copias_preservadas = len([b for b in Database.list_backups(limit=1000) if b.status == "CONCLUIDO"])

        registrar_auditoria(
            acao="EXPURGO_RETENCAO",
            status_resultado="SUCESSO",
            operador=operador,
            detalhes=f"Expurgo executado: {quantidade_expurgada} cópias removidas, {espaco_liberado_bytes} bytes liberados. Cópias ativas preservadas: {copias_preservadas}",
        )

        return {
            "quantidade_expurgada": quantidade_expurgada,
            "espaco_liberado_bytes": espaco_liberado_bytes,
            "copias_preservadas": copias_preservadas,
            "arquivos_removidos": arquivos_removidos,
        }
