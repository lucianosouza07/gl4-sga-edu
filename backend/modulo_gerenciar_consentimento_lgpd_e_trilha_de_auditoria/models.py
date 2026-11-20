"""Modelos relacionais e definições de banco de dados para LGPD e Trilha de Auditoria."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TipoAcaoAuditoria(str, Enum):
    CRIACAO = "CRIACAO"
    ATUALIZACAO = "ATUALIZACAO"
    EXCLUSAO = "EXCLUSAO"
    CONSULTA_SENSIVEL = "CONSULTA_SENSIVEL"
    REVOGACAO_LGPD = "REVOGACAO_LGPD"
    FALHA_SEGURANCA = "FALHA_SEGURANCA"


@dataclass
class TermoConsentimentoModel:
    id_consentimento: Optional[int]
    usuario_id: int
    versao_termo: str
    finalidade: str
    aceito: bool
    data_aceite: datetime
    data_revogacao: Optional[datetime]
    ip_origem: str


@dataclass
class LogAuditoriaModel:
    id_auditoria: Optional[int]
    usuario_id: Optional[int]
    entidade_afetada: str
    id_registro_afetado: Optional[str]
    acao: str
    dados_anteriores: Optional[str]
    dados_novos: Optional[str]
    ip_origem: str
    data_hora: datetime


# DDL para criação das tabelas no SQLite / MySQL
CRIACAO_TABELA_CONSENTIMENTO_SQL = """
CREATE TABLE IF NOT EXISTS TermoConsentimentoLGPD (
    id_consentimento INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    versao_termo VARCHAR(20) NOT NULL,
    finalidade VARCHAR(120) NOT NULL,
    aceito BOOLEAN NOT NULL DEFAULT 1,
    data_aceite DATETIME NOT NULL,
    data_revogacao DATETIME NULL,
    ip_origem VARCHAR(45) NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);
"""

CRIACAO_TABELA_AUDITORIA_SQL = """
CREATE TABLE IF NOT EXISTS LogAuditoriaSistema (
    id_auditoria INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NULL,
    entidade_afetada VARCHAR(80) NOT NULL,
    id_registro_afetado VARCHAR(64) NULL,
    acao VARCHAR(50) NOT NULL,
    dados_anteriores TEXT NULL,
    dados_novos TEXT NULL,
    ip_origem VARCHAR(45) NOT NULL,
    data_hora DATETIME NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES Usuario(id_usuario) ON DELETE SET NULL
);
"""

CRIACAO_INDICES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_consentimento_usuario ON TermoConsentimentoLGPD(usuario_id, versao_termo);",
    "CREATE INDEX IF NOT EXISTS idx_consentimento_status ON TermoConsentimentoLGPD(usuario_id, finalidade, aceito);",
    "CREATE INDEX IF NOT EXISTS idx_auditoria_sis_usuario ON LogAuditoriaSistema(usuario_id);",
    "CREATE INDEX IF NOT EXISTS idx_auditoria_sis_data ON LogAuditoriaSistema(data_hora);",
    "CREATE INDEX IF NOT EXISTS idx_auditoria_sis_entidade ON LogAuditoriaSistema(entidade_afetada);",
]
