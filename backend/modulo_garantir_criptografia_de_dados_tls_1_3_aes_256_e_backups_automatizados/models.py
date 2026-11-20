"""Modelos de dados e repositório de persistência para Criptografia e Backups Automatizados."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class BackupRegistro:
    id_backup: int
    nome_arquivo: str
    tipo_backup: str  # COMPLETO, INCREMENTAL, MANUAL
    caminho_relativo: str
    tamanho_original_bytes: int
    tamanho_cifrado_bytes: int
    checksum_sha256: str
    criado_em: datetime
    expira_em: datetime
    algoritmo_cifragem: str = "AES-256-GCM"
    status: str = "GERANDO"  # GERANDO, CONCLUIDO, FALHO, EXPURGADO
    validado_em: Optional[datetime] = None
    status_integridade: str = "PENDENTE"  # PENDENTE, VALIDO, CORROMPIDO
    iniciado_por: str = "SISTEMA_SCHEDULER"


@dataclass
class PoliticaRetencaoBackup:
    id_politica: int
    frequencia_cron: str = "0 3 * * *"
    dias_retencao_diario: int = 30
    meses_retencao_mensal: int = 12
    copias_minimas_seguranca: int = 7
    compactacao_habilitada: bool = True
    cifragem_habilitada: bool = True
    atualizado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    atualizado_por: Optional[str] = "ADMIN"


@dataclass
class LogAuditoriaBackup:
    id_log: int
    data_hora: datetime
    operador: str
    ip_origem: str
    acao: str
    status_resultado: str  # SUCESSO, FALHA, ALERTA
    backup_id: Optional[int] = None
    detalhes: Optional[str] = None


class Database:
    """Repositório de persistência em memória thread-safe simulando o banco de dados relacional."""

    backups: Dict[int, BackupRegistro] = {}
    politica: Optional[PoliticaRetencaoBackup] = None
    auditoria: List[LogAuditoriaBackup] = []
    _next_backup_id: int = 1
    _next_log_id: int = 1

    @classmethod
    def reset(cls):
        """Reinicializa o repositório de persistência para os padrões iniciais."""
        cls.backups.clear()
        cls.auditoria.clear()
        cls._next_backup_id = 1
        cls._next_log_id = 1
        cls.politica = PoliticaRetencaoBackup(
            id_politica=1,
            frequencia_cron="0 3 * * *",
            dias_retencao_diario=30,
            meses_retencao_mensal=12,
            copias_minimas_seguranca=7,
            compactacao_habilitada=True,
            cifragem_habilitada=True,
            atualizado_em=datetime.now(timezone.utc),
            atualizado_por="SISTEMA_INICIAL",
        )

    @classmethod
    def add_backup(cls, backup: BackupRegistro) -> BackupRegistro:
        if backup.id_backup is None or backup.id_backup <= 0:
            backup.id_backup = cls._next_backup_id
            cls._next_backup_id += 1
        cls.backups[backup.id_backup] = backup
        return backup

    @classmethod
    def get_backup(cls, id_backup: int) -> Optional[BackupRegistro]:
        return cls.backups.get(id_backup)

    @classmethod
    def list_backups(
        cls,
        tipo: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[BackupRegistro]:
        items = list(cls.backups.values())
        if tipo:
            items = [b for b in items if b.tipo_backup.upper() == tipo.upper()]
        if status:
            items = [b for b in items if b.status.upper() == status.upper()]
        # Ordena do mais recente para o mais antigo
        items.sort(key=lambda b: b.criado_em, reverse=True)
        return items[skip : skip + limit]

    @classmethod
    def update_backup(cls, backup: BackupRegistro) -> BackupRegistro:
        cls.backups[backup.id_backup] = backup
        return backup

    @classmethod
    def add_log(
        cls,
        acao: str,
        status_resultado: str,
        operador: str = "SISTEMA",
        ip_origem: str = "127.0.0.1",
        backup_id: Optional[int] = None,
        detalhes: Optional[str] = None,
    ) -> LogAuditoriaBackup:
        log = LogAuditoriaBackup(
            id_log=cls._next_log_id,
            data_hora=datetime.now(timezone.utc),
            operador=operador,
            ip_origem=ip_origem,
            acao=acao,
            status_resultado=status_resultado,
            backup_id=backup_id,
            detalhes=detalhes,
        )
        cls._next_log_id += 1
        cls.auditoria.append(log)
        return log

    @classmethod
    def get_politica(cls) -> PoliticaRetencaoBackup:
        if cls.politica is None:
            cls.reset()
        return cls.politica

    @classmethod
    def update_politica(cls, politica: PoliticaRetencaoBackup) -> PoliticaRetencaoBackup:
        politica.atualizado_em = datetime.now(timezone.utc)
        cls.politica = politica
        return cls.politica


# Inicialização inicial automática do repositório
Database.reset()
