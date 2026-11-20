"""Repositório de persistência relacional para TermoConsentimentoLGPD e LogAuditoriaSistema."""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    CRIACAO_INDICES_SQL,
    CRIACAO_TABELA_AUDITORIA_SQL,
    CRIACAO_TABELA_CONSENTIMENTO_SQL,
)


class LgpdAuditRepository:
    """Gerencia a persistência relacional para termos de consentimento LGPD e logs imutáveis."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False,
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        with conn:
            # Tabela mock de Usuario para integridade referencial em testes
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS Usuario (
                    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                    login VARCHAR(100) NOT NULL UNIQUE,
                    perfil_RBAC INTEGER NOT NULL DEFAULT 1,
                    statusCONTA INTEGER NOT NULL DEFAULT 1
                );
                """
            )
            conn.execute(CRIACAO_TABELA_CONSENTIMENTO_SQL)
            conn.execute(CRIACAO_TABELA_AUDITORIA_SQL)
            for idx_sql in CRIACAO_INDICES_SQL:
                conn.execute(idx_sql)

    def fechar(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # --- Operações de Mock de Usuário para Testes e RBAC ---

    def criar_usuario(
        self,
        login: str,
        perfil_RBAC: int = 1,
        statusCONTA: int = 1,
        usuario_id: Optional[int] = None,
    ) -> int:
        conn = self._get_connection()
        with conn:
            if usuario_id is not None:
                cursor = conn.execute(
                    "INSERT INTO Usuario (id_usuario, login, perfil_RBAC, statusCONTA) VALUES (?, ?, ?, ?)",
                    (usuario_id, login, perfil_RBAC, statusCONTA),
                )
            else:
                cursor = conn.execute(
                    "INSERT INTO Usuario (login, perfil_RBAC, statusCONTA) VALUES (?, ?, ?)",
                    (login, perfil_RBAC, statusCONTA),
                )
            return cursor.lastrowid

    def buscar_usuario_por_id(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.execute("SELECT * FROM Usuario WHERE id_usuario = ?", (usuario_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    # --- Operações de Consentimento LGPD ---

    def registrar_consentimento(
        self,
        usuario_id: int,
        versao_termo: str,
        finalidade: str,
        aceito: bool,
        ip_origem: str,
        data_aceite: datetime,
        data_revogacao: Optional[datetime] = None,
    ) -> int:
        conn = self._get_connection()
        with conn:
            # Se já houver um consentimento anterior da mesma versão e finalidade, atualizamos ou inserimos
            cur = conn.execute(
                """
                SELECT id_consentimento FROM TermoConsentimentoLGPD
                WHERE usuario_id = ? AND versao_termo = ? AND finalidade = ?
                ORDER BY id_consentimento DESC LIMIT 1
                """,
                (usuario_id, versao_termo, finalidade),
            )
            existente = cur.fetchone()
            if existente:
                conn.execute(
                    """
                    UPDATE TermoConsentimentoLGPD
                    SET aceito = ?, data_aceite = ?, data_revogacao = ?, ip_origem = ?
                    WHERE id_consentimento = ?
                    """,
                    (
                        1 if aceito else 0,
                        data_aceite.isoformat(),
                        data_revogacao.isoformat() if data_revogacao else None,
                        ip_origem,
                        existente["id_consentimento"],
                    ),
                )
                return existente["id_consentimento"]
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO TermoConsentimentoLGPD
                    (usuario_id, versao_termo, finalidade, aceito, data_aceite, data_revogacao, ip_origem)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        usuario_id,
                        versao_termo,
                        finalidade,
                        1 if aceito else 0,
                        data_aceite.isoformat(),
                        data_revogacao.isoformat() if data_revogacao else None,
                        ip_origem,
                    ),
                )
                return cursor.lastrowid

    def revogar_consentimento(
        self,
        usuario_id: int,
        versao_termo: str,
        finalidade: str,
        ip_origem: str,
        data_revogacao: datetime,
    ) -> bool:
        """Aplica soft revocation mantendo o registro histórico íntegro."""
        conn = self._get_connection()
        with conn:
            cur = conn.execute(
                """
                UPDATE TermoConsentimentoLGPD
                SET aceito = 0, data_revogacao = ?, ip_origem = ?
                WHERE usuario_id = ? AND versao_termo = ? AND finalidade = ? AND aceito = 1
                """,
                (data_revogacao.isoformat(), ip_origem, usuario_id, versao_termo, finalidade),
            )
            return cur.rowcount > 0

    def buscar_consentimentos_ativos(self, usuario_id: int, versao_termo: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT * FROM TermoConsentimentoLGPD
            WHERE usuario_id = ? AND versao_termo = ? AND aceito = 1
            """,
            (usuario_id, versao_termo),
        )
        return [dict(row) for row in cur.fetchall()]

    def listar_historico_consentimentos(self, usuario_id: int) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT * FROM TermoConsentimentoLGPD
            WHERE usuario_id = ?
            ORDER BY data_aceite DESC, id_consentimento DESC
            """,
            (usuario_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    # --- Operações de Trilha Imutável de Auditoria (Append-Only) ---

    def inserir_log_auditoria(
        self,
        usuario_id: Optional[int],
        entidade_afetada: str,
        id_registro_afetado: Optional[str],
        acao: str,
        dados_anteriores: Optional[str],
        dados_novos: Optional[str],
        ip_origem: str,
        data_hora: datetime,
    ) -> int:
        """Insere um novo evento imutável na trilha de auditoria."""
        conn = self._get_connection()
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO LogAuditoriaSistema
                (usuario_id, entidade_afetada, id_registro_afetado, acao, dados_anteriores, dados_novos, ip_origem, data_hora)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    usuario_id,
                    entidade_afetada,
                    id_registro_afetado,
                    acao,
                    dados_anteriores,
                    dados_novos,
                    ip_origem,
                    data_hora.isoformat(),
                ),
            )
            return cursor.lastrowid

    def atualizar_log_auditoria(self, *args, **kwargs):
        raise RuntimeError("Operações de atualização são proibidas na trilha imutável de auditoria.")

    def excluir_log_auditoria(self, *args, **kwargs):
        raise RuntimeError("Operações de exclusão são proibidas na trilha imutável de auditoria.")

    def buscar_log_por_id(self, id_auditoria: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT * FROM LogAuditoriaSistema WHERE id_auditoria = ?",
            (id_auditoria,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def consultar_logs_auditoria(
        self,
        usuario_id: Optional[int] = None,
        entidade_afetada: Optional[str] = None,
        acao: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        limite: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[Dict[str, Any]]]:
        conn = self._get_connection()
        clausulas = []
        parametros = []

        if usuario_id is not None:
            clausulas.append("usuario_id = ?")
            parametros.append(usuario_id)
        if entidade_afetada:
            clausulas.append("entidade_afetada = ?")
            parametros.append(entidade_afetada)
        if acao:
            clausulas.append("acao = ?")
            parametros.append(acao)
        if data_inicio:
            clausulas.append("data_hora >= ?")
            parametros.append(data_inicio)
        if data_fim:
            clausulas.append("data_hora <= ?")
            parametros.append(data_fim)

        where_sql = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""

        # Total count
        cur_total = conn.execute(f"SELECT COUNT(*) as total FROM LogAuditoriaSistema {where_sql}", parametros)
        total = cur_total.fetchone()["total"]

        # Paged rows
        sql = f"""
            SELECT * FROM LogAuditoriaSistema
            {where_sql}
            ORDER BY data_hora DESC, id_auditoria DESC
            LIMIT ? OFFSET ?
        """
        cur = conn.execute(sql, (*parametros, limite, offset))
        itens = [dict(row) for row in cur.fetchall()]

        return total, itens
