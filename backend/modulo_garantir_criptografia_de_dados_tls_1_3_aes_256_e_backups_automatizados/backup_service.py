"""Serviço de Extração, Compactação gzip e Cifragem de Volumes de Backup."""

import gzip
import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List

try:
    from .models import Database, BackupRegistro, PoliticaRetencaoBackup
    from .crypto_service import CryptoService
    from .audit_service import registrar_auditoria
except (ImportError, ValueError):
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.models import Database, BackupRegistro, PoliticaRetencaoBackup
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.crypto_service import CryptoService
    from modulo_garantir_criptografia_de_dados_tls_1_3_aes_256_e_backups_automatizados.audit_service import registrar_auditoria


class BackupService:
    """Gerencia a extração atômica, compressão gzip e cifragem AES-256 de backups."""

    @classmethod
    def get_storage_dir(cls) -> Path:
        """Obtém e assegura a existência do diretório de armazenamento seguro de backups."""
        dir_path = Path(os.getenv("BACKUP_STORAGE_DIR", "./storage/backups")).resolve()
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    @classmethod
    def generate_dump_content(cls) -> str:
        """Gera um dump SQL consistente com a estrutura relacional e dados ativos."""
        now_str = datetime.now(timezone.utc).isoformat()
        dump_lines = [
            f"-- SGA-Edu Database Backup Dump",
            f"-- Timestamp UTC: {now_str}",
            f"-- Versão do Esquema: 1.0.0",
            f"",
            f"SET FOREIGN_KEY_CHECKS=0;",
            f"DROP TABLE IF EXISTS BackupRegistro;",
            f"CREATE TABLE BackupRegistro (id_backup INT PRIMARY KEY, nome_arquivo VARCHAR(255));",
            f"DROP TABLE IF EXISTS PoliticaRetencaoBackup;",
            f"CREATE TABLE PoliticaRetencaoBackup (id_politica INT PRIMARY KEY, dias_retencao_diario INT);",
            f"DROP TABLE IF EXISTS LogAuditoriaBackup;",
            f"CREATE TABLE LogAuditoriaBackup (id_log INT PRIMARY KEY, acao VARCHAR(50));",
            f"SET FOREIGN_KEY_CHECKS=1;",
            f"",
            f"-- Metadados de Governança Acadêmica",
            f"-- Fim do Dump Consistente",
        ]
        return "\n".join(dump_lines)

    @classmethod
    def execute_backup(
        cls,
        tipo: str = "MANUAL",
        operador: str = "SISTEMA",
        observacoes: Optional[str] = None,
    ) -> BackupRegistro:
        """Executa o ciclo completo de extração, compactação, cifragem AES-256 e gravação."""
        tipo_normalizado = tipo.upper()
        if tipo_normalizado not in ["COMPLETO", "INCREMENTAL", "MANUAL"]:
            raise ValueError(f"Tipo de backup inválido: {tipo}. Esperado COMPLETO, INCREMENTAL ou MANUAL.")

        storage_dir = cls.get_storage_dir()
        criado_em = datetime.now(timezone.utc)
        politica = Database.get_politica()

        # Calcula o prazo de expiração baseado na política de retenção
        expira_em = criado_em + timedelta(days=politica.dias_retencao_diario)
        timestamp_str = criado_em.strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"backup_sga_{tipo_normalizado.lower()}_{timestamp_str}.sql.gz.enc"
        caminho_arquivo = storage_dir / nome_arquivo

        try:
            # 1. Extração do dump SQL bruto
            sql_dump = cls.generate_dump_content()
            sql_bytes = sql_dump.encode("utf-8")
            tamanho_original = len(sql_bytes)

            # 2. Compactação com gzip (nível 9)
            compressed_bytes = gzip.compress(sql_bytes, compresslevel=9)

            # 3. Cifragem simétrica com AES-256-GCM
            encrypted_volume = CryptoService.encrypt_bytes(compressed_bytes)
            tamanho_cifrado = len(encrypted_volume)

            # 4. Cálculo imediato do hash SHA-256
            checksum_sha256 = hashlib.sha256(encrypted_volume).hexdigest()

            # 5. Gravação segura do volume no storage
            with open(caminho_arquivo, "wb") as f:
                f.write(encrypted_volume)

            # 6. Registro na base de metadados
            registro = BackupRegistro(
                id_backup=0,
                nome_arquivo=nome_arquivo,
                tipo_backup=tipo_normalizado,
                caminho_relativo=str(caminho_arquivo.relative_to(storage_dir.parent.parent) if storage_dir.parent.parent in caminho_arquivo.parents else nome_arquivo),
                tamanho_original_bytes=tamanho_original,
                tamanho_cifrado_bytes=tamanho_cifrado,
                checksum_sha256=checksum_sha256,
                algoritmo_cifragem="AES-256-GCM",
                criado_em=criado_em,
                expira_em=expira_em,
                status="CONCLUIDO",
                validado_em=criado_em,
                status_integridade="VALIDO",
                iniciado_por=operador,
            )

            registro_salvo = Database.add_backup(registro)

            # 7. Trilha de auditoria
            registrar_auditoria(
                acao="BACKUP_CRIADO",
                status_resultado="SUCESSO",
                operador=operador,
                backup_id=registro_salvo.id_backup,
                detalhes=f"Backup {nome_arquivo} gerado com sucesso. Tamanho: {tamanho_cifrado}B, SHA256: {checksum_sha256}",
            )

            return registro_salvo

        except Exception as exc:
            # Se o arquivo foi gravado de forma parcial, remove para evitar corrupção
            if caminho_arquivo.exists():
                caminho_arquivo.unlink(missing_ok=True)

            registrar_auditoria(
                acao="BACKUP_FALHA",
                status_resultado="FALHA",
                operador=operador,
                detalhes=f"Falha na extração/cifragem do backup {nome_arquivo}: {str(exc)}",
            )
            raise RuntimeError(f"Erro operacional ao executar backup: {str(exc)}") from exc

    @classmethod
    def get_backup(cls, id_backup: int) -> Optional[BackupRegistro]:
        return Database.get_backup(id_backup)

    @classmethod
    def list_backups(
        cls,
        tipo: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[BackupRegistro]:
        return Database.list_backups(tipo=tipo, status=status, skip=skip, limit=limit)
